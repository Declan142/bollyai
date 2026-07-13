"""Regression gates for the public Western-only BollyAI brand."""

import json
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
PUBLIC_SURFACES = [
    "README.md",
    "site/app/page.tsx",
    "site/app/ask/page.tsx",
    "site/app/watch/page.tsx",
    "site/app/about/page.tsx",
    "site/app/browse/page.tsx",
    "site/lib/seo.ts",
]
FORBIDDEN_POSITIONING = [
    "pan-india",
    "seven desks",
    "indian entertainment",
    "indian cinema",
    "korean drama",
    "k-drama",
    "anime",
    "indian & global",
]


def test_public_positioning_stays_western_only():
    leaks = []
    for relative_path in PUBLIC_SURFACES:
        text = (REPO_ROOT / relative_path).read_text(encoding="utf-8").lower()
        for phrase in FORBIDDEN_POSITIONING:
            if phrase in text:
                leaks.append(f"{relative_path}: {phrase}")
    assert not leaks, "off-brand positioning returned to public surfaces:\n" + "\n".join(leaks)


def test_ask_regions_and_film_desk_match_the_catalogue():
    ask_client = (REPO_ROOT / "site/components/AskClient.tsx").read_text(encoding="utf-8")
    assert 'label: "Indian"' not in ask_client
    assert 'label: "Korean"' not in ask_client
    assert 'label: "Japanese"' not in ask_client
    assert 'rec.k === "Series" ? "streaming" : "hollywood"' in ask_client


def test_footer_links_only_to_real_verdict_hubs():
    footer = (REPO_ROOT / "site/components/Footer.tsx").read_text(encoding="utf-8")
    assert 'href="/hollywood/reviews/"' not in footer
    assert 'href="/hollywood/upcoming/"' not in footer
    assert 'href="/hollywood/"' in footer
    assert 'href="/series/"' in footer


def test_home_leads_with_one_question_and_one_heading():
    homepage = (REPO_ROOT / "site/app/page.tsx").read_text(encoding="utf-8")
    assert 'action="/ask/"' in homepage
    assert homepage.count("<h1") == 1
    assert "latestSeries(8)" in homepage
    assert "Current releases, no legacy filler" in homepage
    assert 'return "Verdict pending"' in homepage


def test_latest_series_contract_is_date_led_and_bounded():
    home_lib = (REPO_ROOT / "site/lib/home.ts").read_text(encoding="utf-8")
    series_lib = (REPO_ROOT / "site/lib/series.ts").read_text(encoding="utf-8")
    assert "LATEST_SERIES_WINDOW_DAYS = 90" in home_lib
    assert "const releaseDate = latestSeasonReleaseDate(series)" in home_lib
    assert "if (!releaseDate) return null" in home_lib
    assert "age >= 0 && age <= windowMs" in home_lib
    assert "b.recency.localeCompare(a.recency) || a.title.localeCompare(b.title)" in home_lib
    assert "const bm = latestSeason(s)?.bollymeter ?? null" in home_lib
    assert "const maxHeroAgeMs = 120 * 86400000" in home_lib
    strict_helper = series_lib.split("export function latestSeasonReleaseDate", 1)[1].split("export function seriesRecency", 1)[0]
    assert "series.date_modified" not in strict_helper
    fresh_helper = series_lib.split("export function isFreshSeries", 1)[1].split("export function getSeriesByRecency", 1)[0]
    assert "const releaseDate = latestSeasonReleaseDate(series)" in fresh_helper
    assert "seriesRecency(series)" not in fresh_helper


def test_deep_reads_use_real_air_dates_and_valid_routes():
    series_lib = (REPO_ROOT / "site/lib/series.ts").read_text(encoding="utf-8")
    homepage = (REPO_ROOT / "site/app/page.tsx").read_text(encoding="utf-8")
    assert "!ep.review_body?.trim() || !ep.air_date" in series_lib
    assert "sort_key: ep.air_date" in series_lib
    assert "series.date_modified" not in series_lib.split("export function getNewestEpisodeReviews", 1)[1]
    assert "/s${card.season_number}/e${episode.number}/" in homepage


def test_new_and_next_reserves_current_and_upcoming_slots():
    home_lib = (REPO_ROOT / "site/lib/home.ts").read_text(encoding="utf-8")
    assert "const droppedSlots = Math.ceil(count / 2)" in home_lib
    assert "const comingSlots = count - droppedSlots" in home_lib
    assert "seriesByTitle.get(seriesLookupKey(e.title))" in home_lib


def test_current_series_seasons_do_not_fall_back_to_legacy_data():
    expected = {
        "silo": (3, "2026-07-03"),
        "avatar-the-last-airbender": (2, "2026-06-25"),
        "little-house-on-the-prairie": (1, "2026-07-09"),
        "the-man-will-burn": (1, "2026-07-09"),
        "maximum-pleasure-guaranteed": (1, "2026-05-20"),
        "cape-fear": (1, "2026-06-05"),
        "sweet-magnolias-season-5": (5, "2026-06-11"),
    }
    for slug, (season_number, release_date) in expected.items():
        path = REPO_ROOT / "data" / "series" / f"{slug}.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        latest = max(payload["seasons"], key=lambda season: season["number"])
        assert latest["number"] == season_number, slug
        assert latest["release_date"]["value"] == release_date, slug


def test_current_upcoming_series_is_in_the_announcement_feed():
    announcements = json.loads((REPO_ROOT / "data" / "ott" / "announcements.json").read_text(encoding="utf-8"))
    by_title = {entry["title"]: entry for entry in announcements}
    stuart = by_title["Stuart Fails to Save the Universe"]
    assert stuart["date"] == "2026-07-23"
    assert stuart["platform"] == "HBO Max"
    assert stuart["sources"][0]["url"] == "https://press.wbd.com/us/media-release/whats-new-hbo-max-july"
