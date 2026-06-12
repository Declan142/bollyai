"""BollyAI fetcher orchestrator.

Fixture mode is safe to run without network and without writes:

    python3 engine/fetchers/run_all.py --fixture-mode

Explicit writes require --write data/.  That path emits the OTT calendar and
IndexNow changed-URL state, and updates existing QID-keyed film JSON files if
present.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path
from typing import Any

from boxoffice import load_fixture_readings, merge_readings_into_film
from common import (
    DATA_DIR,
    FIXTURE_DIR,
    film_url,
    read_json,
    repo_path,
    stable_unique,
    unwrap_value,
    utc_now,
    write_json,
)
from ott_announcements import build_calendar, current_week_start, load_announcements, parse_date, write_week_archives
from wikidata import WikidataClient


LIVE_STATUSES = {"live", "released"}


def load_seed_films(*, fixture_mode: bool, data_dir: Path) -> list[dict[str, Any]]:
    if fixture_mode:
        payload = read_json(FIXTURE_DIR / "run_all_films.json", default={"films": []})
        return payload.get("films", [])

    films = []
    for path in sorted((data_dir / "films").glob("*.json")):
        doc = read_json(path, default=None)
        if isinstance(doc, dict):
            films.append(doc)
    return films


def seed_qid(seed: dict[str, Any]) -> str | None:
    for key in ("qid", "wikidata"):
        value = unwrap_value(seed.get(key))
        if value:
            return str(value)
    ids = seed.get("ids") or {}
    value = unwrap_value(ids.get("wikidata"))
    return str(value) if value else None


def seed_status(seed: dict[str, Any]) -> str | None:
    value = unwrap_value(seed.get("status"))
    if value:
        return str(value)
    release = seed.get("release") or {}
    return str(unwrap_value(release.get("status"))) if release.get("status") else None


def changed_urls_for_seed(seed: dict[str, Any]) -> list[str]:
    industry = unwrap_value(seed.get("canonical_industry")) or unwrap_value(seed.get("industry"))
    slug = unwrap_value(seed.get("slug"))
    page_types = ["box-office", "review", "upcoming"]
    return stable_unique(film_url(str(industry), page_type, str(slug)) for page_type in page_types)


def update_existing_film_doc(data_dir: Path, seed: dict[str, Any], readings_by_film: dict[str, list[Any]]) -> bool:
    qid = seed_qid(seed)
    if qid is None:
        return False
    path = data_dir / "films" / f"{qid}.json"
    if not path.exists():
        return False
    doc = read_json(path, default={})
    readings = readings_by_film.get(str(qid), [])
    if readings:
        doc = merge_readings_into_film(doc, readings)
        write_json(path, doc)
        return True
    return False


def run(args: argparse.Namespace) -> dict[str, Any]:
    fixture_mode = bool(args.fixture_mode)
    data_dir = repo_path(args.write) if args.write else DATA_DIR
    today = parse_date(args.today) if args.today else date.today()
    week_start = current_week_start(today)
    client = WikidataClient(fixture_mode=fixture_mode)
    seeds = load_seed_films(fixture_mode=fixture_mode, data_dir=data_dir)
    if args.live_only:
        fetchable_seeds = [seed for seed in seeds if seed_status(seed) in LIVE_STATUSES]
    else:
        fetchable_seeds = seeds

    metadata = []
    for seed in fetchable_seeds:
        qid = seed_qid(seed)
        if qid is None:
            continue
        metadata.append(client.fetch_by_qid(qid))

    readings = load_fixture_readings() if fixture_mode else []
    readings_by_film: dict[str, list[Any]] = {}
    for reading in readings:
        readings_by_film.setdefault(str(reading.qid), []).append(reading)

    announcements = load_announcements(fixture_mode=fixture_mode, data_dir=data_dir)
    calendar = build_calendar(announcements, films=seeds, start=week_start, weeks=2)
    changed_urls = stable_unique(url for seed in seeds for url in changed_urls_for_seed(seed))

    wrote = []
    if args.write:
        calendar_path = data_dir / "ott" / "calendar.json"
        write_json(calendar_path, calendar)
        wrote.append(str(calendar_path))
        for archive_path in write_week_archives(data_dir, calendar):
            wrote.append(str(archive_path))

        state_payload = {
            "schema": "changed-urls/v1",
            "generated_at": utc_now(),
            "mode": "fixture" if fixture_mode else "live",
            "urls": changed_urls,
        }
        changed_path = data_dir / "_state" / "changed-urls.json"
        write_json(changed_path, state_payload)
        wrote.append(str(changed_path))

        for seed in fetchable_seeds:
            if update_existing_film_doc(data_dir, seed, readings_by_film):
                qid = seed_qid(seed)
                wrote.append(str(data_dir / "films" / f"{qid}.json"))

    return {
        "schema": "run-all-result/v1",
        "generated_at": utc_now(),
        "fixture_mode": fixture_mode,
        "live_only": bool(args.live_only),
        "write_dir": str(data_dir) if args.write else None,
        "films_seen": len(seeds),
        "films_fetched": len(metadata),
        "metadata_enrichment_skipped": sum(1 for item in metadata if item.get("enrichment_skipped")),
        "boxoffice_readings": len(readings),
        "ott_calendar_entries": len(calendar.get("entries", [])),
        "changed_urls": changed_urls,
        "wrote": wrote,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BollyAI data fetchers.")
    parser.add_argument("--fixture-mode", action="store_true", help="Use fixture files; no network.")
    parser.add_argument("--live-only", action="store_true", help="Only refresh live/released films.")
    parser.add_argument("--write", help="Data directory to write, e.g. data/. Omit for dry run.")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD for deterministic fixture runs.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    payload = run(args)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
