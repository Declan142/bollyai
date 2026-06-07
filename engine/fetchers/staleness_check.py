"""Detect stale live tracker data for BollyAI."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, time, timezone
from pathlib import Path
from typing import Any

from common import DATA_DIR, parse_datetime, read_json, repo_path, unwrap_value, utc_now, write_json


LIVE_STATUSES = {"live", "released"}


def load_film_docs(data_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    films_dir = data_dir / "films"
    docs = []
    for path in sorted(films_dir.glob("*.json")):
        doc = read_json(path, default=None)
        if isinstance(doc, dict):
            docs.append((path, doc))
    return docs


def film_status(doc: dict[str, Any]) -> str | None:
    direct = unwrap_value(doc.get("status"))
    if direct:
        return str(direct)
    release = doc.get("release") or {}
    status = release.get("status")
    return str(unwrap_value(status)) if status else None


def latest_boxoffice_time(doc: dict[str, Any]) -> datetime | None:
    box_office = doc.get("box_office") or {}
    rows = box_office.get("day_rows") or []
    candidates = []
    for row in rows:
        as_of = row.get("as_of") or row.get("fetched_at")
        parsed = parse_datetime(as_of)
        if parsed:
            candidates.append(parsed)
            continue
        date_value = row.get("date")
        if date_value:
            try:
                parsed_date = datetime.strptime(str(date_value), "%Y-%m-%d").date()
            except ValueError:
                continue
            candidates.append(datetime.combine(parsed_date, time(23, 59, 59), tzinfo=timezone.utc))
    return max(candidates) if candidates else None


def film_identity(path: Path, doc: dict[str, Any]) -> dict[str, Any]:
    ids = doc.get("ids") or {}
    return {
        "path": str(path),
        "tmdb_id": unwrap_value(doc.get("tmdb_id")) or unwrap_value(ids.get("tmdb")),
        "slug": unwrap_value(doc.get("slug")),
        "title": unwrap_value(doc.get("title")) or unwrap_value((doc.get("titles") or {}).get("default")),
        "status": film_status(doc),
    }


def check_staleness(
    *,
    data_dir: Path,
    sla_hours: float,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = (now or datetime.now(timezone.utc)).astimezone(timezone.utc)
    items = []
    for path, doc in load_film_docs(data_dir):
        status = film_status(doc)
        if status not in LIVE_STATUSES:
            continue
        latest = latest_boxoffice_time(doc)
        age_hours = None
        stale = True
        reason = "no_box_office_rows"
        if latest:
            age_hours = (now - latest).total_seconds() / 3600
            stale = age_hours > sla_hours
            reason = "older_than_sla" if stale else "within_sla"
        item = film_identity(path, doc)
        item.update(
            {
                "latest_boxoffice_at": latest.isoformat().replace("+00:00", "Z") if latest else None,
                "age_hours": round(age_hours, 2) if age_hours is not None else None,
                "stale": stale,
                "reason": reason,
            }
        )
        items.append(item)
    stale_items = [item for item in items if item["stale"]]
    return {
        "schema": "bollyai-staleness/v1",
        "generated_at": utc_now(),
        "sla_hours": sla_hours,
        "checked_count": len(items),
        "stale_count": len(stale_items),
        "ok": not stale_items,
        "items": items,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit live tracker staleness report.")
    parser.add_argument("--sla-hours", type=float, default=26)
    parser.add_argument("--emit", help="Optional JSON output path, e.g. data/_state/staleness.json.")
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--now", help="Override now as ISO timestamp.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    now = parse_datetime(args.now) if args.now else None
    payload = check_staleness(data_dir=repo_path(args.data_dir), sla_hours=args.sla_hours, now=now)
    if args.emit:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
