"""Box-office ingestion and publishing rules for BollyAI.

Numbers are estimates, so this module is deliberately conservative. The
publish rule is a code-level contract:

* >=2 independent sources within 10% publish the lower reading as a trade estimate.
* 10-25% apart publishes the lower reading with a caveat.
* >25% apart or single-source publishes no number and stays tracking.
* Budgets and salaries never pass through this rule.
* Bollywood Hungama + Taran Adarsh never form a valid 2-source pair by themselves.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

try:
    import requests
except ImportError:  # pragma: no cover - fixture mode still works without it.
    requests = None

from common import DATA_DIR, FIXTURE_DIR, USER_AGENT, read_json, repo_path, source_value, utc_now, write_json


BOXOFFICE_CACHE_DIR = repo_path("_cache/boxoffice")
CURRENT_WEEK_PATH = DATA_DIR / "boxoffice" / "current-week.json"
BOXOFFICE_FIGURES = {
    "india_net_inr_cr": "india_net",
    "worldwide_gross_inr_cr": "worldwide_gross",
}
PUBLISHABLE_METRICS = {"india_net", "worldwide_gross"}
DISALLOWED_METRIC_PARTS = {"budget", "salary", "salaries", "fee", "fees", "remuneration"}
LANGUAGE_SLUGS = {
    "hi": "hindi",
    "kn": "kannada",
    "ml": "malayalam",
    "ta": "tamil",
    "te": "telugu",
}
RUPEE = "\\u20b9"
MONEY_CAPTURE = rf"(?:Rs\.?|INR|{RUPEE})?\s*([\d,.]+)\s*(?:crores?|cr)\b"
INDIA_NET_PATTERNS = [
    rf"total\s+india\s+net\s+collections?\s+(?:has\s+)?(?:now\s+)?(?:climbed\s+to|stands?\s+at|reached|to)\s*{MONEY_CAPTURE}",
    rf"india\s+net\s+collections?\s+(?:has\s+)?(?:now\s+)?(?:climbed\s+to|stands?\s+at|reached|to)\s*{MONEY_CAPTURE}",
    rf"overall\s+total\s+india\s+net\s+collection\s*{MONEY_CAPTURE}",
]
WORLDWIDE_GROSS_PATTERNS = [
    rf"worldwide\s+gross\s+collection\s+(?:has\s+)?(?:now\s+)?(?:reached|stands?\s+at|to)\s*{MONEY_CAPTURE}",
    rf"pushes?\s+the\s+worldwide\s+gross\s+collection\s+to\s*{MONEY_CAPTURE}",
    rf"worldwide\s+collection\s+(?:has\s+)?(?:now\s+)?(?:reached|stands?\s+at|to)\s*{MONEY_CAPTURE}",
    rf"worldwide\s+gross\s+(?:collection\s+)?(?:of|at)\s*{MONEY_CAPTURE}",
]

SOURCE_GROUPS = {
    "sacnilk": "sacnilk",
    "tracktollywood": "tracktollywood",
    "andhraboxoffice": "andhraboxoffice",
    "boxofficeindia": "boxofficeindia",
    "mojo_india": "mojo_india",
    "box_office_mojo": "mojo_india",
    "bollywood_hungama": "studio_pr",
    "bh": "studio_pr",
    "taran_adarsh": "studio_pr",
    "taran": "studio_pr",
    "toi": "times_of_india",
}
PR_LEANING = {"bollywood_hungama", "bh", "taran_adarsh", "taran"}
PUBLISH_COPY = {
    "trade_estimate": "trade estimate",
    "lower_conservative": "lower figure",
    "awaited": "tracking",
}


@dataclass(frozen=True)
class SourceReading:
    qid: str
    date: str
    metric: str
    value: float | None
    source: str
    url: str | None = None
    fetched_at: str | None = None
    day: int | None = None
    territory: str = "India"
    week_start: str | None = None
    week_end: str | None = None

    @property
    def source_key(self) -> str:
        return source_key(self.source)

    @property
    def group(self) -> str:
        return SOURCE_GROUPS.get(self.source_key, self.source_key)


@dataclass(frozen=True)
class FetchedPage:
    url: str
    status_code: int
    text: str
    fetched_at: str
    from_cache: bool


def source_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return {
        "bollywoodhungama": "bollywood_hungama",
        "box_office_india": "boxofficeindia",
        "box_office_mojo_india": "mojo_india",
        "the_times_of_india": "times_of_india",
        "times_of_india": "times_of_india",
        "toi": "times_of_india",
    }.get(key, key)


def agreement_pct(a: float, b: float) -> float:
    average = (a + b) / 2
    if average == 0:
        return 0.0
    return abs(a - b) / average * 100


def is_valid_independent_pair(a: SourceReading, b: SourceReading) -> bool:
    if not is_publishable_metric(a.metric) or not is_publishable_metric(b.metric):
        return False
    if a.metric != b.metric:
        return False
    if a.territory.lower() != b.territory.lower():
        return False
    if a.source_key == b.source_key:
        return False
    if a.group == b.group:
        return False
    if a.source_key in PR_LEANING and b.source_key in PR_LEANING:
        return False
    return True


def publish_rule(readings: list[SourceReading]) -> dict[str, Any]:
    valid = [
        reading
        for reading in readings
        if reading.value is not None and is_publishable_metric(reading.metric)
    ]
    pairs: list[tuple[float, SourceReading, SourceReading]] = []
    for index, left in enumerate(valid):
        for right in valid[index + 1 :]:
            if is_valid_independent_pair(left, right):
                pairs.append((agreement_pct(float(left.value), float(right.value)), left, right))
    pairs.sort(key=lambda item: item[0])

    source_payload = [
        {
            "source": reading.source,
            "url": reading.url,
            "value": round(float(reading.value), 2),
            "metric": reading.metric,
            "territory": reading.territory,
            "fetched_at": reading.fetched_at,
        }
        for reading in valid
    ]

    if not pairs:
        reason = "single_source_or_no_valid_independent_pair"
        if readings and not valid:
            reason = "budget_or_salary_metric"
        return {
            "published": False,
            "net_inr_cr": None,
            "sources": source_payload,
            "label": PUBLISH_COPY["awaited"],
            "framing": "awaited",
            "caveat": True,
            "reason": reason,
        }

    best_pct, left, right = pairs[0]
    lower = min(float(left.value), float(right.value))
    if best_pct <= 10:
        return {
            "published": True,
            "net_inr_cr": {"low": round(lower, 2), "high": round(lower, 2)},
            "sources": source_payload,
            "label": PUBLISH_COPY["trade_estimate"],
            "framing": "trade_estimate",
            "agreement_pct": round(best_pct, 2),
            "basis_sources": [left.source, right.source],
            "caveat": False,
        }

    if best_pct <= 25:
        return {
            "published": True,
            "net_inr_cr": {"low": round(lower, 2), "high": round(lower, 2)},
            "sources": source_payload,
            "label": PUBLISH_COPY["lower_conservative"],
            "framing": "lower_conservative",
            "agreement_pct": round(best_pct, 2),
            "basis_sources": [left.source, right.source],
            "caveat": True,
            "caveat_text": "Sources vary by more than 10 percent, so the lower figure is shown.",
        }

    return {
        "published": False,
        "net_inr_cr": None,
        "sources": source_payload,
        "label": PUBLISH_COPY["awaited"],
        "framing": "awaited",
        "agreement_pct": round(best_pct, 2),
        "caveat": True,
        "reason": "independent_sources_disagree_over_25_pct",
    }


def build_day_row(date: str, readings: list[SourceReading]) -> dict[str, Any]:
    fetched_at = utc_now()
    if not readings:
        return {
            "date": date,
            "net_inr_cr": source_value(None, "boxoffice_publish_rule", fetched_at=fetched_at, confidence="unverified"),
            "sources": [],
            "label": PUBLISH_COPY["awaited"],
            "published": False,
        }
    decision = publish_rule(readings)
    days = [reading.day for reading in readings if reading.day is not None]
    source_names = [reading.source for reading in readings]
    confidence = "trade_estimate" if decision["published"] else "unverified"
    return {
        "date": date,
        "day": min(days) if days else None,
        "net_inr_cr": source_value(
            decision["net_inr_cr"],
            "+".join(source_names) if source_names else "boxoffice_publish_rule",
            fetched_at=fetched_at,
            confidence=confidence,
        ),
        "sources": [
            {
                "name": reading.source,
                "url": reading.url or "",
                "as_of": (reading.fetched_at or fetched_at)[:10],
                "fetched_at": reading.fetched_at or fetched_at,
                "group": reading.group,
                "metric": reading.metric,
                "territory": reading.territory,
                "value": round(float(reading.value), 2) if reading.value is not None else None,
            }
            for reading in readings
        ],
        "label": decision["label"],
        "published": decision["published"],
        "framing": decision["framing"],
        "agreement_pct": decision.get("agreement_pct"),
        "basis_sources": decision.get("basis_sources", []),
        "reason": decision.get("reason"),
        "as_of": fetched_at,
    }


def upsert_day_row(film_doc: dict[str, Any], day_row: dict[str, Any]) -> dict[str, Any]:
    box_office = film_doc.setdefault("box_office", {})
    rows = box_office.setdefault("day_rows", [])
    rows = [row for row in rows if row.get("date") != day_row.get("date")]
    rows.append(day_row)
    rows.sort(key=lambda row: row.get("date", ""))
    box_office["day_rows"] = rows
    box_office.setdefault("totals", {})
    return film_doc


def merge_readings_into_film(film_doc: dict[str, Any], readings: list[SourceReading]) -> dict[str, Any]:
    by_date: dict[str, list[SourceReading]] = {}
    for reading in readings:
        by_date.setdefault(reading.date, []).append(reading)
    for date in sorted(by_date):
        upsert_day_row(film_doc, build_day_row(date, by_date[date]))
    return film_doc


class SimpleSacnilkTableParser(HTMLParser):
    """Small fallback parser for simple day-wise tables in saved Sacnilk HTML."""

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


def parse_sacnilk_payload(payload: dict[str, Any], *, qid: str) -> list[SourceReading]:
    if "readings" in payload:
        return [
            reading_from_dict(item, default_source="sacnilk", default_qid=qid)
            for item in payload.get("readings", [])
            if item.get("source", "sacnilk").lower() == "sacnilk" or item.get("source") == "Sacnilk"
        ]

    html = payload.get("html")
    if not html:
        return []
    parser = SimpleSacnilkTableParser()
    parser.feed(html)
    readings: list[SourceReading] = []
    for row in parser.rows:
        row_text = " ".join(row)
        value = extract_inr_cr(row_text)
        date = extract_iso_date(row_text) or payload.get("date")
        if value is None or not date:
            continue
        readings.append(
                SourceReading(
                    qid=qid,
                    date=date,
                    metric="india_net",
                value=value,
                source="sacnilk",
                url=payload.get("url"),
                fetched_at=payload.get("fetched_at") or utc_now(),
                day=extract_day_number(row_text),
            )
        )
    return readings


def reading_from_dict(
    item: dict[str, Any],
    *,
    default_source: str,
    default_qid: str,
) -> SourceReading:
    value = item.get("value")
    if value is None:
        value = item.get("net_inr_cr")
    return SourceReading(
        qid=str(item.get("qid") or default_qid),
        date=str(item["date"]),
        metric=str(item.get("metric") or "india_net"),
        value=float(value),
        source=str(item.get("source") or default_source),
        url=item.get("url"),
        fetched_at=item.get("fetched_at") or utc_now(),
        day=item.get("day"),
    )


def extract_inr_cr(text: str) -> float | None:
    match = re.search(r"([\d,.]+)\s*(?:cr|crore)", text, flags=re.IGNORECASE)
    if not match:
        return None
    return float(match.group(1).replace(",", ""))


def extract_iso_date(text: str) -> str | None:
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", text)
    return match.group(1) if match else None


def extract_day_number(text: str) -> int | None:
    match = re.search(r"\bday\s*(\d+)\b", text, flags=re.IGNORECASE)
    return int(match.group(1)) if match else None


def is_publishable_metric(metric: str) -> bool:
    key = source_key(metric)
    if any(part in key for part in DISALLOWED_METRIC_PARTS):
        return False
    return key in PUBLISHABLE_METRICS


def ist_now() -> str:
    ist = timezone(timedelta(hours=5, minutes=30))
    return datetime.now(ist).isoformat(timespec="seconds")


def html_to_text(markup: str) -> str:
    without_scripts = re.sub(r"<script\b[^>]*>.*?</script>", " ", markup, flags=re.IGNORECASE | re.DOTALL)
    without_styles = re.sub(r"<style\b[^>]*>.*?</style>", " ", without_scripts, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<[^>]+>", " ", without_styles)
    return html.unescape(re.sub(r"\s+", " ", text)).strip()


def extract_title(markup: str) -> str:
    match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.IGNORECASE | re.DOTALL)
    if not match:
        return ""
    return html.unescape(re.sub(r"\s+", " ", match.group(1))).strip()


def extract_money_value(match: re.Match[str]) -> float:
    return float(match.group(1).replace(",", ""))


def find_first_money(patterns: list[str], text: str) -> float | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            return extract_money_value(match)
    return None


def extract_cumulative_metrics(text: str) -> dict[str, float]:
    metrics: dict[str, float] = {}
    india_net = find_first_money(INDIA_NET_PATTERNS, text)
    worldwide_gross = find_first_money(WORLDWIDE_GROSS_PATTERNS, text)
    if india_net is not None:
        metrics["india_net"] = india_net
    if worldwide_gross is not None:
        metrics["worldwide_gross"] = worldwide_gross
    return metrics


def url_cache_path(url: str) -> Path:
    safe = re.sub(r"[^a-z0-9]+", "_", url.lower()).strip("_")[:140]
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()[:12]
    return BOXOFFICE_CACHE_DIR / f"{safe}_{digest}.json"


class CachedHttpFetcher:
    def __init__(self, *, fixture_mode: bool = False) -> None:
        self.fixture_mode = fixture_mode
        self._robots: dict[str, RobotFileParser | None] = {}

    def get(self, url: str) -> FetchedPage | None:
        if self.fixture_mode:
            return self._get_fixture(url)

        cached = self._get_cached(url)
        if cached:
            return cached
        if requests is None:
            return None
        if not self._robots_can_fetch(url):
            return None

        response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}, timeout=20)
        fetched_at = utc_now()
        payload = {
            "url": url,
            "status_code": response.status_code,
            "fetched_at": fetched_at,
            "text": response.text if response.status_code < 400 else "",
        }
        write_json(url_cache_path(url), payload)
        time_sleep_for_etiquette()
        if response.status_code >= 400:
            return None
        return FetchedPage(url=url, status_code=response.status_code, text=response.text, fetched_at=fetched_at, from_cache=False)

    def _get_cached(self, url: str) -> FetchedPage | None:
        payload = read_json(url_cache_path(url), default=None)
        if not isinstance(payload, dict):
            return None
        text = str(payload.get("text") or "")
        if not text:
            return None
        return FetchedPage(
            url=str(payload.get("url") or url),
            status_code=int(payload.get("status_code") or 200),
            text=text,
            fetched_at=str(payload.get("fetched_at") or utc_now()),
            from_cache=True,
        )

    def _get_fixture(self, url: str) -> FetchedPage | None:
        fixtures = read_json(FIXTURE_DIR / "boxoffice_pages.json", default={"pages": []})
        for page in fixtures.get("pages", []):
            if page.get("url") == url:
                return FetchedPage(
                    url=url,
                    status_code=int(page.get("status_code") or 200),
                    text=str(page.get("html") or page.get("text") or ""),
                    fetched_at=str(page.get("fetched_at") or utc_now()),
                    from_cache=True,
                )
        return None

    def _robots_can_fetch(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        robot = self._robots.get(origin)
        if origin not in self._robots:
            robot = RobotFileParser()
            robot.set_url(f"{origin}/robots.txt")
            try:
                robot.read()
            except Exception:
                robot = None
            self._robots[origin] = robot
        if robot is None:
            return True
        return robot.can_fetch(USER_AGENT, url)


def time_sleep_for_etiquette() -> None:
    try:
        import time

        time.sleep(0.35)
    except Exception:
        return


class TradeArticleAdapter:
    name = "trade_article"

    def fetch(self, record: dict[str, Any], fetcher: CachedHttpFetcher) -> list[SourceReading]:
        target_day = infer_target_day(record)
        readings: list[SourceReading] = []
        for figure_key in BOXOFFICE_FIGURES:
            for source in record.get(figure_key, {}).get("sources", []):
                url = str(source.get("url") or "")
                if not url.startswith("https://") or "sacnilk.com" in url:
                    continue
                source_day = extract_day_number(url.replace("-", " "))
                if target_day and source_day and source_day != target_day:
                    continue
                page = fetcher.get(url)
                if page is None:
                    continue
                page_text = f"{extract_title(page.text)}. {html_to_text(page.text)}"
                if target_day and f"day {target_day}" not in page_text.lower():
                    continue
                readings.extend(readings_from_metrics(record, source, page_text, page))
        return readings


class SacnilkQuicknewsAdapter:
    name = "sacnilk_quicknews"

    def fetch(self, record: dict[str, Any], fetcher: CachedHttpFetcher) -> list[SourceReading]:
        target_day = infer_target_day(record)
        if target_day is None:
            return []
        for url in sacnilk_candidate_urls(record, target_day):
            page = fetcher.get(url)
            if page is None:
                continue
            title = extract_title(page.text)
            page_text = f"{title}. {html_to_text(page.text)}"
            if "Latest Movie Reviews" in title:
                continue
            if not title_matches_film(title, str(record["film"]["title"])):
                continue
            if f"day {target_day}" not in page_text.lower():
                continue
            source = {"name": "Sacnilk", "url": url, "as_of": page.fetched_at[:10]}
            readings = readings_from_metrics(record, source, page_text, page)
            if readings:
                return readings
        return []


def readings_from_metrics(
    record: dict[str, Any],
    source: dict[str, Any],
    page_text: str,
    page: FetchedPage,
) -> list[SourceReading]:
    metrics = extract_cumulative_metrics(page_text)
    qid = str(record["film"].get("qid") or "unknown")
    reading_date = str(source.get("as_of") or page.fetched_at[:10])
    return [
        SourceReading(
            qid=qid,
            date=reading_date,
            metric=metric,
            value=value,
            source=str(source.get("name") or source_name_from_url(page.url)),
            url=page.url,
            fetched_at=page.fetched_at,
            day=infer_target_day(record),
            territory="Worldwide" if metric == "worldwide_gross" else str(record.get("territory") or "India"),
            week_start=str(record.get("week", {}).get("start") or ""),
            week_end=str(record.get("week", {}).get("end") or ""),
        )
        for metric, value in metrics.items()
        if metric in PUBLISHABLE_METRICS
    ]


def source_name_from_url(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.").removeprefix("m.")
    return {
        "bollywoodhungama.com": "Bollywood Hungama",
        "economictimes.com": "Economic Times",
        "indianexpress.com": "Indian Express",
        "moneycontrol.com": "Moneycontrol",
        "ndtv.com": "NDTV",
        "sacnilk.com": "Sacnilk",
        "timesofindia.indiatimes.com": "Times of India",
    }.get(host, host)


def infer_target_day(record: dict[str, Any]) -> int | None:
    days: list[int] = []
    for figure_key in BOXOFFICE_FIGURES:
        for source in record.get(figure_key, {}).get("sources", []):
            url = str(source.get("url") or "")
            normalized = url.replace("_", " ").replace("-", " ")
            day = extract_day_number(normalized)
            if day is not None:
                days.append(day)
    return max(days) if days else None


def sacnilk_candidate_urls(record: dict[str, Any], day: int) -> list[str]:
    film = record.get("film") or {}
    title = str(film.get("title") or "")
    qid = str(film.get("qid") or "")
    film_doc = read_json(DATA_DIR / "films" / f"{qid}.json", default={}) if qid else {}
    release_date = nested_value(film_doc.get("release_date")) or ""
    release_year = int(str(release_date)[:4]) if re.match(r"20\d{2}", str(release_date)) else int(str(record["week"]["start"])[:4])
    language = LANGUAGE_SLUGS.get(str(nested_value(film_doc.get("original_language")) or "").lower())
    title_slug = slug_words(title)
    candidates: list[str] = []
    for year in (release_year, release_year - 1):
        if language:
            candidates.append(f"{title_slug}_{language}_{year}")
        candidates.append(f"{title_slug}_{year}")
    output = []
    for candidate in stable_unique_text(candidates):
        output.append(f"https://www.sacnilk.com/quicknews/{candidate}_Box_Office_Collection_Day_{day}")
        output.append(f"https://www.sacnilk.com/quicknews/{titlecase_underscored(candidate)}_Box_Office_Collection_Day_{day}")
    return stable_unique_text(output)


def nested_value(value: Any) -> Any:
    if isinstance(value, dict) and "value" in value:
        return value.get("value")
    return value


def slug_words(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")


def titlecase_underscored(value: str) -> str:
    return "_".join(part[:1].upper() + part[1:] for part in value.split("_") if part)


def stable_unique_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    output: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        output.append(item)
    return output


def title_matches_film(title: str, film_title: str) -> bool:
    title_key = slug_words(title)
    film_key = slug_words(film_title)
    return film_key in title_key


def source_payload_from_reading(reading: SourceReading) -> dict[str, Any]:
    return {
        "name": reading.source,
        "url": reading.url or "",
        "as_of": (reading.fetched_at or reading.date)[:10],
        "fetched_at": reading.fetched_at,
        "group": reading.group,
        "metric": reading.metric,
        "territory": reading.territory,
        "value": round(float(reading.value), 2) if reading.value is not None else None,
    }


def dedupe_readings(readings: list[SourceReading]) -> list[SourceReading]:
    seen: set[tuple[str, str, str, float | None]] = set()
    output: list[SourceReading] = []
    for reading in readings:
        key = (reading.metric, reading.source_key, reading.url or "", round(float(reading.value), 2) if reading.value is not None else None)
        if key in seen:
            continue
        seen.add(key)
        output.append(reading)
    return output


def build_weekly_figure(metric: str, readings: list[SourceReading]) -> dict[str, Any]:
    metric_readings = dedupe_readings([reading for reading in readings if reading.metric == metric])
    decision = publish_rule(metric_readings)
    return {
        "label": decision["label"],
        "sources": [source_payload_from_reading(reading) for reading in metric_readings],
        "value": decision["net_inr_cr"] if decision["published"] else None,
    }


def count_tracking_figures(board: dict[str, Any]) -> int:
    count = 0
    for record in board.get("records", []):
        for figure_key in BOXOFFICE_FIGURES:
            if record.get(figure_key, {}).get("value") is None:
                count += 1
    return count


def fill_current_week(*, fixture_mode: bool = False, write: bool = False) -> dict[str, Any]:
    board = read_json(CURRENT_WEEK_PATH, default=None)
    if not isinstance(board, dict):
        raise FileNotFoundError(f"Missing box-office board: {CURRENT_WEEK_PATH}")

    before_tracking = count_tracking_figures(board)
    fetcher = CachedHttpFetcher(fixture_mode=fixture_mode)
    adapters = [SacnilkQuicknewsAdapter(), TradeArticleAdapter()]
    adapter_hits: dict[str, int] = {adapter.name: 0 for adapter in adapters}

    for record in board.get("records", []):
        readings: list[SourceReading] = []
        for adapter in adapters:
            adapter_readings = adapter.fetch(record, fetcher)
            adapter_hits[adapter.name] += len(adapter_readings)
            readings.extend(adapter_readings)
        readings = dedupe_readings(readings)
        for figure_key, metric in BOXOFFICE_FIGURES.items():
            record[figure_key] = build_weekly_figure(metric, readings)
        if readings:
            record["notes"] = "Verified source readings attached. Renderer still recomputes the publish rule."

    board["DATA_PENDING"] = count_tracking_figures(board) == len(board.get("records", [])) * len(BOXOFFICE_FIGURES)
    board["generated_at"] = ist_now()
    after_tracking = count_tracking_figures(board)
    if write:
        write_json(CURRENT_WEEK_PATH, board)

    return {
        "schema": "boxoffice-fill-result/v1",
        "generated_at": utc_now(),
        "fixture_mode": fixture_mode,
        "records_seen": len(board.get("records", [])),
        "figures_seen": len(board.get("records", [])) * len(BOXOFFICE_FIGURES),
        "tracking_before": before_tracking,
        "tracking_after": after_tracking,
        "published_figures": len(board.get("records", [])) * len(BOXOFFICE_FIGURES) - after_tracking,
        "adapter_hits": adapter_hits,
        "written": str(CURRENT_WEEK_PATH) if write else None,
    }


def load_fixture_readings(qid: str | None = None) -> list[SourceReading]:
    fixture = read_json(FIXTURE_DIR / "boxoffice_readings.json", default={"readings": []})
    readings = [
        reading_from_dict(item, default_source=str(item.get("source") or "fixture"), default_qid=str(item.get("qid") or "unknown"))
        for item in fixture.get("readings", [])
    ]
    if qid:
        readings = [reading for reading in readings if reading.qid == str(qid)]
    return readings


def fetch_sacnilk_primary(
    *,
    qid: str,
    url: str | None = None,
    fixture_mode: bool = False,
) -> list[SourceReading]:
    if fixture_mode:
        fixture = read_json(FIXTURE_DIR / f"sacnilk_{qid}.json", default=None)
        if fixture:
            return parse_sacnilk_payload(fixture, qid=qid)
        return [reading for reading in load_fixture_readings(qid) if reading.source_key == "sacnilk"]

    if not url:
        return []
    page = CachedHttpFetcher(fixture_mode=False).get(url)
    if page is None:
        return []
    return parse_sacnilk_payload({"html": page.text, "url": url, "fetched_at": page.fetched_at}, qid=qid)


def secondary_source_stub(industry: str) -> list[dict[str, Any]]:
    stubs = {
        "tollywood": ["TrackTollywood", "AndhraBoxOffice"],
        "bollywood": ["BoxOfficeIndia"],
        "hollywood": ["Mojo-India"],
        "kollywood": [],
        "mollywood": [],
        "sandalwood": [],
        "streaming": [],
    }
    return [
        {
            "source": name,
            "industry": industry,
            "status": "stub",
            "note": "Fetcher boundary reserved; publish rule consumes readings only after parser verification.",
        }
        for name in stubs.get(industry, [])
    ]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Apply BollyAI box-office publish rules.")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--from-fixtures", action="store_true", help="Alias for --fixture-mode.")
    parser.add_argument("--qid")
    parser.add_argument("--date")
    parser.add_argument("--industry", default="tollywood")
    parser.add_argument("--emit", help="Optional JSON output path.")
    parser.add_argument("--fill-current-week", action="store_true", help="Fetch source readings for data/boxoffice/current-week.json.")
    parser.add_argument("--write-current-week", action="store_true", help="Write current-week.json after --fill-current-week.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fixture_mode = bool(args.fixture_mode or args.from_fixtures)
    if args.fill_current_week:
        payload = fill_current_week(fixture_mode=fixture_mode, write=bool(args.write_current_week))
        json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
        sys.stdout.write("\n")
        return 0

    readings = load_fixture_readings(args.qid) if fixture_mode else []
    if args.date:
        readings = [reading for reading in readings if reading.date == args.date]
    by_date: dict[str, list[SourceReading]] = {}
    for reading in readings:
        by_date.setdefault(reading.date, []).append(reading)
    rows = [build_day_row(date, by_date[date]) for date in sorted(by_date)]
    payload = {
        "schema": "boxoffice-decision/v1",
        "generated_at": utc_now(),
        "qid": args.qid,
        "day_rows": rows,
        "secondary_stubs": secondary_source_stub(args.industry),
    }
    if args.emit:
        write_json(repo_path(args.emit), payload)
    json.dump(payload, sys.stdout, ensure_ascii=True, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
