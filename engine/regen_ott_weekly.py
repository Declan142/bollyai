"""Regenerate the weekly OTT calendar surface.

This is the cron-safe entrypoint for the Mon/Thu OTT roll. It writes the stable
current calendar, week archive JSON snapshots, and the changed URL sidecar. It
does not deploy, push, or ping IndexNow.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path
from typing import Any


FETCHERS_DIR = Path(__file__).resolve().parent / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

from common import DATA_DIR, read_json, repo_path, stable_unique, utc_now, write_json  # noqa: E402
from ott_announcements import (  # noqa: E402
    build_calendar,
    current_week_start,
    load_announcements,
    normalized_platform,
    parse_date,
    write_week_archives,
)


def load_films(data_dir: Path) -> list[dict[str, Any]]:
    films_dir = data_dir / "films"
    if not films_dir.exists():
        return []
    films = []
    for path in sorted(films_dir.glob("*.json")):
        doc = read_json(path, default=None)
        if isinstance(doc, dict):
            films.append(doc)
    return films


def load_series(data_dir: Path) -> list[dict[str, Any]]:
    series_dir = data_dir / "series"
    if not series_dir.exists():
        return []
    series = []
    for path in sorted(series_dir.glob("*.json")):
        doc = read_json(path, default=None)
        if isinstance(doc, dict):
            series.append(doc)
    return series


def platform_url(platform: str) -> str:
    return f"/ott/{normalized_platform(platform)}/"


def changed_urls(calendar: dict[str, Any]) -> list[str]:
    entries = calendar.get("entries", [])
    platforms = calendar.get("tracking", {}).get("platforms", [])
    urls = ["/ott/calendar/"]
    urls.extend(week.get("archive_url") for week in calendar.get("weeks", []))
    urls.extend(platform_url(platform) for platform in platforms)
    urls.extend(entry.get("url") for entry in entries if entry.get("url"))
    return stable_unique(str(url) for url in urls if url)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Regenerate BollyAI weekly OTT calendar data.")
    parser.add_argument("--fixture-mode", action="store_true", help="Use saved fixtures where fetchers support them.")
    parser.add_argument("--data-dir", default="data", help="Data directory to read and write.")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD. The week starts on Monday.")
    parser.add_argument("--weeks", type=int, default=2)
    parser.add_argument("--past-weeks", type=int, default=0, help="Extend window this many weeks into the past (default 0).")
    parser.add_argument("--dry-run", action="store_true", help="Print result only; do not write files.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = repo_path(args.data_dir)
    today = parse_date(args.today) if args.today else date.today()
    current_monday = current_week_start(today)
    past_weeks = max(0, args.past_weeks)
    adjusted_start = current_monday - timedelta(days=past_weeks * 7)
    total_weeks = past_weeks + args.weeks
    start = adjusted_start
    announcements = load_announcements(fixture_mode=args.fixture_mode, data_dir=data_dir)
    calendar = build_calendar(announcements, films=load_films(data_dir), series=load_series(data_dir), start=start, weeks=total_weeks)
    urls = changed_urls(calendar)

    wrote: list[str] = []
    if not args.dry_run:
        calendar_path = data_dir / "ott" / "calendar.json"
        write_json(calendar_path, calendar)
        wrote.append(str(calendar_path))
        for archive_path in write_week_archives(data_dir, calendar):
            wrote.append(str(archive_path))
        changed_path = data_dir / "_state" / "changed-urls.json"
        write_json(
            changed_path,
            {
                "schema": "changed-urls/v1",
                "generated_at": utc_now(),
                "mode": "ott-weekly",
                "urls": urls,
            },
        )
        wrote.append(str(changed_path))

    result = {
        "schema": "ott-weekly-regen-result/v1",
        "generated_at": utc_now(),
        "week_start": start.isoformat(),
        "entries": len(calendar.get("entries", [])),
        "weeks": [week.get("iso_week") for week in calendar.get("weeks", [])],
        "changed_urls": urls,
        "wrote": wrote,
    }
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
