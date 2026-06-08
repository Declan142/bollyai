"""Gate for the spoiler-FULL "Ending Explained" surface.

This is the one place BollyAI writes spoilers, so the fences are STRICTER:
  - spoiler flag must be literally true,
  - every walkthrough must cite >= 1 source (the published record it is grounded
    in) — an uncited ending is treated as a fabrication risk and hard-fails,
  - no first-person viewing claims (same regex gate as the rest of the site),
  - no em-/en-dashes in prose (house style; everything else is dash-stripped),
  - slug must resolve to a real series, finale season must exist on that series.
"""
from pathlib import Path
import json
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.gates.viewing_claim_regex import scan_text

ENDINGS_DIR = REPO_ROOT / "data" / "endings"
SERIES_DIR = REPO_ROOT / "data" / "series"

ENDING_FILES = sorted(ENDINGS_DIR.glob("*.json")) if ENDINGS_DIR.exists() else []
FANCY_DASHES = ("—", "–", "‒", "―")  # em, en, figure, horizontal bar


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prose_blobs(e: dict) -> list[str]:
    blobs = [e.get("hook", "")]
    for sec in e.get("sections", []) or []:
        blobs += [sec.get("heading", ""), sec.get("body", "")]
    if e.get("final_image"):
        blobs.append(e["final_image"])
    for qa in e.get("lingering_questions", []) or []:
        blobs += [qa.get("q", ""), qa.get("a", "")]
    return [b for b in blobs if b]


@pytest.mark.parametrize("path", ENDING_FILES, ids=lambda p: p.stem)
def test_ending_schema_and_fences(path: Path):
    e = _load(path)

    # --- required shape ---
    assert e.get("slug") == path.stem, f"slug must match filename: {path.stem}"
    assert isinstance(e.get("title"), str) and e["title"].strip(), "title required"
    assert isinstance(e.get("season_number"), int), "season_number must be int"
    assert e.get("spoiler") is True, "spoiler must be literally true"
    assert isinstance(e.get("hook"), str) and len(e["hook"].split()) >= 8, "hook too thin"
    assert isinstance(e.get("date_modified"), str) and e["date_modified"], "date_modified required"

    sections = e.get("sections")
    assert isinstance(sections, list) and len(sections) >= 3, "need >= 3 walkthrough sections"
    for sec in sections:
        assert isinstance(sec.get("heading"), str) and sec["heading"].strip(), "section heading"
        assert isinstance(sec.get("body"), str) and len(sec["body"].split()) >= 25, "section body too thin"

    # --- grounding: >= 1 real source ---
    sources = e.get("sources")
    assert isinstance(sources, list) and len(sources) >= 1, "an ending MUST cite >= 1 source"
    for s in sources:
        assert isinstance(s.get("title"), str) and s["title"].strip(), "source title"
        assert isinstance(s.get("url"), str) and s["url"].startswith("http"), "source url must be http(s)"

    # --- referential integrity ---
    series_path = SERIES_DIR / f"{path.stem}.json"
    assert series_path.exists(), f"no series for ending {path.stem}"
    series = _load(series_path)
    season_nums = {s.get("number") for s in series.get("seasons", [])}
    assert e["season_number"] in season_nums, f"season {e['season_number']} not on series"

    # --- honesty fences over every prose blob ---
    for blob in _prose_blobs(e):
        findings = scan_text(blob)
        assert not findings, f"viewing-claim in {path.stem}: {findings} :: {blob[:80]}"
        bad = [d for d in FANCY_DASHES if d in blob]
        assert not bad, f"fancy dash {bad} in {path.stem}: {blob[:80]}"


def test_endings_dir_exists():
    # Surface is live; the directory and at least the exemplar must exist.
    assert ENDINGS_DIR.exists(), "data/endings/ missing"
    assert ENDING_FILES, "no ending files present"
