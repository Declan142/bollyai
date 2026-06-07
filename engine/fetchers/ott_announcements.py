"""Official-announcement OTT calendar assembler.

The layer consumes attributed announcements from two places:

* data/ott/announcements.json, curated by QID.
* Saved Sacnilk OTT-list fixtures, with a small HTML/table fallback parser.

Live parsing is intentionally best-effort and degrades to an empty source when
the page cannot be fetched.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - fixture and registry mode still work.
    requests = None

from common import DATA_DIR, FIXTURE_DIR, USER_AGENT, read_json, repo_path, source_value, unwrap_value, utc_now, write_json


SOURCE_TYPES = {"press", "official_social", "trade"}
DEFAULT_REGISTRY = DATA_DIR / "ott" / "announcements.json"


@dataclass(frozen=True)
class Announcement:
    qid: str
    platform: str
    date: str
    source_url: str
    source_type: str
    fetched_at: str
    title: str | None = None
    slug: str | None = None
    industry: str | None = None
    language: str | None = None
    content_type: str = "film"


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def default_today() -> date:
    return date.today()


def load_announcements(*, fixture_mode: bool = False, data_dir: Path = DATA_DIR) -> list[dict[str, Any]]:
    entries = load_registry(data_dir / "ott" / "announcements.json")
    entries.extend(load_sacnilk_announcements(fixture_mode=fixture_mode))
    return [announcement_to_dict(item) for item in entries]


def load_registry(path: Path = DEFAULT_REGISTRY) -> list[Announcement]:
    payload = read_json(path, default=[])
    entries = payload if isinstance(payload, list) else payload.get("entries", [])
    return [announcement_from_dict(item) for item in entries if isinstance(item, dict)]


def load_sacnilk_announcements(
    *,
    fixture_mode: bool = False,
    fixture_path: Path | None = None,
    url: str | None = None,
) -> list[Announcement]:
    if fixture_mode:
        payload = read_json(fixture_path or FIXTURE_DIR / "ott_sacnilk_releases.json", default={"entries": []})
        return parse_sacnilk_payload(payload)

    if not url or requests is None:
        return []
    try:
        response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}, timeout=20)
    except requests.RequestException:
        return []
    if response.status_code == 429 or response.status_code >= 500:
        return []
    if response.status_code >= 400:
        return []
    return parse_sacnilk_payload({"html": response.text, "source_url": url, "fetched_at": utc_now()})


def parse_sacnilk_payload(payload: dict[str, Any]) -> list[Announcement]:
    if "entries" in payload:
        return [announcement_from_dict(item, default_source_type="trade") for item in payload.get("entries", [])]

    html = payload.get("html")
    if not html:
        return []
    parser = SacnilkOttParser()
    parser.feed(html)
    announcements = []
    for row in parser.rows:
        parsed = parse_row_cells(row, default_url=payload.get("source_url") or "")
        if parsed:
            announcements.append(
                announcement_from_dict(
                    {
                        **parsed,
                        "source_type": "trade",
                        "fetched_at": payload.get("fetched_at") or utc_now(),
                    }
                )
            )
    return announcements


class SacnilkOttParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.in_cell = False
        self.current_cell: list[str] = []
        self.current_row: list[str] = []
        self.rows: list[list[str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"td", "th"}:
            self.in_cell = True
            self.current_cell = []

    def handle_data(self, data: str) -> None:
        if self.in_cell:
            self.current_cell.append(data)

    def handle_endtag(self, tag: str) -> None:
        lower = tag.lower()
        if lower in {"td", "th"} and self.in_cell:
            self.current_row.append(" ".join(self.current_cell).strip())
            self.in_cell = False
        elif lower == "tr" and self.current_row:
            self.rows.append(self.current_row)
            self.current_row = []


def parse_row_cells(cells: list[str], *, default_url: str) -> dict[str, Any] | None:
    row_text = " ".join(cells)
    date_value = extract_iso_date(row_text)
    if not date_value:
        return None
    platform = next((cell for cell in cells if platform_like(cell)), None)
    qid = next((match.group(0) for cell in cells for match in [re.search(r"\bQ\d+\b", cell)] if match), None)
    if not platform or not qid:
        return None
    return {
        "qid": qid,
        "platform": platform,
        "date": date_value,
        "source_url": default_url,
        "source_type": "trade",
    }


def platform_like(value: str) -> bool:
    lower = value.lower()
    hints = ("netflix", "prime", "hotstar", "jio", "zee5", "sonyliv", "aha", "sunnxt")
    return any(hint in lower for hint in hints)


def extract_iso_date(text: str) -> str | None:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    return match.group(1) if match else None


def announcement_from_dict(item: dict[str, Any], *, default_source_type: str | None = None) -> Announcement:
    source_type = str(item.get("source_type") or default_source_type or "")
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"Unsupported OTT announcement source_type: {source_type}")
    qid = str(item["qid"])
    platform = str(item["platform"])
    return Announcement(
        qid=qid,
        platform=platform,
        date=str(item["date"]),
        source_url=str(item["source_url"]),
        source_type=source_type,
        fetched_at=str(item.get("fetched_at") or utc_now()),
        title=item.get("title"),
        slug=item.get("slug"),
        industry=item.get("industry"),
        language=item.get("language"),
        content_type=str(item.get("type") or item.get("content_type") or "film"),
    )


def announcement_to_dict(item: Announcement) -> dict[str, Any]:
    return {
        "qid": item.qid,
        "platform": item.platform,
        "date": item.date,
        "source_url": item.source_url,
        "source_type": item.source_type,
        "fetched_at": item.fetched_at,
        "title": item.title,
        "slug": item.slug,
        "industry": item.industry,
        "language": item.language,
        "type": item.content_type,
    }


def build_calendar(
    entries: list[dict[str, Any]],
    *,
    films: list[dict[str, Any]] | None = None,
    start: date | None = None,
    weeks: int = 4,
) -> dict[str, Any]:
    start = start or default_today()
    end = start + timedelta(days=weeks * 7)
    generated_at = utc_now()
    films_by_qid = {str(unwrap_value(film.get("qid"))): film for film in films or [] if unwrap_value(film.get("qid"))}
    output_entries = []
    seen: set[tuple[str, str]] = set()

    for raw in entries:
        announcement = announcement_from_dict(raw)
        release_date = parse_date(announcement.date)
        if not (start <= release_date < end):
            continue
        key = (announcement.qid, normalized_platform(announcement.platform))
        if key in seen:
            continue
        seen.add(key)
        film = films_by_qid.get(announcement.qid, {})
        title = announcement.title or unwrap_value(film.get("title")) or "Untitled"
        output_entries.append(
            {
                "qid": announcement.qid,
                "title": title,
                "slug": announcement.slug or unwrap_value(film.get("slug")),
                "industry": announcement.industry or unwrap_value(film.get("canonical_industry")) or unwrap_value(film.get("industry")),
                "platform": announcement.platform,
                "type": announcement.content_type,
                "language": announcement.language or unwrap_value(film.get("original_language")),
                "release_date": source_value(
                    release_date.isoformat(),
                    "ott_announcements",
                    fetched_at=announcement.fetched_at or generated_at,
                    confidence="verified",
                ),
                "source_url": announcement.source_url,
                "source_type": announcement.source_type,
                "fetched_at": announcement.fetched_at,
                "_status": "verified",
            }
        )

    output_entries.sort(key=lambda item: (item["release_date"]["value"], item.get("platform") or "", item.get("title") or ""))
    return {
        "schema": "ott-calendar/v1",
        "generated_at": generated_at,
        "window": {
            "start": start.isoformat(),
            "end": (end - timedelta(days=1)).isoformat(),
            "weeks": weeks,
            "basis": "official_announcements",
        },
        "entries": output_entries,
        "_provenance": {
            "source": "official_announcements",
        },
    }


def normalized_platform(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit next-four-weeks OTT calendar from attributed announcements.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--fixture-path")
    parser.add_argument("--registry", default="data/ott/announcements.json")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD.")
    parser.add_argument("--weeks", type=int, default=4)
    parser.add_argument("--emit", default="data/ott/calendar.json")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not write --emit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    start = parse_date(args.today) if args.today else default_today()
    entries = [announcement_to_dict(item) for item in load_registry(repo_path(args.registry))]
    entries.extend(
        announcement_to_dict(item)
        for item in load_sacnilk_announcements(
            fixture_mode=args.fixture_mode,
            fixture_path=repo_path(args.fixture_path) if args.fixture_path else None,
        )
    )
    payload = build_calendar(entries, start=start, weeks=args.weeks)
    if not args.dry_run:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
