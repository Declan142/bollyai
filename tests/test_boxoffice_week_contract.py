from __future__ import annotations

import copy
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

from boxoffice_week_schema import (  # noqa: E402
    BOARD_SCHEMA,
    BoxOfficeContractError,
    FIXTURE_SOURCE_GROUPS,
    build_board_from_source_payload,
    closed_week,
    validate_board as validate_raw_board,
)
from boxoffice_western import fetch_western_boxoffice  # noqa: E402


FIXTURE_PATH = REPO_ROOT / "data" / "cache" / "fixtures" / "boxoffice_week_exact.json"
READY_FIXTURE_PATH = REPO_ROOT / "tests" / "fixtures" / "boxoffice" / "ready-v3.json"


def validate_board(payload, **kwargs):
    kwargs.setdefault("trusted_source_groups", FIXTURE_SOURCE_GROUPS)
    return validate_raw_board(payload, **kwargs)


@pytest.fixture
def source_payload() -> dict:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_closed_week_is_the_latest_complete_monday_to_sunday():
    assert closed_week(date(2026, 7, 26)) == {
        "start": "2026-07-13",
        "end": "2026-07-19",
        "label": "13 to 19 July 2026",
    }
    assert closed_week(date(2026, 7, 27)) == {
        "start": "2026-07-20",
        "end": "2026-07-26",
        "label": "20 to 26 July 2026",
    }


def test_offline_fixture_builds_source_consensus_without_relabelling(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )

    assert validate_board(board) is board
    assert board["schema"] == BOARD_SCHEMA
    assert board["status"] == "ready"
    assert board["week"] == source_payload["week"]
    figures = {
        record["film"]["slug"]: record["week_gross_usd"]
        for record in board["records"]
    }
    assert figures["fixture-alpha"]["value"] == 105_000_000
    assert figures["fixture-alpha"]["label"] == "trade estimate"
    assert figures["fixture-beta"]["value"] == 48_000_000
    assert figures["fixture-beta"]["label"] == "lower figure"
    assert figures["fixture-gamma"]["value"] is None
    assert figures["fixture-gamma"]["label"] == "tracking"


def test_shared_ready_fixture_passes_the_python_contract():
    payload = json.loads(READY_FIXTURE_PATH.read_text(encoding="utf-8"))

    assert validate_board(payload) is payload
    assert payload["records"][0]["week_gross_usd"]["value"] == 100_000_000


def test_live_mode_has_no_lifetime_fallback():
    outcome = fetch_western_boxoffice(
        fixture_mode=False,
        expected_week=closed_week(date(2026, 7, 26)),
    )

    assert outcome["status"] == "data_pending"
    assert outcome["code"] == "NO_EXACT_WEEK_SOURCE"
    assert outcome["source_readings"] == 0
    assert outcome["board"]["records"] == []


def test_stale_fixture_period_is_rejected_instead_of_relabelled(source_payload):
    with pytest.raises(BoxOfficeContractError, match="requested closed week") as exc:
        build_board_from_source_payload(
            source_payload,
            expected_week=closed_week(date(2026, 8, 2)),
        )

    assert exc.value.code == "SOURCE_PERIOD_MISMATCH"


@pytest.mark.parametrize(
    ("mutation", "code"),
    [
        (
            lambda payload: payload["readings"][0]["source"].update(
                {"metric": "worldwide_gross_usd"}
            ),
            "FORBIDDEN_METRIC",
        ),
        (
            lambda payload: payload["readings"][1]["source"].update(
                {"group": "fixture_trade_a"}
            ),
            "UNTRUSTED_SOURCE_GROUP",
        ),
        (
            lambda payload: payload["readings"][0].update({"language": "hi"}),
            "OFFBRAND_RECORD",
        ),
        (
            lambda payload: payload["readings"][0]["film"].update(
                {"title": "Fixture Alpha \u2013 Reissue"}
            ),
            "FORBIDDEN_DASH",
        ),
        (
            lambda payload: payload["readings"][0]["source"].update(
                {"url": "https://user@example.com/reading"}
            ),
            "INVALID_SOURCE",
        ),
        (
            lambda payload: payload["readings"][0]["source"].update(
                {"url": "https://example.com/reading\n"}
            ),
            "INVALID_SOURCE",
        ),
        (
            lambda payload: payload["readings"][0]["source"].update(
                {"fetched_at": "2026-07-20T08:01:00Z"}
            ),
            "INVALID_SOURCE_TIME",
        ),
        (
            lambda payload: payload["readings"][0]["source"].update(
                {
                    "as_of": "2026-07-19",
                    "fetched_at": "2026-07-19T23:59:59Z",
                }
            ),
            "INVALID_SOURCE_TIME",
        ),
        (
            lambda payload: payload["readings"][0].update(
                {"release_date": "2026-07-20"}
            ),
            "INVALID_RELEASE_DATE",
        ),
        (
            lambda payload: payload["readings"][0]["film"].update(
                {"url": "/streaming/box-office/fixture-alpha/"}
            ),
            "INVALID_FILM_URL",
        ),
        (
            lambda payload: payload["week"].update(
                {"label": "Current week"}
            ),
            "INVALID_WEEK",
        ),
    ],
)
def test_source_payload_rejects_unsafe_inputs(source_payload, mutation, code):
    mutation(source_payload)

    with pytest.raises(BoxOfficeContractError) as exc:
        build_board_from_source_payload(
            source_payload,
            expected_week=closed_week(date(2026, 7, 26)),
        )

    assert exc.value.code == code


def test_board_rejects_legacy_schema_and_lifetime_field(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    board["schema"] = "bollyai-boxoffice-week/v2"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "UNSUPPORTED_SCHEMA"

    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    figure = board["records"][0].pop("week_gross_usd")
    board["records"][0]["worldwide_gross_usd"] = figure

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "FORBIDDEN_METRIC"


def test_board_recomputes_consensus_and_rejects_dishonest_label(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    dishonest = copy.deepcopy(board)
    alpha = next(
        record
        for record in dishonest["records"]
        if record["film"]["slug"] == "fixture-alpha"
    )
    alpha["week_gross_usd"]["label"] = "lower figure"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(dishonest)

    assert exc.value.code == "DISHONEST_FIGURE"


def test_board_rejects_one_source_url_disguised_as_two_groups(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    alpha = next(
        record
        for record in board["records"]
        if record["film"]["slug"] == "fixture-alpha"
    )
    alpha["week_gross_usd"]["sources"][1]["url"] = (
        alpha["week_gross_usd"]["sources"][0]["url"]
    )
    alpha["week_gross_usd"]["sources"][1]["group"] = "fixture_trade_a"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "DUPLICATE_SOURCE"


def test_source_independence_is_code_owned_and_url_identity_is_canonical():
    board = json.loads(READY_FIXTURE_PATH.read_text(encoding="utf-8"))
    with pytest.raises(BoxOfficeContractError) as exc:
        validate_raw_board(board)
    assert exc.value.code == "UNTRUSTED_SOURCE_GROUP"

    spoofed = copy.deepcopy(board)
    spoofed["records"][0]["week_gross_usd"]["sources"][1]["group"] = (
        "fixture_trade_a"
    )
    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(spoofed)
    assert exc.value.code == "UNTRUSTED_SOURCE_GROUP"

    duplicate = copy.deepcopy(board)
    sources = duplicate["records"][0]["week_gross_usd"]["sources"]
    sources[1]["url"] = "https://EXAMPLE.com:443/fixture-alpha-trade-a"
    sources[1]["group"] = "fixture_trade_a"
    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(duplicate)
    assert exc.value.code == "DUPLICATE_SOURCE"


@pytest.mark.parametrize(
    "hostname",
    [
        "127.0.0.1",
        "169.254.1.1",
        "10.0.0.1",
        "[::1]",
        "127.1",
        "0177.0.0.1",
        "0x7f.0.0.1",
        "127.0.0.01",
    ],
)
def test_non_public_source_hosts_fail_closed(hostname):
    board = json.loads(READY_FIXTURE_PATH.read_text(encoding="utf-8"))
    board["records"][0]["week_gross_usd"]["sources"][0]["url"] = (
        f"https://{hostname}/reading"
    )
    groups = dict(FIXTURE_SOURCE_GROUPS)
    groups[hostname.strip("[]")] = "fixture_trade_a"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_raw_board(board, trusted_source_groups=groups)

    assert exc.value.code == "INVALID_SOURCE"


@pytest.mark.parametrize(
    "invalid_value",
    [10**400, 2**53 + 1, 9e307, 100.5],
)
def test_non_safe_integer_is_a_structured_contract_failure(
    source_payload,
    invalid_value,
):
    source_payload["readings"][0]["source"]["value"] = invalid_value

    with pytest.raises(BoxOfficeContractError) as exc:
        build_board_from_source_payload(
            source_payload,
            expected_week=closed_week(date(2026, 7, 26)),
        )

    assert exc.value.code == "INVALID_NUMBER"


def test_board_rejects_duplicate_film_identity(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    duplicate = copy.deepcopy(board)
    duplicate["records"].append(copy.deepcopy(duplicate["records"][0]))

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(duplicate)

    assert exc.value.code == "DUPLICATE_RECORD"


def test_board_rejects_same_qid_under_a_different_slug(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    original = next(
        record for record in board["records"] if record["film"]["qid"] is not None
    )
    duplicate = copy.deepcopy(original)
    duplicate["film"]["slug"] = "fixture-beta-reissue"
    duplicate["film"]["url"] = "/hollywood/box-office/fixture-beta-reissue/"
    board["records"].append(duplicate)

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "DUPLICATE_RECORD"


def test_board_rejects_same_slug_with_a_new_qid(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    original = next(
        record for record in board["records"] if record["film"]["qid"] is None
    )
    duplicate = copy.deepcopy(original)
    duplicate["film"]["qid"] = "Q987654321"
    board["records"].append(duplicate)

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "DUPLICATE_RECORD"


def test_board_timestamp_is_compared_in_utc(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    board["generated_at"] = "2026-07-19T00:30:00+14:00"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "INVALID_TIMESTAMP"


def test_board_rejects_generation_before_sunday_has_fully_closed(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    board["generated_at"] = "2026-07-19T23:59:59Z"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "INVALID_TIMESTAMP"


def test_board_rejects_future_generation_time(source_payload):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    board["generated_at"] = "2099-07-20T08:00:00Z"

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(
            board,
            now=datetime(2026, 7, 26, tzinfo=timezone.utc),
        )

    assert exc.value.code == "FUTURE_TIMESTAMP"


@pytest.mark.parametrize("invalid_date", ["20260710", "2026-W28-5", "0000-07-10"])
def test_python_dates_match_the_canonical_javascript_contract(
    source_payload,
    invalid_date,
):
    source_payload["readings"][0]["release_date"] = invalid_date

    with pytest.raises(BoxOfficeContractError) as exc:
        build_board_from_source_payload(
            source_payload,
            expected_week=closed_week(date(2026, 7, 26)),
        )

    assert exc.value.code == "INVALID_DATE"


@pytest.mark.parametrize(
    "generated_at",
    [
        "2026-02-30T08:00:00Z",
        "2026-07-20 08:00:00Z",
        "July 20 2026 08:00:00Z",
        "2026-07-20T08:00:00.0001Z",
    ],
)
def test_board_rejects_noncanonical_timestamps(source_payload, generated_at):
    board = build_board_from_source_payload(
        source_payload,
        expected_week=closed_week(date(2026, 7, 26)),
    )
    board["generated_at"] = generated_at

    with pytest.raises(BoxOfficeContractError) as exc:
        validate_board(board)

    assert exc.value.code == "INVALID_TIMESTAMP"
