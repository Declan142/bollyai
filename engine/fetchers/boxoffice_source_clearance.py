"""Offline activation gate for weekly box-office source candidates.

This module does not fetch provider data and does not authorize a provider.
It evaluates the checked-in source registry against a code-owned production
contract before any live adapter can be considered operational.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections.abc import Collection
from pathlib import Path
from typing import Any

from boxoffice_week_schema import (
    BoxOfficeContractError,
    LOWER_FIGURE_MAX_PERCENT,
    TRADE_ESTIMATE_MAX_PERCENT,
    _canonical_source_url,
)
from common import DATA_DIR, read_json


REGISTRY_SCHEMA = "bollyai-boxoffice-source-registry/v1"
CLEARANCE_SCHEMA = "bollyai-boxoffice-source-clearance/v1"
DEFAULT_REGISTRY_PATH = DATA_DIR / "boxoffice" / "source-candidates.json"
REQUIRED_POLICY = {
    "minimum_independent_sources": 2,
    "territory": "Worldwide",
    "measurement": "exact_week",
    "week_start": "Monday",
    "week_end": "Sunday",
    "time_zone": "UTC",
    "closed_period": True,
    "currency": "USD",
    "consensus": {
        "trade_estimate_max_pct": TRADE_ESTIMATE_MAX_PERCENT,
        "lower_figure_max_pct": LOWER_FIGURE_MAX_PERCENT,
        "published_value": "lowest",
        "over_max_action": "hold",
    },
}
REGISTRY_KEYS = {"schema", "policy", "candidates"}
CANDIDATE_KEYS = {
    "id",
    "name",
    "assessment",
    "access_model",
    "coverage",
    "independence",
    "provenance",
    "activation",
}
COVERAGE_KEYS = {
    "territory",
    "measurement",
    "week_start",
    "week_end",
    "time_zone",
    "closed_period",
    "currency",
}
INDEPENDENCE_KEYS = {"group", "attested", "attestation_ref"}
PROVENANCE_KEYS = {
    "documentation_urls",
    "coverage_review",
    "legal_review",
    "terms_review",
    "license_review",
}
ACTIVATION_KEYS = {"approved", "approval_ref", "configured", "adapter"}
ASSESSMENTS = {"needs_review", "scope_mismatch", "policy_blocked", "cleared"}
ACCESS_MODELS = {"public", "licensed_candidate", "commercial_candidate"}
REVIEW_STATES = {"pending", "partial", "approved", "blocked", "not_required"}
PASSING_REVIEW_STATES = {"approved", "not_required"}
PRODUCTION_ADAPTERS: frozenset[str] = frozenset()
REFERENCE_PATTERN = re.compile(r"[a-z0-9][a-z0-9._:/-]{2,127}")
IDENTIFIER_PATTERN = re.compile(r"[a-z0-9]+(?:_[a-z0-9]+)*")
ADAPTER_PATTERN = re.compile(r"[a-z0-9_./:-]+")


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
            "INVALID_SOURCE_REGISTRY",
            f"{where} fields differ: missing={sorted(expected - actual)}, "
            f"unexpected={sorted(actual - expected)}",
        )


def _optional_text(value: Any, where: str) -> str | None:
    if value is None:
        return None
    if (
        not isinstance(value, str)
        or not value
        or value != value.strip()
        or any(character.isspace() for character in value)
    ):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be null or stable text")
    return value


def _optional_reference(value: Any, where: str) -> str | None:
    text = _optional_text(value, where)
    if text is not None and not REFERENCE_PATTERN.fullmatch(text):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be a sanitized reference")
    return text


def _validate_coverage(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be an object")
    _require_exact_keys(value, COVERAGE_KEYS, where)
    for field in (
        "territory",
        "measurement",
        "week_start",
        "week_end",
        "time_zone",
        "currency",
    ):
        _optional_text(value[field], f"{where}.{field}")
    if value["closed_period"] is not None and not isinstance(value["closed_period"], bool):
        _fail(
            "INVALID_SOURCE_REGISTRY",
            f"{where}.closed_period must be boolean or null",
        )
    return value


def _validate_independence(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be an object")
    _require_exact_keys(value, INDEPENDENCE_KEYS, where)
    group = _optional_text(value["group"], f"{where}.group")
    if group is not None and not IDENTIFIER_PATTERN.fullmatch(group):
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.group must be a stable key")
    if not isinstance(value["attested"], bool):
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.attested must be boolean")
    _optional_reference(value["attestation_ref"], f"{where}.attestation_ref")
    return value


def _validate_provenance(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be an object")
    _require_exact_keys(value, PROVENANCE_KEYS, where)
    urls = value["documentation_urls"]
    if not isinstance(urls, list) or not urls:
        _fail(
            "INVALID_SOURCE_REGISTRY",
            f"{where}.documentation_urls must be a non-empty list",
        )
    canonical_urls = [
        _canonical_source_url(url, f"{where}.documentation_urls[{index}]")[0]
        for index, url in enumerate(urls)
    ]
    if len(canonical_urls) != len(set(canonical_urls)):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} repeats documentation URLs")
    for field in (
        "coverage_review",
        "legal_review",
        "terms_review",
        "license_review",
    ):
        if value[field] not in REVIEW_STATES:
            _fail("INVALID_SOURCE_REGISTRY", f"{where}.{field} is invalid")
    return value


def _validate_activation(value: Any, where: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be an object")
    _require_exact_keys(value, ACTIVATION_KEYS, where)
    for field in ("approved", "configured"):
        if not isinstance(value[field], bool):
            _fail("INVALID_SOURCE_REGISTRY", f"{where}.{field} must be boolean")
    _optional_reference(value["approval_ref"], f"{where}.approval_ref")
    adapter = _optional_text(value["adapter"], f"{where}.adapter")
    if adapter is not None and not ADAPTER_PATTERN.fullmatch(adapter):
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.adapter is invalid")
    return value


def _validate_candidate(value: Any, index: int) -> dict[str, Any]:
    where = f"source_registry.candidates[{index}]"
    if not isinstance(value, dict):
        _fail("INVALID_SOURCE_REGISTRY", f"{where} must be an object")
    _require_exact_keys(value, CANDIDATE_KEYS, where)
    identifier = value["id"]
    if not isinstance(identifier, str) or not IDENTIFIER_PATTERN.fullmatch(identifier):
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.id must be a stable key")
    if not isinstance(value["name"], str) or not value["name"].strip():
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.name must be non-empty")
    if value["assessment"] not in ASSESSMENTS:
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.assessment is invalid")
    if value["access_model"] not in ACCESS_MODELS:
        _fail("INVALID_SOURCE_REGISTRY", f"{where}.access_model is invalid")
    _validate_coverage(value["coverage"], f"{where}.coverage")
    _validate_independence(value["independence"], f"{where}.independence")
    _validate_provenance(value["provenance"], f"{where}.provenance")
    _validate_activation(value["activation"], f"{where}.activation")
    return value


def validate_source_registry(payload: Any) -> dict[str, Any]:
    """Validate registry shape and its immutable production policy."""

    if not isinstance(payload, dict):
        _fail("INVALID_SOURCE_REGISTRY", "source registry must be an object")
    _require_exact_keys(payload, REGISTRY_KEYS, "source_registry")
    if payload["schema"] != REGISTRY_SCHEMA:
        _fail("UNSUPPORTED_SOURCE_REGISTRY", "source registry schema is unsupported")
    actual_policy = json.dumps(
        payload["policy"],
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    required_policy = json.dumps(
        REQUIRED_POLICY,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    if actual_policy != required_policy:
        _fail(
            "SOURCE_POLICY_MISMATCH",
            "source registry policy differs from the code-owned production policy",
        )
    candidates = payload["candidates"]
    if not isinstance(candidates, list):
        _fail("INVALID_SOURCE_REGISTRY", "source_registry.candidates must be a list")
    validated = [
        _validate_candidate(candidate, index)
        for index, candidate in enumerate(candidates)
    ]
    identifiers = [candidate["id"] for candidate in validated]
    if len(identifiers) != len(set(identifiers)):
        _fail("DUPLICATE_SOURCE_CANDIDATE", "source registry repeats a candidate")
    return payload


def _candidate_reasons(
    candidate: dict[str, Any],
    *,
    configured_adapters: Collection[str],
) -> list[str]:
    coverage = candidate["coverage"]
    independence = candidate["independence"]
    provenance = candidate["provenance"]
    activation = candidate["activation"]
    reasons: list[str] = []
    if candidate["assessment"] != "cleared":
        reasons.append("ASSESSMENT_NOT_CLEARED")
    for field, expected in (
        ("territory", REQUIRED_POLICY["territory"]),
        ("measurement", REQUIRED_POLICY["measurement"]),
        ("week_start", REQUIRED_POLICY["week_start"]),
        ("week_end", REQUIRED_POLICY["week_end"]),
        ("time_zone", REQUIRED_POLICY["time_zone"]),
        ("closed_period", REQUIRED_POLICY["closed_period"]),
        ("currency", REQUIRED_POLICY["currency"]),
    ):
        if coverage[field] != expected:
            reasons.append(f"COVERAGE_{field.upper()}_MISMATCH")
    if not independence["group"]:
        reasons.append("INDEPENDENCE_GROUP_MISSING")
    if not independence["attested"]:
        reasons.append("INDEPENDENCE_NOT_ATTESTED")
    if not independence["attestation_ref"]:
        reasons.append("INDEPENDENCE_ATTESTATION_MISSING")
    if provenance["coverage_review"] != "approved":
        reasons.append("COVERAGE_REVIEW_INCOMPLETE")
    for field in ("legal_review", "terms_review"):
        if provenance[field] != "approved":
            reasons.append(f"{field.upper()}_INCOMPLETE")
    if provenance["license_review"] not in PASSING_REVIEW_STATES:
        reasons.append("LICENSE_REVIEW_INCOMPLETE")
    if not activation["approved"]:
        reasons.append("ACTIVATION_NOT_APPROVED")
    if not activation["approval_ref"]:
        reasons.append("ACTIVATION_APPROVAL_MISSING")
    if not activation["configured"]:
        reasons.append("ADAPTER_NOT_CONFIGURED")
    if not activation["adapter"]:
        reasons.append("ADAPTER_REFERENCE_MISSING")
    elif activation["adapter"] not in configured_adapters:
        reasons.append("ADAPTER_NOT_CODE_REGISTERED")
    return reasons


def evaluate_source_clearance(
    payload: Any,
    *,
    configured_adapters: Collection[str] = PRODUCTION_ADAPTERS,
) -> dict[str, Any]:
    """Return a deterministic, sanitized activation decision."""

    registry = validate_source_registry(payload)
    candidate_results = []
    qualifying_groups: list[str] = []
    for candidate in registry["candidates"]:
        reasons = _candidate_reasons(
            candidate,
            configured_adapters=configured_adapters,
        )
        group = candidate["independence"]["group"]
        if not reasons and group is not None:
            qualifying_groups.append(group)
        candidate_results.append(
            {
                "id": candidate["id"],
                "qualifies": not reasons,
                "reasons": reasons,
            }
        )
    unique_groups = sorted(set(qualifying_groups))
    qualifying_sources = sum(item["qualifies"] for item in candidate_results)
    required = REQUIRED_POLICY["minimum_independent_sources"]
    ready = qualifying_sources >= required and len(unique_groups) >= required
    return {
        "schema": CLEARANCE_SCHEMA,
        "status": "ready" if ready else "data_pending",
        "code": "SOURCE_CLEARANCE_READY" if ready else "SOURCE_CLEARANCE_PENDING",
        "required_sources": required,
        "qualifying_sources": qualifying_sources,
        "qualifying_independence_groups": len(unique_groups),
        "candidates": candidate_results,
    }


def load_source_clearance(path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, Any]:
    payload = read_json(path, default=None)
    if payload is None:
        _fail("SOURCE_REGISTRY_MISSING", "source candidate registry is unavailable")
    return evaluate_source_clearance(payload)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate the offline weekly box-office source activation gate.",
    )
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    args = parser.parse_args(argv)
    try:
        result = load_source_clearance(args.registry)
    except BoxOfficeContractError as exc:
        json.dump(
            {
                "schema": CLEARANCE_SCHEMA,
                "status": "failed",
                "code": exc.code,
            },
            sys.stderr,
            indent=2,
            sort_keys=True,
        )
        sys.stderr.write("\n")
        return 1
    json.dump(result, sys.stdout, indent=2, sort_keys=True)
    sys.stdout.write("\n")
    return 0 if result["status"] == "ready" else 2


if __name__ == "__main__":
    raise SystemExit(main())
