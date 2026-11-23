from datetime import date
import json
from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "engine"))
from refresh_ott_daily import APPLE_ORIGIN, SourceError, build_calendar, refresh


TODAY = date(2026, 11, 24)
MONDAY = date(2026, 11, 23)
PRESS = "https://www.apple.com/tv-pr/originals/example/"


def apple(day="2026-11-25"):
    return {"id": "film-example", "title": "Example", "platform": "Apple TV+", "type": "film",
            "date": day, "language": "en", "industry": "streaming", "origin": APPLE_ORIGIN,
            "sources": [{"name": "Apple TV Press", "url": PRESS, "type": "press"}]}


def initial(path):
    root = path / "ott"
    root.mkdir()
    netflix = {"id": "film-existing", "title": "Existing", "platform": "Netflix", "type": "film",
               "date": "2026-12-02", "language": "en", "industry": "streaming", "fetched_at": "2026-11-23T06:00:00Z",
               "sources": [{"name": "Netflix", "url": "https://www.netflix.com/tudum/articles/example", "type": "press"}]}
    (root / "announcements.json").write_text(json.dumps([netflix]))
    (root / "calendar.json").write_text(json.dumps(build_calendar([netflix], start=MONDAY)))
    return root


def snapshot(root):
    return {f.name: f.read_bytes() for f in root.iterdir()}


def test_verified_updates_keep_curated_rows_and_are_byte_stable_on_repeat(tmp_path):
    root = initial(tmp_path)
    def source(known, start, end):
        assert start == MONDAY and end > date(2026, 12, 31)
        return [apple()], {PRESS}
    assert "updated" in refresh(tmp_path, TODAY, source)
    first = snapshot(root)
    assert [r["title"]["value"] for r in json.loads(first["calendar.json"])["entries"]] == ["Example", "Existing"]
    assert "unchanged" in refresh(tmp_path, TODAY, source)
    assert snapshot(root) == first
    assert set(first) == {"announcements.json", "calendar.json"}


@pytest.mark.parametrize("kind", ["unavailable", "unread", "incomplete"])
def test_source_failure_preserves_every_last_good_byte(tmp_path, kind):
    root = initial(tmp_path)
    refresh(tmp_path, TODAY, lambda *_: ([apple()], {PRESS}))
    old = snapshot(root)
    def broken(*_):
        if kind == "unavailable":
            raise SourceError("fixture network failure")
        return ([], set()) if kind == "unread" else ([], {"https://www.apple.com/tv-pr/originals/another/"})
    with pytest.raises(SourceError):
        refresh(tmp_path, TODAY, broken)
    assert snapshot(root) == old


def test_confirmed_reschedule_survives_outside_visitor_window(tmp_path):
    root = initial(tmp_path)
    refresh(tmp_path, TODAY, lambda *_: ([apple()], {PRESS}))
    def moved(known, *_):
        assert known == {PRESS}
        return [apple("2027-01-13")], {PRESS}
    refresh(tmp_path, TODAY, moved)
    assert [r["title"]["value"] for r in json.loads((root / "calendar.json").read_text())["entries"]] == ["Existing"]
    assert json.loads((root / "announcements.json").read_text())[1]["date"] == "2027-01-13"
    refresh(tmp_path, date(2027, 1, 12), moved)
    assert [r["title"]["value"] for r in json.loads((root / "calendar.json").read_text())["entries"]] == ["Example"]


def test_new_window_with_a_confirmed_empty_discovery_is_honest_and_idempotent(tmp_path):
    root = initial(tmp_path)
    source = lambda *_: ([], {PRESS})
    assert "0 verified releases" in refresh(tmp_path, date(2027, 1, 12), source)
    past_window = snapshot(root)
    assert json.loads(past_window["calendar.json"])["entries"] == []
    assert "unchanged" in refresh(tmp_path, date(2027, 1, 12), source)
    assert snapshot(root) == past_window


def test_native_apple_result_does_not_overwrite_a_curated_decision(tmp_path):
    root = initial(tmp_path)
    rows = json.loads((root / "announcements.json").read_text())
    curated = apple("2026-11-26")
    curated.pop("origin")
    curated["fetched_at"] = "2026-11-20T07:55:00Z"
    rows.append(curated)
    (root / "announcements.json").write_text(json.dumps(rows))
    refresh(tmp_path, TODAY, lambda *_: ([apple()], {PRESS}))
    assert json.loads((root / "announcements.json").read_text()) == rows
