"""Offline-first adapter for the strict Western exact-week contract.

No operational source adapter is enabled yet. A live run evaluates the
checked-in source-clearance gate, reports ``SOURCE_CLEARANCE_PENDING``, and
leaves the last known good board untouched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

FETCHERS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(FETCHERS_DIR))

from boxoffice_source_adapters import (  # noqa: E402
    cleared_production_adapters,
    fetch_adapter_batch,
)
from boxoffice_fixture_adapters import fixture_adapters  # noqa: E402
from boxoffice_source_clearance import (  # noqa: E402
    DEFAULT_REGISTRY_PATH,
    load_source_clearance,
)
from boxoffice_week_schema import (  # noqa: E402
    BOARD_SCHEMA,
    BoxOfficeContractError,
    PRODUCTION_SOURCE_GROUPS,
    build_board_from_source_payload,
    closed_week,
    pending_board,
    validate_board,
)
from common import (  # noqa: E402
    DATA_DIR,
    FIXTURE_DIR,
    read_json,
    repo_path,
    utc_now,
    write_json,
)


DEFAULT_FIXTURE_PATH = FIXTURE_DIR / "boxoffice_week_exact.json"
CANONICAL_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def fetch_western_boxoffice(
    *,
    fixture_mode: bool = False,
    fixture_path: Path | None = None,
    source_registry_path: Path | None = None,
    expected_week: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Return a structured exact-week outcome without unsafe fallback data."""

    requested_week = expected_week or closed_week()
    if not fixture_mode:
        registry_path = source_registry_path or DEFAULT_REGISTRY_PATH
        source_clearance = load_source_clearance(registry_path)
        if source_clearance["status"] != "ready":
            return {
                "status": "data_pending",
                "code": source_clearance["code"],
                "board": pending_board(week=requested_week),
                "source_readings": 0,
                "published_records": 0,
                "source_clearance": source_clearance,
                "adapter_states": [],
            }
        registry = read_json(registry_path, default=None)
        if registry is None:
            raise BoxOfficeContractError(
                "SOURCE_REGISTRY_MISSING",
                "source candidate registry is unavailable",
            )
        adapters = cleared_production_adapters(registry, source_clearance)
        adapter_batch = fetch_adapter_batch(adapters, requested_week)
        if adapter_batch["source_payload"] is None:
            return {
                "status": "data_pending",
                "code": adapter_batch["code"],
                "board": pending_board(week=requested_week),
                "source_readings": 0,
                "published_records": 0,
                "source_clearance": source_clearance,
                "adapter_states": adapter_batch["adapters"],
            }
        board = build_board_from_source_payload(
            adapter_batch["source_payload"],
            expected_week=requested_week,
            trusted_source_groups=PRODUCTION_SOURCE_GROUPS,
        )
        return {
            "status": board["status"],
            "code": (
                "SOURCE_ADAPTERS_READY"
                if board["status"] == "ready"
                else adapter_batch["code"]
            ),
            "board": board,
            "source_readings": len(adapter_batch["source_payload"]["readings"]),
            "published_records": sum(
                record["week_gross_usd"]["value"] is not None
                for record in board["records"]
            ),
            "source_clearance": source_clearance,
            "adapter_states": adapter_batch["adapters"],
        }

    adapter_batch = None
    if fixture_path is None:
        adapter_batch = fetch_adapter_batch(
            fixture_adapters(),
            requested_week,
        )
        source_payload = adapter_batch["source_payload"]
        if source_payload is None:
            return {
                "status": "data_pending",
                "code": adapter_batch["code"],
                "board": pending_board(week=requested_week),
                "source_readings": 0,
                "published_records": 0,
                "adapter_states": adapter_batch["adapters"],
            }
    else:
        source_payload = read_json(fixture_path, default=None)
        if source_payload is None:
            raise BoxOfficeContractError(
                "FIXTURE_NOT_FOUND",
                f"offline fixture not found: {fixture_path}",
            )
    board = build_board_from_source_payload(
        source_payload,
        expected_week=requested_week,
    )
    return {
        "status": board["status"],
        "code": (
            "FIXTURE_READY"
            if board["status"] == "ready"
            else (
                adapter_batch["code"]
                if adapter_batch
                else "NO_EXACT_WEEK_CONSENSUS"
            )
        ),
        "board": board,
        "source_readings": len(source_payload["readings"]),
        "published_records": sum(
            record["week_gross_usd"]["value"] is not None
            for record in board["records"]
        ),
        "adapter_states": adapter_batch["adapters"] if adapter_batch else [],
    }


def build_current_week_json(
    records: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper that now enforces the v3 closed-week contract."""

    week = closed_week(today)
    payload = {
        "schema": BOARD_SCHEMA,
        "status": "ready" if records else "data_pending",
        "generated_at": utc_now(),
        "territory": "Worldwide",
        "week": week,
        "records": records,
    }
    return validate_board(payload)


def _parse_cli_date(value: str) -> date:
    if not CANONICAL_DATE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("--today must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--today must be a valid calendar date") from exc


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build the exact-week Western box-office board.",
    )
    parser.add_argument(
        "--fixture-mode",
        action="store_true",
        help="Use the local offline source fixture.",
    )
    parser.add_argument(
        "--fixture",
        type=Path,
        help="Override the offline source fixture path.",
    )
    parser.add_argument(
        "--today",
        type=_parse_cli_date,
        help="Override today as YYYY-MM-DD.",
    )
    parser.add_argument(
        "--emit",
        type=Path,
        help="Write only a ready board; pending preserves any existing file.",
    )
    args = parser.parse_args(argv)
    if args.fixture and not args.fixture_mode:
        parser.error("--fixture requires --fixture-mode")
    emit_path = repo_path(args.emit) if args.emit else None
    if (
        args.fixture_mode
        and emit_path
        and emit_path.resolve().is_relative_to(DATA_DIR.resolve())
    ):
        parser.error("fixture mode cannot emit inside the public data directory")
    outcome = fetch_western_boxoffice(
        fixture_mode=args.fixture_mode,
        fixture_path=args.fixture,
        expected_week=closed_week(args.today),
    )
    if emit_path and outcome["status"] == "ready":
        write_json(emit_path, outcome["board"])
    json.dump(outcome, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    if outcome["status"] != "ready":
        sys.stderr.write(
            "ERROR: box-office fetch produced no current data "
            f"[{outcome['code']}] for {outcome['board']['week']['start']} "
            f"to {outcome['board']['week']['end']}\n"
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
