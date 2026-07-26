from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

from boxoffice_source_clearance import (  # noqa: E402
    DEFAULT_REGISTRY_PATH,
    REQUIRED_POLICY,
    evaluate_source_clearance,
)
from boxoffice_week_schema import BoxOfficeContractError  # noqa: E402


@pytest.fixture
def registry() -> dict:
    return json.loads(DEFAULT_REGISTRY_PATH.read_text(encoding="utf-8"))


def clear_candidate(candidate: dict, *, group: str, suffix: str) -> None:
    candidate["assessment"] = "cleared"
    candidate["coverage"] = {
        "territory": "Worldwide",
        "measurement": "exact_week",
        "week_start": "Monday",
        "week_end": "Sunday",
        "time_zone": "UTC",
        "closed_period": True,
        "currency": "USD",
    }
    candidate["independence"] = {
        "group": group,
        "attested": True,
        "attestation_ref": f"review/independence-{suffix}",
    }
    candidate["provenance"].update(
        {
            "coverage_review": "approved",
            "legal_review": "approved",
            "terms_review": "approved",
            "license_review": "approved",
        }
    )
    candidate["activation"] = {
        "approved": True,
        "approval_ref": f"review/activation-{suffix}",
        "configured": True,
        "adapter": f"boxoffice_adapter:{suffix}",
    }


def test_checked_in_candidates_are_fail_closed_and_unconfigured(registry):
    result = evaluate_source_clearance(registry)

    assert result["status"] == "data_pending"
    assert result["code"] == "SOURCE_CLEARANCE_PENDING"
    assert result["required_sources"] == 2
    assert result["qualifying_sources"] == 0
    assert result["qualifying_independence_groups"] == 0
    assert {candidate["id"] for candidate in result["candidates"]} == {
        "box_office_mojo_public_weekly",
        "the_numbers_public_charts",
        "imdb_box_office_bulk",
        "comscore_global_box_office",
    }
    assert all(not candidate["qualifies"] for candidate in result["candidates"])
    assert all(
        candidate["activation"]
        == {
            "approved": False,
            "approval_ref": None,
            "configured": False,
            "adapter": None,
        }
        for candidate in registry["candidates"]
    )


def test_public_domestic_friday_to_thursday_chart_cannot_qualify(registry):
    candidate = registry["candidates"][0]
    candidate["assessment"] = "cleared"
    candidate["independence"] = {
        "group": "public_trade_a",
        "attested": True,
        "attestation_ref": "review/independence-public-a",
    }
    candidate["provenance"].update(
        {
            "coverage_review": "approved",
            "legal_review": "approved",
            "terms_review": "approved",
            "license_review": "not_required",
        }
    )
    candidate["activation"] = {
        "approved": True,
        "approval_ref": "review/activation-public-a",
        "configured": True,
        "adapter": "boxoffice_adapter:public_a",
    }

    result = evaluate_source_clearance(registry)
    reasons = result["candidates"][0]["reasons"]

    assert "COVERAGE_TERRITORY_MISMATCH" in reasons
    assert "COVERAGE_MEASUREMENT_MISMATCH" in reasons
    assert "COVERAGE_WEEK_START_MISMATCH" in reasons
    assert "COVERAGE_WEEK_END_MISMATCH" in reasons
    assert "COVERAGE_TIME_ZONE_MISMATCH" in reasons
    assert result["candidates"][0]["qualifies"] is False


def test_one_cleared_source_is_not_enough(registry):
    clear_candidate(registry["candidates"][0], group="trade_a", suffix="a")

    result = evaluate_source_clearance(
        registry,
        configured_adapters={"boxoffice_adapter:a"},
    )

    assert result["qualifying_sources"] == 1
    assert result["qualifying_independence_groups"] == 1
    assert result["status"] == "data_pending"


def test_two_sources_from_one_group_are_not_independent(registry):
    clear_candidate(registry["candidates"][0], group="same_owner", suffix="a")
    clear_candidate(registry["candidates"][1], group="same_owner", suffix="b")

    result = evaluate_source_clearance(
        registry,
        configured_adapters={
            "boxoffice_adapter:a",
            "boxoffice_adapter:b",
        },
    )

    assert result["qualifying_sources"] == 2
    assert result["qualifying_independence_groups"] == 1
    assert result["status"] == "data_pending"


def test_two_fully_cleared_independent_sources_open_the_gate(registry):
    clear_candidate(registry["candidates"][0], group="trade_a", suffix="a")
    clear_candidate(registry["candidates"][1], group="trade_b", suffix="b")

    result = evaluate_source_clearance(
        registry,
        configured_adapters={
            "boxoffice_adapter:a",
            "boxoffice_adapter:b",
        },
    )

    assert result["qualifying_sources"] == 2
    assert result["qualifying_independence_groups"] == 2
    assert result["status"] == "ready"
    assert result["code"] == "SOURCE_CLEARANCE_READY"


def test_registry_claim_cannot_invent_a_code_registered_adapter(registry):
    clear_candidate(registry["candidates"][0], group="trade_a", suffix="a")
    clear_candidate(registry["candidates"][1], group="trade_b", suffix="b")

    result = evaluate_source_clearance(registry)

    assert result["status"] == "data_pending"
    assert result["qualifying_sources"] == 0
    assert all(
        "ADAPTER_NOT_CODE_REGISTERED" in candidate["reasons"]
        for candidate in result["candidates"][:2]
    )


def test_registry_cannot_weaken_the_code_owned_consensus_policy(registry):
    registry["policy"]["consensus"]["lower_figure_max_pct"] = 100

    with pytest.raises(BoxOfficeContractError) as exc:
        evaluate_source_clearance(registry)

    assert exc.value.code == "SOURCE_POLICY_MISMATCH"
    assert REQUIRED_POLICY["consensus"]["lower_figure_max_pct"] == 25


def test_registry_policy_rejects_boolean_number_type_confusion(registry):
    registry["policy"]["closed_period"] = 1

    with pytest.raises(BoxOfficeContractError) as exc:
        evaluate_source_clearance(registry)

    assert exc.value.code == "SOURCE_POLICY_MISMATCH"


@pytest.mark.parametrize(
    "mutation",
    [
        lambda candidate: candidate["activation"].update(
            {"approved": True, "approval_ref": None}
        ),
        lambda candidate: candidate["independence"].update(
            {"attested": True, "attestation_ref": None}
        ),
        lambda candidate: candidate["provenance"].update(
            {"coverage_review": "partial"}
        ),
    ],
)
def test_partial_clearance_never_qualifies(registry, mutation):
    candidate = registry["candidates"][0]
    clear_candidate(candidate, group="trade_a", suffix="a")
    mutation(candidate)

    result = evaluate_source_clearance(
        registry,
        configured_adapters={"boxoffice_adapter:a"},
    )

    assert result["candidates"][0]["qualifies"] is False
    assert result["status"] == "data_pending"


def test_registry_rejects_credentialed_documentation_urls(registry):
    registry["candidates"][0]["provenance"]["documentation_urls"] = [
        "https://user@example.com/source"
    ]

    with pytest.raises(BoxOfficeContractError) as exc:
        evaluate_source_clearance(registry)

    assert exc.value.code == "INVALID_SOURCE"


def test_registry_rejects_unknown_fields_instead_of_ignoring_them(registry):
    registry["candidates"][0]["endpoint"] = "https://example.com/api"

    with pytest.raises(BoxOfficeContractError) as exc:
        evaluate_source_clearance(registry)

    assert exc.value.code == "INVALID_SOURCE_REGISTRY"


def test_candidate_result_order_is_stable(registry):
    first = evaluate_source_clearance(copy.deepcopy(registry))
    second = evaluate_source_clearance(copy.deepcopy(registry))

    assert first == second
