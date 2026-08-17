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
    default_today,
    load_announcements,
    normalized_platform,
    parse_date,
    write_week_archives,
)
from ott_western import fetch_western_ott  # noqa: E402


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


def merge_announcement_entries(
    existing: list[dict[str, Any]], fetched: list[dict[str, Any]]
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """Append-only registry merge. Hand-curated entries always win; a fetched entry is a
    dupe if EITHER its (qid, platform) or its (id, platform) already exists - the two
    fetch paths (Wikidata carries qid, TMDB does not) share slugged ids, so keying on
    both stops the same title entering twice across runs.

    One exception to append-only (2026-07-07 R2): platforms reschedule constantly, and a
    pure append meant a moved release date stayed wrong forever - the key matched, the
    stale date won. When BOTH sides are fetched-origin and the incoming date differs, the
    existing entry takes the corrected date (plus the newer sources/fetched_at) in place.
    Entries without origin == "fetched" are curated: never touched, ever.

    Returns (merged, {"added": n, "updated": n})."""

    def keys(item: dict[str, Any]) -> set[tuple[str, str, str]]:
        platform = normalized_platform(str(item.get("platform") or ""))
        out = set()
        if item.get("qid"):
            out.add(("qid", str(item["qid"]), platform))
        if item.get("id"):
            out.add(("id", str(item["id"]), platform))
        return out

    by_key: dict[tuple[str, str, str], dict[str, Any]] = {}
    for item in existing:
        for k in keys(item):
            by_key.setdefault(k, item)
    merged = list(existing)
    added = updated = 0
    for item in fetched:
        item_keys = keys(item)
        hit = next((by_key[k] for k in item_keys if k in by_key), None)
        if hit is not None:
            if (
                hit.get("origin") == "fetched"
                and item.get("origin") == "fetched"
                and item.get("date")
                and item["date"] != hit.get("date")
            ):
                hit["date"] = item["date"]
                if item.get("fetched_at"):
                    hit["fetched_at"] = item["fetched_at"]
                if item.get("sources"):
                    hit["sources"] = item["sources"]
                updated += 1
            continue
        for k in item_keys:
            by_key[k] = item
        merged.append(item)
        added += 1
    return merged, {"added": added, "updated": updated}


def refresh_registry(data_dir: Path, window_start: date, window_end: date) -> dict[str, int]:
    """Pull fresh Western OTT announcements into the registry (append-only, curated wins).
    The caller fails closed before calendar writes when every live fetcher returns
    zero; --no-fetch is the explicit registry-only rebuild path."""
    fetched = fetch_western_ott(window_start=window_start, window_end=window_end)
    registry_path = data_dir / "ott" / "announcements.json"
    raw = read_json(registry_path, default=[])
    existing = raw if isinstance(raw, list) else raw.get("entries", [])
    merged, stats = merge_announcement_entries(existing, fetched)
    if stats["added"] or stats["updated"]:
        # sort_keys=False: preserve each entry's own key order so the diff is a pure
        # append (or a surgical date correction on a fetched-origin entry).
        write_json(registry_path, merged, sort_keys=False)
    return {"fetched": len(fetched), "added": stats["added"], "updated": stats["updated"]}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Regenerate BollyAI weekly OTT calendar data.")
    parser.add_argument("--fixture-mode", action="store_true", help="Use saved fixtures where fetchers support them.")
    parser.add_argument("--data-dir", default="data", help="Data directory to read and write.")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD. The week starts on Monday.")
    parser.add_argument("--weeks", type=int, default=2)
    parser.add_argument("--past-weeks", type=int, default=0, help="Extend window this many weeks into the past (default 0).")
    parser.add_argument("--dry-run", action="store_true", help="Print result only; do not write files.")
    parser.add_argument("--no-fetch", action="store_true", help="Skip the announcements fetch; rebuild from the registry as-is.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = repo_path(args.data_dir)
    today = parse_date(args.today) if args.today else default_today()
    current_monday = current_week_start(today)
    past_weeks = max(0, args.past_weeks)
    adjusted_start = current_monday - timedelta(days=past_weeks * 7)
    total_weeks = past_weeks + args.weeks
    start = adjusted_start
    registry_stats = {"fetched": 0, "added": 0, "updated": 0}
    if not (args.no_fetch or args.fixture_mode or args.dry_run):
        registry_stats = refresh_registry(data_dir, start, start + timedelta(days=total_weeks * 7))
    announcements = load_announcements(fixture_mode=args.fixture_mode, data_dir=data_dir)
    calendar = build_calendar(announcements, films=load_films(data_dir), series=load_series(data_dir), start=start, weeks=total_weeks)
    if (
        not (args.no_fetch or args.fixture_mode or args.dry_run)
        and registry_stats["fetched"] == 0
    ):
        print(
            "ERROR: live OTT refresh fetched zero announcements; calendar was not written from potentially stale registry data. "
            "Inspect source availability or use --no-fetch for an explicit registry-only rebuild.",
            file=sys.stderr,
        )
        return 2
    # Honesty stamp (2026-07-07 R2): a registry-only rebuild used to write a calendar
    # byte-identical in shape to a fetch-refreshed one - generated_at moved, so a dead
    # network or a --no-fetch run LOOKED fresh downstream. The artifact now records how
    # it was refreshed; auditors and the QA lane read it instead of guessing.
    refresh_mode = (
        "fixture" if args.fixture_mode
        else "no-fetch" if args.no_fetch
        else "dry-run" if args.dry_run
        else "fetched"
    )
    calendar.setdefault("_provenance", {})["refresh"] = {
        "mode": refresh_mode,
        "fetched": registry_stats["fetched"],
        "added": registry_stats["added"],
        "updated": registry_stats["updated"],
        "at": utc_now(),
    }
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
        "refresh_mode": refresh_mode,
        "registry_fetched": registry_stats["fetched"],
        "registry_added": registry_stats["added"],
        "registry_updated": registry_stats["updated"],
        "weeks": [week.get("iso_week") for week in calendar.get("weeks", [])],
        "changed_urls": urls,
        "wrote": wrote,
    }
    json.dump(result, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
