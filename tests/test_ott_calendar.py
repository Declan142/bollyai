from datetime import date
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

from ott_announcements import build_calendar  # noqa: E402


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


def test_generated_calendar_has_source_envelopes():
    calendar = json.loads((REPO_ROOT / "data" / "ott" / "calendar.json").read_text(encoding="utf-8"))

    assert calendar["window"]["start"] == "2026-06-08"
    assert calendar["window"]["end"] == "2026-06-21"
    assert len(calendar["weeks"]) == 2
    assert calendar["entries"], "weekly OTT calendar should not be empty"

    for entry in calendar["entries"]:
        for field in ("title", "platform", "release_date", "language", "industry"):
            claim = entry[field]
            assert "value" in claim, f"{field} must be a source envelope"
            assert claim["confidence"] == "verified"
            assert claim["sources"], f"{field} must cite at least one source"
        official = any(source["type"] in {"press", "official_social"} for source in entry["sources"])
        trade_count = len({source["url"] for source in entry["sources"] if source["type"] == "trade"})
        assert official or trade_count >= 2
