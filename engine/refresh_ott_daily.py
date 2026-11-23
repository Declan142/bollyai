"""Refresh the public two-week calendar from Apple's press feed and verified registry."""

from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

from regen_ott_weekly import load_films, load_series
from apple_ott_press import SourceError, fetch_press
from common import DATA_DIR, read_json, utc_now, write_json
from ott_announcements import build_calendar, current_week_start, default_today


APPLE_ORIGIN = "apple-tv-press"
PRESS_PREFIX = "https://www.apple.com/tv-pr/originals/"


def press_url(row: dict) -> str:
    urls = [source["url"] for source in row["sources"] if source["url"].startswith(PRESS_PREFIX)]
    if len(urls) != 1:
        raise ValueError(f"Expected one Apple Originals receipt for {row['id']}")
    return urls[0]


def identity(row: dict) -> tuple[str, str, str]:
    platform = row["platform"].replace("Apple TV+", "Apple TV")
    return platform, row.get("type", "film"), " ".join(row["title"].casefold().split())


def merge_apple(registry: list[dict], fetched: list[dict], checked: set[str],
                start: date, stamp: str) -> list[dict]:
    """Retain curated decisions and historical rows. A changed official date keeps its source ID."""
    incoming = {press_url(row): row for row in fetched}
    if len(incoming) != len(fetched) or not incoming.keys() <= checked:
        raise ValueError("Apple announcement identities do not match checked title pages")
    merged = []
    protected = {identity(row) for row in registry if row.get("origin") not in (APPLE_ORIGIN, "fetched")}
    incoming_titles = {identity(row) for row in fetched}
    for old in registry:
        if old.get("origin") != APPLE_ORIGIN:
            if old.get("origin") == "fetched" and identity(old) in incoming_titles - protected:
                continue
            merged.append(old)
            continue
        url = press_url(old)
        if url not in checked:
            if old["date"] >= start.isoformat():
                raise SourceError(f"Previously announced title did not receive a current check: {url}")
            merged.append(old)
            continue
        new = incoming.pop(url, None)
        if new is None:
            if old["date"] < start.isoformat():
                merged.append(old)
            continue
        if identity(new) in protected:
            continue
        prior = {key: value for key, value in old.items() if key != "fetched_at"}
        merged.append(old if prior == new else dict(new, fetched_at=stamp))
    merged.extend(dict(row, fetched_at=stamp) for row in incoming.values() if identity(row) not in protected)
    return merged


def edition_content(calendar: dict) -> dict:
    # The weekly writer has its own discovery/clock metadata. Only changes to the
    # calendar itself warrant a new public edition or a new issue timestamp.
    return {key: calendar[key] for key in ("schema", "window", "entries", "weeks", "tracking")}


def refresh(data_dir: Path = DATA_DIR, today: date | None = None, fetch=fetch_press) -> str:
    start = current_week_start(today or default_today())
    registry_path = data_dir / "ott" / "announcements.json"
    calendar_path = data_dir / "ott" / "calendar.json"
    registry = read_json(registry_path)
    previous = read_json(calendar_path)
    if not isinstance(registry, list) or not isinstance(previous, dict):
        raise ValueError("Both existing public calendar files are required")
    known = {press_url(row) for row in registry if row.get("origin") == APPLE_ORIGIN and row["date"] >= start.isoformat()}
    # Keep future announced dates in the registry even when the short news feed
    # rolls past them. The visitor edition itself always covers exactly two weeks.
    candidates, checked = fetch(known, start, date.max)
    if not checked:
        raise SourceError("No official Apple Originals pages were checked")
    merged = merge_apple(registry, candidates, checked, start, utc_now())
    calendar = build_calendar(merged, films=load_films(data_dir), series=load_series(data_dir), start=start, weeks=2)
    different = edition_content(calendar) != edition_content(previous)
    if different:
        calendar["_provenance"]["daily_source"] = {
            "feed": "https://www.apple.com/tv-pr/news-feed.xml",
            "scope": "Apple Originals streaming premieres checked against Apple TV India",
        }
    # Every upstream lookup and calendar validation completes before any public
    # file is written. GitHub publishes both tracked files in one commit.
    if merged != registry:
        write_json(registry_path, merged, sort_keys=False)
    if different:
        write_json(calendar_path, calendar)
    result = "updated" if different or merged != registry else "unchanged"
    return (f"Checked {len(checked)} Apple Originals pages. Calendar {result}: "
            f"{len(calendar['entries'])} verified releases for {start} to {calendar['window']['end']}.")


if __name__ == "__main__":
    try:
        print(refresh())
    except (SourceError, ValueError, OSError) as error:
        print(f"OTT calendar refresh failed: {error}", file=sys.stderr)
        sys.exit(1)
