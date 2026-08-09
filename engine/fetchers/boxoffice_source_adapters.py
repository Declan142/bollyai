"""Offline-first adapters for exact-week Worldwide USD box office.

The production registry is intentionally empty. Fixture adapters exercise the
provider boundary without network access, commercial credentials, or real
box-office numbers. Source clearance and publication consensus remain separate
gates owned by ``boxoffice_source_clearance`` and ``boxoffice_week_schema``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timezone
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping

from boxoffice_week_schema import SOURCE_FIXTURE_SCHEMA


AdapterState = Literal["fresh", "stale", "empty", "failed"]
AdapterFactory = Callable[[], "WeeklyBoxOfficeSourceAdapter"]


@dataclass(frozen=True)
class NormalizedWeeklyRow:
    """One provider reading normalized to the strict source-payload shape."""

    film: dict[str, Any]
    language: str
    industry: str
    release_date: str
    source_url: str
    value_usd: int
    as_of: str
    fetched_at: str

    def as_reading(
        self,
        *,
        source_name: str,
        independence_group: str,
        week: dict[str, str],
    ) -> dict[str, Any]:
        return {
            "film": self.film,
            "language": self.language,
            "industry": self.industry,
            "territory": "Worldwide",
            "release_date": self.release_date,
            "source": {
                "name": source_name,
                "url": self.source_url,
                "group": independence_group,
                "as_of": self.as_of,
                "fetched_at": self.fetched_at,
                "metric": "week_gross_usd",
                "measurement": "exact_week",
                "period": week,
                "territory": "Worldwide",
                "currency": "USD",
                "value": self.value_usd,
            },
        }


@dataclass(frozen=True)
class AdapterResult:
    """Honest adapter outcome, including stale and failed states."""

    adapter_ref: str
    source_id: str
    source_name: str
    independence_group: str
    state: AdapterState
    code: str
    requested_week: dict[str, str]
    observed_week: dict[str, str] | None
    fetched_at: str | None
    rows: tuple[NormalizedWeeklyRow, ...] = ()

    def summary(
        self,
        *,
        used: bool,
        exclusion_code: str | None,
        state: AdapterState | None = None,
        code: str | None = None,
    ) -> dict[str, Any]:
        return {
            "adapter": self.adapter_ref,
            "source_id": self.source_id,
            "independence_group": self.independence_group,
            "state": state or self.state,
            "code": code or self.code,
            "requested_week": self.requested_week,
            "observed_week": self.observed_week,
            "fetched_at": self.fetched_at,
            "row_count": len(self.rows),
            "used": used,
            "exclusion_code": exclusion_code,
        }


class WeeklyBoxOfficeSourceAdapter(ABC):
    """Provider boundary for one exact closed Monday-to-Sunday UTC window."""

    adapter_ref: str
    source_id: str
    source_name: str
    independence_group: str
    fixture_only: bool

    @abstractmethod
    def fetch_closed_week(self, week: dict[str, str]) -> AdapterResult:
        """Return normalized Worldwide USD rows or an explicit non-fresh state."""


PRODUCTION_ADAPTER_FACTORIES: Mapping[str, AdapterFactory] = MappingProxyType({})


def production_adapter_references() -> frozenset[str]:
    return frozenset(PRODUCTION_ADAPTER_FACTORIES)


def cleared_production_adapters(
    registry: dict[str, Any],
    clearance: dict[str, Any],
) -> tuple[WeeklyBoxOfficeSourceAdapter, ...]:
    qualifying_ids = {
        candidate["id"]
        for candidate in clearance["candidates"]
        if candidate["qualifies"]
    }
    references = [
        candidate["activation"]["adapter"]
        for candidate in registry["candidates"]
        if candidate["id"] in qualifying_ids
    ]
    return tuple(PRODUCTION_ADAPTER_FACTORIES[reference]() for reference in references)


def _observation_time(value: Any) -> datetime | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return None
    return parsed.astimezone(timezone.utc)


def _result_contract(
    adapter: WeeklyBoxOfficeSourceAdapter,
    result: AdapterResult,
    week: dict[str, str],
) -> tuple[AdapterState, str, list[tuple[datetime, str]]]:
    identity = (
        result.adapter_ref == adapter.adapter_ref
        and result.source_id == adapter.source_id
        and result.source_name == adapter.source_name
        and result.independence_group == adapter.independence_group
    )
    if not identity or result.requested_week != week:
        return "failed", "ADAPTER_RESULT_MISMATCH", []
    if result.state != "fresh":
        if result.rows:
            return "failed", "ADAPTER_STATE_CONTRADICTION", []
        return result.state, result.code, []
    if result.observed_week != week:
        return "stale", "SOURCE_PERIOD_STALE", []
    if not result.rows:
        return "empty", "SOURCE_EMPTY", []

    result_time = _observation_time(result.fetched_at)
    row_times = [
        (_observation_time(row.fetched_at), row.fetched_at)
        for row in result.rows
    ]
    if result_time is None or any(parsed is None for parsed, _text in row_times):
        return "failed", "SOURCE_TIMESTAMP_MISSING", []
    observations = [(parsed, text) for parsed, text in row_times if parsed is not None]
    if result_time != max(parsed for parsed, _text in observations):
        return "failed", "SOURCE_TIMESTAMP_MISMATCH", []
    return "fresh", result.code, observations


def _batch_code(
    *,
    ready: bool,
    adapters: tuple[WeeklyBoxOfficeSourceAdapter, ...],
    summaries: list[dict[str, Any]],
) -> str:
    if ready:
        return "ADAPTER_BATCH_READY"
    if not adapters:
        return "NO_OPERATIONAL_SOURCE_ADAPTER"
    for state in ("failed", "stale", "empty"):
        match = next((item for item in summaries if item["state"] == state), None)
        if match is not None:
            return str(match["code"])
    return "INSUFFICIENT_FRESH_SOURCES"


def fetch_adapter_batch(
    adapters: tuple[WeeklyBoxOfficeSourceAdapter, ...],
    week: dict[str, str],
) -> dict[str, Any]:
    """Fetch adapters and admit at most one fresh source per independence group."""

    results = [adapter.fetch_closed_week(week) for adapter in adapters]
    used_groups: set[str] = set()
    readings: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    used_results: list[AdapterResult] = []
    observation_times: list[tuple[datetime, str]] = []
    for adapter, result in zip(adapters, results, strict=True):
        state, code, result_times = _result_contract(adapter, result, week)
        exclusion_code = None
        used = state == "fresh"
        if used and result.independence_group in used_groups:
            used = False
            exclusion_code = "DUPLICATE_INDEPENDENCE_GROUP"
        elif used:
            used_groups.add(result.independence_group)
            used_results.append(result)
            observation_times.extend(result_times)
            readings.extend(
                row.as_reading(
                    source_name=result.source_name,
                    independence_group=result.independence_group,
                    week=week,
                )
                for row in result.rows
            )
        summaries.append(
            result.summary(
                used=used,
                exclusion_code=exclusion_code,
                state=state,
                code=code,
            )
        )
    source_count = len(used_results)
    group_count = len(used_groups)
    ready = source_count >= 2 and group_count >= 2
    source_payload = None
    if observation_times:
        generated_at = max(observation_times, key=lambda item: item[0])[1]
        source_payload = {
            "schema": SOURCE_FIXTURE_SCHEMA,
            "generated_at": generated_at,
            "territory": "Worldwide",
            "week": week,
            "readings": readings,
        }
    return {
        "status": "ready" if ready else "data_pending",
        "code": _batch_code(ready=ready, adapters=adapters, summaries=summaries),
        "qualifying_sources": source_count,
        "qualifying_independence_groups": group_count,
        "adapters": summaries,
        "source_payload": source_payload,
    }
