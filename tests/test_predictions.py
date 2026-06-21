"""Gate for the forward-looking "Finale Predictions" surface.

Honesty fences distinct from endings.ts - speculation must be clearly labelled:
  - every prediction cites >= 1 source (grounding in published episode record),
  - theories must carry a likelihood field (flags speculation as BollyAI analysis),
  - no first-person viewing claims (same regex gate as the rest of the site),
  - no em-/en-dashes in prose (house style),
  - slug must resolve to a real series, predicted season must exist on that series.
"""
from pathlib import Path
import json
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.gates.viewing_claim_regex import scan_text

PREDICTIONS_DIR = REPO_ROOT / "data" / "predictions"
SERIES_DIR = REPO_ROOT / "data" / "series"

PREDICTION_FILES = sorted(PREDICTIONS_DIR.glob("*.json")) if PREDICTIONS_DIR.exists() else []
FANCY_DASHES = ("—", "–", "‒", "―")  # em, en, figure, horizontal bar


def _load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def _prose_blobs(p: dict) -> list[str]:
    blobs = [p.get("hook", "")]
    for sec in p.get("sections", []) or []:
        blobs += [sec.get("heading", ""), sec.get("body", "")]
    for theory in p.get("theories", []) or []:
        blobs += [theory.get("title", ""), theory.get("basis", ""), theory.get("likelihood", "")]
    for qa in p.get("lingering_questions", []) or []:
        blobs += [qa.get("q", ""), qa.get("a", "")]
    return [b for b in blobs if b]


@pytest.mark.parametrize("path", PREDICTION_FILES, ids=lambda p: p.stem)
def test_prediction_schema_and_fences(path: Path):
    p = _load(path)

    # --- required shape ---
    assert p.get("slug") == path.stem, f"slug must match filename: {path.stem}"
    assert isinstance(p.get("title"), str) and p["title"].strip(), "title required"
    assert isinstance(p.get("season_number"), int), "season_number must be int"
    assert isinstance(p.get("hook"), str) and len(p["hook"].split()) >= 8, "hook too thin"
    assert isinstance(p.get("date_modified"), str) and p["date_modified"], "date_modified required"

    sections = p.get("sections")
    assert isinstance(sections, list) and len(sections) >= 2, "need >= 2 context sections"
    for sec in sections:
        assert isinstance(sec.get("heading"), str) and sec["heading"].strip(), "section heading"
        assert isinstance(sec.get("body"), str) and len(sec["body"].split()) >= 25, "section body too thin"

    theories = p.get("theories")
    assert isinstance(theories, list) and 6 <= len(theories) <= 9, "need 6-9 theories"
    for theory in theories:
        assert isinstance(theory.get("title"), str) and theory["title"].strip(), "theory title"
        assert isinstance(theory.get("basis"), str) and theory["basis"].strip(), "theory basis"
        assert isinstance(theory.get("likelihood"), str) and theory["likelihood"].strip(), "theory likelihood"

    # --- grounding: >= 1 real source ---
    sources = p.get("sources")
    assert isinstance(sources, list) and len(sources) >= 1, "a prediction MUST cite >= 1 source"
    for s in sources:
        assert isinstance(s.get("title"), str) and s["title"].strip(), "source title"
        assert isinstance(s.get("url"), str) and s["url"].startswith("http"), "source url must be http(s)"

    # --- referential integrity ---
    series_path = SERIES_DIR / f"{path.stem}.json"
    assert series_path.exists(), f"no series for prediction {path.stem}"
    series = _load(series_path)
    season_nums = {s.get("number") for s in series.get("seasons", [])}
    assert p["season_number"] in season_nums, f"season {p['season_number']} not on series"

    # --- honesty fences over every prose blob ---
    for blob in _prose_blobs(p):
        findings = scan_text(blob)
        assert not findings, f"viewing-claim in {path.stem}: {findings} :: {blob[:80]}"
        bad = [d for d in FANCY_DASHES if d in blob]
        assert not bad, f"fancy dash {bad} in {path.stem}: {blob[:80]}"


def test_predictions_dir_exists():
    assert PREDICTIONS_DIR.exists(), "data/predictions/ missing"
    assert PREDICTION_FILES, "no prediction files present"
