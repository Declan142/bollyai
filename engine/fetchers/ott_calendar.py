"""Build the rolling next-four-weeks OTT calendar.

The v1 assembler consumes TMDB watch-provider delta records.  Fixture mode uses
data/cache/fixtures/ott_provider_deltas.json and performs no network access.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

from common import (
    FIXTURE_DIR,
    JUSTWATCH_ATTRIBUTION,
    JUSTWATCH_COUNTRY_LINKS,
    repo_path,
    source_value,
    utc_now,
    read_json,
    write_json,
)


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def default_today() -> date:
    return date.today()


def load_provider_deltas(*, fixture_mode: bool = False, fixture_path: Path | None = None) -> list[dict[str, Any]]:
    path = fixture_path or FIXTURE_DIR / "ott_provider_deltas.json"
    payload = read_json(path, default={"entries": []})
    return payload.get("entries", [])


def build_calendar(
    entries: list[dict[str, Any]],
    *,
    start: date | None = None,
    weeks: int = 4,
    region: str = "IN",
) -> dict[str, Any]:
    start = start or default_today()
    end = start + timedelta(days=weeks * 7)
    generated_at = utc_now()
    output_entries = []
    for entry in entries:
        release_value = entry.get("release_date") or entry.get("available_date")
        if not release_value:
            continue
        release_date = parse_date(str(release_value))
        if not (start <= release_date < end):
            continue
        status = "verified" if entry.get("verified", True) else "unverified"
        output_entries.append(
            {
                "title": entry.get("title"),
                "tmdb_id": entry.get("tmdb_id"),
                "slug": entry.get("slug"),
                "industry": entry.get("industry"),
                "platform": entry.get("platform") or entry.get("provider"),
                "type": entry.get("type", "film"),
                "language": entry.get("language"),
                "release_date": source_value(
                    release_date.isoformat(),
                    entry.get("source", "tmdb_watch_providers"),
                    fetched_at=entry.get("fetched_at") or generated_at,
                    confidence="verified" if status == "verified" else "unverified",
                ),
                "watch_provider_attribution": JUSTWATCH_ATTRIBUTION,
                "country": region,
                "country_link": entry.get("country_link") or JUSTWATCH_COUNTRY_LINKS.get(region, "https://www.justwatch.com/in"),
                "tmdb_watch_link": entry.get("tmdb_watch_link"),
                "_status": status,
            }
        )
    output_entries.sort(key=lambda item: (item["release_date"]["value"], item.get("platform") or "", item.get("title") or ""))
    return {
        "schema": "ott-calendar/v1",
        "generated_at": generated_at,
        "window": {
            "start": start.isoformat(),
            "end": (end - timedelta(days=1)).isoformat(),
            "weeks": weeks,
            "region": region,
        },
        "entries": output_entries,
        "_provenance": {
            "source": "tmdb_watch_providers_delta",
            "attribution": JUSTWATCH_ATTRIBUTION,
            "country_link": JUSTWATCH_COUNTRY_LINKS.get(region, "https://www.justwatch.com/in"),
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit next-four-weeks OTT calendar JSON.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--fixture-path")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD.")
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--region", default="IN")
    parser.add_argument("--emit", default="data/ott/calendar.json")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not write --emit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    start = parse_date(args.today) if args.today else default_today()
    deltas = load_provider_deltas(
        fixture_mode=args.fixture_mode,
        fixture_path=repo_path(args.fixture_path) if args.fixture_path else None,
    )
    payload = build_calendar(deltas, start=start, weeks=args.weeks, region=args.region)
    if not args.dry_run:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
