from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
FETCHERS_DIR = REPO_ROOT / "engine" / "fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

import common  # noqa: E402


def test_write_json_reports_identical_payload_as_noop(tmp_path):
    target = tmp_path / "nested" / "payload.json"

    assert common.write_json(target, {"b": 2, "a": 1}) is True
    first_bytes = target.read_bytes()
    first_inode = target.stat().st_ino
    assert common.write_json(target, {"a": 1, "b": 2}) is False

    assert target.read_bytes() == first_bytes
    assert target.stat().st_ino == first_inode


def test_write_json_replace_failure_preserves_original_and_cleans_temp(
    monkeypatch,
    tmp_path,
):
    target = tmp_path / "payload.json"
    original = b'{"last_good":true}\n'
    target.write_bytes(original)

    def replace_failure(*_args, **_kwargs):
        raise OSError("simulated replace failure")

    monkeypatch.setattr(common.os, "replace", replace_failure)

    with pytest.raises(OSError, match="simulated replace failure"):
        common.write_json(target, {"candidate": True})

    assert target.read_bytes() == original
    assert list(tmp_path.glob(".payload.json.*.tmp")) == []


def test_write_json_reports_post_replace_directory_sync_failure(
    monkeypatch,
    tmp_path,
):
    target = tmp_path / "payload.json"
    target.write_bytes(b'{"last_good":true}\n')
    real_fsync = common.os.fsync
    calls = 0

    def fail_directory_sync(descriptor):
        nonlocal calls
        calls += 1
        if calls == 2:
            raise OSError("simulated directory sync failure")
        return real_fsync(descriptor)

    monkeypatch.setattr(common.os, "fsync", fail_directory_sync)

    with pytest.raises(common.AtomicWriteError) as exc:
        common.write_json(target, {"candidate": True})

    assert exc.value.replaced is True
    assert target.read_text(encoding="utf-8") == '{\n  "candidate": true\n}\n'
    assert list(tmp_path.glob(".payload.json.*.tmp")) == []


def test_write_json_reports_post_replace_directory_open_failure(
    monkeypatch,
    tmp_path,
):
    target = tmp_path / "payload.json"
    target.write_bytes(b'{"last_good":true}\n')

    def fail_directory_open(path, flags, *args, **kwargs):
        if Path(path) == target.parent:
            raise OSError("simulated directory open failure")
        return real_open(path, flags, *args, **kwargs)

    real_open = common.os.open
    monkeypatch.setattr(common.os, "open", fail_directory_open)

    with pytest.raises(common.AtomicWriteError) as exc:
        common.write_json(target, {"candidate": True})

    assert exc.value.replaced is True
    assert target.read_text(encoding="utf-8") == '{\n  "candidate": true\n}\n'
    assert list(tmp_path.glob(".payload.json.*.tmp")) == []
