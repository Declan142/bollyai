#!/usr/bin/env python3
"""Resolve the exact infobox |image= file from article wikitext (catches non-free posters)."""
import glob, json, os, re, sys, time, urllib.parse
import requests
from io import BytesIO
from PIL import Image
UA="BollyAI-poster-harvester/1.0 (https://bollyai.in; takedown@bollyai.in) editorial-fair-dealing"
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT=os.path.join(ROOT,"site","public","img","series"); API="https://en.wikipedia.org/w/api.php"; TARGET=(342,513)
def wiki_title(d):
    url=(d.get("renewal") or {}).get("source_url","") or ""
    m=re.search(r"/wiki/([^#?]+)",url)
    return urllib.parse.unquote(m.group(1)) if (m and "wikipedia.org" in url) else d["title"]["value"].replace(" ","_")
def wikitext(title):
    r=requests.get(API,headers={"User-Agent":UA},timeout=25,params={"action":"query","prop":"revisions","rvprop":"content","rvslots":"main","titles":title,"format":"json","redirects":1})
    pages=r.json().get("query",{}).get("pages",{})
    for p in pages.values():
        try: return p["revisions"][0]["slots"]["main"]["*"]
        except: pass
    return ""
def infobox_image(wt):
    # |image = File.jpg  OR |image = [[File:Name.jpg|...]]
    for pat in [r"\|\s*image\s*=\s*\[\[\s*[Ff]ile:([^\|\]\n]+\.(?:jpg|jpeg|png))",
                r"\|\s*image\s*=\s*([^\|\[\]\n<]+\.(?:jpg|jpeg|png))"]:
        m=re.search(pat,wt)
        if m: return m.group(1).strip()
    return None
def file_url(fn):
    r=requests.get(API,headers={"User-Agent":UA},timeout=25,params={"action":"query","titles":"File:"+fn,"prop":"imageinfo","iiprop":"url|size","format":"json"})
    for p in r.json().get("query",{}).get("pages",{}).values():
        ii=(p.get("imageinfo") or [{}])[0]; return ii.get("url"),ii.get("width",0),ii.get("height",0)
    return None,0,0
def crop(img):
    img=img.convert("RGB"); w,h=img.size; tw,th=TARGET; s=max(tw/w,th/h)
    nw,nh=int(w*s+.5),int(h*s+.5); img=img.resize((nw,nh),Image.LANCZOS)
    l=(nw-tw)//2; t=(nh-th)//3; return img.crop((l,t,l+tw,t+th))
def main():
    files={os.path.basename(f)[:-5]:f for f in glob.glob(os.path.join(ROOT,"data/series/*.json"))}
    ok=fail=0
    for slug in sys.argv[1:]:
        d=json.load(open(files[slug])); saved=False
        for title in [wiki_title(d), d["title"]["value"].replace(" ","_")]:
            try:
                fn=infobox_image(wikitext(title))
                if not fn: continue
                url,w,h=file_url(fn)
                if not url or h<w: continue
                ir=requests.get(url,headers={"User-Agent":UA},timeout=30)
                if ir.status_code!=200: continue
                crop(Image.open(BytesIO(ir.content))).save(os.path.join(OUT,slug,"poster.jpg") if os.path.isdir(os.path.join(OUT,slug)) else (os.makedirs(os.path.join(OUT,slug),exist_ok=True) or os.path.join(OUT,slug,"poster.jpg")),"JPEG",quality=86,optimize=True)
                print(f"OK   {slug} <- {fn}",flush=True); ok+=1; saved=True; break
            except Exception as e: continue
            finally: time.sleep(0.2)
        if not saved: print(f"FAIL {slug}",flush=True); fail+=1
        time.sleep(0.3)
    print(f"\nDONE ok={ok} fail={fail}",flush=True)
if __name__=="__main__": main()
