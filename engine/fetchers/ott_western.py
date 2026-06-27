from __future__ import annotations
import json, os, re, sys, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

FETCHERS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FETCHERS_DIR))
from common import USER_AGENT, utc_now

TMDB_BASE = "https://api.themoviedb.org/3"
WIKIDATA_SPARQL = "https://query.wikidata.org/sparql"

WIKIDATA_PLATFORM_QIDS = {
    "Q907311": "Netflix", "Q836821": "Prime Video", "Q90008673": "Disney+",
    "Q105857697": "Max", "Q62467956": "Apple TV+", "Q538460": "Hulu",
    "Q22134960": "Paramount+", "Q77591797": "Peacock",
}
TMDB_US_PROVIDER_IDS = {8: "Netflix", 9: "Prime Video", 337: "Disney+", 1899: "Max", 350: "Apple TV+", 15: "Hulu", 531: "Paramount+", 386: "Peacock"}
WIKIDATA_LANG_CODES = {"Q1860": "en", "Q150": "fr", "Q188": "de", "Q1321": "es", "Q652": "it", "Q5146": "pt"}

def _slugify(t): return re.sub(r"[^a-z0-9]+", "-", t.lower()).strip("-")

def _http_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json,application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception:
        return None

def fetch_wikidata_ott(*, window_start, window_end):
    pv = " ".join(f"wd:{q}" for q in WIKIDATA_PLATFORM_QIDS)
    lv = " ".join(f"wd:{q}" for q in WIKIDATA_LANG_CODES)
    start_s = window_start.isoformat() + "T00:00:00Z"
    end_s = window_end.isoformat() + "T00:00:00Z"
    sparql = (
        "SELECT DISTINCT ?item ?itemLabel ?date ?platQid ?langItem ?typeLabel WHERE {"
        + f" VALUES ?platItem {{ {pv} }}"
        + f" VALUES ?langItem {{ {lv} }}"
        + ' { ?item wdt:P31 wd:Q11424 . BIND("film" AS ?typeLabel) }'
        + ' UNION { ?item wdt:P31 wd:Q5398426 . BIND("series" AS ?typeLabel) }'
        + " ?item wdt:P364 ?langItem . ?item wdt:P577 ?date ."
        + f' FILTER(?date >= "{start_s}"^^xsd:dateTime && ?date < "{end_s}"^^xsd:dateTime)'
        + " { ?item wdt:P750 ?platItem . BIND(?platItem AS ?platQid) }"
        + " UNION { ?item wdt:P4947 ?platItem . BIND(?platItem AS ?platQid) }"
        + ' SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }'
        + "} ORDER BY ?date LIMIT 100"
    )
    url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({"format": "json", "query": sparql})
    data = _http_get(url)
    if not data:
        return []
    rows = data.get("results", {}).get("bindings", [])
    entries, seen = [], set()
    for row in rows:
        qid = row["item"]["value"].split("/")[-1]
        title = row.get("itemLabel", {}).get("value", "")
        release_date = row.get("date", {}).get("value", "")[:10]
        plat_qid = row.get("platQid", {}).get("value", "").split("/")[-1]
        platform = WIKIDATA_PLATFORM_QIDS.get(plat_qid, "")
        ct = row.get("typeLabel", {}).get("value", "film")
        lq = row.get("langItem", {}).get("value", "").split("/")[-1]
        lc = WIKIDATA_LANG_CODES.get(lq, "en")
        if not title or title == qid or not release_date or not platform:
            continue
        key = (qid, platform)
        if key in seen:
            continue
        seen.add(key)
        entries.append({"id": f"{ct}-{_slugify(title)}", "qid": qid, "title": title, "slug": None,
            "industry": "streaming", "language": lc, "type": ct, "platform": platform, "date": release_date,
            "fetched_at": utc_now(), "sources": [{"name": "Wikidata", "url": f"https://www.wikidata.org/wiki/{qid}", "type": "press"}],
            "url": None, "verdict_line": None})
    return entries

def fetch_tmdb_ott(*, window_start, window_end, api_key):
    entries, seen, fetched_at = [], set(), utc_now()
    provider_ids = "|".join(str(pid) for pid in TMDB_US_PROVIDER_IDS)
    for media_type in ("movie", "tv"):
        df = "primary_release_date" if media_type == "movie" else "first_air_date"
        params = {"api_key": api_key, "with_watch_providers": provider_ids, "watch_region": "US",
            "with_original_language": "en", f"{df}.gte": window_start.isoformat(), f"{df}.lte": window_end.isoformat(), "sort_by": f"{df}.asc"}
        url = f"{TMDB_BASE}/discover/{media_type}?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=30) as r: data = json.loads(r.read())
        except Exception: continue
        for item in data.get("results", [])[:40]:
            tid = str(item.get("id", ""))
            title = item.get("title") or item.get("name") or ""
            rd = item.get("release_date") or item.get("first_air_date") or ""
            if not title or not rd or tid in seen: continue
            seen.add(tid)
            ct = "film" if media_type == "movie" else "series"
            src = f"https://www.themoviedb.org/{media_type}/{tid}"
            entries.append({"id": f"{ct}-{_slugify(title)}", "qid": None, "title": title, "slug": None,
                "industry": "streaming", "language": item.get("original_language", "en"), "type": ct,
                "platform": "Streaming", "date": rd, "fetched_at": fetched_at,
                "sources": [{"name": "TMDB", "url": src, "type": "press"}], "url": None, "verdict_line": None})
    return entries

def fetch_western_ott(*, window_start=None, window_end=None, weeks_ahead=3, weeks_back=4):
    today = date.today()
    if window_start is None: window_start = today - timedelta(days=weeks_back * 7)
    if window_end is None: window_end = today + timedelta(days=weeks_ahead * 7)
    api_key = os.environ.get("TMDB_API_KEY", "")
    if api_key:
        results = fetch_tmdb_ott(window_start=window_start, window_end=window_end, api_key=api_key)
        if results: return results
    return fetch_wikidata_ott(window_start=window_start, window_end=window_end)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--weeks-ahead", type=int, default=3)
    p.add_argument("--weeks-back", type=int, default=4)
    p.add_argument("--emit")
    args = p.parse_args()
    results = fetch_western_ott(weeks_ahead=args.weeks_ahead, weeks_back=args.weeks_back)
    out = json.dumps(results, ensure_ascii=True, indent=2, sort_keys=True)
    if args.emit: Path(args.emit).write_text(out); print(f"Wrote {len(results)} entries", file=sys.stderr)
    else: print(out)
