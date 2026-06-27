from __future__ import annotations
import json, os, re, sys, urllib.parse, urllib.request
from datetime import date, timedelta
from pathlib import Path
from typing import Any

FETCHERS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FETCHERS_DIR))
from common import USER_AGENT, utc_now

TMDB_BASE = 'https://api.themoviedb.org/3'
WIKIDATA_SPARQL = 'https://query.wikidata.org/sparql'

def _slugify(t):
    import re as _re
    return _re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')

def _http_get(url):
    req = urllib.request.Request(url, headers={
        'User-Agent': USER_AGENT,
        'Accept': 'application/sparql-results+json,application/json',
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.loads(r.read())
    except Exception:
        return None

def fetch_wikidata_boxoffice(*, year_start=2024, year_end=2026, limit=30):
    dq = chr(34)
    sparql = (
        'SELECT DISTINCT ?item ?itemLabel ?gross ?release WHERE {'
        + ' ?item wdt:P31 wd:Q11424 . ?item wdt:P364 wd:Q1860 .'
        + ' ?item p:P2142 ?stmt . ?stmt ps:P2142 ?gross .'
        + ' ?stmt psv:P2142/wikibase:quantityUnit ?cur .'
        + ' ?cur rdfs:label ?cl .'
        + " FILTER(LANG(?cl) = 'en' && STR(?cl) = 'United States dollar')"
        + ' ?item wdt:P577 ?release .'
        + f' FILTER(YEAR(?release) >= {year_start} && YEAR(?release) <= {year_end})'
        + " SERVICE wikibase:label {{ bd:serviceParam wikibase:language 'en'. }}"
        + ' } ORDER BY DESC(?gross) LIMIT ' + str(limit)
    )
    url = WIKIDATA_SPARQL + '?' + urllib.parse.urlencode({'format': 'json', 'query': sparql})
    data = _http_get(url)
    if not data: return []
    rows = data.get('results', {}).get('bindings', [])
    records, seen = [], set()
    as_of = date.today().isoformat()
    fetched_at = utc_now()
    for row in rows:
        qid = row['item']['value'].split('/')[-1]
        title = row.get('itemLabel', {}).get('value', '')
        gross_str = row.get('gross', {}).get('value', '')
        release = row.get('release', {}).get('value', '')[:10]
        if not title or title == qid or not gross_str or qid in seen: continue
        seen.add(qid)
        try: gross_usd = float(gross_str)
        except ValueError: continue
        source_url = f'https://www.wikidata.org/wiki/' + qid
        records.append({
            'film': {
                'title': title, 'type': 'film',
                'qid': qid, 'slug': _slugify(title),
                'url': '/hollywood/review/' + _slugify(title) + '/',
            },
            'language': 'en', 'industry': 'hollywood',
            'territory': 'Worldwide', 'release_date': release,
            'worldwide_gross_usd': {
                'value': gross_usd, 'label': 'trade estimate',
                'as_of': as_of,
                'sources': [{
                    'name': 'Wikidata', 'url': source_url,
                    'as_of': as_of, 'fetched_at': fetched_at,
                    'metric': 'worldwide_gross_usd', 'value': gross_usd,
                }],
            },
        })
    return records

def fetch_tmdb_boxoffice(*, api_key, limit=20):
    records, seen = [], set()
    as_of = date.today().isoformat()
    fetched_at = utc_now()
    url = TMDB_BASE + '/movie/now_playing?' + urllib.parse.urlencode({'api_key': api_key, 'language': 'en-US', 'region': 'US', 'page': '1'})
    data = _http_get(url)
    if not data: return []
    for item in data.get('results', [])[:limit]:
        tid = str(item.get('id', ''))
        if tid in seen: continue
        seen.add(tid)
        detail = _http_get(TMDB_BASE + '/movie/' + tid + '?' + urllib.parse.urlencode({'api_key': api_key, 'language': 'en-US'}))
        if not detail: continue
        revenue = detail.get('revenue')
        if not revenue: continue
        title = detail.get('title', '')
        release_date = detail.get('release_date', '')
        source_url = 'https://www.themoviedb.org/movie/' + tid
        records.append({
            'film': {
                'title': title, 'type': 'film',
                'qid': None, 'slug': _slugify(title),
                'url': '/hollywood/review/' + _slugify(title) + '/',
            },
            'language': detail.get('original_language', 'en'),
            'industry': 'hollywood',
            'territory': 'Worldwide',
            'release_date': release_date,
            'worldwide_gross_usd': {
                'value': float(revenue), 'label': 'trade estimate',
                'as_of': as_of,
                'sources': [{
                    'name': 'TMDB', 'url': source_url,
                    'as_of': as_of, 'fetched_at': fetched_at,
                    'metric': 'worldwide_gross_usd', 'value': float(revenue),
                }],
            },
        })
    return records

def fetch_western_boxoffice(*, limit=20):
    api_key = os.environ.get('TMDB_API_KEY', '')
    if api_key:
        results = fetch_tmdb_boxoffice(api_key=api_key, limit=limit)
        if results: return sorted(results, key=lambda r: r['worldwide_gross_usd']['value'], reverse=True)
    return fetch_wikidata_boxoffice()

def build_current_week_json(records):
    today = date.today()
    ws = today - timedelta(days=today.weekday())
    we = ws + timedelta(days=6)
    label = ws.strftime('%-d %B %Y')
    return {
        'schema': 'bollyai-boxoffice-week/v2',
        'DATA_PENDING': len(records) == 0,
        'generated_at': utc_now(),
        'territory': 'Worldwide',
        'week': {
            'start': ws.isoformat(),
            'end': we.isoformat(),
            'label': f'Week of ' + label,
        },
        'records': records,
    }

if __name__ == '__main__':
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument('--limit', type=int, default=20)
    p.add_argument('--emit')
    args = p.parse_args()
    records = fetch_western_boxoffice(limit=args.limit)
    payload = build_current_week_json(records)
    out = json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True)
    if args.emit:
        Path(args.emit).write_text(out)
        print(f'Wrote ' + str(len(records)) + ' records', file=sys.stderr)
    else:
        print(out)
