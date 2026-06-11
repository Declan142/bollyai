"""Official-only image harvester for BollyAI.

The v2 posture is strict:
* TMDB, IMDb, JustWatch, Letterboxd, social mirrors, stock sites, and
  watermarked paparazzi sources are rejected.
* Served images are self-hosted local files.
* Every v2 write emits a manifest beside the image with source name, source URL,
  attribution, and takedown policy.

Series poster harvesting follows the blueprint chain:
Wikipedia REST lead image, official page og:image, Wikipedia page og:image,
then the Wikipedia infobox image.
"""

from __future__ import annotations

import argparse
import io
import json
import re
import sys
import time
from functools import lru_cache
from pathlib import Path
from typing import Any
from urllib.parse import quote, unquote, urljoin, urlparse

try:
    import requests
except ImportError:  # pragma: no cover - dry runs can still validate candidates.
    requests = None

try:
    from PIL import Image
except ImportError:  # pragma: no cover - expected in stdlib-only installs.
    Image = None

try:
    from .common import FIXTURE_DIR, REPO_ROOT, read_json, repo_path, stable_unique, utc_now, write_json
except ImportError:  # pragma: no cover - direct script execution.
    from common import FIXTURE_DIR, REPO_ROOT, read_json, repo_path, stable_unique, utc_now, write_json


IMAGE_USER_AGENT = (
    "BollyAI-image-harvester/2.0 "
    "(https://bollyai.in; takedown@bollyai.in) editorial-fair-dealing"
)

SITE_PUBLIC = REPO_ROOT / "site" / "public"
SERIES_DATA_DIR = REPO_ROOT / "data" / "series"
SERIES_IMAGE_ROOT = SITE_PUBLIC / "img" / "series"
FILM_IMAGE_ROOT = SITE_PUBLIC / "img" / "films"

POSTER_TARGET = (500, 750)
VARIANT_WIDTHS = (185, 342, 500)

ALLOWED_SOURCE_TYPES = {
    "studio_press_kit",
    "official_og_image",
    "youtube_official_trailer_thumbnail",
    "platform_press_kit",
    "wikipedia_rest_lead_image",
    "wikipedia_page_og_image",
    "wikipedia_infobox_image",
}

OFFICIAL_HOST_HINTS = (
    "wikipedia.org",
    "wikimedia.org",
    "youtube.com",
    "ytimg.com",
    "netflix.com",
    "nflxso.net",
    "primevideo.com",
    "aboutamazon.",
    "media-amazon.com",
    "hotstar.com",
    "jiocinema.com",
    "zee5.com",
    "sonyliv.com",
    "aha.video",
    "sunnxt.com",
    "lionsgateplay.com",
    "apple.com",
    "hbo.com",
    "max.com",
    "disney.com",
    "disneyplus.com",
    "fxnetworks.com",
    "paramount",
    "peacocktv.com",
    "press",
    "media",
    "studio",
    "pictures",
    "films",
)

REJECT_HINTS = (
    "paparazzi",
    "watermark",
    "watermarked",
    "getty",
    "shutterstock",
    "alamy",
    "pinterest",
    "reddit",
    "instagram.com",
    "facebook.com",
    "x.com",
    "twitter.com",
    "fanpage",
)

BANNED_HOST_HINTS = (
    "tmdb.org",
    "themoviedb.org",
    "image.tmdb.org",
    "justwatch.",
    "imdb.com",
    "letterboxd.com",
)


def _host(url: str) -> str:
    return urlparse(url).netloc.lower()


def _candidate_haystack(candidate: dict[str, Any]) -> str:
    url = str(candidate.get("url") or "").lower()
    page_url = str(candidate.get("page_url") or "").lower()
    return " ".join((url, _host(url), page_url, _host(page_url)))


def validate_candidate(candidate: dict[str, Any]) -> dict[str, Any]:
    url = str(candidate.get("url") or "")
    source_type = str(candidate.get("source_type") or "")
    haystack = _candidate_haystack(candidate)
    reasons = []

    if not url.startswith(("https://", "http://")):
        reasons.append("not_http_url")
    if source_type not in ALLOWED_SOURCE_TYPES:
        reasons.append("source_type_not_official")
    if any(hint in haystack for hint in BANNED_HOST_HINTS):
        reasons.append("banned_source_host")
    if any(hint in haystack for hint in REJECT_HINTS):
        reasons.append("rejected_host_or_watermark_hint")
    if url.lower().split("?", 1)[0].endswith(".svg"):
        reasons.append("svg_not_served_as_poster")
    if not any(hint in haystack for hint in OFFICIAL_HOST_HINTS):
        reasons.append("no_official_host_hint")

    return {
        "candidate": candidate,
        "accepted": not reasons,
        "reasons": reasons,
    }


def _get(url: str, *, accept: str = "*/*", timeout: int = 30):
    if requests is None:
        return None
    return requests.get(
        url,
        headers={"User-Agent": IMAGE_USER_AGENT, "Accept": accept},
        timeout=timeout,
    )


def fetch_image_bytes(url: str) -> bytes | None:
    response = _get(url, accept="image/avif,image/webp,image/png,image/jpeg,image/*")
    if response is None or response.status_code >= 400:
        return None
    content_type = response.headers.get("Content-Type", "").split(";", 1)[0].lower()
    lower_url = url.lower().split("?", 1)[0]
    if content_type == "image/svg+xml" or lower_url.endswith(".svg"):
        return None
    if not content_type.startswith("image/") and not re.search(r"\.(jpe?g|png|webp|avif)$", lower_url):
        return None
    return response.content


def crop_2x3(image: Any, target: tuple[int, int] = POSTER_TARGET) -> Any:
    image = image.convert("RGB")
    width, height = image.size
    target_width, target_height = target
    scale = max(target_width / width, target_height / height)
    resized_width = int(width * scale + 0.5)
    resized_height = int(height * scale + 0.5)
    image = image.resize((resized_width, resized_height), Image.LANCZOS)
    left = (resized_width - target_width) // 2
    top = (resized_height - target_height) // 3
    return image.crop((left, top, left + target_width, top + target_height))


def _usable_poster_image(image: Any) -> tuple[bool, str | None]:
    width, height = image.size
    if width < 160 or height < 240:
        return False, "image_too_small"
    if height < width * 1.05:
        return False, "not_portrait_poster"
    return True, None


def _manifest_payload(
    *,
    slug: str,
    kind: str,
    candidate: dict[str, Any],
    poster_path: Path,
    source_width: int,
    source_height: int,
    attribution_line: str | None,
) -> dict[str, Any]:
    source_name = candidate.get("source_name") or candidate.get("credit") or "official image source"
    source_url = candidate["url"]
    return {
        "schema": "bollyai-image-harvest/v2",
        "slug": slug,
        "kind": kind,
        "generated_at": utc_now(),
        "source": {
            "name": source_name,
            "url": source_url,
            "page_url": candidate.get("page_url"),
            "type": candidate.get("source_type"),
        },
        "attribution": {
            "line": attribution_line or build_attribution_line(candidate),
            "source_name": source_name,
            "source_url": source_url,
            "takedown_url": "https://bollyai.in/takedown/",
        },
        "poster": {
            "path": "/" + str(poster_path.relative_to(SITE_PUBLIC)),
            "width": POSTER_TARGET[0],
            "height": POSTER_TARGET[1],
            "source_width": source_width,
            "source_height": source_height,
        },
        "policy": {
            "served_image": "self_hosted",
            "allowed_chain": "official press, official og:image, official trailer still, Wikipedia lead or infobox image",
            "rejected_sources": ["tmdb", "justwatch", "imdb", "letterboxd", "stock", "social_mirrors"],
        },
        "variants": [],
    }


def write_variants(
    *,
    slug: str,
    image_bytes: bytes,
    source_url: str,
    output_root: Path = FILM_IMAGE_ROOT,
) -> dict[str, Any]:
    output_dir = output_root / slug
    if Image is None:
        return {
            "slug": slug,
            "source_url": source_url,
            "pil_available": False,
            "variants": [],
            "degraded": True,
            "reason": "Pillow unavailable; image variant generation skipped.",
        }

    output_dir.mkdir(parents=True, exist_ok=True)
    image = Image.open(io.BytesIO(image_bytes))
    variants = []
    for width in VARIANT_WIDTHS:
        copy = image.copy()
        height = max(1, round(copy.height * (width / copy.width)))
        copy = copy.resize((width, height), Image.LANCZOS)
        for extension, pil_format in (("webp", "WEBP"), ("avif", "AVIF")):
            path = output_dir / f"w{width}.{extension}"
            try:
                copy.save(path, format=pil_format, quality=82)
            except Exception as exc:  # Pillow builds commonly lack AVIF.
                variants.append({"width": width, "format": pil_format, "skipped": True, "reason": exc.__class__.__name__})
                continue
            variants.append({"width": width, "format": pil_format, "path": "/" + str(path.relative_to(SITE_PUBLIC))})
    manifest = {
        "schema": "bollyai-image-harvest/v1",
        "slug": slug,
        "source_url": source_url,
        "generated_at": utc_now(),
        "pil_available": True,
        "variants": variants,
    }
    write_json(output_dir / "manifest.json", manifest)
    return manifest


def harvest_candidates(
    *,
    slug: str,
    candidates: list[dict[str, Any]],
    write: bool = False,
) -> dict[str, Any]:
    checked = [validate_candidate(candidate) for candidate in candidates]
    accepted = [item["candidate"] for item in checked if item["accepted"]]
    manifest: dict[str, Any] | None = None
    if write and accepted:
        first = accepted[0]
        image_bytes = fetch_image_bytes(first["url"])
        if image_bytes is None:
            manifest = {
                "slug": slug,
                "source_url": first["url"],
                "degraded": True,
                "reason": "Image fetch unavailable or failed.",
                "variants": [],
            }
        else:
            manifest = write_variants(slug=slug, image_bytes=image_bytes, source_url=first["url"])
    return {
        "schema": "bollyai-image-harvest-check/v1",
        "slug": slug,
        "checked_at": utc_now(),
        "accepted_count": len(accepted),
        "checks": checked,
        "manifest": manifest,
        "attribution_line": build_attribution_line(accepted[0]) if accepted else None,
    }


def build_attribution_line(candidate: dict[str, Any]) -> str:
    credit = candidate.get("credit") or candidate.get("source_name") or "official source"
    return (
        f"Image via {credit}. Used for criticism and review under fair dealing "
        f"(Sec 52(1)(a)). Takedown: bollyai.in/takedown"
    )


def load_fixture_candidates(slug: str) -> list[dict[str, Any]]:
    fixture = read_json(FIXTURE_DIR / "image_candidates.json", default={"films": {}})
    return fixture.get("films", {}).get(slug, [])


def wiki_title(series: dict[str, Any]) -> str:
    url = (series.get("renewal") or {}).get("source_url", "") or ""
    match = re.search(r"/wiki/([^#?]+)", url)
    if match and "wikipedia.org" in url:
        return unquote(match.group(1))
    return str((series.get("title") or {}).get("value") or series.get("slug") or "").replace(" ", "_")


def qid_value(series: dict[str, Any]) -> str | None:
    qid = series.get("qid")
    if isinstance(qid, dict):
        qid = qid.get("value")
    if isinstance(qid, str) and re.fullmatch(r"Q\d+", qid):
        return qid
    return None


@lru_cache(maxsize=2048)
def wikidata_enwiki_title(qid: str) -> str | None:
    response = _get(
        f"https://www.wikidata.org/wiki/Special:EntityData/{qid}.json",
        accept="application/json",
        timeout=20,
    )
    if response is None or response.status_code != 200:
        return None
    entity = response.json().get("entities", {}).get(qid, {})
    title = ((entity.get("sitelinks") or {}).get("enwiki") or {}).get("title")
    if not title:
        return None
    return str(title).replace(" ", "_")


def series_title_candidates(series: dict[str, Any]) -> list[str]:
    title = str((series.get("title") or {}).get("value") or "").replace(" ", "_")
    guesses = [
        f"{title}_(TV_series)",
        f"{title}_(television_series)",
        f"{title}_(web_series)",
        f"{title}_(Indian_TV_series)",
        f"{title}_(Indian_web_series)",
    ] if title else []
    qid_title = wikidata_enwiki_title(qid_value(series)) if qid_value(series) else None
    return stable_unique([qid_title, wiki_title(series), *guesses, title])


def _wikipedia_page_url(title: str) -> str:
    return "https://en.wikipedia.org/wiki/" + quote(title, safe="")


@lru_cache(maxsize=4096)
def wikipedia_summary_payload(title: str) -> tuple[dict[str, Any] | None, str | None]:
    api = "https://en.wikipedia.org/api/rest_v1/page/summary/" + quote(title, safe="")
    response = _get(api, accept="application/json")
    if response is None:
        return None, "requests_unavailable"
    if response.status_code != 200:
        return None, f"summary_{response.status_code}"
    return response.json(), None


def _summary_looks_like_series(payload: dict[str, Any]) -> bool:
    text = " ".join((
        str(payload.get("title") or ""),
        str(payload.get("description") or ""),
        str(payload.get("extract") or ""),
    )).lower()
    series_terms = (
        "television series",
        "tv series",
        "web series",
        "streaming television",
        "miniseries",
        "mini-series",
        "anime television",
        "drama series",
        "comedy series",
        "sitcom",
        "serial",
        "television show",
    )
    return any(term in text for term in series_terms)


def wikipedia_page_matches_series(title: str, expected_qid: str | None) -> tuple[bool, str | None]:
    payload, reason = wikipedia_summary_payload(title)
    if not payload:
        return False, reason
    if expected_qid and payload.get("wikibase_item") != expected_qid:
        return False, "wiki_qid_mismatch"
    if not expected_qid and not _summary_looks_like_series(payload):
        return False, "wiki_page_not_series"
    return True, None


def wikipedia_summary_candidate(title: str, expected_qid: str | None = None) -> tuple[dict[str, Any] | None, str | None]:
    matches, reason = wikipedia_page_matches_series(title, expected_qid)
    if not matches:
        return None, reason
    payload, _ = wikipedia_summary_payload(title)
    if not payload:
        return None, "summary_unavailable"
    image = (payload.get("originalimage") or {}).get("source") or (payload.get("thumbnail") or {}).get("source")
    if not image:
        return None, "summary_no_image"
    page_url = ((payload.get("content_urls") or {}).get("desktop") or {}).get("page") or _wikipedia_page_url(title)
    return {
        "source_type": "wikipedia_rest_lead_image",
        "source_name": "Wikipedia REST summary lead image",
        "credit": "Wikipedia REST summary lead image",
        "url": image,
        "page_url": page_url,
        "title": title,
    }, None


def _parse_og_image(html: str, page_url: str) -> str | None:
    patterns = (
        r"<meta[^>]+(?:property|name)=[\"']og:image[\"'][^>]+content=[\"']([^\"']+)[\"']",
        r"<meta[^>]+content=[\"']([^\"']+)[\"'][^>]+(?:property|name)=[\"']og:image[\"']",
    )
    for pattern in patterns:
        match = re.search(pattern, html, flags=re.I)
        if match:
            return urljoin(page_url, match.group(1))
    return None


def _official_page_url(url: str) -> bool:
    haystack = f"{url.lower()} {_host(url)}"
    if any(hint in haystack for hint in BANNED_HOST_HINTS + REJECT_HINTS):
        return False
    return any(hint in haystack for hint in OFFICIAL_HOST_HINTS) and "wikipedia.org" not in haystack


def official_og_candidates(series: dict[str, Any]) -> list[dict[str, Any]]:
    urls = stable_unique([(series.get("renewal") or {}).get("source_url")])
    candidates: list[dict[str, Any]] = []
    for page_url in urls:
        if not page_url or not _official_page_url(page_url):
            continue
        response = _get(page_url, accept="text/html")
        if response is None or response.status_code != 200:
            continue
        image = _parse_og_image(response.text, page_url)
        if not image:
            continue
        host = _host(page_url).replace("www.", "")
        candidates.append({
            "source_type": "official_og_image",
            "source_name": f"{host} og:image",
            "credit": host,
            "url": image,
            "page_url": page_url,
        })
    return candidates


def wikipedia_og_candidate(title: str, expected_qid: str | None = None) -> tuple[dict[str, Any] | None, str | None]:
    matches, reason = wikipedia_page_matches_series(title, expected_qid)
    if not matches:
        return None, reason
    page_url = _wikipedia_page_url(title)
    response = _get(page_url, accept="text/html")
    if response is None:
        return None, "requests_unavailable"
    if response.status_code != 200:
        return None, f"wiki_page_{response.status_code}"
    image = _parse_og_image(response.text, page_url)
    if not image:
        return None, "wiki_page_no_og_image"
    return {
        "source_type": "wikipedia_page_og_image",
        "source_name": "Wikipedia page og:image",
        "credit": "Wikipedia page og:image",
        "url": image,
        "page_url": page_url,
        "title": title,
    }, None


def _wikitext(title: str) -> str:
    api = "https://en.wikipedia.org/w/api.php"
    response = _get(
        api
        + "?"
        + "&".join((
            "action=query",
            "prop=revisions",
            "rvprop=content",
            "rvslots=main",
            "format=json",
            "redirects=1",
            "titles=" + quote(title, safe=""),
        )),
        accept="application/json",
    )
    if response is None or response.status_code != 200:
        return ""
    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        try:
            return page["revisions"][0]["slots"]["main"]["*"]
        except (KeyError, IndexError, TypeError):
            continue
    return ""


def _infobox_image_filename(wikitext: str) -> str | None:
    patterns = (
        r"\|\s*image\s*=\s*\[\[\s*(?:[Ff]ile|[Ii]mage):([^\|\]\n]+)",
        r"\|\s*image\s*=\s*([^\|\[\]\n<]+?\.(?:jpg|jpeg|png|webp))",
    )
    for pattern in patterns:
        match = re.search(pattern, wikitext)
        if match:
            return match.group(1).strip()
    return None


def _file_image_candidate(filename: str, title: str) -> dict[str, Any] | None:
    api = "https://en.wikipedia.org/w/api.php"
    response = _get(
        api
        + "?"
        + "&".join((
            "action=query",
            "prop=imageinfo",
            "iiprop=url|size|mime",
            "format=json",
            "titles=File:" + quote(filename, safe=""),
        )),
        accept="application/json",
    )
    if response is None or response.status_code != 200:
        return None
    pages = response.json().get("query", {}).get("pages", {})
    for page in pages.values():
        info = (page.get("imageinfo") or [{}])[0]
        url = info.get("url")
        if not url:
            continue
        return {
            "source_type": "wikipedia_infobox_image",
            "source_name": "Wikipedia infobox image",
            "credit": "Wikipedia infobox image",
            "url": url,
            "page_url": _wikipedia_page_url(title),
            "title": title,
            "filename": filename,
            "width": info.get("width"),
            "height": info.get("height"),
            "mime": info.get("mime"),
        }
    return None


def wikipedia_infobox_candidate(title: str, expected_qid: str | None = None) -> tuple[dict[str, Any] | None, str | None]:
    matches, reason = wikipedia_page_matches_series(title, expected_qid)
    if not matches:
        return None, reason
    filename = _infobox_image_filename(_wikitext(title))
    if not filename:
        return None, "infobox_no_image"
    candidate = _file_image_candidate(filename, title)
    if not candidate:
        return None, "infobox_no_url"
    return candidate, None


def series_candidate_chain(series: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    candidates: list[dict[str, Any]] = []
    notes: list[str] = []
    titles = series_title_candidates(series)
    expected_qid = qid_value(series)

    for title in titles:
        candidate, reason = wikipedia_summary_candidate(title, expected_qid)
        if candidate:
            candidates.append(candidate)
        elif reason:
            notes.append(f"{title}: {reason}")

    candidates.extend(official_og_candidates(series))

    for title in titles:
        candidate, reason = wikipedia_og_candidate(title, expected_qid)
        if candidate:
            candidates.append(candidate)
        elif reason:
            notes.append(f"{title}: {reason}")

    for title in titles:
        candidate, reason = wikipedia_infobox_candidate(title, expected_qid)
        if candidate:
            candidates.append(candidate)
        elif reason:
            notes.append(f"{title}: {reason}")

    seen_urls: set[str] = set()
    unique_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        url = candidate.get("url")
        if not url or url in seen_urls:
            continue
        seen_urls.add(url)
        unique_candidates.append(candidate)
    return unique_candidates, notes


def _series_poster_path(slug: str) -> Path:
    return SERIES_IMAGE_ROOT / slug / "poster.jpg"


def _series_src_missing(series: dict[str, Any]) -> bool:
    src = ((series.get("poster") or {}).get("src") or "")
    if "_fallback" in src:
        return True
    if not src.startswith("/"):
        return True
    return not (SITE_PUBLIC / src.lstrip("/")).exists()


def load_series_files() -> dict[str, Path]:
    return {path.stem: path for path in sorted(SERIES_DATA_DIR.glob("*.json"))}


def series_targets(slugs: list[str]) -> list[tuple[str, Path, dict[str, Any]]]:
    files = load_series_files()
    if slugs:
        chosen = slugs
    else:
        chosen = []
        for slug, path in files.items():
            series = read_json(path, default={})
            if _series_src_missing(series):
                chosen.append(slug)

    targets = []
    for slug in chosen:
        path = files.get(slug)
        if not path:
            continue
        targets.append((slug, path, read_json(path, default={})))
    return targets


def harvest_series_poster(slug: str, series: dict[str, Any], *, overwrite: bool = False) -> dict[str, Any]:
    if Image is None:
        return {"slug": slug, "status": "fail", "reason": "pillow_unavailable"}
    output_path = _series_poster_path(slug)
    is_fallback_src = "_fallback" in (((series.get("poster") or {}).get("src") or ""))
    if output_path.exists() and not overwrite and not is_fallback_src:
        return {"slug": slug, "status": "skip", "reason": "poster_exists", "path": "/" + str(output_path.relative_to(SITE_PUBLIC))}

    candidates, notes = series_candidate_chain(series)
    checked = [validate_candidate(candidate) for candidate in candidates]
    accepted = [item["candidate"] for item in checked if item["accepted"]]

    attempts = []
    for candidate in accepted:
        image_bytes = fetch_image_bytes(candidate["url"])
        if not image_bytes:
            attempts.append({"url": candidate["url"], "reason": "fetch_failed"})
            continue
        try:
            image = Image.open(io.BytesIO(image_bytes))
            usable, reason = _usable_poster_image(image)
            if not usable:
                attempts.append({"url": candidate["url"], "reason": reason, "size": image.size})
                continue
            output_path.parent.mkdir(parents=True, exist_ok=True)
            crop_2x3(image).save(output_path, "JPEG", quality=88, optimize=True)
            manifest = _manifest_payload(
                slug=slug,
                kind="series-poster",
                candidate=candidate,
                poster_path=output_path,
                source_width=image.size[0],
                source_height=image.size[1],
                attribution_line=(series.get("poster") or {}).get("attribution") or None,
            )
            write_json(output_path.parent / "manifest.json", manifest)
            return {
                "slug": slug,
                "status": "ok",
                "path": "/" + str(output_path.relative_to(SITE_PUBLIC)),
                "source_name": manifest["source"]["name"],
                "source_url": manifest["source"]["url"],
                "checked": checked,
                "notes": notes,
                "attempts": attempts,
            }
        except Exception as exc:
            attempts.append({"url": candidate["url"], "reason": f"decode_{exc.__class__.__name__}"})

    return {
        "slug": slug,
        "status": "fail",
        "reason": "no_usable_candidate",
        "checked": checked,
        "notes": notes,
        "attempts": attempts,
    }


def run_series_poster_cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Harvest attributed series posters from official-only sources.")
    parser.add_argument("slugs", nargs="*", help="Optional series slugs. Defaults to missing or fallback posters.")
    parser.add_argument("--overwrite", action="store_true", help="Refresh existing poster.jpg files too.")
    parser.add_argument("--emit", help="Optional JSON report path.")
    parser.add_argument("--sleep", type=float, default=0.4, help="Delay between titles.")
    args = parser.parse_args(argv)

    results = []
    targets = series_targets(args.slugs)
    known = {slug for slug, _, _ in targets}
    for slug in args.slugs:
        if slug not in known:
            print(f"SKIP {slug}: no json", flush=True)
            results.append({"slug": slug, "status": "skip", "reason": "no_json"})

    for slug, _, series in targets:
        result = harvest_series_poster(slug, series, overwrite=args.overwrite)
        results.append(result)
        if result["status"] == "ok":
            print(f"OK   {slug} <- {result['source_name']}", flush=True)
        elif result["status"] == "skip":
            print(f"SKIP {slug}: {result['reason']}", flush=True)
        else:
            print(f"FAIL {slug}: {result.get('reason', 'unknown')}", flush=True)
        time.sleep(args.sleep)

    summary = {
        "schema": "bollyai-series-poster-sweep/v2",
        "generated_at": utc_now(),
        "target_count": len(targets),
        "ok": sum(1 for item in results if item["status"] == "ok"),
        "skip": sum(1 for item in results if item["status"] == "skip"),
        "fail": sum(1 for item in results if item["status"] == "fail"),
        "results": results,
    }
    print(f"\nDONE ok={summary['ok']} skip={summary['skip']} fail={summary['fail']}", flush=True)
    if args.emit:
        write_json(repo_path(args.emit), summary)
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate and optionally harvest official film images.")
    parser.add_argument("--slug", required=True)
    parser.add_argument("--film-json", help="Film JSON containing image_candidates.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--write", action="store_true", help="Fetch and write variants when accepted and Pillow exists.")
    parser.add_argument("--emit", help="Optional JSON output path for the harvest report.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.fixture_mode:
        candidates = load_fixture_candidates(args.slug)
    elif args.film_json:
        film = read_json(repo_path(args.film_json), default={})
        candidates = film.get("image_candidates", [])
    else:
        candidates = []
    payload = harvest_candidates(slug=args.slug, candidates=candidates, write=args.write)
    if args.emit:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
