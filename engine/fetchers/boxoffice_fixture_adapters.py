"""Two synthetic, offline-only weekly box-office source adapters."""

from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Mapping
from urllib.parse import urljoin

from boxoffice_source_adapters import (
    AdapterResult,
    AdapterState,
    NormalizedWeeklyRow,
    WeeklyBoxOfficeSourceAdapter,
)
from common import FIXTURE_DIR


LEDGER_FIXTURE_PATH = FIXTURE_DIR / "boxoffice_adapters" / "fixture_ledger.json"
BULLETIN_FIXTURE_PATH = FIXTURE_DIR / "boxoffice_adapters" / "fixture_bulletin.json"


def _failed(
    adapter: WeeklyBoxOfficeSourceAdapter,
    week: dict[str, str],
    code: str,
) -> AdapterResult:
    return AdapterResult(
        adapter_ref=adapter.adapter_ref,
        source_id=adapter.source_id,
        source_name=adapter.source_name,
        independence_group=adapter.independence_group,
        state="failed",
        code=code,
        requested_week=week,
        observed_week=None,
        fetched_at=None,
    )


def _stale(
    adapter: WeeklyBoxOfficeSourceAdapter,
    week: dict[str, str],
    observed_week: dict[str, str],
    fetched_at: Any,
) -> AdapterResult:
    return AdapterResult(
        adapter.adapter_ref,
        adapter.source_id,
        adapter.source_name,
        adapter.independence_group,
        "stale",
        "SOURCE_PERIOD_STALE",
        week,
        observed_week,
        fetched_at if isinstance(fetched_at, str) else None,
    )


def _result(
    adapter: WeeklyBoxOfficeSourceAdapter,
    week: dict[str, str],
    fetched_at: str,
    rows: tuple[NormalizedWeeklyRow, ...],
) -> AdapterResult:
    state: AdapterState = "fresh" if rows else "empty"
    return AdapterResult(
        adapter.adapter_ref,
        adapter.source_id,
        adapter.source_name,
        adapter.independence_group,
        state,
        "SOURCE_FRESH" if rows else "SOURCE_EMPTY",
        week,
        week,
        fetched_at,
        rows,
    )


def _fixture_time(value: Any, week: dict[str, str]) -> str:
    if not isinstance(value, str):
        raise ValueError("fixture timestamp must be text")
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        raise ValueError("fixture timestamp must include a timezone")
    parsed = parsed.astimezone(timezone.utc)
    if parsed.date() <= date.fromisoformat(week["end"]):
        raise ValueError("fixture timestamp does not follow the closed week")
    return value


def _positive_usd(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError("weekly USD must be a positive integer")
    if value > 9_007_199_254_740_991:
        raise ValueError("weekly USD exceeds the cross-runtime safe range")
    return value


def _film(
    *,
    title: Any,
    kind: Any,
    qid: Any,
    slug: Any,
    industry: Any,
) -> dict[str, Any]:
    identity = (title, kind, slug, industry)
    if not all(isinstance(value, str) and value for value in identity):
        raise ValueError("fixture film identity is incomplete")
    return {
        "title": title,
        "type": kind,
        "qid": qid,
        "slug": slug,
        "url": f"/{industry}/box-office/{slug}/",
    }


def _base_url(row: Mapping[str, Any]) -> str:
    base_url = row.get("base_url")
    if not isinstance(base_url, str) or not base_url.startswith("https://"):
        raise ValueError("fixture base URL must be public HTTPS")
    return base_url


class FixtureLedgerAdapter(WeeklyBoxOfficeSourceAdapter):
    """Parse the synthetic ledger fixture without any network path."""

    adapter_ref = "fixture_adapter:ledger"
    source_id = "fixture_ledger"
    source_name = "Fixture Ledger"
    independence_group = "fixture_trade_a"
    fixture_only = True

    def __init__(self, fixture_path: Path = LEDGER_FIXTURE_PATH):
        self.fixture_path = fixture_path

    def fetch_closed_week(self, week: dict[str, str]) -> AdapterResult:
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            if payload.get("schema") != "bollyai-fixture-ledger/v1":
                return _failed(self, week, "FIXTURE_SCHEMA_MISMATCH")
            observed_week = payload["week"]
            if observed_week != week:
                return _stale(self, week, observed_week, payload.get("published_at"))
            fetched_at = _fixture_time(payload["published_at"], week)
            rows = tuple(self._normalize(row, fetched_at) for row in payload["rows"])
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return _failed(self, week, "FIXTURE_PAYLOAD_INVALID")
        return _result(self, week, fetched_at, rows)

    def _normalize(
        self,
        row: dict[str, Any],
        fetched_at: str,
    ) -> NormalizedWeeklyRow:
        industry = row["industry"]
        return NormalizedWeeklyRow(
            film=_film(
                title=row["film"]["title"],
                kind=row["film"]["type"],
                qid=row["film"]["qid"],
                slug=row["film"]["slug"],
                industry=industry,
            ),
            language=row["language"],
            industry=industry,
            release_date=row["release_date"],
            source_url=urljoin(_base_url(row), row["reading_path"]),
            value_usd=_positive_usd(row["gross_usd"]),
            as_of=fetched_at[:10],
            fetched_at=fetched_at,
        )


class FixtureBulletinAdapter(WeeklyBoxOfficeSourceAdapter):
    """Parse a differently shaped synthetic bulletin fixture offline."""

    adapter_ref = "fixture_adapter:bulletin"
    source_id = "fixture_bulletin"
    source_name = "Fixture Bulletin"
    independence_group = "fixture_trade_b"
    fixture_only = True

    def __init__(self, fixture_path: Path = BULLETIN_FIXTURE_PATH):
        self.fixture_path = fixture_path

    def fetch_closed_week(self, week: dict[str, str]) -> AdapterResult:
        try:
            payload = json.loads(self.fixture_path.read_text(encoding="utf-8"))
            if payload.get("schema") != "bollyai-fixture-bulletin/v1":
                return _failed(self, week, "FIXTURE_SCHEMA_MISMATCH")
            report = payload["report"]
            observed_week = report["period"]
            if observed_week != week:
                return _stale(self, week, observed_week, report.get("finalized_at"))
            if (
                report["territory"] != "Worldwide"
                or report["currency"] != "USD"
                or report["measurement"] != "exact_week"
            ):
                return _failed(self, week, "SOURCE_SCOPE_MISMATCH")
            fetched_at = _fixture_time(report["finalized_at"], week)
            rows = tuple(self._normalize(entry, fetched_at) for entry in payload["entries"])
        except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
            return _failed(self, week, "FIXTURE_PAYLOAD_INVALID")
        return _result(self, week, fetched_at, rows)

    def _normalize(
        self,
        entry: dict[str, Any],
        fetched_at: str,
    ) -> NormalizedWeeklyRow:
        amount = entry["weekly_usd"]
        if not isinstance(amount, str) or not amount.isascii() or not amount.isdigit():
            raise ValueError("bulletin weekly USD must be integer text")
        industry = entry["desk"]
        return NormalizedWeeklyRow(
            film=_film(
                title=entry["title"],
                kind=entry["kind"],
                qid=entry["qid"],
                slug=entry["slug"],
                industry=industry,
            ),
            language=entry["language"],
            industry=industry,
            release_date=entry["released"],
            source_url=entry["evidence_url"],
            value_usd=_positive_usd(int(amount)),
            as_of=fetched_at[:10],
            fetched_at=fetched_at,
        )


def fixture_adapters() -> tuple[WeeklyBoxOfficeSourceAdapter, ...]:
    return (FixtureLedgerAdapter(), FixtureBulletinAdapter())
