from datetime import date, datetime as real_datetime
from dataclasses import replace
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine" / "fetchers"))

import ott_announcements  # noqa: E402
from ott_announcements import build_calendar  # noqa: E402


def eligible_announcement(item):
    announcement = ott_announcements.announcement_from_dict(item)
    return replace(announcement, sources=ott_announcements.eligible_sources(announcement))


def test_generated_pages_sitemap_has_unique_platform_routes():
    root = ET.parse(REPO_ROOT / "site" / "public" / "sitemap-pages.xml").getroot()
    locations = [node.text for node in root.findall("{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc")]
    assert len(locations) == len(set(locations))
    assert locations.count("https://bollyai.in/ott/apple-tv/") == 1


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
            "sources": [{"name": "Prime Video", "url": "https://www.primevideo.com/detail/example", "type": "press"}],
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
                {"name": "Outlet B", "url": "https://another.example/b", "type": "trade"},
            ],
        },
    ]

    calendar = build_calendar(entries, start=date(2026, 6, 8), weeks=2)

    titles = [entry["title"]["value"] for entry in calendar["entries"]]
    assert titles == ["Official Claim", "Two Trade Claim"]
    assert calendar["tracking"]["omitted_unverified"] == [{"id": "single-trade", "title": "Single Trade Claim"}]
    assert calendar["weeks"][0]["iso_week"] == "2026-W24"
    assert calendar["weeks"][1]["iso_week"] == "2026-W25"
    assert calendar["entries"][0]["release_date"]["sources"][0]["url"] == "https://www.primevideo.com/detail/example"
    assert calendar["entries"][0]["verdict_line"] == "English-language film listed for Prime Video on 2026-06-12."
    assert calendar["entries"][0]["verdict_line_basis"]["kind"] == "calendar_facts"


def test_press_label_on_arbitrary_or_reference_hosts_is_not_official():
    for url in (
        "https://example.com/press-release",
        "https://www.wikidata.org/wiki/Q42",
        "https://en.wikipedia.org/wiki/Example",
        "http://www.netflix.com/tudum/example",
        "https://user:password@www.netflix.com/tudum/example",
        "https://www.netflix.com/tudum/example?campaign=release",
        "https://www.netflix.com/tudum/example#release",
        "javascript:alert(1)",
    ):
        assert not ott_announcements.is_official_source(
            ott_announcements.SourceRef("Press", url, "press"),
            "Netflix",
        )


def test_platform_controlled_https_host_is_official():
    assert ott_announcements.is_official_source(
        ott_announcements.SourceRef("Hulu Press", "https://press.hulu.com/schedule/august-2026/", "press"),
        "Hulu",
    )


def test_first_party_host_must_match_the_claimed_platform():
    apple = ott_announcements.SourceRef("Apple TV Press", "https://www.apple.com/tv-pr/news/example", "press")
    assert ott_announcements.is_official_source(apple, "Apple TV+")
    assert not ott_announcements.is_official_source(apple, "Netflix")


def test_official_social_metadata_does_not_verify_without_an_account_allowlist():
    social = ott_announcements.SourceRef("Netflix", "https://www.netflix.com/tudum/example", "official_social")
    assert not ott_announcements.is_official_source(social, "Netflix")


def test_two_trade_urls_from_one_host_are_not_independent():
    item = {
        "id": "same-host-trades",
        "title": "Same Host Trades",
        "platform": "Netflix",
        "date": "2026-06-12",
        "industry": "streaming",
        "language": "en",
        "type": "series",
        "sources": [
            {"name": "Outlet A", "url": "https://example.com/one", "type": "trade"},
            {"name": "Outlet A", "url": "https://example.com/two", "type": "trade"},
        ],
    }
    calendar = build_calendar([item], start=date(2026, 6, 8), weeks=1)
    assert calendar["entries"] == []
    assert calendar["tracking"]["omitted_unverified"] == [{"id": "same-host-trades", "title": "Same Host Trades"}]


def test_unsafe_trade_urls_never_verify_or_render():
    item = {
        "id": "script-trades",
        "title": "Script Trades",
        "platform": "Netflix",
        "date": "2026-06-12",
        "industry": "streaming",
        "language": "en",
        "type": "series",
        "sources": [
            {"name": "Outlet A", "url": "javascript:alert(1)", "type": "trade"},
            {"name": "Outlet B", "url": "javascript:alert(2)", "type": "trade"},
        ],
    }
    calendar = build_calendar([item], start=date(2026, 6, 8), weeks=1)
    assert calendar["entries"] == []


def test_calendar_verdict_line_uses_catalogue_season_basis():
    entries = [
        {
            "id": "catalogue-season",
            "title": "Example Show Season 2",
            "slug": "example-show",
            "platform": "Netflix",
            "date": "2026-06-19",
            "industry": "streaming",
            "language": "hi",
            "type": "series",
            "sources": [{"name": "Platform", "url": "https://www.netflix.com/tudum/example", "type": "press"}],
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


def test_uncatalogued_slug_does_not_create_a_broken_local_link():
    entries = [
        {
            "id": "uncatalogued-series",
            "title": "Uncatalogued Series",
            "slug": "uncatalogued-series",
            "platform": "Netflix",
            "date": "2026-06-19",
            "industry": "streaming",
            "language": "en",
            "type": "series",
            "sources": [{"name": "Netflix", "url": "https://www.netflix.com/tudum/example", "type": "press"}],
        }
    ]
    calendar = build_calendar(entries, start=date(2026, 6, 15), weeks=1)
    assert calendar["entries"][0]["slug"] == "uncatalogued-series"
    assert calendar["entries"][0]["url"] is None


def test_backslash_paths_cannot_escape_the_local_origin():
    for unsafe_url in (r"/\evil", r"/\\evil", "/\n//evil", "/\r//evil", "/\t//evil"):
        entries = [
            {
                "id": "unsafe-local-url",
                "title": "Unsafe Local URL",
                "platform": "Netflix",
                "date": "2026-06-19",
                "industry": "streaming",
                "language": "en",
                "type": "series",
                "url": unsafe_url,
                "sources": [
                    {
                        "name": "Netflix",
                        "url": "https://www.netflix.com/tudum/example",
                        "type": "press",
                    }
                ],
            }
        ]

        calendar = build_calendar(entries, start=date(2026, 6, 15), weeks=1)

        assert calendar["entries"][0]["url"] is None


def test_calendar_does_not_reuse_an_older_season_basis_for_a_new_season():
    entries = [
        {
            "id": "catalogue-season-2",
            "title": "Example Show Season 2",
            "slug": "example-show",
            "platform": "Apple TV",
            "date": "2026-08-28",
            "industry": "streaming",
            "language": "en",
            "type": "series",
            "sources": [
                {
                    "name": "Platform",
                    "url": "https://www.apple.com/tv-pr/news/example",
                    "type": "press",
                }
            ],
        }
    ]
    series = [
        {
            "slug": "example-show",
            "title": {"value": "Example Show"},
            "seasons": [
                {
                    "number": 1,
                    "bollymeter": {
                        "score": 8.0,
                        "basis": "Season 1 catalogue basis must not leak.",
                    },
                }
            ],
        }
    ]

    calendar = build_calendar(
        entries,
        series=series,
        start=date(2026, 8, 24),
        weeks=1,
    )

    assert (
        calendar["entries"][0]["verdict_line"]
        == "English-language series listed for Apple TV on 2026-08-28."
    )
    assert calendar["entries"][0]["verdict_line_basis"] == {
        "kind": "calendar_facts",
        "source_url": None,
        "source_field": "calendar.platform_date_language",
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

    rendered_titles = {entry["title"]["value"] for entry in calendar["entries"]}
    verified_in_window = {
        entry["title"]
        for entry in announcements
        if win_start <= date.fromisoformat(entry["date"]) <= win_end
        and ott_announcements.is_verified_announcement(eligible_announcement(entry))
    }
    assert verified_in_window <= rendered_titles, "active calendar dropped a verified announcement in its own window"
    if not calendar["entries"]:
        assert not verified_in_window, (
            "an empty calendar is valid only when its window has no source-verified announcements"
        )

    for entry in calendar["entries"]:
        for field in ("title", "platform", "release_date", "language", "industry"):
            claim = entry[field]
            assert "value" in claim, f"{field} must be a source envelope"
            assert claim["confidence"] == "verified"
            assert claim["sources"], f"{field} must cite at least one source"
        official = any(
            ott_announcements.is_official_source(
                ott_announcements.SourceRef(source["name"], source["url"], source["type"]),
                entry["platform"]["value"],
            )
            for source in entry["sources"]
        )
        trade_hosts = ott_announcements.trade_source_hosts(
            tuple(ott_announcements.SourceRef(source["name"], source["url"], source["type"]) for source in entry["sources"])
        )
        assert official or len(trade_hosts) >= 2
        assert all(ott_announcements.is_safe_source_url(source["url"]) for source in entry["sources"])
        assert entry.get("verdict_line"), "calendar entry must render a verdict line"
        assert entry.get("verdict_line_basis", {}).get("kind") in {"catalogue_page", "calendar_facts"}
        if entry["language"]["value"] == "und":
            assert "UND-language" not in entry["verdict_line"]
            assert entry["verdict_line_basis"]["source_field"] == "calendar.platform_date"
