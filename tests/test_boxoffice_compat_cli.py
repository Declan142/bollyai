from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPT = REPO_ROOT / "scripts" / "boxoffice" / "fetch_boxoffice.py"
CURRENT_WEEK = REPO_ROOT / "data" / "boxoffice" / "current-week.json"
RUN_ALL = REPO_ROOT / "engine" / "fetchers" / "run_all.py"
WESTERN = REPO_ROOT / "engine" / "fetchers" / "boxoffice_western.py"
LEGACY = REPO_ROOT / "engine" / "fetchers" / "boxoffice.py"
TENTPOLE = REPO_ROOT / "scripts" / "ops" / "tentpole_live.py"


def run_script(script: Path, *args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )


def run_cli(*args: str) -> subprocess.CompletedProcess[str]:
    return run_script(SCRIPT, *args)


def test_fixture_cli_delegates_to_strict_job_without_writing():
    before = CURRENT_WEEK.read_bytes()

    result = run_cli("--fixture-mode", "--today", "2026-07-26")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["status"] == "dry_run"
    assert payload["code"] == "FIXTURE_READY"
    assert payload["source_period"]["start"] == "2026-07-13"
    assert CURRENT_WEEK.read_bytes() == before


def test_fixture_cli_cannot_overwrite_the_public_board():
    before = CURRENT_WEEK.read_bytes()

    result = run_cli("--fixture-mode", "--write", "--today", "2026-07-26")

    assert result.returncode == 2
    assert "fixture mode cannot write the public board" in result.stderr
    assert CURRENT_WEEK.read_bytes() == before


def test_report_and_source_status_fail_loudly_when_no_current_data_exists():
    report = run_cli("--report", "--today", "2026-08-09")
    sources = run_cli("--list-sources")

    assert report.returncode == 2
    report_error = json.loads(report.stderr)
    assert report_error["code"] == "STALE_BOXOFFICE_BOARD"
    assert report_error["expected_week"]["end"] == "2026-08-02"
    assert sources.returncode == 2
    source_payload = json.loads(sources.stdout)
    assert source_payload["code"] == "SOURCE_CLEARANCE_PENDING"
    assert source_payload["operational_sources"] == []
    assert source_payload["clearance"]["qualifying_sources"] == 0
    assert "no cleared operational box-office source pair" in sources.stderr


def test_report_accepts_current_ready_fixture_and_rejects_it_when_stale():
    ready = REPO_ROOT / "tests" / "fixtures" / "boxoffice" / "ready-v3.json"
    current = run_cli(
        "--report",
        "--board",
        str(ready),
        "--fixture-mode",
        "--today",
        "2026-07-26",
    )
    stale = run_cli(
        "--report",
        "--board",
        str(ready),
        "--fixture-mode",
        "--today",
        "2026-08-09",
    )

    assert current.returncode == 0
    assert json.loads(current.stdout)["board_schema"] == "bollyai-boxoffice-week/v3"
    assert stale.returncode == 2
    assert json.loads(stale.stderr)["code"] == "STALE_BOXOFFICE_BOARD"


def test_current_empty_board_report_is_nonzero():
    result = run_cli("--report", "--today", "2026-07-26")

    assert result.returncode == 2
    assert json.loads(result.stderr)["code"] == "NO_CURRENT_BOXOFFICE_DATA"


def test_stale_adapter_fetch_is_nonzero_and_keeps_specific_error():
    result = run_cli("--fixture-mode", "--today", "2026-08-09")

    assert result.returncode == 2
    assert json.loads(result.stdout)["code"] == "SOURCE_PERIOD_STALE"
    assert "ERROR: box-office fetch did not produce current data" in result.stderr


def test_owner_clis_reject_fixture_publication(tmp_path):
    before = CURRENT_WEEK.read_bytes()

    run_all = run_script(
        RUN_ALL,
        "--fixture-mode",
        "--today",
        "2026-07-26",
        "--write",
        "data",
    )
    western = run_script(
        WESTERN,
        "--fixture-mode",
        "--today",
        "2026-07-26",
        "--emit",
        "data/boxoffice/current-week.json",
    )
    legacy = run_script(
        LEGACY,
        "--fixture-mode",
        "--emit",
        "data/boxoffice/current-week.json",
    )
    tentpole = run_script(TENTPOLE, "--fixture-mode", "--force")

    assert run_all.returncode == 2
    assert "fixture mode cannot write the public data directory" in run_all.stderr
    assert western.returncode == 2
    assert "fixture mode cannot emit inside the public data directory" in western.stderr
    assert legacy.returncode == 1
    assert "restricted to the isolated _cache/boxoffice directory" in legacy.stderr
    assert tentpole.returncode == 2
    assert "fixture mode cannot write the public data directory" in tentpole.stderr
    assert CURRENT_WEEK.read_bytes() == before

    temp_data = tmp_path / "data"
    allowed = run_script(
        RUN_ALL,
        "--fixture-mode",
        "--today",
        "2026-07-26",
        "--write",
        str(temp_data),
    )
    assert allowed.returncode == 0
    assert json.loads(allowed.stdout)["overall_status"] == "ok"
    assert (temp_data / "boxoffice" / "current-week.json").is_file()


def test_tentpole_dry_run_passes_the_complete_fetcher_contract():
    result = run_script(
        TENTPOLE,
        "--fixture-mode",
        "--force",
        "--dry-run",
        "--today",
        "2026-07-26",
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["schema"] == "tentpole-live-result/v1"
    assert payload["fetcher"]["overall_status"] == "ok"
    assert payload["fetcher"]["jobs"]["boxoffice"]["status"] == "dry_run"


def test_tentpole_propagates_stale_fixture_failure():
    result = run_script(
        TENTPOLE,
        "--fixture-mode",
        "--force",
        "--dry-run",
        "--today",
        "2026-08-09",
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["fetcher"]["overall_status"] == "degraded"
    assert payload["fetcher"]["jobs"]["boxoffice"]["code"] == "SOURCE_PERIOD_STALE"
    assert "ERROR: tentpole fetch has no current box-office data" in result.stderr
