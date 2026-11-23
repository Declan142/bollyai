"""Discover Apple Originals from the public press Atom feed and confirm their Indian streaming dates."""

import json
import re
import xml.etree.ElementTree as ET
from datetime import date, datetime, timedelta, timezone
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from common import USER_AGENT


class SourceError(RuntimeError):
    """The source could not establish a current, complete result."""


FEED = "https://www.apple.com/tv-pr/news-feed.xml"
ATOM = {"a": "http://www.w3.org/2005/Atom"}
SLUG = r"[a-z0-9]+(?:-[a-z0-9]+)*"
NEWS = re.compile(rf"https://www\.apple\.com/tv-pr/news/\d{{4}}/(?:0[1-9]|1[0-2])/{SLUG}/")
ORIGINAL = re.compile(rf"https://www\.apple\.com/tv-pr/originals/({SLUG})/")
STORE = re.compile(rf"https://tv\.apple\.com/(us|in)/(movie|show)/{SLUG}/umc\.cmc\.[a-z0-9]+")
TYPES = {"movie": "film", "tvseries": "series"}
DETAILS = {"View film details": "film", "View show details": "series"}
LANGUAGES = {
    "English": "en", "French": "fr", "German": "de", "Spanish": "es", "Italian": "it", "Dutch": "nl",
    "Swedish": "sv", "Danish": "da", "Norwegian": "no", "Finnish": "fi", "Icelandic": "is", "Polish": "pl",
    "Czech": "cs", "Slovak": "sk", "Hungarian": "hu", "Romanian": "ro", "Greek": "el", "Catalan": "ca",
    "Portuguese": "pt", "Galician": "gl", "Luxembourgish": "lb", "Yiddish": "yi", "Irish": "ga",
}
COUNTRIES = {
    "United States", "Canada", "United Kingdom", "Ireland", "France", "Germany", "Spain", "Italy",
    "Portugal", "Netherlands", "Belgium", "Austria", "Switzerland", "Sweden", "Norway", "Denmark",
    "Finland", "Iceland", "Australia", "New Zealand", "Poland", "Czechia", "Slovakia", "Hungary",
    "Romania", "Greece", "Luxembourg",
}


def fetch_response(url: str) -> str:
    if url != FEED and not any(rule.fullmatch(url) for rule in (NEWS, ORIGINAL, STORE)):
        raise SourceError(f"Unexpected source URL: {url}")
    try:
        with requests.Session() as session:
            session.trust_env = False
            with session.get(url, headers={"User-Agent": USER_AGENT}, allow_redirects=False,
                             timeout=(5, 15), stream=True) as response:
                if response.status_code != 200:
                    raise SourceError(f"HTTP {response.status_code} at {url}")
                body = bytearray()
                for block in response.iter_content(65536):
                    body.extend(block)
                    if len(body) > 5_000_000:
                        raise SourceError(f"Unexpected response size at {url}")
                return body.decode("utf-8")
    except (requests.RequestException, UnicodeError) as error:
        raise SourceError(f"Unable to read {url}: {error}") from error


def text(node) -> str:
    return " ".join(node.stripped_strings) if node else ""


def news_urls(xml: str) -> set[str]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as error:
        raise SourceError("Apple TV Press did not return an Atom feed") from error
    entries = root.findall("a:entry", ATOM)
    if (root.tag != "{http://www.w3.org/2005/Atom}feed" or root.findtext("a:title", namespaces=ATOM) != "Apple TV Press"
            or not 1 <= len(entries) <= 40):
        raise SourceError("Unrecognised or empty Apple TV Press feed")
    try:
        updated = datetime.fromisoformat(root.findtext("a:updated", default="", namespaces=ATOM))
        if updated.tzinfo is None:
            raise ValueError("Feed timestamp has no time zone")
    except ValueError as error:
        raise SourceError("The Apple feed did not identify its edition") from error
    age = datetime.now(timezone.utc) - updated
    if age < -timedelta(days=1) or age > timedelta(days=30):
        raise SourceError("The Apple press feed is outside its normal publication window")
    urls = set()
    for entry in entries:
        links = [node.get("href", "") for node in entry.findall("a:link", ATOM) if node.get("rel", "alternate") == "alternate"]
        if len(links) != 1 or not NEWS.fullmatch(links[0]) or not entry.findtext("a:title", namespaces=ATOM):
            raise SourceError("Unrecognised Apple TV Press news entry")
        urls.add(links[0])
    return urls


def title_pages(html: str, article: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    canonical = soup.select_one('link[rel="canonical"]')
    if not text(soup.select_one("h1.headline")) or not canonical or canonical.get("href") != article:
        raise SourceError(f"Expected an original Apple TV Press article at {article}")
    result = {}
    for link in soup.select("a[href]"):
        kind = DETAILS.get(text(link))
        if kind:
            url = urljoin(article, link["href"])
            if not ORIGINAL.fullmatch(url) or result.setdefault(url, kind) != kind:
                raise SourceError(f"Unrecognised Originals link in {article}")
    return result


def release_day(tagline: str) -> date | None:
    if not tagline:
        raise SourceError("Apple Originals release heading is missing")
    if re.search(r"\bseason\b|\btb[ad]\b|coming soon|to be announced|theat(?:re|er)|cinema", tagline, re.I):
        return None
    match = re.fullmatch(r"(?:release|premiere) date:\s*(?:([a-z]+),\s*)?([a-z]+ \d{1,2}, \d{4})", tagline, re.I)
    if not match:
        raise SourceError(f"Unrecognised Apple release heading: {tagline}")
    try:
        day = datetime.strptime(match[2], "%B %d, %Y").date()
    except ValueError as error:
        raise SourceError(f"Invalid Apple release date: {tagline}") from error
    if match[1] and match[1].lower() != day.strftime("%A").lower():
        raise SourceError(f"Weekday and release date disagree: {tagline}")
    return day


def structured_title(soup, name: str) -> tuple[str, dict]:
    found = []
    for tag in soup.select('script[type="application/ld+json"]'):
        try:
            node = json.loads(tag.string or "")
        except ValueError as error:
            raise SourceError("Apple supplied malformed structured programme metadata") from error
        if isinstance(node, dict) and str(node.get("@type", "")).lower() in TYPES:
            if " ".join(str(node.get("name", "")).split()).casefold() == name.casefold():
                found.append((TYPES[node["@type"].lower()], node))
    if len(found) != 1:
        raise SourceError(f"Apple structured data did not uniquely identify {name}")
    return found[0]


def candidate(url: str, discovered_kind: str | None, start: date, end: date, required: bool, fetch):
    page = BeautifulSoup(fetch(url), "html.parser")
    title = " ".join(text(page.select_one("h1.description-title")).split())
    if not title:
        raise SourceError(f"Missing Originals title at {url}")
    day = release_day(text(page.select_one("h2.description-tagline")))
    if not day or not start <= day < end:
        return None
    must_confirm = required or day < start + timedelta(weeks=2)
    kind, _ = structured_title(page, title)
    links = {a["href"] for a in page.select("a[href]") if text(a) == "Watch on Apple TV"}
    if not links and not must_confirm:
        return None  # Newly announced titles can precede their programme listings.
    if len(links) != 1 or (discovered_kind and discovered_kind != kind):
        raise SourceError(f"Programme type or store link is ambiguous at {url}")
    store = links.pop()
    match = STORE.fullmatch(store)
    if not match or match[2] != ("movie" if kind == "film" else "show"):
        raise SourceError(f"Invalid Apple programme link at {url}")
    india = store.replace("tv.apple.com/us/", "tv.apple.com/in/", 1)
    listing = BeautifulSoup(fetch(india), "html.parser")
    listed_kind, metadata = structured_title(listing, title)
    published = metadata.get("datePublished") or ""
    if listed_kind != kind or not re.fullmatch(r"\d{4}-\d\d-\d\d(?:T[^\s]+)?", published) or published[:10] != day.isoformat():
        if must_confirm:
            raise SourceError(f"Apple Press and Apple TV India now disagree for {title}")
        return None  # Region or distribution date is not confirmed.
    language = text(listing.select_one('[data-testid="languages-original-value"]'))
    countries = text(listing.select_one('[data-testid="information-countries-value"]'))
    if not language or not countries:
        if must_confirm:
            raise SourceError(f"Original audio or region metadata missing for {title}")
        return None  # A future programme can have a partial advance listing.
    if language not in LANGUAGES or not set(re.split(r"\s*(?:,|;|&|\band\b)\s*", countries)) <= COUNTRIES:
        return None
    return {
        "id": f"{kind}-{ORIGINAL.fullmatch(url)[1]}", "title": title, "platform": "Apple TV+",
        "date": day.isoformat(), "language": LANGUAGES[language], "type": kind, "industry": "streaming",
        "origin": "apple-tv-press", "sources": [
            {"name": "Apple TV India", "url": india, "type": "press"},
            {"name": "Apple TV Press", "url": url, "type": "press"},
        ],
    }


def fetch_press(known_urls: set[str], window_start: date, window_end: date, fetch=fetch_response):
    if not all(ORIGINAL.fullmatch(url) for url in known_urls):
        raise SourceError("Stored Apple Originals source is invalid")
    discovered = {}
    for article in sorted(news_urls(fetch(FEED))):
        for url, kind in title_pages(fetch(article), article).items():
            if discovered.setdefault(url, kind) != kind:
                raise SourceError(f"Apple published conflicting title types for {url}")
    urls = known_urls | discovered.keys()
    if not discovered or len(urls) > 200:
        raise SourceError("The Apple feed contained no verifiable Originals links or exceeded the expected size")
    records = []
    for url in sorted(urls):
        row = candidate(url, discovered.get(url), window_start, window_end, url in known_urls, fetch)
        if row:
            records.append(row)
    return records, set(urls)
