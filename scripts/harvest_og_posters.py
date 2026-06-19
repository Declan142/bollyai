#!/usr/bin/env python3
"""Harvest official platform og:image key-art for series missing a poster on disk.

Cheap, keyless coverage extension to the Wikipedia-first harvester. For each series
with no poster.jpg, resolve its Netflix title id from Wikidata (P1874), pull the
official og:image (nflxso.net key-art, a whitelisted source), center-crop to 2:3,
and write an attributed poster + manifest.

Key-art is landscape by design, so the engine's portrait gate is relaxed here; a
raw-size floor + official-host check + attribution manifest are still enforced.
Only the Netflix path is wired (Hotstar is a JS SPA with no server og:image;
official sites mostly host off non-whitelisted CDNs).
"""
from __future__ import annotations

import io
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import urllib.request

from PIL import Image

from engine.fetchers.image_harvester import (
    SITE_PUBLIC,
    _manifest_payload,
    _series_poster_path,
    crop_2x3,
    fetch_image_bytes,
    load_series_files,
    qid_value,
)
from engine.fetchers.common import write_json

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
import re

OG_RE = re.compile(r'og:image["\'][^>]+content=["\']([^"\']+)', re.I)


def _http(url: str) -> str | None:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        return urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "ignore")
    except Exception:
        return None


def _wikidata_netflix_ids(qids: list[str]) -> dict[str, str]:
    out: dict[str, str] = {}
    for i in range(0, len(qids), 45):
        chunk = qids[i : i + 45]
        url = (
            "https://www.wikidata.org/w/api.php?action=wbgetentities&props=claims&format=json&ids="
            + "|".join(chunk)
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "BollyAI-og/1 (bollyai.in)"})
            ent = json.loads(urllib.request.urlopen(req, timeout=30).read()).get("entities", {})
        except Exception:
            continue
        for q in chunk:
            cl = ent.get(q, {}).get("claims", {})
            if "P1874" in cl:
                try:
                    out[q] = cl["P1874"][0]["mainsnak"]["datavalue"]["value"]
                except Exception:
                    pass
        time.sleep(0.2)
    return out


def harvest_one(slug: str, series: dict, netflix_id: str) -> dict:
    out_path = _series_poster_path(slug)
    if out_path.exists():
        return {"slug": slug, "status": "skip", "reason": "poster_exists"}
    page = f"https://www.netflix.com/title/{netflix_id}"
    html = _http(page)
    if not html:
        return {"slug": slug, "status": "fail", "reason": "page_unreachable"}
    m = OG_RE.search(html)
    if not m:
        return {"slug": slug, "status": "fail", "reason": "no_og_image"}
    img_url = m.group(1)
    if "nflxso.net" not in img_url and "netflix" not in img_url:
        return {"slug": slug, "status": "fail", "reason": "og_not_official_host"}
    raw = fetch_image_bytes(img_url)
    if not raw:
        return {"slug": slug, "status": "fail", "reason": "image_fetch_failed"}
    try:
        image = Image.open(io.BytesIO(raw))
    except Exception as exc:
        return {"slug": slug, "status": "fail", "reason": f"decode_{exc.__class__.__name__}"}
    w, h = image.size
    if w < 500 or h < 280:  # key-art floor (landscape); 2:3 crop yields >= 480x720 from this
        return {"slug": slug, "status": "fail", "reason": f"too_small_{w}x{h}"}
    poster = crop_2x3(image)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    poster.save(out_path, "JPEG", quality=88, optimize=True)
    candidate = {
        "source_type": "platform_press_kit",
        "source_name": "Netflix key art",
        "credit": "Netflix",
        "url": img_url,
        "page_url": page,
    }
    attribution = (
        (series.get("poster") or {}).get("attribution")
        or f"Key art © Netflix. Used for criticism and review under fair dealing "
        f"(Sec 52(1)(a)). Takedown: bollyai.in/takedown"
    )
    manifest = _manifest_payload(
        slug=slug,
        kind="series-poster",
        candidate=candidate,
        poster_path=out_path,
        source_width=w,
        source_height=h,
        attribution_line=attribution,
    )
    write_json(out_path.parent / "manifest.json", manifest)
    return {"slug": slug, "status": "ok", "source": "netflix_og", "size": f"{w}x{h}"}


def main() -> int:
    files = load_series_files()
    missing = []
    for slug, path in files.items():
        if not _series_poster_path(slug).exists():
            series = json.loads(path.read_text())
            q = qid_value(series)
            if q:
                missing.append((slug, series, q))
    print(f"missing-on-disk with QID: {len(missing)}", flush=True)
    nf = _wikidata_netflix_ids([q for _, _, q in missing])
    targets = [(s, ser, nf[q]) for s, ser, q in missing if q in nf]
    print(f"resolvable via Netflix og: {len(targets)}", flush=True)
    results = []
    for slug, series, nfid in targets:
        r = harvest_one(slug, series, nfid)
        results.append(r)
        print(f"{r['status'].upper():4} {slug} {r.get('reason') or r.get('size','')}", flush=True)
        time.sleep(0.3)
    ok = sum(1 for r in results if r["status"] == "ok")
    print(f"\nDONE ok={ok} fail={sum(1 for r in results if r['status']=='fail')} "
          f"skip={sum(1 for r in results if r['status']=='skip')}", flush=True)
    write_json(ROOT / "data/_state/og-poster-sweep.json",
               {"ok": ok, "total": len(targets), "results": results})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
