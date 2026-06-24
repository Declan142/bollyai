#!/usr/bin/env python3
"""Seed recent and upcoming Western (Hollywood) films from Wikidata SPARQL.

Queries films with:
- P31 wd:Q11424 (film)
- P364 wd:Q1860 (English language)
- P495 USA or UK (country of origin)
- P577 release date in 2025-10-01..2027-03-31
- sitelinks >= 8 (notability filter)

Writes data/films/<QID>.json for each new film (skips existing QIDs/slugs).
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "engine"))
sys.path.insert(0, str(ROOT / "engine" / "fetchers"))

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"
USER_AGENT = "BollyAI/1.0 (bollyai.in; takedown@bollyai.in) seed_western_recent"
FILMS_DIR = ROOT / "data" / "films"
DATE_FROM = "2025-10-01"
DATE_TO = "2027-03-31"
TODAY = datetime.now(tz=timezone.utc).date()
FETCHED_AT = datetime.now(tz=timezone.utc).astimezone(
    timezone(datetime.now().astimezone().utcoffset())
).isoformat()

SPARQL_QUERY = """
SELECT ?film ?filmLabel ?date ?desc (COUNT(DISTINCT ?sl) AS ?sitelinks)
WHERE {
  ?film wdt:P31 wd:Q11424 ;
        wdt:P364 wd:Q1860 ;
        wdt:P577 ?date .
  ?film wdt:P495 ?country .
  FILTER(?country IN (wd:Q30, wd:Q145))
  FILTER(?date >= "2025-10-01T00:00:00Z"^^xsd:dateTime)
  FILTER(?date <= "2027-03-31T23:59:59Z"^^xsd:dateTime)
  OPTIONAL { ?sl schema:about ?film ; schema:isPartOf/wikibase:wikiGroup "wikipedia" . }
  OPTIONAL { ?film schema:description ?desc . FILTER(LANG(?desc) = "en") }
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en" . }
}
GROUP BY ?film ?filmLabel ?date ?desc
HAVING (COUNT(DISTINCT ?sl) >= 8)
ORDER BY DESC(?sitelinks)
LIMIT 150
"""


def sparql_query(query: str) -> list[dict]:
    params = urlencode({"query": query, "format": "json"})
    url = f"{SPARQL_ENDPOINT}?{params}"
    req = Request(url, headers={
        "User-Agent": USER_AGENT,
        "Accept": "application/sparql-results+json",
    })
    with urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read())
    return data["results"]["bindings"]


def slugify(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def make_slug(title: str, existing_slugs: set[str]) -> str:
    base = slugify(title)
    slug = base
    i = 2
    while slug in existing_slugs:
        slug = f"{base}-{i}"
        i += 1
    return slug


def source_value(value, *, source="wikidata", confidence="verified") -> dict:
    return {
        "value": value,
        "source": source,
        "fetched_at": FETCHED_AT,
        "confidence": confidence,
    }


def box_office_skeleton() -> dict:
    return {
        "day_rows": [
            {
                "date": str(TODAY),
                "day": 0,
                "label": "figures not yet pair-verified",
                "framing": "awaited",
                "published": False,
                "reason": "single_source_or_no_valid_independent_pair",
                "as_of": FETCHED_AT,
                "net_inr_cr": source_value(None, source="pending independent pair", confidence="unverified"),
                "sources": [
                    {
                        "name": "pending independent pair",
                        "url": "https://sacnilk.com/box-office-collections?tab=top-100",
                        "as_of": str(TODAY),
                    }
                ],
            }
        ],
        "totals": {
            "as_of": str(TODAY),
            "india_net_inr_cr": source_value(None, source="pending independent pair", confidence="unverified"),
            "worldwide_gross_inr_cr": source_value(None, source="pending independent pair", confidence="unverified"),
        },
    }


def dedupe_by_qid(rows: list[dict]) -> list[dict]:
    """For each QID keep the row with the earliest date (MIN date)."""
    seen: dict[str, dict] = {}
    for row in rows:
        qid = row["film"]["value"].rsplit("/", 1)[-1]
        date_str = row["date"]["value"][:10]
        if qid not in seen or date_str < seen[qid]["_date"]:
            seen[qid] = {**row, "_qid": qid, "_date": date_str}
    return list(seen.values())


def load_existing() -> tuple[set[str], set[str]]:
    qids: set[str] = set()
    slugs: set[str] = set()
    for f in FILMS_DIR.glob("Q*.json"):
        qids.add(f.stem)
        try:
            d = json.loads(f.read_text())
            s = d.get("slug", "")
            if s:
                slugs.add(s)
        except Exception:
            pass
    return qids, slugs


def seed_films(dry_run: bool = False) -> tuple[list[dict], list[str]]:
    print(f"Querying Wikidata SPARQL for Western films {DATE_FROM}..{DATE_TO} ...")
    rows = sparql_query(SPARQL_QUERY)
    print(f"Raw SPARQL rows returned: {len(rows)}")

    deduped = dedupe_by_qid(rows)
    print(f"Distinct films after QID dedup: {len(deduped)}")

    # Sort by sitelinks desc, keep top 60
    deduped.sort(key=lambda r: -int(r.get("sitelinks", {}).get("value", 0)))
    top = deduped[:60]
    print(f"Keeping top {len(top)} by sitelinks")

    existing_qids, existing_slugs = load_existing()
    print(f"Existing films: {len(existing_qids)} QIDs, {len(existing_slugs)} slugs")

    written: list[dict] = []
    skipped: list[str] = []

    for row in top:
        qid = row["_qid"]
        title = row.get("filmLabel", {}).get("value", "")
        release_date = row["_date"]
        desc = row.get("desc", {}).get("value", "")

        if not title or not qid:
            skipped.append(f"{qid} (no title/qid)")
            continue

        if qid in existing_qids:
            skipped.append(f"{qid} ({title}) - existing QID")
            continue

        candidate_slug = slugify(title)
        if candidate_slug in existing_slugs:
            skipped.append(f"{qid} ({title}) - slug collision")
            continue

        slug = make_slug(title, existing_slugs)
        existing_slugs.add(slug)
        existing_qids.add(qid)

        try:
            rel_date = datetime.fromisoformat(release_date).date()
        except Exception:
            rel_date = None

        if rel_date is None:
            status = "upcoming"
        elif rel_date > TODAY:
            status = "upcoming"
        else:
            status = "released"

        # logline from Wikidata description only; no embellishment
        logline = desc.strip() if desc else ""

        film = {
            "qid": source_value(qid),
            "slug": slug,
            "canonical_industry": "hollywood",
            "title": source_value(title),
            "original_language": source_value("en"),
            "release_date": source_value(release_date),
            "status": status,
            "logline": logline,
            "budget": None,
            "box_office": box_office_skeleton(),
            "verdict": {"ladder_rung": None, "tracking": False},
            "bollymeter": None,
            "ott": None,
            "poster": None,
            "_quarantine": [],
            "date_modified": FETCHED_AT,
        }

        if not dry_run:
            path = FILMS_DIR / f"{qid}.json"
            path.write_text(json.dumps(film, ensure_ascii=False, indent=2))

        written.append({"qid": qid, "slug": slug, "title": title, "release_date": release_date, "status": status})
        print(f"  WROTE {qid} | {title} | {release_date} | {status} -> {slug}")

    return written, skipped


if __name__ == "__main__":
    dry_run = "--dry-run" in sys.argv
    written, skipped = seed_films(dry_run=dry_run)
    print(f"\nDone. Written: {len(written)}, Skipped: {len(skipped)}")
    if skipped:
        print("Skipped:")
        for s in skipped:
            print(f"  {s}")
