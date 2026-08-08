from __future__ import annotations

import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

import staleness_check  # noqa: E402
from boxoffice_week_schema import FIXTURE_SOURCE_GROUPS  # noqa: E402


READY_BOARD = REPO_ROOT / "tests" / "fixtures" / "boxoffice" / "ready-v3.json"
PENDING_BOARD = REPO_ROOT / "data" / "boxoffice" / "current-week.json"
SCRIPT = FETCHERS_DIR / "staleness_check.py"


def install_board(data_dir: Path, source: Path) -> Path:
    target = data_dir / "boxoffice" / "current-week.json"
    target.parent.mkdir(parents=True)
    shutil.copyfile(source, target)
    return target


def test_weekly_ready_board_is_healthy_only_for_latest_closed_week(tmp_path):
    install_board(tmp_path, READY_BOARD)

    current = staleness_check.check_staleness(
        data_dir=tmp_path,
        sla_hours=26,
        now=datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
        trusted_source_groups=FIXTURE_SOURCE_GROUPS,
    )
    stale = staleness_check.check_staleness(
        data_dir=tmp_path,
        sla_hours=26,
        now=datetime(2026, 8, 9, 12, tzinfo=timezone.utc),
        trusted_source_groups=FIXTURE_SOURCE_GROUPS,
    )

    assert current["ok"] is True
    assert current["checked_count"] == 1
    assert current["items"][0]["code"] == "BOXOFFICE_CURRENT"
    assert stale["ok"] is False
    assert stale["stale_count"] == 1
    assert stale["items"][0]["code"] == "STALE_BOXOFFICE_BOARD"


def test_current_week_without_records_is_unhealthy(tmp_path):
    install_board(tmp_path, PENDING_BOARD)

    payload = staleness_check.check_staleness(
        data_dir=tmp_path,
        sla_hours=26,
        now=datetime(2026, 7, 26, 12, tzinfo=timezone.utc),
    )

    assert payload["ok"] is False
    assert payload["items"][0]["code"] == "NO_CURRENT_BOXOFFICE_DATA"
    assert payload["items"][0]["latest_boxoffice_at"] is None


def test_staleness_cli_exits_nonzero_with_explicit_weekly_error(tmp_path):
    install_board(tmp_path, READY_BOARD)

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--data-dir",
            str(tmp_path),
            "--fixture-mode",
            "--now",
            "2026-08-09T12:00:00Z",
        ],
        cwd=REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    assert result.returncode == 1
    payload = json.loads(result.stdout)
    assert payload["ok"] is False
    assert payload["items"][0]["code"] == "STALE_BOXOFFICE_BOARD"
    assert "ERROR: staleness check failed" in result.stderr
    assert "weekly_boxoffice=STALE_BOXOFFICE_BOARD" in result.stderr
