#!/usr/bin/env python3
"""BollyAI box-office fetcher - CLI entrypoint.

Wraps engine/fetchers/boxoffice.py to pull and verify trade figures for
current and recent (last ~8 weeks) major pan-India theatrical releases.

Publish rule (CLAUDE.md fence #7):
  >= 2 independent sources within 10%  => trade estimate
  10-25% apart                         => lower figure w/ caveat
  > 25% or single-source              => tracking (null)
  budgets/salaries                     => never published

Usage:
  python3 scripts/boxoffice/fetch_boxoffice.py
  python3 scripts/boxoffice/fetch_boxoffice.py --write
  python3 scripts/boxoffice/fetch_boxoffice.py --fixture-mode --write
  python3 scripts/boxoffice/fetch_boxoffice.py --report
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_FETCHERS = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(ENGINE_FETCHERS))

import boxoffice as bo  # noqa: E402
from common import DATA_DIR, utc_now  # noqa: E402


CURRENT_WEEK_PATH = DATA_DIR / "boxoffice" / "current-week.json"

SOURCE_REGISTRY = {
    "sacnilk": {
        "name": "Sacnilk",
        "url": "https://www.sacnilk.com",
        "bias": "neutral",
        "group": "sacnilk",
        "note": "Day-wise tables + quicknews articles; strong on South Indian circuits.",
    },
    "times_of_india": {
        "name": "Times of India",
        "url": "https://timesofindia.indiatimes.com",
        "bias": "neutral",
        "group": "times_of_india",
        "note": "Trade articles with cumulative figures; pan-India coverage.",
    },
    "tracktollywood": {
        "name": "TrackTollywood",
        "url": "https://www.tracktollywood.com",
        "bias": "neutral",
        "group": "tracktollywood",
        "note": "Telugu/Tollywood specialist; day-wise worldwide + AP/TS splits.",
    },
    "boxofficeindia": {
        "name": "Box Office India",
        "url": "https://www.boxofficeindia.com",
        "bias": "neutral",
        "group": "boxofficeindia",
        "note": "Legacy Hindi BO tracker; all-India net focus.",
    },
    "andhraboxoffice": {
        "name": "Andhra Box Office",
        "url": "https://www.andhraboxoffice.com",
        "bias": "neutral",
        "group": "andhraboxoffice",
        "note": "AP/TS circuit figures; secondary for Tollywood pairs.",
    },
}

PR_ONLY_PAIR_NOTICE = (
    "Bollywood Hungama and Taran Adarsh are both classified as studio-PR sources "
    "and do NOT form a valid independent pair under fence #7."
)


def summarize_board(board: dict) -> dict:
    records = board.get("records", [])
    published = 0
    tracking = 0
    for record in records:
        for key in bo.BOXOFFICE_FIGURES:
            fig = record.get(key, {})
            if fig.get("value") is not None:
                published += 1
            else:
                tracking += 1
    return {
        "films": len(records),
        "figures_published": published,
        "figures_tracking": tracking,
        "data_pending": board.get("DATA_PENDING", True),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="BollyAI box-office fetcher.")
    parser.add_argument(
        "--write", action="store_true",
        help="Write updated figures back to current-week.json.",
    )
    parser.add_argument(
        "--fixture-mode", action="store_true",
        help="Use cached fixtures instead of live HTTP (for CI / offline).",
    )
    parser.add_argument(
        "--report", action="store_true",
        help="Print a summary report of current-week.json coverage.",
    )
    parser.add_argument(
        "--list-sources", action="store_true",
        help="List configured source registry.",
    )
    return parser


def cmd_report(board: dict) -> None:
    summary = summarize_board(board)
    print(f"Films tracked     : {summary['films']}")
    print(f"Figures published : {summary['figures_published']}")
    print(f"Figures tracking  : {summary['figures_tracking']}")
    print(f"DATA_PENDING      : {summary['data_pending']}")
    print()
    rank_label = {
        "tollywood": "Tollywood (Telugu)",
        "kollywood": "Kollywood (Tamil)",
        "mollywood": "Mollywood (Malayalam)",
        "sandalwood": "Sandalwood (Kannada)",
        "bollywood": "Bollywood (Hindi)",
        "hollywood": "Hollywood",
        "streaming": "Streaming",
    }
    for record in board.get("records", []):
        film = record.get("film", {})
        industry = record.get("industry", "unknown")
        print(f"  [{rank_label.get(industry, industry)}] {film.get('title', '?')}")
        for key in bo.BOXOFFICE_FIGURES:
            fig = record.get(key, {})
            val = fig.get("value")
            label = fig.get("label", "tracking")
            srcs = [s.get("name", "?") for s in fig.get("sources", [])]
            val_str = f"INR {val['low']} cr" if isinstance(val, dict) else "tracking"
            print(f"    {key}: {val_str}  [{label}]  sources={srcs}")


def cmd_list_sources() -> None:
    for key, meta in SOURCE_REGISTRY.items():
        print(f"  {meta['name']} ({key})")
        print(f"    url   : {meta['url']}")
        print(f"    group : {meta['group']}")
        print(f"    note  : {meta['note']}")


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.list_sources:
        cmd_list_sources()
        return 0

    board = bo.read_json(CURRENT_WEEK_PATH, default=None)
    if not isinstance(board, dict):
        print(f"ERROR: missing board at {CURRENT_WEEK_PATH}", file=sys.stderr)
        return 1

    if args.report:
        cmd_report(board)
        return 0

    result = bo.fill_current_week(fixture_mode=args.fixture_mode, write=args.write)
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
