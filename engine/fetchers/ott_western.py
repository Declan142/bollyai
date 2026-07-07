from __future__ import annotations
import json, os, re, sys, time, urllib.error, urllib.parse, urllib.request
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

def _log(msg):
    print(f"ott_western: {msg}", file=sys.stderr)

def _http_get(url, *, retries=2, timeout=30):
    """GET JSON with bounded retry on 429/5xx. Failures are logged, never silent -
    the 2026-07 audit traced an empty calendar to errors this function used to swallow."""
    for attempt in range(retries + 1):
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/sparql-results+json,application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            if e.code in (429, 500, 502, 503, 504) and attempt < retries:
                retry_after = e.headers.get("Retry-After") if e.headers else None
                delay = min(int(retry_after) if (retry_after or "").isdigit() else 20 * (attempt + 1), 60)
                _log(f"HTTP {e.code}, retry {attempt + 1}/{retries} in {delay}s: {url[:96]}")
                time.sleep(delay)
                continue
            _log(f"HTTP {e.code} (giving up): {url[:96]}")
            return None
        except Exception as e:
            if attempt < retries:
                _log(f"{type(e).__name__}: {e} - retry {attempt + 1}/{retries}: {url[:96]}")
                time.sleep(10 * (attempt + 1))
                continue
            _log(f"{type(e).__name__}: {e} (giving up): {url[:96]}")
            return None
    return None

def wikidata_ott_query(*, start_s, end_s):
    # Platform-first shape: the inner select binds only items tagged to the 8 target
    # platforms (a bounded set), THEN the date window filters those. The flat shape
    # date-scanned every film/series on Wikidata and blew the query deadline.
    # P750 = distributed by (films); P449 = original broadcaster (how platform
    # originals are tagged). P449 shipped as P4947 (TMDb film ID, a string
    # identifier) - it could never bind a platform QID, so originals were invisible
    # and the fetch returned 0 rows forever.
    pv = " ".join(f"wd:{q}" for q in WIKIDATA_PLATFORM_QIDS)
    lv = " ".join(f"wd:{q}" for q in WIKIDATA_LANG_CODES)
    return (
        "SELECT DISTINCT ?item ?itemLabel ?date ?platQid ?langItem ?typeLabel WHERE {"
        + " { SELECT DISTINCT ?item ?platQid WHERE {"
        + f" VALUES ?platQid {{ {pv} }}"
        + " ?item wdt:P449|wdt:P750 ?platQid ."
        + " } }"
        + " ?item wdt:P577 ?date ."
        + f' FILTER(?date >= "{start_s}"^^xsd:dateTime && ?date < "{end_s}"^^xsd:dateTime)'
        + f" VALUES ?langItem {{ {lv} }}"
        + " ?item wdt:P364 ?langItem ."
        + ' { ?item wdt:P31 wd:Q11424 . BIND("film" AS ?typeLabel) }'
        + ' UNION { ?item wdt:P31 wd:Q5398426 . BIND("series" AS ?typeLabel) }'
        + ' SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }'
        + "} ORDER BY ?date LIMIT 100"
    )

def fetch_wikidata_ott(*, window_start, window_end):
    sparql = wikidata_ott_query(start_s=window_start.isoformat() + "T00:00:00Z", end_s=window_end.isoformat() + "T00:00:00Z")
    url = WIKIDATA_SPARQL + "?" + urllib.parse.urlencode({"format": "json", "query": sparql})
    data = _http_get(url, timeout=55)
    if not data:
        _log(f"wikidata: no data for {window_start}..{window_end} (errors above)")
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
    _log(f"wikidata: {len(entries)} entries for {window_start}..{window_end}")
    return entries

def resolve_tmdb_platform(providers_payload, *, region="US"):
    """Map a TMDB watch/providers payload to one target platform, or None.
    Discover only proves a title is on SOME target provider; naming which one
    requires the per-title providers endpoint - a guessed platform would ship a
    false verified claim, so unresolvable titles are skipped, not labeled."""
    if not isinstance(providers_payload, dict):
        return None
    region_data = (providers_payload.get("results") or {}).get(region) or {}
    for bucket in ("flatrate", "free", "ads"):
        for provider in region_data.get(bucket) or []:
            name = TMDB_US_PROVIDER_IDS.get(provider.get("provider_id"))
            if name:
                return name
    return None

def fetch_tmdb_ott(*, window_start, window_end, api_key):
    entries, seen, fetched_at, skipped = [], set(), utc_now(), 0
    provider_ids = "|".join(str(pid) for pid in TMDB_US_PROVIDER_IDS)
    for media_type in ("movie", "tv"):
        df = "primary_release_date" if media_type == "movie" else "first_air_date"
        params = {"api_key": api_key, "with_watch_providers": provider_ids, "watch_region": "US",
            "with_original_language": "en", f"{df}.gte": window_start.isoformat(), f"{df}.lte": window_end.isoformat(), "sort_by": f"{df}.asc"}
        data = _http_get(f"{TMDB_BASE}/discover/{media_type}?" + urllib.parse.urlencode(params))
        if not data: continue
        for item in data.get("results", [])[:40]:
            tid = str(item.get("id", ""))
            title = item.get("title") or item.get("name") or ""
            rd = item.get("release_date") or item.get("first_air_date") or ""
            if not title or not rd or tid in seen: continue
            seen.add(tid)
            providers = _http_get(f"{TMDB_BASE}/{media_type}/{tid}/watch/providers?" + urllib.parse.urlencode({"api_key": api_key}))
            platform = resolve_tmdb_platform(providers)
            if not platform:
                skipped += 1
                continue
            ct = "film" if media_type == "movie" else "series"
            src = f"https://www.themoviedb.org/{media_type}/{tid}"
            entries.append({"id": f"{ct}-{_slugify(title)}", "qid": None, "title": title, "slug": None,
                "industry": "streaming", "language": item.get("original_language", "en"), "type": ct,
                "platform": platform, "date": rd, "fetched_at": fetched_at,
                "sources": [{"name": "TMDB", "url": src, "type": "press"}], "url": None, "verdict_line": None})
    _log(f"tmdb: {len(entries)} entries, {skipped} skipped (unresolvable platform) for {window_start}..{window_end}")
    return entries

def _union_fetch_paths(primary, secondary):
    """Union the two fetch paths on (id, platform). Primary wins a collision - callers
    pass Wikidata first because its entries carry a QID and TMDB's never do."""
    merged = list(primary)
    seen = {(e.get("id"), e.get("platform")) for e in merged}
    for e in secondary:
        key = (e.get("id"), e.get("platform"))
        if key in seen:
            continue
        seen.add(key)
        merged.append(e)
    return merged


def fetch_western_ott(*, window_start=None, window_end=None, weeks_ahead=3, weeks_back=4):
    today = date.today()
    if window_start is None: window_start = today - timedelta(days=weeks_back * 7)
    if window_end is None: window_end = today + timedelta(days=weeks_ahead * 7)
    api_key = os.environ.get("TMDB_API_KEY", "")
    # The two paths are COMPLEMENTS, not alternatives. TMDB discover is hard-filtered to
    # original-language en, so it can never see the Western-European (fr/de/es/it/pt)
    # originals the brand lock keeps; Wikidata sees those but is sparse on fresh English
    # titles. Returning TMDB *instead of* Wikidata (the pre-2026-07-07 shape) made every
    # non-English Western original invisible whenever a TMDB key was present. Union both;
    # Wikidata wins collisions because it carries the QID.
    tmdb = fetch_tmdb_ott(window_start=window_start, window_end=window_end, api_key=api_key) if api_key else []
    wikidata = fetch_wikidata_ott(window_start=window_start, window_end=window_end)
    entries = _union_fetch_paths(wikidata, tmdb)
    for e in entries:
        e["origin"] = "fetched"
    return entries

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
