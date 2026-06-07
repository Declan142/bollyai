#!/usr/bin/env python3
"""Harvest series lead images from Wikipedia REST summary API (fair-dealing, attributed in JSON)."""
import glob, json, os, re, sys, time, urllib.parse
import requests
from io import BytesIO
from PIL import Image

UA = "BollyAI-poster-harvester/1.0 (https://bollyai.in; takedown@bollyai.in) editorial-fair-dealing"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "public", "img", "series")
TARGET = (342, 513)  # 2:3

def wiki_title(d):
    url = (d.get("renewal") or {}).get("source_url", "") or ""
    m = re.search(r"/wiki/([^#?]+)", url)
    if m and "wikipedia.org" in url:
        return urllib.parse.unquote(m.group(1))
    return d["title"]["value"].replace(" ", "_")

def fetch_image(title):
    api = "https://en.wikipedia.org/api/rest_v1/page/summary/" + urllib.parse.quote(title, safe="")
    r = requests.get(api, headers={"User-Agent": UA}, timeout=20)
    if r.status_code != 200:
        return None, f"summary {r.status_code}"
    j = r.json()
    src = (j.get("originalimage") or {}).get("source") or (j.get("thumbnail") or {}).get("source")
    if not src:
        return None, "no image in summary"
    ir = requests.get(src, headers={"User-Agent": UA}, timeout=30)
    if ir.status_code != 200:
        return None, f"img {ir.status_code}"
    return ir.content, src

def crop_2x3(img):
    img = img.convert("RGB")
    w, h = img.size
    tw, th = TARGET
    scale = max(tw / w, th / h)
    nw, nh = int(w * scale + 0.5), int(h * scale + 0.5)
    img = img.resize((nw, nh), Image.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 3  # bias toward top (posters: title/face usually upper)
    return img.crop((left, top, left + tw, top + th))

def main():
    slugs = sys.argv[1:]
    files = {os.path.basename(f)[:-5]: f for f in glob.glob(os.path.join(ROOT, "data/series/*.json"))}
    if not slugs:
        slugs = [s for s in files if not os.path.exists(os.path.join(OUT, s, "poster.jpg"))]
    ok = fail = 0
    for slug in slugs:
        f = files.get(slug)
        if not f:
            print(f"SKIP {slug}: no json", flush=True); continue
        d = json.load(open(f))
        title = wiki_title(d)
        try:
            content, info = fetch_image(title)
        except Exception as e:
            content, info = None, str(e)
        if not content:
            # retry with bare title
            alt = d["title"]["value"].replace(" ", "_")
            if alt != title:
                try: content, info = fetch_image(alt)
                except Exception as e: content, info = None, str(e)
        if not content:
            print(f"FAIL {slug}: {info}", flush=True); fail += 1; time.sleep(0.4); continue
        try:
            img = crop_2x3(Image.open(BytesIO(content)))
            os.makedirs(os.path.join(OUT, slug), exist_ok=True)
            img.save(os.path.join(OUT, slug, "poster.jpg"), "JPEG", quality=86, optimize=True)
            print(f"OK   {slug} <- {title}", flush=True); ok += 1
        except Exception as e:
            print(f"FAIL {slug}: decode {e}", flush=True); fail += 1
        time.sleep(0.5)
    print(f"\nDONE ok={ok} fail={fail}", flush=True)

if __name__ == "__main__":
    main()
