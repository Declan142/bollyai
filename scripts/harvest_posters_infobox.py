#!/usr/bin/env python3
"""Third pass: pick the best raster poster from a Wikipedia article's image list via MediaWiki API."""
import glob, json, os, re, sys, time, urllib.parse
import requests
from io import BytesIO
from PIL import Image

UA = "BollyAI-poster-harvester/1.0 (https://bollyai.in; takedown@bollyai.in) editorial-fair-dealing"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "public", "img", "series")
API = "https://en.wikipedia.org/w/api.php"
TARGET = (342, 513)
GOOD = ("poster", "promotional", "promo", "teaser", "title_card", "titlecard", "cover", "key_art", "keyart")
BADEXT = (".svg",)

def wiki_title(d):
    url = (d.get("renewal") or {}).get("source_url", "") or ""
    m = re.search(r"/wiki/([^#?]+)", url)
    if m and "wikipedia.org" in url:
        return urllib.parse.unquote(m.group(1))
    return d["title"]["value"].replace(" ", "_")

def page_images(title):
    r = requests.get(API, headers={"User-Agent": UA}, timeout=25, params={
        "action": "parse", "page": title, "prop": "images", "format": "json", "redirects": 1})
    j = r.json()
    return j.get("parse", {}).get("images", []) if "parse" in j else []

def image_url(filename):
    r = requests.get(API, headers={"User-Agent": UA}, timeout=25, params={
        "action": "query", "titles": "File:" + filename, "prop": "imageinfo",
        "iiprop": "url|size|mime", "format": "json"})
    pages = r.json().get("query", {}).get("pages", {})
    for p in pages.values():
        ii = (p.get("imageinfo") or [{}])[0]
        return ii.get("url"), ii.get("width", 0), ii.get("height", 0), ii.get("mime", "")
    return None, 0, 0, ""

def pick(images):
    cands = [f for f in images if not f.lower().endswith(BADEXT)]
    # rank: poster-ish name first, then any jpg/png
    scored = []
    for f in cands:
        lf = f.lower()
        if not (lf.endswith(".jpg") or lf.endswith(".jpeg") or lf.endswith(".png")): continue
        score = 0
        if any(g in lf for g in GOOD): score += 10
        if "logo" in lf or "wordmark" in lf or "icon" in lf: score -= 8
        scored.append((score, f))
    scored.sort(key=lambda x: -x[0])
    return [f for _, f in scored]

def crop(img):
    img = img.convert("RGB"); w,h = img.size; tw,th = TARGET
    s = max(tw/w, th/h); nw,nh = int(w*s+.5), int(h*s+.5)
    img = img.resize((nw,nh), Image.LANCZOS)
    l=(nw-tw)//2; t=(nh-th)//3
    return img.crop((l,t,l+tw,t+th))

def main():
    slugs = sys.argv[1:]
    files = {os.path.basename(f)[:-5]: f for f in glob.glob(os.path.join(ROOT,"data/series/*.json"))}
    ok=fail=0
    for slug in slugs:
        d = json.load(open(files[slug]))
        title = wiki_title(d)
        try:
            cands = pick(page_images(title))
        except Exception as e:
            cands = []
        saved = False
        for fn in cands[:6]:
            try:
                url, w, h, mime = image_url(fn)
                if not url or w < 200 or h < 280: continue
                if h < w: continue  # posters are portrait; skip landscape stills
                ir = requests.get(url, headers={"User-Agent": UA}, timeout=30)
                if ir.status_code != 200: continue
                img = crop(Image.open(BytesIO(ir.content)))
                os.makedirs(os.path.join(OUT, slug), exist_ok=True)
                img.save(os.path.join(OUT, slug, "poster.jpg"), "JPEG", quality=86, optimize=True)
                print(f"OK   {slug} <- {fn}", flush=True); ok+=1; saved=True; break
            except Exception:
                continue
            finally:
                time.sleep(0.2)
        if not saved:
            print(f"FAIL {slug} (cands={len(cands)})", flush=True); fail+=1
        time.sleep(0.4)
    print(f"\nDONE ok={ok} fail={fail}", flush=True)

if __name__ == "__main__": main()
