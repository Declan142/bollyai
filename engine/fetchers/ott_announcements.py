"""Weekly OTT calendar assembler from attributed announcements.

The calendar is intentionally announcement-led. A title ships only when it has
one official platform source or at least two distinct trade sources. Single
trade-source claims stay out of the rendered calendar.
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

from common import (
    DATA_DIR,
    FIXTURE_DIR,
    USER_AGENT,
    film_url,
    read_json,
    repo_path,
    unwrap_value,
    utc_now,
    write_json,
)


SOURCE_TYPES = {"press", "official_social", "trade"}
OFFICIAL_SOURCE_TYPES = {"press", "official_social"}
DEFAULT_REGISTRY = DATA_DIR / "ott" / "announcements.json"
ARCHIVE_DIRNAME = "calendar"
TARGET_PLATFORMS = ["Netflix", "Prime Video", "JioHotstar", "ZEE5", "SonyLIV", "aha"]
SOUTH_FIRST_INDUSTRIES = {
    "tollywood": 0,
    "kollywood": 1,
    "mollywood": 2,
    "sandalwood": 3,
    "streaming": 4,
    "bollywood": 5,
    "hollywood": 6,
}


@dataclass(frozen=True)
class SourceRef:
    name: str
    url: str
    source_type: str


@dataclass(frozen=True)
class Announcement:
    item_id: str
    platform: str
    date: str
    sources: tuple[SourceRef, ...]
    fetched_at: str
    title: str
    qid: str | None = None
    slug: str | None = None
    industry: str | None = None
    language: str | None = None
    content_type: str = "film"
    url: str | None = None


def parse_date(value: str) -> date:
    return datetime.strptime(value, "%Y-%m-%d").date()


def default_today() -> date:
    return date.today()


def current_week_start(value: date | None = None) -> date:
    value = value or default_today()
    return value - timedelta(days=value.weekday())


def iso_week_key(value: date) -> str:
    year, week, _ = value.isocalendar()
    return f"{year}-W{week:02d}"


def week_archive_url(value: date) -> str:
    year, week, _ = value.isocalendar()
    return f"/ott/calendar/{year}/wk-{week:02d}/"


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
    title = next((cell for cell in cells if cell and not platform_like(cell) and not re.search(r"\bQ\d+\b", cell)), None)
    if not platform or not (qid or title):
        return None
    return {
        "id": qid or slugify(title or row_text),
        "qid": qid,
        "title": title or qid or "Untitled",
        "platform": platform,
        "date": date_value,
        "source_url": default_url,
        "source_name": "Sacnilk",
        "source_type": "trade",
    }


def platform_like(value: str) -> bool:
    lower = value.lower()
    hints = ("netflix", "prime", "hotstar", "jio", "zee5", "sonyliv", "sony liv", "aha", "sunnxt")
    return any(hint in lower for hint in hints)


def extract_iso_date(text: str) -> str | None:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    return match.group(1) if match else None


def source_refs_from_item(item: dict[str, Any], *, default_source_type: str | None = None) -> tuple[SourceRef, ...]:
    raw_sources = item.get("sources")
    refs: list[SourceRef] = []
    if isinstance(raw_sources, list):
        for raw in raw_sources:
            if not isinstance(raw, dict):
                continue
            url = str(raw.get("url") or "").strip()
            if not url:
                continue
            source_type = str(raw.get("type") or raw.get("source_type") or default_source_type or "trade")
            if source_type not in SOURCE_TYPES:
                raise ValueError(f"Unsupported OTT announcement source_type: {source_type}")
            refs.append(SourceRef(name=str(raw.get("name") or source_type_label(source_type)), url=url, source_type=source_type))

    if not refs and item.get("source_url"):
        source_type = str(item.get("source_type") or default_source_type or "")
        if source_type not in SOURCE_TYPES:
            raise ValueError(f"Unsupported OTT announcement source_type: {source_type}")
        refs.append(
            SourceRef(
                name=str(item.get("source_name") or source_type_label(source_type)),
                url=str(item["source_url"]),
                source_type=source_type,
            )
        )

    return tuple(refs)


def source_type_label(source_type: str) -> str:
    return {
        "press": "Official press",
        "official_social": "Official social",
        "trade": "Trade source",
    }.get(source_type, source_type)


def announcement_from_dict(item: dict[str, Any], *, default_source_type: str | None = None) -> Announcement:
    sources = source_refs_from_item(item, default_source_type=default_source_type)
    title = str(item.get("title") or item.get("name") or "").strip()
    qid_value = item.get("qid")
    qid = str(qid_value) if qid_value not in (None, "") else None
    item_id = str(item.get("id") or qid or item.get("slug") or slugify(title))
    if not item_id:
        raise ValueError("OTT announcement needs id, qid, slug, or title")
    if not title:
        raise ValueError(f"OTT announcement {item_id} needs a title")
    if not sources:
        raise ValueError(f"OTT announcement {item_id} needs at least one source")
    return Announcement(
        item_id=item_id,
        qid=qid,
        platform=str(item["platform"]),
        date=str(item["date"]),
        sources=sources,
        fetched_at=str(item.get("fetched_at") or utc_now()),
        title=title,
        slug=item.get("slug"),
        industry=item.get("industry"),
        language=item.get("language"),
        content_type=str(item.get("type") or item.get("content_type") or "film"),
        url=item.get("url"),
    )


def announcement_to_dict(item: Announcement) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "id": item.item_id,
        "qid": item.qid,
        "platform": item.platform,
        "date": item.date,
        "sources": [source_ref_to_dict(source) for source in item.sources],
        "fetched_at": item.fetched_at,
        "title": item.title,
        "slug": item.slug,
        "industry": item.industry,
        "language": item.language,
        "type": item.content_type,
    }
    if item.url:
        payload["url"] = item.url
    return payload


def source_ref_to_dict(source: SourceRef) -> dict[str, str]:
    return {"name": source.name, "url": source.url, "type": source.source_type}


def build_calendar(
    entries: list[dict[str, Any]],
    *,
    films: list[dict[str, Any]] | None = None,
    series: list[dict[str, Any]] | None = None,
    start: date | None = None,
    weeks: int = 2,
) -> dict[str, Any]:
    start = start or current_week_start()
    end = start + timedelta(days=weeks * 7)
    generated_at = utc_now()
    films_by_qid = {str(unwrap_value(film.get("qid"))): film for film in films or [] if unwrap_value(film.get("qid"))}
    films_by_slug = {str(unwrap_value(film.get("slug"))): film for film in films or [] if unwrap_value(film.get("slug"))}
    series_by_slug = {str(unwrap_value(item.get("slug"))): item for item in series or [] if unwrap_value(item.get("slug"))}
    output_entries = []
    omitted_unverified: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    for raw in entries:
        announcement = announcement_from_dict(raw)
        release_date = parse_date(announcement.date)
        if not (start <= release_date < end):
            continue
        if not is_verified_announcement(announcement):
            omitted_unverified.append({"id": announcement.item_id, "title": announcement.title})
            continue
        key = (announcement.item_id, normalized_platform(announcement.platform))
        if key in seen:
            continue
        seen.add(key)
        film = films_by_qid.get(announcement.qid or "", {}) or films_by_slug.get(str(announcement.slug or ""), {})
        series_doc = series_by_slug.get(str(announcement.slug or ""), {})
        industry = announcement.industry or unwrap_value(film.get("canonical_industry")) or unwrap_value(film.get("industry")) or "streaming"
        language = announcement.language or unwrap_value(film.get("original_language")) or "und"
        slug = announcement.slug or unwrap_value(film.get("slug"))
        resolved_url = resolve_local_url(announcement, industry=str(industry), slug=str(slug) if slug else None)
        week_start = current_week_start(release_date)
        week_index = (week_start - start).days // 7
        first_source = announcement.sources[0]
        sources = [source_ref_to_dict(source) for source in announcement.sources]
        title = announcement.title or unwrap_value(film.get("title")) or "Untitled"
        verdict_line, verdict_line_basis = calendar_verdict_line(
            announcement=announcement,
            film=film,
            series_doc=series_doc,
            title=str(title),
            language=str(language),
            platform=announcement.platform,
            release_date=release_date.isoformat(),
            resolved_url=resolved_url,
        )
        output_entries.append(
            {
                "id": announcement.item_id,
                "qid": announcement.qid,
                "title": claim(title, announcement, generated_at=generated_at),
                "slug": slug,
                "url": resolved_url,
                "industry": claim(str(industry), announcement, generated_at=generated_at),
                "platform": claim(announcement.platform, announcement, generated_at=generated_at),
                "type": announcement.content_type,
                "language": claim(str(language), announcement, generated_at=generated_at),
                "release_date": claim(release_date.isoformat(), announcement, generated_at=generated_at),
                "sources": sources,
                "source_url": first_source.url,
                "source_type": first_source.source_type,
                "verdict_line": verdict_line,
                "verdict_line_basis": verdict_line_basis,
                "fetched_at": announcement.fetched_at,
                "confidence": "verified",
                "verification": verification_basis(announcement),
                "week": iso_week_key(week_start),
                "section": "this_week" if week_index == 0 else "coming",
                "_status": "verified",
            }
        )

    output_entries.sort(key=entry_sort_key)
    week_payloads = build_week_payloads(start=start, weeks=weeks, entries=output_entries)
    present_platforms = {normalized_platform(unwrap_claim(entry["platform"])) for entry in output_entries}
    missing_platforms = [platform for platform in TARGET_PLATFORMS if normalized_platform(platform) not in present_platforms]
    return {
        "schema": "ott-calendar/v1",
        "generated_at": generated_at,
        "window": {
            "start": start.isoformat(),
            "end": (end - timedelta(days=1)).isoformat(),
            "weeks": weeks,
            "basis": "official_announcements",
        },
        "tracking": {
            "platforms": TARGET_PLATFORMS,
            "missing_platforms": missing_platforms,
            "omitted_unverified": omitted_unverified,
        },
        "weeks": week_payloads,
        "entries": output_entries,
        "_provenance": {
            "source": "official_announcements",
            "verification_rule": "official source or two distinct trade sources",
        },
    }


def build_week_payloads(*, start: date, weeks: int, entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payloads = []
    counts_by_week: dict[str, int] = {}
    for entry in entries:
        counts_by_week[str(entry.get("week"))] = counts_by_week.get(str(entry.get("week")), 0) + 1
    for index in range(weeks):
        week_start = start + timedelta(days=index * 7)
        week_end = week_start + timedelta(days=6)
        iso_key = iso_week_key(week_start)
        iso = week_start.isocalendar()
        payloads.append(
            {
                "iso_week": iso_key,
                "year": iso.year,
                "week": iso.week,
                "label": "This week" if index == 0 else "Coming next week",
                "status": "current" if index == 0 else "coming",
                "start": week_start.isoformat(),
                "end": week_end.isoformat(),
                "archive_url": week_archive_url(week_start),
                "entry_count": counts_by_week.get(iso_key, 0),
            }
        )
    return payloads


def write_week_archives(data_dir: Path, calendar: dict[str, Any]) -> list[Path]:
    archive_dir = data_dir / "ott" / ARCHIVE_DIRNAME
    written: list[Path] = []
    for week in calendar.get("weeks", []):
        iso_key = week.get("iso_week")
        if not iso_key:
            continue
        entries = [entry for entry in calendar.get("entries", []) if entry.get("week") == iso_key]
        payload = {
            "schema": "ott-calendar-week/v1",
            "generated_at": calendar.get("generated_at"),
            "week": week,
            "entries": entries,
            "_provenance": calendar.get("_provenance", {}),
        }
        path = archive_dir / f"{iso_key}.json"
        write_json(path, payload)
        written.append(path)
    return written


def is_verified_announcement(announcement: Announcement) -> bool:
    if any(source.source_type in OFFICIAL_SOURCE_TYPES for source in announcement.sources):
        return True
    trade_urls = {source.url for source in announcement.sources if source.source_type == "trade"}
    return len(trade_urls) >= 2


def verification_basis(announcement: Announcement) -> str:
    if any(source.source_type in OFFICIAL_SOURCE_TYPES for source in announcement.sources):
        return "official_source"
    return "two_trade_sources"


def claim(value: Any, announcement: Announcement, *, generated_at: str) -> dict[str, Any]:
    return {
        "value": value,
        "sources": [source_ref_to_dict(source) for source in announcement.sources],
        "fetched_at": announcement.fetched_at or generated_at,
        "confidence": "verified",
    }


def calendar_verdict_line(
    *,
    announcement: Announcement,
    film: dict[str, Any],
    series_doc: dict[str, Any],
    title: str,
    language: str,
    platform: str,
    release_date: str,
    resolved_url: str | None,
) -> tuple[str, dict[str, Any]]:
    if announcement.content_type == "film" and film:
        line, source_field = film_verdict_line(film)
        if line:
            return line, verdict_basis("catalogue_page", resolved_url, source_field)
    if announcement.content_type == "series" and series_doc:
        line, source_field = series_verdict_line(series_doc, title)
        if line:
            return line, verdict_basis("catalogue_page", resolved_url, source_field)
    return neutral_calendar_line(
        content_type=announcement.content_type,
        language=language,
        platform=platform,
        release_date=release_date,
    ), verdict_basis("calendar_facts", None, "calendar.platform_date_language")


def verdict_basis(kind: str, source_url: str | None, source_field: str) -> dict[str, Any]:
    return {
        "kind": kind,
        "source_url": source_url,
        "source_field": source_field,
    }


def film_verdict_line(film: dict[str, Any]) -> tuple[str | None, str]:
    bollymeter = film.get("bollymeter")
    if isinstance(bollymeter, dict):
        basis = clean_verdict_line(bollymeter.get("basis"))
        if basis:
            return basis, "film.bollymeter.basis"

    verdict = film.get("verdict") if isinstance(film.get("verdict"), dict) else {}
    rung = verdict.get("ladder_rung")
    if rung:
        return f"Catalogue trade verdict: {clean_verdict_line(rung)}.", "film.verdict.ladder_rung"

    logline = clean_verdict_line(film.get("logline"))
    if logline:
        return limit_sentences(logline), "film.logline"

    if verdict.get("tracking") is True:
        return "Catalogue verdict is still tracking until the run closes.", "film.verdict.tracking"
    return None, ""


def series_verdict_line(series_doc: dict[str, Any], entry_title: str) -> tuple[str | None, str]:
    season = select_series_season(series_doc, entry_title)
    if not season:
        return None, ""

    season_number = season.get("number")
    bollymeter = season.get("bollymeter")
    if isinstance(bollymeter, dict):
        basis = clean_verdict_line(bollymeter.get("basis"))
        if basis:
            return basis, f"series.seasons[{season_number}].bollymeter.basis"

    verdict = clean_verdict_line(season.get("verdict"))
    if verdict:
        title = clean_verdict_line(unwrap_value(series_doc.get("title")) or series_doc.get("slug") or entry_title)
        return f"{title} Season {season_number} carries a {verdict} catalogue verdict.", f"series.seasons[{season_number}].verdict"

    review_body = str(season.get("review_body") or "")
    open_sentence = sentence_matching(review_body, ("critical reviews", "verdict", "bollymeter"))
    if open_sentence:
        return open_sentence, f"series.seasons[{season_number}].review_body"
    return None, ""


def select_series_season(series_doc: dict[str, Any], entry_title: str) -> dict[str, Any] | None:
    seasons = [season for season in series_doc.get("seasons") or [] if isinstance(season, dict)]
    if not seasons:
        return None
    requested = season_number_from_title(entry_title)
    if requested is not None:
        for season in seasons:
            if season.get("number") == requested:
                return season
    return sorted(seasons, key=lambda season: int(season.get("number") or 0), reverse=True)[0]


def season_number_from_title(title: str) -> int | None:
    match = re.search(r"\bseason\s+(\d+)\b|\bs(\d+)\b", title, flags=re.IGNORECASE)
    if not match:
        return None
    return int(match.group(1) or match.group(2))


def sentence_matching(text: str, needles: tuple[str, ...]) -> str | None:
    for sentence in split_sentences(text):
        lower = sentence.lower()
        if any(needle in lower for needle in needles):
            return clean_verdict_line(sentence)
    return None


def split_sentences(text: str) -> list[str]:
    normalized = clean_verdict_line(text)
    if not normalized:
        return []
    return [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]


def limit_sentences(text: str, max_sentences: int = 2) -> str:
    sentences = split_sentences(text)
    if not sentences:
        return clean_verdict_line(text)
    return " ".join(sentences[:max_sentences])


def clean_verdict_line(value: Any) -> str:
    text = str(value or "").strip()
    text = text.replace("\u2014", " - ").replace("\u2013", " - ")
    return re.sub(r"\s+", " ", text).strip()


def neutral_calendar_line(*, content_type: str, language: str, platform: str, release_date: str) -> str:
    type_label = "film" if content_type == "film" else "series"
    language_label = language_name(language)
    return f"{language_label}-language {type_label} listed for {platform} on {release_date}."


def language_name(code: str) -> str:
    return {
        "bn": "Bengali",
        "en": "English",
        "hi": "Hindi",
        "ml": "Malayalam",
        "ta": "Tamil",
        "te": "Telugu",
    }.get(code.lower(), code.upper())


def unwrap_claim(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def resolve_local_url(announcement: Announcement, *, industry: str, slug: str | None) -> str | None:
    if announcement.url:
        return announcement.url
    if not slug:
        return None
    if announcement.content_type == "series":
        return f"/series/{slug}/"
    if announcement.content_type == "film":
        return film_url(industry, "review", slug)
    return None


def entry_sort_key(item: dict[str, Any]) -> tuple[str, int, str, str]:
    release_date = str(unwrap_claim(item.get("release_date")) or "")
    industry = str(unwrap_claim(item.get("industry")) or "")
    platform = str(unwrap_claim(item.get("platform")) or "")
    title = str(unwrap_claim(item.get("title")) or "")
    return (release_date, SOUTH_FIRST_INDUSTRIES.get(industry, 99), platform, title)


def normalized_platform(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def slugify(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Emit two-week OTT calendar from attributed announcements.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--fixture-path")
    parser.add_argument("--registry", default="data/ott/announcements.json")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD. The week starts on Monday.")
    parser.add_argument("--weeks", type=int, default=2)
    parser.add_argument("--emit", default="data/ott/calendar.json")
    parser.add_argument("--no-archives", action="store_true", help="Do not write week archive JSON files.")
    parser.add_argument("--dry-run", action="store_true", help="Print only; do not write --emit.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    today = parse_date(args.today) if args.today else default_today()
    start = current_week_start(today)
    entries = [announcement_to_dict(item) for item in load_registry(repo_path(args.registry))]
    entries.extend(
        announcement_to_dict(item)
        for item in load_sacnilk_announcements(
            fixture_mode=args.fixture_mode,
            fixture_path=repo_path(args.fixture_path) if args.fixture_path else None,
        )
    )
    payload = build_calendar(entries, start=start, weeks=args.weeks)
    emit_path = repo_path(args.emit)
    archive_data_dir = emit_path.parents[1] if emit_path.name == "calendar.json" and emit_path.parent.name == "ott" else DATA_DIR
    if not args.dry_run:
        write_json(emit_path, payload)
        if not args.no_archives:
            write_week_archives(archive_data_dir, payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
