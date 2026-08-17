from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "engine"))

import regen_ott_weekly  # noqa: E402


def test_live_empty_fetch_fails_closed_without_writing(tmp_path, monkeypatch):
    (tmp_path / "ott").mkdir()
    (tmp_path / "films").mkdir()
    (tmp_path / "series").mkdir()
    (tmp_path / "ott" / "announcements.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(regen_ott_weekly, "refresh_registry", lambda *args, **kwargs: {"fetched": 0, "added": 0, "updated": 0})

    result = regen_ott_weekly.main(["--data-dir", str(tmp_path), "--today", "2026-08-17", "--weeks", "2"])

    assert result == 2
    assert not (tmp_path / "ott" / "calendar.json").exists()


def test_live_zero_fetch_does_not_relabel_stale_registry_entries_as_fetched(tmp_path, monkeypatch):
    (tmp_path / "ott").mkdir()
    (tmp_path / "films").mkdir()
    (tmp_path / "series").mkdir()
    (tmp_path / "ott" / "announcements.json").write_text("[]", encoding="utf-8")
    monkeypatch.setattr(
        regen_ott_weekly,
        "refresh_registry",
        lambda *args, **kwargs: {"fetched": 0, "added": 0, "updated": 0},
    )
    monkeypatch.setattr(
        regen_ott_weekly,
        "build_calendar",
        lambda *args, **kwargs: {"entries": [{"slug": "stale-registry-entry"}]},
    )

    result = regen_ott_weekly.main(
        ["--data-dir", str(tmp_path), "--today", "2026-08-17", "--weeks", "2"]
    )

    assert result == 2
    assert not (tmp_path / "ott" / "calendar.json").exists()
