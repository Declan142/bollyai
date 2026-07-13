from datetime import date, datetime as real_datetime
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

import ott_announcements  # noqa: E402
from ott_announcements import build_calendar  # noqa: E402


def test_default_today_uses_india_calendar_date(monkeypatch):
    class FrozenDateTime:
        @classmethod
        def now(cls, timezone):
            assert timezone.key == "Asia/Kolkata"
            return real_datetime(2026, 7, 13, 0, 30, tzinfo=timezone)

    monkeypatch.setattr(ott_announcements, "datetime", FrozenDateTime)
    assert ott_announcements.default_today() == date(2026, 7, 13)


def test_weekly_calendar_requires_official_or_two_trade_sources():
    entries = [
        {
            "id": "single-trade",
            "title": "Single Trade Claim",
            "platform": "Netflix",
            "date": "2026-06-12",
            "industry": "streaming",
            "language": "en",
            "type": "series",
            "sources": [{"name": "One Outlet", "url": "https://example.com/one", "type": "trade"}],
        },
        {
            "id": "official",
            "title": "Official Claim",
            "platform": "Prime Video",
            "date": "2026-06-12",
            "industry": "streaming",
            "language": "en",
            "type": "film",
            "sources": [{"name": "Prime Video", "url": "https://example.com/prime", "type": "press"}],
        },
        {
            "id": "two-trade",
            "title": "Two Trade Claim",
            "platform": "ZEE5",
            "date": "2026-06-13",
            "industry": "streaming",
            "language": "hi",
            "type": "series",
            "sources": [
                {"name": "Outlet A", "url": "https://example.com/a", "type": "trade"},
                {"name": "Outlet B", "url": "https://example.com/b", "type": "trade"},
            ],
        },
    ]

    calendar = build_calendar(entries, start=date(2026, 6, 8), weeks=2)

    titles = [entry["title"]["value"] for entry in calendar["entries"]]
    assert titles == ["Official Claim", "Two Trade Claim"]
    assert calendar["tracking"]["omitted_unverified"] == [{"id": "single-trade", "title": "Single Trade Claim"}]
    assert calendar["weeks"][0]["iso_week"] == "2026-W24"
    assert calendar["weeks"][1]["iso_week"] == "2026-W25"
    assert calendar["entries"][0]["release_date"]["sources"][0]["url"] == "https://example.com/prime"
    assert calendar["entries"][0]["verdict_line"] == "English-language film listed for Prime Video on 2026-06-12."
    assert calendar["entries"][0]["verdict_line_basis"]["kind"] == "calendar_facts"


def test_calendar_verdict_line_uses_catalogue_season_basis():
    entries = [
        {
            "id": "catalogue-season",
            "title": "Example Show Season 2",
            "slug": "example-show",
            "platform": "JioHotstar",
            "date": "2026-06-19",
            "industry": "streaming",
            "language": "hi",
            "type": "series",
            "sources": [{"name": "Platform", "url": "https://example.com/platform", "type": "press"}],
        }
    ]
    series = [
        {
            "slug": "example-show",
            "title": {"value": "Example Show"},
            "seasons": [
                {"number": 1, "bollymeter": {"score": 5.0, "basis": "Season 1 basis."}},
                {"number": 2, "bollymeter": {"score": 8.0, "basis": "Season 2 basis from the catalogue page."}},
            ],
        }
    ]

    calendar = build_calendar(entries, series=series, start=date(2026, 6, 15), weeks=1)

    assert calendar["entries"][0]["verdict_line"] == "Season 2 basis from the catalogue page."
    assert calendar["entries"][0]["verdict_line_basis"] == {
        "kind": "catalogue_page",
        "source_url": "/series/example-show/",
        "source_field": "series.seasons[2].bollymeter.basis",
    }


def test_generated_calendar_has_source_envelopes():
    calendar = json.loads((REPO_ROOT / "data" / "ott" / "calendar.json").read_text(encoding="utf-8"))
    announcements = json.loads((REPO_ROOT / "data" / "ott" / "announcements.json").read_text(encoding="utf-8"))

    # The window rolls forward weekly (a cron regenerates it every Monday), so assert its
    # STRUCTURE - a two-week span from Monday to Sunday - instead of frozen literal dates
    # that go stale every week. This still catches a malformed or wrongly-sized window.
    win_start = date.fromisoformat(calendar["window"]["start"])
    win_end = date.fromisoformat(calendar["window"]["end"])
    assert win_start.weekday() == 0, "OTT calendar window must start on a Monday"
    assert win_end.weekday() == 6, "OTT calendar window must end on a Sunday"
    assert (win_end - win_start).days == 13, "OTT calendar window must span two weeks"
    assert len(calendar["weeks"]) == 2
    assert calendar["entries"], "weekly OTT calendar should not be empty"

    rendered_titles = {entry["title"]["value"] for entry in calendar["entries"]}
    verified_in_window = {
        entry["title"]
        for entry in announcements
        if win_start <= date.fromisoformat(entry["date"]) <= win_end
        and (
            any(source["type"] in {"press", "official_social"} for source in entry["sources"])
            or len({source["url"] for source in entry["sources"] if source["type"] == "trade"}) >= 2
        )
    }
    assert verified_in_window <= rendered_titles, "active calendar dropped a verified announcement in its own window"

    for entry in calendar["entries"]:
        for field in ("title", "platform", "release_date", "language", "industry"):
            claim = entry[field]
            assert "value" in claim, f"{field} must be a source envelope"
            assert claim["confidence"] == "verified"
            assert claim["sources"], f"{field} must cite at least one source"
        official = any(source["type"] in {"press", "official_social"} for source in entry["sources"])
        trade_count = len({source["url"] for source in entry["sources"] if source["type"] == "trade"})
        assert official or trade_count >= 2
        assert entry.get("verdict_line"), "calendar entry must render a verdict line"
        assert entry.get("verdict_line_basis", {}).get("kind") in {"catalogue_page", "calendar_facts"}
