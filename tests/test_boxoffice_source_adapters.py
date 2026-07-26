from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

from boxoffice_fixture_adapters import (  # noqa: E402
    LEDGER_FIXTURE_PATH,
    FixtureBulletinAdapter,
    FixtureLedgerAdapter,
    fixture_adapters,
)
from boxoffice_source_adapters import (  # noqa: E402
    WeeklyBoxOfficeSourceAdapter,
    fetch_adapter_batch,
    production_adapter_references,
)
from boxoffice_week_schema import (  # noqa: E402
    build_board_from_source_payload,
    closed_week,
)
from boxoffice_western import fetch_western_boxoffice  # noqa: E402


EXACT_WEEK = closed_week(date(2026, 7, 26))


def write_fixture(path: Path, payload: dict) -> Path:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return path


def test_adapter_interface_declares_scope_and_independence_group():
    adapters = fixture_adapters()

    assert len(adapters) == 2
    assert all(isinstance(adapter, WeeklyBoxOfficeSourceAdapter) for adapter in adapters)
    assert all(adapter.fixture_only for adapter in adapters)
    assert {adapter.independence_group for adapter in adapters} == {
        "fixture_trade_a",
        "fixture_trade_b",
    }
    assert production_adapter_references() == frozenset()


def test_two_fixture_adapters_normalize_into_the_existing_consensus_oracle():
    batch = fetch_adapter_batch(fixture_adapters(), EXACT_WEEK)
    payload = batch["source_payload"]
    board = build_board_from_source_payload(payload, expected_week=EXACT_WEEK)

    assert batch["status"] == "ready"
    assert batch["qualifying_sources"] == 2
    assert batch["qualifying_independence_groups"] == 2
    assert len(payload["readings"]) == 6
    assert {item["state"] for item in batch["adapters"]} == {"fresh"}
    assert all(item["used"] for item in batch["adapters"])
    assert board["status"] == "ready"
    figures = {
        record["film"]["slug"]: record["week_gross_usd"]
        for record in board["records"]
    }
    assert figures["fixture-alpha"]["label"] == "trade estimate"
    assert figures["fixture-beta"]["label"] == "lower figure"
    assert figures["fixture-gamma"]["label"] == "tracking"


def test_stale_adapter_period_is_explicit_and_contributes_no_rows():
    requested_week = closed_week(date(2026, 8, 2))
    batch = fetch_adapter_batch(fixture_adapters(), requested_week)

    assert batch["status"] == "data_pending"
    assert batch["qualifying_sources"] == 0
    assert batch["qualifying_independence_groups"] == 0
    assert batch["source_payload"]["readings"] == []
    assert {item["state"] for item in batch["adapters"]} == {"stale"}
    assert {item["code"] for item in batch["adapters"]} == {
        "SOURCE_PERIOD_STALE"
    }


def test_malformed_fixture_returns_sanitized_failure_state(tmp_path):
    payload = json.loads(LEDGER_FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["rows"][0]["gross_usd"] = False
    fixture_path = write_fixture(tmp_path / "invalid-ledger.json", payload)

    result = FixtureLedgerAdapter(fixture_path).fetch_closed_week(EXACT_WEEK)

    assert result.state == "failed"
    assert result.code == "FIXTURE_PAYLOAD_INVALID"
    assert result.rows == ()
    assert result.fetched_at is None


def test_same_group_adapters_never_become_two_independent_sources():
    class SameGroupBulletin(FixtureBulletinAdapter):
        adapter_ref = "fixture_adapter:same_group_bulletin"
        independence_group = "fixture_trade_a"

    batch = fetch_adapter_batch(
        (FixtureLedgerAdapter(), SameGroupBulletin()),
        EXACT_WEEK,
    )
    board = build_board_from_source_payload(
        batch["source_payload"],
        expected_week=EXACT_WEEK,
    )

    assert batch["qualifying_sources"] == 1
    assert batch["qualifying_independence_groups"] == 1
    assert batch["adapters"][1]["used"] is False
    assert batch["adapters"][1]["exclusion_code"] == (
        "DUPLICATE_INDEPENDENCE_GROUP"
    )
    assert len(batch["source_payload"]["readings"]) == 3
    assert board["status"] == "data_pending"
    assert board["records"] == []


def test_source_identity_is_adapter_owned_not_fixture_owned(tmp_path):
    payload = json.loads(LEDGER_FIXTURE_PATH.read_text(encoding="utf-8"))
    payload["rows"][0]["source_name"] = "Spoofed Commercial Provider"
    fixture_path = write_fixture(tmp_path / "extra-provider-field.json", payload)

    result = FixtureLedgerAdapter(fixture_path).fetch_closed_week(EXACT_WEEK)
    reading = result.rows[0].as_reading(
        source_name=result.source_name,
        independence_group=result.independence_group,
        week=EXACT_WEEK,
    )

    assert result.source_name == "Fixture Ledger"
    assert result.independence_group == "fixture_trade_a"
    assert reading["source"]["name"] == "Fixture Ledger"
    assert reading["source"]["group"] == "fixture_trade_a"


def test_default_fixture_fetcher_runs_both_adapters_offline():
    outcome = fetch_western_boxoffice(
        fixture_mode=True,
        expected_week=EXACT_WEEK,
    )

    assert outcome["code"] == "FIXTURE_READY"
    assert outcome["source_readings"] == 6
    assert len(outcome["adapter_states"]) == 2
    assert all(state["state"] == "fresh" for state in outcome["adapter_states"])


def test_fixture_objects_do_not_expose_live_transport_configuration():
    for adapter in fixture_adapters():
        attributes = vars(adapter)
        assert "endpoint" not in attributes
        assert "api_key" not in attributes
        assert "token" not in attributes
