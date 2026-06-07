#!/usr/bin/env python3
"""Fallback: scrape og:image from the Wikipedia article page for slugs the summary API missed."""
import glob, json, os, re, sys, time, urllib.parse
import requests
from io import BytesIO
from PIL import Image

UA = "BollyAI-poster-harvester/1.0 (https://bollyai.in; takedown@bollyai.in) editorial-fair-dealing"
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "site", "public", "img", "series")
TARGET = (342, 513)

def wiki_title(d):
    url = (d.get("renewal") or {}).get("source_url", "") or ""
    m = re.search(r"/wiki/([^#?]+)", url)
    if m and "wikipedia.org" in url:
        return urllib.parse.unquote(m.group(1))
    return d["title"]["value"].replace(" ", "_")

def og_image(title):
    page = "https://en.wikipedia.org/wiki/" + urllib.parse.quote(title, safe="")
    r = requests.get(page, headers={"User-Agent": UA}, timeout=25)
    if r.status_code != 200:
        return None
    m = re.search(r'<meta property="og:image" content="([^"]+)"', r.text)
    return m.group(1) if m else None

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
        for title in [wiki_title(d), d["title"]["value"].replace(" ","_")]:
            try:
                src = og_image(title)
                if not src: continue
                ir = requests.get(src, headers={"User-Agent":UA}, timeout=30)
                if ir.status_code!=200: continue
                img = crop(Image.open(BytesIO(ir.content)))
                os.makedirs(os.path.join(OUT,slug), exist_ok=True)
                img.save(os.path.join(OUT,slug,"poster.jpg"),"JPEG",quality=86,optimize=True)
                print(f"OK   {slug} <- {title} (og)", flush=True); ok+=1; break
            except Exception as e:
                continue
        else:
            print(f"FAIL {slug}", flush=True); fail+=1
        time.sleep(0.5)
    print(f"\nDONE ok={ok} fail={fail}", flush=True)

if __name__=="__main__": main()
