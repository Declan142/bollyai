"""Box-office ingestion and publishing rules for BollyAI.

Numbers are estimates, so this module is deliberately conservative.  The
publish rule is a code-level contract:

* >=2 independent sources within 10% -> publish a trade-estimate range.
* 10-25% apart -> publish the lower figure.
* >25% apart or single-source -> publish no number, label early estimates awaited.
* Bollywood Hungama + Taran Adarsh never form a valid 2-source pair by themselves.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any

try:
    import requests
except ImportError:  # pragma: no cover - fixture mode still works without it.
    requests = None

from common import FIXTURE_DIR, USER_AGENT, read_json, repo_path, source_value, utc_now, write_json


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
}
PR_LEANING = {"bollywood_hungama", "bh", "taran_adarsh", "taran"}
PUBLISH_COPY = {
    "trade_estimate": "Trade estimate",
    "lower_conservative": "Early trade estimates, sources vary",
    "awaited": "early estimates awaited",
}


@dataclass(frozen=True)
class SourceReading:
    qid: str
    date: str
    metric: str
    value: float
    source: str
    url: str | None = None
    fetched_at: str | None = None
    day: int | None = None

    @property
    def source_key(self) -> str:
        return source_key(self.source)

    @property
    def group(self) -> str:
        return SOURCE_GROUPS.get(self.source_key, self.source_key)


def source_key(value: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", value.strip().lower()).strip("_")
    return {
        "bollywoodhungama": "bollywood_hungama",
        "box_office_india": "boxofficeindia",
        "box_office_mojo_india": "mojo_india",
    }.get(key, key)


def agreement_pct(a: float, b: float) -> float:
    average = (a + b) / 2
    if average == 0:
        return 0.0
    return abs(a - b) / average * 100


def is_valid_independent_pair(a: SourceReading, b: SourceReading) -> bool:
    if a.source_key == b.source_key:
        return False
    if a.group == b.group:
        return False
    if a.source_key in PR_LEANING and b.source_key in PR_LEANING:
        return False
    return True


def publish_rule(readings: list[SourceReading]) -> dict[str, Any]:
    valid = [reading for reading in readings if reading.value is not None]
    pairs: list[tuple[float, SourceReading, SourceReading]] = []
    for index, left in enumerate(valid):
        for right in valid[index + 1 :]:
            if is_valid_independent_pair(left, right):
                pairs.append((agreement_pct(left.value, right.value), left, right))
    pairs.sort(key=lambda item: item[0])

    source_payload = [
        {
            "source": reading.source,
            "url": reading.url,
            "value": round(reading.value, 2),
            "fetched_at": reading.fetched_at,
        }
        for reading in valid
    ]

    if not pairs:
        return {
            "published": False,
            "net_inr_cr": None,
            "sources": source_payload,
            "label": PUBLISH_COPY["awaited"],
            "framing": "awaited",
            "reason": "single_source_or_no_valid_independent_pair",
        }

    best_pct, left, right = pairs[0]
    if best_pct <= 10:
        low = min(left.value, right.value)
        high = max(left.value, right.value)
        return {
            "published": True,
            "net_inr_cr": {"low": round(low, 2), "high": round(high, 2)},
            "sources": source_payload,
            "label": PUBLISH_COPY["trade_estimate"],
            "framing": "trade_estimate",
            "agreement_pct": round(best_pct, 2),
            "basis_sources": [left.source, right.source],
        }

    if best_pct <= 25:
        lower = min(left.value, right.value)
        return {
            "published": True,
            "net_inr_cr": {"low": round(lower, 2), "high": round(lower, 2)},
            "sources": source_payload,
            "label": PUBLISH_COPY["lower_conservative"],
            "framing": "lower_conservative",
            "agreement_pct": round(best_pct, 2),
            "basis_sources": [left.source, right.source],
        }

    return {
        "published": False,
        "net_inr_cr": None,
        "sources": source_payload,
        "label": PUBLISH_COPY["awaited"],
        "framing": "awaited",
        "agreement_pct": round(best_pct, 2),
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
    if requests is None:
        return []
    response = requests.get(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html"}, timeout=20)
    if response.status_code >= 400:
        return []
    return parse_sacnilk_payload({"html": response.text, "url": url, "fetched_at": utc_now()}, qid=qid)


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
    parser.add_argument("--qid")
    parser.add_argument("--date")
    parser.add_argument("--industry", default="tollywood")
    parser.add_argument("--emit", help="Optional JSON output path.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    readings = load_fixture_readings(args.qid) if args.fixture_mode else []
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
