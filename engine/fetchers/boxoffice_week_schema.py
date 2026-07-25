"""Strict v3 Western weekly box-office publication contract.

The public board accepts only one metric: gross earned during one exact,
already-closed Monday-to-Sunday week. Lifetime, cumulative, opening-weekend,
and week-to-date readings cannot enter this module's v3 output.

There is deliberately no live source adapter yet. Live runs return a
structured ``data_pending`` outcome and preserve the existing published file.
Fixture mode exercises the complete consensus and validation path without
network access.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from datetime import date, datetime, timedelta, timezone
from ipaddress import ip_address
from types import MappingProxyType
from typing import Any
from urllib.parse import urlparse, urlunparse

from common import utc_now


BOARD_SCHEMA = "bollyai-boxoffice-week/v3"
SOURCE_FIXTURE_SCHEMA = "bollyai-boxoffice-week-source/v1"
ALLOWED_INDUSTRIES = {"hollywood", "streaming"}
ALLOWED_LANGUAGES = {
    "bg", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu",
    "fi", "fr", "ga", "gl", "hr", "hu", "is", "it", "lt", "lv", "nb",
    "nl", "no", "pl", "pt", "ro", "sk", "sl", "sr", "sv",
}
BOARD_KEYS = {"schema", "status", "generated_at", "territory", "week", "records"}
RECORD_KEYS = {
    "film", "language", "industry", "territory", "release_date", "week",
    "week_gross_usd",
}
FIGURE_KEYS = {
    "value", "currency", "measurement", "period", "territory", "label",
    "sources",
}
SOURCE_KEYS = {
    "name", "url", "group", "as_of", "fetched_at", "metric",
    "measurement", "period", "territory", "currency", "value",
}
FORBIDDEN_FIELD_PARTS = {
    "budget", "salary", "lifetime", "cumulative", "opening_weekend",
    "week_to_date", "worldwide_gross_usd",
}
TIMESTAMP_PATTERN = re.compile(
    r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"
    r"(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})"
)
DATE_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")
MAX_FUTURE_SKEW = timedelta(minutes=5)
MAX_SAFE_INTEGER = 9_007_199_254_740_991
PRODUCTION_SOURCE_GROUPS: Mapping[str, str] = MappingProxyType({})
FIXTURE_SOURCE_GROUPS: Mapping[str, str] = MappingProxyType(
    {
        "example.com": "fixture_trade_a",
        "example.org": "fixture_trade_b",
        "example.net": "fixture_trade_c",
    }
)


class BoxOfficeContractError(ValueError):
    """A stable, sanitized publication-contract failure."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code


def _fail(code: str, message: str) -> None:
    raise BoxOfficeContractError(code, message)


def _require_exact_keys(
    value: dict[str, Any],
    expected: set[str],
    where: str,
) -> None:
    actual = set(value)
    if actual != expected:
        _fail(
            "INVALID_FIELDS",
            f"{where} fields differ: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}",
        )


def _parse_date(value: Any, where: str) -> date:
    if not isinstance(value, str) or not DATE_PATTERN.fullmatch(value):
        _fail("INVALID_DATE", f"{where} must be an ISO date")
    try:
        return date.fromisoformat(value)
    except ValueError:
        _fail("INVALID_DATE", f"{where} must be an ISO date")


def _parse_timestamp(value: Any, where: str) -> datetime:
    if not isinstance(value, str) or not TIMESTAMP_PATTERN.fullmatch(value):
        _fail("INVALID_TIMESTAMP", f"{where} must be an ISO timestamp")
    text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        _fail("INVALID_TIMESTAMP", f"{where} must be an ISO timestamp")
    if parsed.tzinfo is None:
        _fail("INVALID_TIMESTAMP", f"{where} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _positive_number(value: Any, where: str) -> int:
    if (
        isinstance(value, bool)
        or not isinstance(value, int)
        or value <= 0
        or value > MAX_SAFE_INTEGER
    ):
        _fail("INVALID_NUMBER", f"{where} must be a positive safe integer")
    return value


def _canonical_source_url(value: Any, where: str) -> tuple[str, str]:
    if (
        not isinstance(value, str)
        or value != value.strip()
        or any(character.isspace() for character in value)
    ):
        _fail("INVALID_SOURCE", f"{where} must be public HTTPS")
    try:
        parsed = urlparse(value)
        hostname = parsed.hostname
        port = parsed.port
    except ValueError:
        _fail("INVALID_SOURCE", f"{where} must be public HTTPS")
    if (
        parsed.scheme != "https"
        or not hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.fragment
    ):
        _fail("INVALID_SOURCE", f"{where} must be public HTTPS")
    try:
        canonical_host = hostname.rstrip(".").encode("idna").decode("ascii").lower()
    except UnicodeError:
        _fail("INVALID_SOURCE", f"{where} must be public HTTPS")
    if (
        "." not in canonical_host
        or canonical_host == "localhost"
        or canonical_host.endswith(".localhost")
        or canonical_host.endswith(".local")
        or canonical_host.endswith(".internal")
        or canonical_host.endswith(".home.arpa")
    ):
        _fail("INVALID_SOURCE", f"{where} must be public HTTPS")
    host_labels = canonical_host.split(".")
    if all(
        re.fullmatch(r"(?:0x[0-9a-f]+|[0-9]+)", label, re.IGNORECASE)
        for label in host_labels
    ):
        _fail("INVALID_SOURCE", f"{where} must use a public source hostname")
    try:
        ip_address(canonical_host)
    except ValueError:
        pass
    else:
        _fail("INVALID_SOURCE", f"{where} must use a public source hostname")
    if port not in {None, 443}:
        canonical_netloc = f"{canonical_host}:{port}"
    else:
        canonical_netloc = canonical_host
    canonical = urlunparse(
        (
            "https",
            canonical_netloc,
            parsed.path or "/",
            parsed.params,
            parsed.query,
            "",
        )
    )
    return canonical, canonical_host


def _assert_no_forbidden_dashes(value: Any, where: str = "payload") -> None:
    if isinstance(value, str) and ("\u2013" in value or "\u2014" in value):
        _fail("FORBIDDEN_DASH", f"{where} contains a forbidden dash")
    if isinstance(value, list):
        for index, item in enumerate(value):
            _assert_no_forbidden_dashes(item, f"{where}[{index}]")
    if isinstance(value, dict):
        for key, item in value.items():
            _assert_no_forbidden_dashes(item, f"{where}.{key}")


def _validate_field_names(value: Any, where: str = "payload") -> None:
    if isinstance(value, list):
        for index, item in enumerate(value):
            _validate_field_names(item, f"{where}[{index}]")
    if not isinstance(value, dict):
        return
    for key, item in value.items():
        normalized = str(key).strip().lower().replace("-", "_")
        if any(part in normalized for part in FORBIDDEN_FIELD_PARTS):
            _fail("FORBIDDEN_METRIC", f"{where}.{key} is not an exact-week field")
        _validate_field_names(item, f"{where}.{key}")


def closed_week(today: date | None = None) -> dict[str, str]:
    """Return the latest fully closed Monday-to-Sunday period."""

    reference = today or date.today()
    start = reference - timedelta(days=reference.weekday() + 7)
    end = start + timedelta(days=6)
    return {
        "start": start.isoformat(),
        "end": end.isoformat(),
        "label": _week_label(start, end),
    }


def _week_label(start: date, end: date) -> str:
    if start.month == end.month:
        return f"{start.day} to {end.day} {end.strftime('%B %Y')}"
    return (
        f"{start.day} {start.strftime('%B')} to "
        f"{end.day} {end.strftime('%B %Y')}"
    )


def _validate_week(value: Any, where: str) -> dict[str, str]:
    if not isinstance(value, dict):
        _fail("INVALID_WEEK", f"{where} must be an object")
    _require_exact_keys(value, {"start", "end", "label"}, where)
    start = _parse_date(value["start"], f"{where}.start")
    end = _parse_date(value["end"], f"{where}.end")
    if end - start != timedelta(days=6) or start.weekday() != 0 or end.weekday() != 6:
        _fail("INVALID_WEEK", f"{where} must be one Monday-to-Sunday week")
    if value["label"] != _week_label(start, end):
        _fail("INVALID_WEEK", f"{where}.label must match the exact period")
    return value


def _validate_film(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_FILM", f"{where} must be an object")
    _require_exact_keys(value, {"title", "type", "qid", "slug", "url"}, where)
    if not isinstance(value["title"], str) or not value["title"].strip():
        _fail("INVALID_FILM", f"{where}.title must be non-empty")
    if value["type"] not in {"film", "series"}:
        _fail("INVALID_FILM", f"{where}.type is unsupported")
    qid = value["qid"]
    if qid is not None and (not isinstance(qid, str) or not re.fullmatch(r"Q[1-9]\d*", qid)):
        _fail("INVALID_FILM", f"{where}.qid must be null or a verified-looking QID")
    slug = value["slug"]
    if not isinstance(slug, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        _fail("INVALID_FILM", f"{where}.slug is invalid")
    url = value["url"]
    if not isinstance(url, str) or not url.startswith("/") or not url.endswith("/"):
        _fail("INVALID_FILM", f"{where}.url must be a local absolute path")
    return value


def _film_identity(film: dict[str, Any]) -> tuple[str, str]:
    qid = film["qid"]
    return ("qid", qid) if qid else ("slug", film["slug"])


def _validate_source(
    value: Any,
    *,
    generated_at: datetime,
    week: dict[str, str],
    territory: str,
    trusted_source_groups: Mapping[str, str],
    where: str,
) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_SOURCE", f"{where} must be an object")
    _require_exact_keys(value, SOURCE_KEYS, where)
    for field in ("name", "group"):
        if not isinstance(value[field], str) or not value[field].strip():
            _fail("INVALID_SOURCE", f"{where}.{field} must be non-empty")
    if not re.fullmatch(r"[a-z0-9]+(?:_[a-z0-9]+)*", value["group"]):
        _fail("INVALID_SOURCE", f"{where}.group must be a stable lowercase key")
    _canonical_url, source_host = _canonical_source_url(
        value["url"],
        f"{where}.url",
    )
    if trusted_source_groups.get(source_host) != value["group"]:
        _fail(
            "UNTRUSTED_SOURCE_GROUP",
            f"{where}.group is not registered for its source hostname",
        )
    if value["metric"] != "week_gross_usd" or value["measurement"] != "exact_week":
        _fail("FORBIDDEN_METRIC", f"{where} is not an exact-week gross reading")
    if value["currency"] != "USD" or value["territory"] != territory:
        _fail("SOURCE_SCOPE_MISMATCH", f"{where} currency or territory differs")
    source_period = _validate_week(value["period"], f"{where}.period")
    if source_period != week:
        _fail("SOURCE_PERIOD_MISMATCH", f"{where}.period differs from board week")
    as_of = _parse_date(value["as_of"], f"{where}.as_of")
    fetched_at = _parse_timestamp(value["fetched_at"], f"{where}.fetched_at")
    week_end = _parse_date(week["end"], "week.end")
    if (
        as_of < week_end
        or as_of > fetched_at.date()
        or fetched_at.date() <= week_end
        or fetched_at > generated_at
    ):
        _fail("INVALID_SOURCE_TIME", f"{where} timestamps do not close the week")
    _positive_number(value["value"], f"{where}.value")
    return value


def _consensus(sources: list[dict[str, Any]]) -> tuple[int, str] | None:
    if len(sources) < 2:
        return None
    groups = [source["group"] for source in sources]
    if len(groups) != len(set(groups)):
        _fail("DUPLICATE_SOURCE_GROUP", "one independent group may contribute once")
    values = sorted(_positive_number(source["value"], "source.value") for source in sources)
    difference = values[-1] - values[0]
    total = values[-1] + values[0]
    if 20 * difference <= total:
        return values[0], "trade estimate"
    if 8 * difference <= total:
        return values[0], "lower figure"
    return None


def _validate_record(
    value: Any,
    *,
    generated_at: datetime,
    week: dict[str, str],
    territory: str,
    trusted_source_groups: Mapping[str, str],
    where: str,
) -> bool:
    if not isinstance(value, dict):
        _fail("INVALID_RECORD", f"{where} must be an object")
    _require_exact_keys(value, RECORD_KEYS, where)
    film = _validate_film(value["film"], f"{where}.film")
    if value["industry"] not in ALLOWED_INDUSTRIES:
        _fail("OFFBRAND_RECORD", f"{where}.industry is outside the Western brand")
    if value["language"] not in ALLOWED_LANGUAGES:
        _fail("OFFBRAND_RECORD", f"{where}.language is outside the Western allowlist")
    if value["territory"] != territory or value["week"] != week:
        _fail("RECORD_SCOPE_MISMATCH", f"{where} period or territory differs")
    release_date = _parse_date(value["release_date"], f"{where}.release_date")
    if release_date > _parse_date(week["end"], "week.end"):
        _fail("INVALID_RELEASE_DATE", f"{where}.release_date follows the closed week")
    expected_url = f"/{value['industry']}/box-office/{film['slug']}/"
    if film["url"] != expected_url:
        _fail("INVALID_FILM_URL", f"{where}.film.url differs from its canonical route")

    figure = value["week_gross_usd"]
    if not isinstance(figure, dict):
        _fail("INVALID_FIGURE", f"{where}.week_gross_usd must be an object")
    _require_exact_keys(figure, FIGURE_KEYS, f"{where}.week_gross_usd")
    if (
        figure["currency"] != "USD"
        or figure["measurement"] != "exact_week"
        or figure["period"] != week
        or figure["territory"] != territory
    ):
        _fail("FIGURE_SCOPE_MISMATCH", f"{where}.week_gross_usd scope differs")
    if not isinstance(figure["sources"], list):
        _fail("INVALID_SOURCES", f"{where}.week_gross_usd.sources must be a list")
    sources = [
        _validate_source(
            source,
            generated_at=generated_at,
            week=week,
            territory=territory,
            trusted_source_groups=trusted_source_groups,
            where=f"{where}.week_gross_usd.sources[{index}]",
        )
        for index, source in enumerate(figure["sources"])
    ]
    source_urls = [
        _canonical_source_url(source["url"], f"{where}.source.url")[0]
        for source in sources
    ]
    if len(source_urls) != len(set(source_urls)):
        _fail("DUPLICATE_SOURCE", f"{where} repeats a source URL")

    decision = _consensus(sources)
    if decision is None:
        if figure["value"] is not None or figure["label"] != "tracking":
            _fail("DISHONEST_FIGURE", f"{where} must remain tracking")
        return False

    expected_value, expected_label = decision
    actual_value = _positive_number(figure["value"], f"{where}.week_gross_usd.value")
    if actual_value != expected_value or figure["label"] != expected_label:
        _fail("DISHONEST_FIGURE", f"{where} does not match source consensus")
    return True


def validate_board(
    payload: Any,
    *,
    now: datetime | None = None,
    trusted_source_groups: Mapping[str, str] = PRODUCTION_SOURCE_GROUPS,
) -> dict[str, Any]:
    """Validate and return a strict v3 board."""

    if not isinstance(payload, dict):
        _fail("INVALID_BOARD", "board must be an object")
    _assert_no_forbidden_dashes(payload)
    _validate_field_names(payload)
    _require_exact_keys(payload, BOARD_KEYS, "board")
    if payload["schema"] != BOARD_SCHEMA:
        _fail("UNSUPPORTED_SCHEMA", f"board.schema must be {BOARD_SCHEMA}")
    if payload["status"] not in {"ready", "data_pending"}:
        _fail("INVALID_STATUS", "board.status is invalid")
    if payload["territory"] != "Worldwide":
        _fail("INVALID_TERRITORY", "board.territory must be Worldwide")
    week = _validate_week(payload["week"], "board.week")
    generated_at = _parse_timestamp(payload["generated_at"], "board.generated_at")
    current_time = now or datetime.now(timezone.utc)
    if current_time.tzinfo is None:
        _fail("INVALID_CLOCK", "validation clock must include a timezone")
    current_time = current_time.astimezone(timezone.utc)
    if generated_at.date() <= _parse_date(week["end"], "board.week.end"):
        _fail("INVALID_TIMESTAMP", "board.generated_at does not follow the closed week")
    if generated_at > current_time + MAX_FUTURE_SKEW:
        _fail("FUTURE_TIMESTAMP", "board.generated_at is ahead of the validation clock")
    if not isinstance(payload["records"], list):
        _fail("INVALID_RECORDS", "board.records must be a list")
    if payload["status"] == "data_pending" and payload["records"]:
        _fail("INVALID_PENDING_BOARD", "data_pending boards must not carry records")

    seen_slugs: set[str] = set()
    seen_qids: set[str] = set()
    published_count = 0
    for index, record in enumerate(payload["records"]):
        if not isinstance(record, dict):
            _fail("INVALID_RECORD", f"board.records[{index}] must be an object")
        if _validate_record(
            record,
            generated_at=generated_at,
            week=week,
            territory=payload["territory"],
            trusted_source_groups=trusted_source_groups,
            where=f"board.records[{index}]",
        ):
            published_count += 1
        film = record["film"]
        slug = film["slug"]
        qid = film["qid"]
        if slug in seen_slugs or (qid is not None and qid in seen_qids):
            _fail("DUPLICATE_RECORD", f"board.records[{index}] repeats a film")
        seen_slugs.add(slug)
        if qid is not None:
            seen_qids.add(qid)
    if payload["status"] == "ready" and published_count == 0:
        _fail("EMPTY_READY_BOARD", "ready board needs a publishable exact-week figure")
    return payload


def pending_board(*, week: dict[str, str], generated_at: str | None = None) -> dict[str, Any]:
    payload = {
        "schema": BOARD_SCHEMA,
        "status": "data_pending",
        "generated_at": generated_at or utc_now(),
        "territory": "Worldwide",
        "week": week,
        "records": [],
    }
    return validate_board(payload)


def build_board_from_source_payload(
    payload: Any,
    *,
    expected_week: dict[str, str],
) -> dict[str, Any]:
    if not isinstance(payload, dict):
        _fail("INVALID_SOURCE_PAYLOAD", "source payload must be an object")
    _assert_no_forbidden_dashes(payload)
    _validate_field_names(payload)
    _require_exact_keys(
        payload,
        {"schema", "generated_at", "territory", "week", "readings"},
        "source_payload",
    )
    if payload["schema"] != SOURCE_FIXTURE_SCHEMA:
        _fail("UNSUPPORTED_SOURCE_SCHEMA", "source payload schema is unsupported")
    if payload["territory"] != "Worldwide":
        _fail("INVALID_TERRITORY", "source payload must be Worldwide")
    week = _validate_week(payload["week"], "source_payload.week")
    if week != expected_week:
        _fail("SOURCE_PERIOD_MISMATCH", "source payload is not the requested closed week")
    generated_at = _parse_timestamp(
        payload["generated_at"],
        "source_payload.generated_at",
    )
    if generated_at.date() <= _parse_date(week["end"], "source_payload.week.end"):
        _fail("INVALID_TIMESTAMP", "source payload does not follow the closed week")
    if not isinstance(payload["readings"], list):
        _fail("INVALID_SOURCE_PAYLOAD", "source_payload.readings must be a list")

    grouped: dict[tuple[str, str], dict[str, Any]] = {}
    for index, reading in enumerate(payload["readings"]):
        where = f"source_payload.readings[{index}]"
        if not isinstance(reading, dict):
            _fail("INVALID_SOURCE", f"{where} must be an object")
        _require_exact_keys(
            reading,
            {"film", "language", "industry", "territory", "release_date", "source"},
            where,
        )
        film = _validate_film(reading["film"], f"{where}.film")
        if reading["industry"] not in ALLOWED_INDUSTRIES or reading["language"] not in ALLOWED_LANGUAGES:
            _fail("OFFBRAND_RECORD", f"{where} is outside the Western brand")
        if reading["territory"] != payload["territory"]:
            _fail("RECORD_SCOPE_MISMATCH", f"{where}.territory differs")
        release_date = _parse_date(
            reading["release_date"],
            f"{where}.release_date",
        )
        if release_date > _parse_date(week["end"], "source_payload.week.end"):
            _fail("INVALID_RELEASE_DATE", f"{where}.release_date follows the closed week")
        expected_url = f"/{reading['industry']}/box-office/{film['slug']}/"
        if film["url"] != expected_url:
            _fail("INVALID_FILM_URL", f"{where}.film.url differs from its canonical route")
        source = _validate_source(
            reading["source"],
            generated_at=generated_at,
            week=week,
            territory=payload["territory"],
            trusted_source_groups=FIXTURE_SOURCE_GROUPS,
            where=f"{where}.source",
        )
        identity = _film_identity(film)
        metadata = {
            "film": film,
            "language": reading["language"],
            "industry": reading["industry"],
            "territory": reading["territory"],
            "release_date": reading["release_date"],
        }
        current = grouped.setdefault(identity, {"metadata": metadata, "sources": []})
        if current["metadata"] != metadata:
            _fail("CONFLICTING_RECORD", f"{where} conflicts with an earlier film reading")
        current["sources"].append(source)

    records: list[dict[str, Any]] = []
    published_count = 0
    ordered_groups = sorted(
        grouped.values(),
        key=lambda item: (
            item["metadata"]["film"]["title"].casefold(),
            item["metadata"]["film"]["slug"],
        ),
    )
    for item in ordered_groups:
        sources = sorted(item["sources"], key=lambda source: (source["group"], source["name"]))
        decision = _consensus(sources)
        if decision is None:
            value, label = None, "tracking"
        else:
            value, label = decision
            published_count += 1
        records.append(
            {
                **item["metadata"],
                "week": week,
                "week_gross_usd": {
                    "value": value,
                    "currency": "USD",
                    "measurement": "exact_week",
                    "period": week,
                    "territory": payload["territory"],
                    "label": label,
                    "sources": sources,
                },
            }
        )

    board = {
        "schema": BOARD_SCHEMA,
        "status": "ready" if published_count else "data_pending",
        "generated_at": payload["generated_at"],
        "territory": payload["territory"],
        "week": week,
        "records": records if published_count else [],
    }
    return validate_board(
        board,
        trusted_source_groups=FIXTURE_SOURCE_GROUPS,
    )
