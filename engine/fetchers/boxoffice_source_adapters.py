"""Offline-first adapters for exact-week Worldwide USD box office.

The production registry is intentionally empty. Fixture adapters exercise the
provider boundary without network access, commercial credentials, or real
box-office numbers. Source clearance and publication consensus remain separate
gates owned by ``boxoffice_source_clearance`` and ``boxoffice_week_schema``.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Callable, Literal, Mapping

from boxoffice_week_schema import SOURCE_FIXTURE_SCHEMA
from common import utc_now


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
    ) -> dict[str, Any]:
        return {
            "adapter": self.adapter_ref,
            "source_id": self.source_id,
            "independence_group": self.independence_group,
            "state": self.state,
            "code": self.code,
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
    for result in results:
        exclusion_code = None
        used = result.state == "fresh"
        if used and result.independence_group in used_groups:
            used = False
            exclusion_code = "DUPLICATE_INDEPENDENCE_GROUP"
        elif used:
            used_groups.add(result.independence_group)
            used_results.append(result)
            readings.extend(
                row.as_reading(
                    source_name=result.source_name,
                    independence_group=result.independence_group,
                    week=week,
                )
                for row in result.rows
            )
        summaries.append(
            result.summary(used=used, exclusion_code=exclusion_code)
        )
    fetched_times = [
        result.fetched_at
        for result in used_results
        if result.fetched_at is not None
    ]
    generated_at = max(fetched_times) if fetched_times else utc_now()
    source_count = len(used_results)
    group_count = len(used_groups)
    ready = source_count >= 2 and group_count >= 2
    return {
        "status": "ready" if ready else "data_pending",
        "code": "ADAPTER_BATCH_READY" if ready else "ADAPTER_BATCH_PENDING",
        "qualifying_sources": source_count,
        "qualifying_independence_groups": group_count,
        "adapters": summaries,
        "source_payload": {
            "schema": SOURCE_FIXTURE_SCHEMA,
            "generated_at": generated_at,
            "territory": "Worldwide",
            "week": week,
            "readings": readings,
        },
    }
