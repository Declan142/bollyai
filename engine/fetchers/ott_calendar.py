"""Compatibility wrapper for the official-announcements OTT calendar."""

from __future__ import annotations

import argparse
import json
import sys

from common import repo_path, write_json
from ott_announcements import build_calendar, default_today, load_announcements, parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit next-four-weeks OTT calendar JSON.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--fixture-path")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD.")
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--emit", default="data/ott/calendar.json")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not write --emit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    start = parse_date(args.today) if args.today else default_today()
    entries = load_announcements(fixture_mode=args.fixture_mode)
    payload = build_calendar(entries, start=start, weeks=args.weeks)
    if not args.dry_run:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
