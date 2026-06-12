"""Compatibility wrapper for the weekly official-announcements OTT calendar."""

from __future__ import annotations

import argparse
import json
import sys

from common import repo_path, write_json
from ott_announcements import build_calendar, current_week_start, default_today, load_announcements, parse_date, write_week_archives


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit this-week plus next-week OTT calendar JSON.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--fixture-path")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD.")
    parser.add_argument("--weeks", type=int, default=2)
    parser.add_argument("--emit", default="data/ott/calendar.json")
    parser.add_argument("--no-archives", action="store_true", help="Do not write week archive JSON files.")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not write --emit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    today = parse_date(args.today) if args.today else default_today()
    start = current_week_start(today)
    entries = load_announcements(fixture_mode=args.fixture_mode)
    payload = build_calendar(entries, start=start, weeks=args.weeks)
    emit_path = repo_path(args.emit)
    if not args.dry_run:
        write_json(emit_path, payload)
        if not args.no_archives:
            archive_data_dir = emit_path.parents[1] if emit_path.name == "calendar.json" and emit_path.parent.name == "ott" else repo_path("data")
            write_week_archives(archive_data_dir, payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
