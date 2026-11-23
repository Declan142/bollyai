from datetime import date, datetime, timezone
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine" / "fetchers"))
from apple_ott_press import FEED, SourceError, fetch_press, release_day


START, END = date(2026, 11, 23), date(2026, 12, 7)
ARTICLE = "https://www.apple.com/tv-pr/news/2026/11/premieres/"
BASE = "https://www.apple.com/tv-pr/originals/"


def card(kind, name, day=None):
    data = {"@type": kind, "name": name}
    if day:
        data["datePublished"] = day
    return '<script type="application/ld+json">' + json.dumps(data) + "</script>"


def example_pages():
    updated = datetime.now(timezone.utc).isoformat()
    pages = {FEED: f'''<feed xmlns="http://www.w3.org/2005/Atom"><title>Apple TV Press</title>
      <updated>{updated}</updated><entry><title>Short feed headline</title><link href="{ARTICLE}"/>
      <link rel="enclosure" href="https://example.org/artwork"/></entry></feed>'''}
    titles = [
        ("way-of-the-warrior-kid", "Way of the Warrior Kid", "November 25, 2026", "2026-11-25"),
        ("fraggle-rock-a-holiday-gift", "Fraggle Rock: A Holiday Gift", "Friday, December 4, 2026", "2026-12-04"),
    ]
    story = f'<link rel="canonical" href="{ARTICLE}"><h1 class="headline">Full official headline</h1>'
    for slug, title, heading, day in titles:
        original = BASE + slug + "/"
        usa = f"https://tv.apple.com/us/movie/{slug}/umc.cmc.test"
        india = usa.replace("/us/", "/in/")
        story += f'<a href="{original}">View film details</a>'
        pages[original] = (f'<h1 class="description-title">{title}</h1><h2 class="description-tagline">Release Date: {heading}</h2>'
                           + card("movie", title) + f'<a href="{usa}">Watch on Apple TV</a>')
        pages[india] = (card("Movie", title, day + "T00:00:00.000Z")
                        + '<dd data-testid="languages-original-value">English</dd>'
                        + '<dd data-testid="information-countries-value">United States</dd>')
    pages[ARTICLE] = story
    return pages


def test_official_premieres_are_confirmed_on_the_indian_streaming_listing():
    pages = example_pages()
    rows, checked = fetch_press(set(), START, END, pages.__getitem__)
    assert {r["title"]: r["date"] for r in rows} == {
        "Way of the Warrior Kid": "2026-11-25", "Fraggle Rock: A Holiday Gift": "2026-12-04"}
    for row in rows:
        assert row["language"] == "en" and row["type"] == "film"
        assert row["sources"][0]["url"].startswith("https://tv.apple.com/in/movie/")
        assert row["sources"][1]["url"] in checked
        assert row["origin"] == "apple-tv-press"


@pytest.mark.parametrize("tagline", ["Season 2 Release Date: December 2, 2026", "In theatres November 25", "Coming Soon"])
def test_season_renewal_theatre_and_undated_windows_are_not_initial_streaming_premieres(tagline):
    assert release_day(tagline) is None


@pytest.mark.parametrize("tagline", ["", "Saturday November", "Release Date: Monday, December 4, 2026"])
def test_an_unrecognized_date_never_turns_into_zero_releases(tagline):
    with pytest.raises(SourceError):
        release_day(tagline)


def test_healthy_feed_with_all_dates_outside_the_window_is_genuinely_empty():
    pages = example_pages()
    for url in list(pages):
        if url.startswith("https://tv.apple.com/"):
            del pages[url]  # No storefront access is necessary for past releases.
    rows, checked = fetch_press(set(), date(2027, 1, 4), date(2027, 1, 18), pages.__getitem__)
    assert rows == [] and len(checked) == 2


@pytest.mark.parametrize("issue", ["http", "empty", "stale", "new_domain", "lost_structure", "wrong_region_date", "missing_audio"])
def test_partial_or_unreadable_upstream_fails_closed(issue):
    pages = example_pages()
    store = next(k for k in pages if "/in/movie/" in k)
    if issue == "http":
        def lookup(url):
            if url == store:
                raise SourceError("HTTP 503")
            return pages[url]
    else:
        lookup = pages.__getitem__
        if issue == "empty":
            pages[FEED] = "<feed/>"
        elif issue == "stale":
            group = pages[FEED].split("<updated>")[1].split("</updated>")[0]
            pages[FEED] = pages[FEED].replace(group, "2000-01-01T00:00:00Z")
        elif issue == "new_domain":
            pages[ARTICLE] = pages[ARTICLE].replace(BASE, "https://example.org/")
        elif issue == "lost_structure":
            pages[ARTICLE] = "<h1>Temporary unavailable</h1>"
        elif issue == "wrong_region_date":
            pages[store] = pages[store].replace("2026-11-25", "2026-11-20")
        elif issue == "missing_audio":
            pages[store] = pages[store].replace("languages-original-value", "dubbed-audio-value")
    with pytest.raises(SourceError):
        fetch_press(set(), START, END, lookup)


def test_english_dub_of_nonwestern_original_does_not_enter_calendar():
    pages = example_pages()
    store = next(k for k in pages if "/in/movie/" in k)
    pages[store] = pages[store].replace(">English<", ">Japanese<") + '<dd data-testid="audio-dub">English</dd>'
    rows, _ = fetch_press(set(), START, END, pages.__getitem__)
    assert len(rows) == 1 and rows[0]["title"] == "Fraggle Rock: A Holiday Gift"


def test_previously_recorded_title_still_checked_when_news_moves_out_of_atom():
    pages = example_pages()
    old = BASE + "way-of-the-warrior-kid/"
    pages[ARTICLE] = pages[ARTICLE].replace(f'<a href="{old}">View film details</a>', "")
    rows, checked = fetch_press({old}, START, END, pages.__getitem__)
    assert old in checked and len(rows) == 2
