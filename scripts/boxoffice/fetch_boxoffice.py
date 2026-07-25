#!/usr/bin/env python3
"""Compatibility CLI for BollyAI's strict Western weekly box-office job.

The legacy India adapters no longer own the public v3 board. This entrypoint
delegates to the same exact-week job as ``engine/fetchers/run_all.py`` so old
operator muscle memory cannot bypass the publication contract.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

from boxoffice_week_schema import BoxOfficeContractError, validate_board  # noqa: E402
from common import DATA_DIR, read_json  # noqa: E402
from run_all import run_boxoffice_job  # noqa: E402


CURRENT_WEEK_PATH = DATA_DIR / "boxoffice" / "current-week.json"
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


def _parse_date(value: str | None, parser: argparse.ArgumentParser) -> date:
    if value is None:
        return date.today()
    if not DATE_PATTERN.fullmatch(value):
        parser.error("--today must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError:
        parser.error("--today must be a real calendar date")


def _summary(board: dict[str, Any]) -> dict[str, Any]:
    figures = [record["week_gross_usd"] for record in board["records"]]
    return {
        "schema": "boxoffice-report/v2",
        "board_schema": board["schema"],
        "status": board["status"],
        "week": board["week"],
        "films": len(board["records"]),
        "figures_published": sum(figure["value"] is not None for figure in figures),
        "figures_tracking": sum(figure["value"] is None for figure in figures),
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the strict Western exact-week box-office job.",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write a validated live result; pending results preserve last-good bytes.",
    )
    parser.add_argument(
        "--fixture-mode",
        action="store_true",
        help="Use the offline invented-source fixture.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Override the offline fixture path.",
    )
    parser.add_argument("--today", help="Override today using YYYY-MM-DD.")
    parser.add_argument(
        "--report",
        action="store_true",
        help="Validate and summarize the current public v3 board.",
    )
    parser.add_argument(
        "--list-sources",
        action="store_true",
        help="Report operational exact-week source availability.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.fixture and not args.fixture_mode:
        parser.error("--fixture requires --fixture-mode")
    if args.fixture_mode and args.write:
        parser.error("fixture mode cannot write the public board")

    if args.list_sources:
        json.dump(
            {
                "schema": "boxoffice-source-status/v1",
                "operational_sources": [],
                "status": "data_pending",
                "code": "NO_EXACT_WEEK_SOURCE",
            },
            sys.stdout,
            indent=2,
            sort_keys=True,
        )
        sys.stdout.write("\n")
        return 0

    if args.report:
        board = read_json(CURRENT_WEEK_PATH, default=None)
        try:
            validated = validate_board(board)
        except BoxOfficeContractError as exc:
            json.dump(
                {
                    "schema": "boxoffice-report-error/v1",
                    "status": "failed",
                    "code": exc.code,
                },
                sys.stderr,
                indent=2,
                sort_keys=True,
            )
            sys.stderr.write("\n")
            return 1
        json.dump(_summary(validated), sys.stdout, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    result = run_boxoffice_job(
        fixture_mode=args.fixture_mode,
        fixture_path=args.fixture,
        data_dir=DATA_DIR,
        today=_parse_date(args.today, parser),
        write=args.write,
    )
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 1 if result["status"] == "failed" else 0


if __name__ == "__main__":
    raise SystemExit(main())
