from __future__ import annotations

import json
import subprocess
import sys
from argparse import Namespace
from datetime import date
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

import run_all  # noqa: E402
import common  # noqa: E402
from boxoffice_week_schema import FIXTURE_SOURCE_GROUPS  # noqa: E402
from boxoffice_western import DEFAULT_FIXTURE_PATH  # noqa: E402
from common import write_json  # noqa: E402

READY_BOARD_PATH = REPO_ROOT / "tests" / "fixtures" / "boxoffice" / "ready-v3.json"
PENDING_BOARD_PATH = REPO_ROOT / "data" / "boxoffice" / "current-week.json"


def boxoffice_target(data_dir: Path) -> Path:
    return data_dir / "boxoffice" / "current-week.json"


def test_cli_rejects_noncanonical_today_without_traceback():
    for script in ("run_all.py", "boxoffice_western.py"):
        for value, expected_error in (
            ("20260726", "--today must use YYYY-MM-DD"),
            ("bogus", "--today must use YYYY-MM-DD"),
            ("2026-02-30", "--today must be a valid calendar date"),
        ):
            result = subprocess.run(
                [
                    sys.executable,
                    str(FETCHERS_DIR / script),
                    "--fixture-mode",
                    "--today",
                    value,
                ],
                cwd=REPO_ROOT,
                check=False,
                capture_output=True,
                text=True,
            )

            assert result.returncode == 2
            assert expected_error in result.stderr
            assert "Traceback" not in result.stderr


def test_pending_live_job_preserves_last_good_bytes(tmp_path):
    target = boxoffice_target(tmp_path)
    target.parent.mkdir(parents=True)
    original = READY_BOARD_PATH.read_bytes()
    target.write_bytes(original)

    result = run_all.run_boxoffice_job(
        fixture_mode=False,
        fixture_path=None,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
        trusted_source_groups=FIXTURE_SOURCE_GROUPS,
    )

    assert result["status"] == "preserved_last_good"
    assert result["code"] == "SOURCE_CLEARANCE_PENDING"
    assert result["source_clearance"]["qualifying_sources"] == 0
    assert result["changed"] is False
    assert result["preserved_previous_bytes"] is True
    assert target.read_bytes() == original


def test_pending_live_job_does_not_call_pending_bytes_last_good(tmp_path):
    target = boxoffice_target(tmp_path)
    target.parent.mkdir(parents=True)
    original = PENDING_BOARD_PATH.read_bytes()
    target.write_bytes(original)

    result = run_all.run_boxoffice_job(
        fixture_mode=False,
        fixture_path=None,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )

    assert result["status"] == "preserved_pending"
    assert result["previous_board_status"] == "data_pending"
    assert result["preserved_previous_bytes"] is True
    assert target.read_bytes() == original


def test_invalid_existing_board_fails_without_claiming_last_good(tmp_path):
    target = boxoffice_target(tmp_path)
    target.parent.mkdir(parents=True)
    original = b'{"sentinel":"not-v3"}\n'
    target.write_bytes(original)

    result = run_all.run_boxoffice_job(
        fixture_mode=False,
        fixture_path=None,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )

    assert result["status"] == "failed"
    assert result["code"] == "INVALID_EXISTING_BOARD"
    assert result["previous_board_status"] == "invalid"
    assert result["preserved_previous_bytes"] is True
    assert target.read_bytes() == original


def test_invalid_candidate_preserves_last_good_bytes(tmp_path):
    target = boxoffice_target(tmp_path)
    target.parent.mkdir(parents=True)
    original = READY_BOARD_PATH.read_bytes()
    target.write_bytes(original)
    fixture = json.loads(DEFAULT_FIXTURE_PATH.read_text(encoding="utf-8"))
    fixture["readings"][0]["source"]["metric"] = "worldwide_gross_usd"
    fixture_path = tmp_path / "invalid-source.json"
    write_json(fixture_path, fixture)

    result = run_all.run_boxoffice_job(
        fixture_mode=True,
        fixture_path=fixture_path,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )

    assert result["status"] == "failed"
    assert result["code"] == "FORBIDDEN_METRIC"
    assert result["changed"] is False
    assert target.read_bytes() == original


def test_ready_candidate_updates_once_then_becomes_byte_identical_noop(tmp_path):
    first = run_all.run_boxoffice_job(
        fixture_mode=True,
        fixture_path=DEFAULT_FIXTURE_PATH,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )
    first_bytes = boxoffice_target(tmp_path).read_bytes()
    second = run_all.run_boxoffice_job(
        fixture_mode=True,
        fixture_path=DEFAULT_FIXTURE_PATH,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )

    assert first["status"] == "updated"
    assert first["changed"] is True
    assert second["status"] == "unchanged"
    assert second["changed"] is False
    assert second["previous_sha256"] == second["candidate_sha256"]
    assert boxoffice_target(tmp_path).read_bytes() == first_bytes


def test_writer_failure_is_structured_and_preserves_last_good(monkeypatch, tmp_path):
    target = boxoffice_target(tmp_path)
    target.parent.mkdir(parents=True)
    original = READY_BOARD_PATH.read_bytes()
    target.write_bytes(original)

    def fail_write(*_args, **_kwargs):
        raise OSError("simulated writer failure")

    monkeypatch.setattr(run_all, "write_json", fail_write)
    result = run_all.run_boxoffice_job(
        fixture_mode=True,
        fixture_path=DEFAULT_FIXTURE_PATH,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )

    assert result["status"] == "failed"
    assert result["code"] == "BOXOFFICE_WRITE_ERROR"
    assert result["error_type"] == "OSError"
    assert result["changed"] is False
    assert result["preserved_previous_bytes"] is True
    assert target.read_bytes() == original


def test_post_replace_sync_failure_reports_changed_bytes(monkeypatch, tmp_path):
    target = boxoffice_target(tmp_path)
    target.parent.mkdir(parents=True)
    original = PENDING_BOARD_PATH.read_bytes()
    target.write_bytes(original)
    real_fsync = common.os.fsync
    calls = 0

    def fail_directory_sync(descriptor):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated directory sync failure")
        return real_fsync(descriptor)

    monkeypatch.setattr(common.os, "fsync", fail_directory_sync)
    result = run_all.run_boxoffice_job(
        fixture_mode=True,
        fixture_path=DEFAULT_FIXTURE_PATH,
        data_dir=tmp_path,
        today=date(2026, 7, 26),
        write=True,
    )

    assert result["status"] == "failed"
    assert result["code"] == "BOXOFFICE_WRITE_DURABILITY_ERROR"
    assert result["error_type"] == "AtomicWriteError"
    assert result["changed"] is True
    assert result["preserved_previous_bytes"] is False
    assert target.read_bytes() != original


def test_fixture_run_reports_structured_offline_status(monkeypatch):
    def network_forbidden(*_args, **_kwargs):
        raise AssertionError("fixture mode attempted network access")

    monkeypatch.setattr("wikidata.urlopen", network_forbidden)
    args = Namespace(
        fixture_mode=True,
        live_only=False,
        write=None,
        today="2026-07-26",
        boxoffice_fixture=None,
    )

    payload = run_all.run(args)

    assert payload["schema"] == "run-all-result/v2"
    assert payload["overall_status"] == "ok"
    assert payload["jobs"]["boxoffice"]["status"] == "dry_run"
    assert payload["jobs"]["boxoffice"]["code"] == "FIXTURE_READY"
    assert payload["jobs"]["boxoffice"]["requested_period"] == {
        "start": "2026-07-13",
        "end": "2026-07-19",
        "label": "13 to 19 July 2026",
    }
    assert payload["wrote"] == []
