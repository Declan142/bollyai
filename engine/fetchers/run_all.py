"""BollyAI fetcher orchestrator.

Fixture mode is fully offline. Box-office publication is a separate,
fail-closed job: existing bytes earn "last good" status only after v3
validation, pre-replacement failures preserve them, and any post-replacement
durability failure reports the measured on-disk state.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from collections.abc import Mapping
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

FETCHERS_DIR = Path(__file__).resolve().parent
if str(FETCHERS_DIR) not in sys.path:
    sys.path.insert(0, str(FETCHERS_DIR))

from boxoffice_week_schema import (
    BoxOfficeContractError,
    FIXTURE_SOURCE_GROUPS,
    PRODUCTION_SOURCE_GROUPS,
    closed_week,
    validate_board,
)
from boxoffice_western import fetch_western_boxoffice
from common import (
    AtomicWriteError,
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
from ott_announcements import (
    build_calendar,
    current_week_start,
    load_announcements,
    write_week_archives,
)
from wikidata import WikidataClient


LIVE_STATUSES = {"live", "released"}
CANONICAL_DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}\Z")


def parse_cli_date(value: str | date) -> date:
    """Parse only the documented extended ISO calendar-date spelling."""

    if isinstance(value, date):
        return value
    if not CANONICAL_DATE_PATTERN.fullmatch(value):
        raise argparse.ArgumentTypeError("--today must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("--today must be a valid calendar date") from exc


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


def load_seed_series(*, fixture_mode: bool, data_dir: Path) -> list[dict[str, Any]]:
    if fixture_mode:
        return []

    series = []
    for path in sorted((data_dir / "series").glob("*.json")):
        doc = read_json(path, default=None)
        if isinstance(doc, dict):
            series.append(doc)
    return series


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


def update_existing_film_doc(
    data_dir: Path,
    seed: dict[str, Any],
    readings_by_film: dict[str, list[Any]],
) -> bool:
    qid = seed_qid(seed)
    if qid is None:
        return False
    path = data_dir / "films" / f"{qid}.json"
    if not path.exists():
        return False
    doc = read_json(path, default={})
    readings = readings_by_film.get(str(qid), [])
    if not readings:
        return False
    return write_json(path, doc)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _existing_board_status(
    previous_bytes: bytes | None,
    *,
    expected_week: dict[str, str],
    trusted_source_groups: Mapping[str, str],
) -> str:
    if previous_bytes is None:
        return "missing"
    try:
        payload = json.loads(previous_bytes)
        board = validate_board(
            payload,
            trusted_source_groups=trusted_source_groups,
        )
    except (
        BoxOfficeContractError,
        UnicodeDecodeError,
        json.JSONDecodeError,
        TypeError,
    ):
        return "invalid"
    if board["week"] != expected_week:
        return "stale"
    return str(board["status"])


def run_boxoffice_job(
    *,
    fixture_mode: bool,
    fixture_path: Path | None,
    data_dir: Path,
    today: date,
    write: bool,
    trusted_source_groups: Mapping[str, str] | None = None,
) -> dict[str, Any]:
    target = data_dir / "boxoffice" / "current-week.json"
    previous_bytes = target.read_bytes() if target.exists() else None
    source_groups = (
        trusted_source_groups
        if trusted_source_groups is not None
        else (FIXTURE_SOURCE_GROUPS if fixture_mode else PRODUCTION_SOURCE_GROUPS)
    )
    requested_week = closed_week(today)
    previous_status = _existing_board_status(
        previous_bytes,
        expected_week=requested_week,
        trusted_source_groups=source_groups,
    )
    base = {
        "requested_period": requested_week,
        "target": str(target),
        "previous_sha256": _sha256_bytes(previous_bytes) if previous_bytes is not None else None,
        "previous_board_status": previous_status,
        "changed": False,
    }
    if previous_status == "invalid":
        return {
            **base,
            "status": "failed",
            "code": "INVALID_EXISTING_BOARD",
            "error_type": "BoxOfficeContractError",
            "source_period": None,
            "source_readings": 0,
            "published_records": 0,
            "candidate_sha256": None,
            "preserved_previous_bytes": True,
        }

    try:
        outcome = fetch_western_boxoffice(
            fixture_mode=fixture_mode,
            fixture_path=fixture_path,
            expected_week=requested_week,
        )
        board = validate_board(
            outcome["board"],
            trusted_source_groups=source_groups,
        )
    except BoxOfficeContractError as exc:
        return {
            **base,
            "status": "failed",
            "code": exc.code,
            "error_type": type(exc).__name__,
            "source_period": None,
            "source_readings": 0,
            "published_records": 0,
            "candidate_sha256": None,
            "preserved_previous_bytes": (
                previous_bytes is not None and target.read_bytes() == previous_bytes
            ),
        }
    except (OSError, TypeError, ValueError, KeyError) as exc:
        return {
            **base,
            "status": "failed",
            "code": "BOXOFFICE_JOB_ERROR",
            "error_type": type(exc).__name__,
            "source_period": None,
            "source_readings": 0,
            "published_records": 0,
            "candidate_sha256": None,
            "preserved_previous_bytes": (
                previous_bytes is not None and target.read_bytes() == previous_bytes
            ),
        }

    candidate_bytes = (
        json.dumps(board, ensure_ascii=True, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")
    common = {
        **base,
        "code": outcome["code"],
        "source_period": board["week"],
        "source_readings": outcome["source_readings"],
        "published_records": outcome["published_records"],
        "candidate_sha256": _sha256_bytes(candidate_bytes),
        "source_clearance": outcome.get("source_clearance"),
        "adapter_states": outcome.get("adapter_states", []),
    }
    if outcome["status"] != "ready":
        pending_status = {
            "missing": "data_pending",
            "data_pending": "preserved_pending",
            "ready": "preserved_last_good",
            "stale": "preserved_stale",
        }[previous_status]
        return {
            **common,
            "status": pending_status,
            "preserved_previous_bytes": previous_bytes is not None,
        }
    if not write:
        return {**common, "status": "dry_run", "preserved_previous_bytes": None}

    try:
        changed = write_json(target, board)
    except OSError as exc:
        current_bytes = target.read_bytes() if target.exists() else None
        replaced = isinstance(exc, AtomicWriteError) and exc.replaced
        return {
            **common,
            "status": "failed",
            "code": (
                "BOXOFFICE_WRITE_DURABILITY_ERROR"
                if replaced
                else "BOXOFFICE_WRITE_ERROR"
            ),
            "error_type": type(exc).__name__,
            "changed": current_bytes != previous_bytes,
            "preserved_previous_bytes": (
                previous_bytes is not None and current_bytes == previous_bytes
            ),
        }
    return {
        **common,
        "status": "updated" if changed else "unchanged",
        "changed": changed,
        "preserved_previous_bytes": None,
    }


def run(args: argparse.Namespace) -> dict[str, Any]:
    fixture_mode = bool(args.fixture_mode)
    data_dir = repo_path(args.write) if args.write else DATA_DIR
    if (
        fixture_mode
        and args.write
        and data_dir.resolve() == DATA_DIR.resolve()
    ):
        raise ValueError("fixture mode cannot write the public data directory")
    today = (
        parse_cli_date(args.today)
        if args.today
        else datetime.now(timezone.utc).date()
    )
    week_start = current_week_start(today)
    boxoffice_fixture = getattr(args, "boxoffice_fixture", None)
    fixture_path = Path(boxoffice_fixture) if boxoffice_fixture else None

    boxoffice_job = run_boxoffice_job(
        fixture_mode=fixture_mode,
        fixture_path=fixture_path,
        data_dir=data_dir,
        today=today,
        write=bool(args.write),
    )

    client = WikidataClient(fixture_mode=fixture_mode)
    seeds = load_seed_films(fixture_mode=fixture_mode, data_dir=data_dir)
    series_seeds = load_seed_series(fixture_mode=fixture_mode, data_dir=data_dir)
    if args.live_only:
        fetchable_seeds = [seed for seed in seeds if seed_status(seed) in LIVE_STATUSES]
    else:
        fetchable_seeds = seeds

    metadata = []
    for seed in fetchable_seeds:
        qid = seed_qid(seed)
        if qid is not None:
            metadata.append(client.fetch_by_qid(qid))

    readings: list[Any] = []
    readings_by_film: dict[str, list[Any]] = {}
    for reading in readings:
        readings_by_film.setdefault(str(reading.qid), []).append(reading)

    announcements = load_announcements(fixture_mode=fixture_mode, data_dir=data_dir)
    calendar = build_calendar(
        announcements,
        films=seeds,
        series=series_seeds,
        start=week_start,
        weeks=2,
    )
    changed_urls = stable_unique(url for seed in seeds for url in changed_urls_for_seed(seed))

    wrote: list[str] = []
    if args.write:
        calendar_path = data_dir / "ott" / "calendar.json"
        if write_json(calendar_path, calendar):
            wrote.append(str(calendar_path))
        wrote.extend(str(path) for path in write_week_archives(data_dir, calendar))

        if boxoffice_job["status"] == "updated":
            wrote.append(boxoffice_job["target"])

        state_payload = {
            "schema": "changed-urls/v1",
            "generated_at": utc_now(),
            "mode": "fixture" if fixture_mode else "live",
            "urls": changed_urls,
        }
        changed_path = data_dir / "_state" / "changed-urls.json"
        if write_json(changed_path, state_payload):
            wrote.append(str(changed_path))

        for seed in fetchable_seeds:
            if update_existing_film_doc(data_dir, seed, readings_by_film):
                qid = seed_qid(seed)
                wrote.append(str(data_dir / "films" / f"{qid}.json"))

    if boxoffice_job["status"] == "failed":
        overall_status = "failed"
    elif boxoffice_job["status"] in {
        "preserved_last_good",
        "preserved_pending",
        "preserved_stale",
        "data_pending",
    }:
        overall_status = "degraded"
    else:
        overall_status = "ok"

    return {
        "schema": "run-all-result/v2",
        "overall_status": overall_status,
        "generated_at": utc_now(),
        "fixture_mode": fixture_mode,
        "live_only": bool(args.live_only),
        "write_dir": str(data_dir) if args.write else None,
        "films_seen": len(seeds),
        "films_fetched": len(metadata),
        "metadata_enrichment_skipped": sum(
            1 for item in metadata if item.get("enrichment_skipped")
        ),
        "boxoffice_readings": boxoffice_job["source_readings"],
        "ott_calendar_entries": len(calendar.get("entries", [])),
        "changed_urls": changed_urls,
        "jobs": {"boxoffice": boxoffice_job},
        "wrote": wrote,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run BollyAI data fetchers.")
    parser.add_argument("--fixture-mode", action="store_true", help="Use local fixtures only; no network.")
    parser.add_argument("--live-only", action="store_true", help="Only refresh live or released films.")
    parser.add_argument("--write", help="Data directory to write, for example data/. Omit for dry run.")
    parser.add_argument(
        "--today",
        type=parse_cli_date,
        help="Override today as YYYY-MM-DD for deterministic runs.",
    )
    parser.add_argument(
        "--boxoffice-fixture",
        help="Override the exact-week source fixture path in fixture mode.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.boxoffice_fixture and not args.fixture_mode:
        parser.error("--boxoffice-fixture requires --fixture-mode")
    if (
        args.fixture_mode
        and args.write
        and repo_path(args.write).resolve() == DATA_DIR.resolve()
    ):
        parser.error("fixture mode cannot write the public data directory")
    payload = run(args)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    if payload["overall_status"] != "ok":
        job = payload["jobs"]["boxoffice"]
        sys.stderr.write(
            "ERROR: box-office refresh did not produce current data "
            f"[{job['code']}] status={job['status']} "
            f"source_readings={job['source_readings']}\n"
        )
        return 1 if payload["overall_status"] == "failed" else 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
