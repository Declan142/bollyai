"""Tests for scripts/batch/validate_films.py — tmp fixtures only."""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
VALIDATE_SCRIPT = REPO_ROOT / "scripts" / "batch" / "validate_films.py"


def _load_mod():
    spec = importlib.util.spec_from_file_location("validate_films", VALIDATE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


VALID_FILM = {
    "qid": {"value": "Q12345", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "slug": "test-film",
    "canonical_industry": "bollywood",
    "title": {"value": "Test Film", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "logline": "A test film about a heist.",
    "_quarantine": [],
    "date_modified": "2026-01-01T00:00:00+05:30",
}

VALID_REVIEW = {
    "spoiler_free": "The film opens on a rooftop that establishes both geography and character without a word. The first act is precise. The heist sequence earns its length through spatial clarity. Criticism: the third-act reveal rushes what earlier scenes earned through patience.",
    "the_moment": "The rooftop standoff that reframes the opening scene.",
    "bollymeter": None,
    "critic_note": None,
    "merged_at": "2026-06-13T09:00:00+05:30",
}


def _write(tmp_path, data, stem="Q12345"):
    p = tmp_path / f"{stem}.json"
    p.write_text(json.dumps(data), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Basic sanity
# ---------------------------------------------------------------------------

def test_valid_film_no_review_passes(tmp_path):
    mod = _load_mod()
    p = _write(tmp_path, VALID_FILM)
    assert mod.validate_file(p) == []


def test_valid_film_with_review_passes(tmp_path):
    mod = _load_mod()
    d = {**VALID_FILM, "review": VALID_REVIEW}
    p = _write(tmp_path, d)
    assert mod.validate_file(p) == []


def test_missing_required_fields(tmp_path):
    mod = _load_mod()
    for field in ("qid", "slug", "canonical_industry"):
        d = {k: v for k, v in VALID_FILM.items() if k != field}
        p = _write(tmp_path, d)
        errs = mod.validate_file(p)
        assert any(field in e for e in errs), f"expected error for missing {field}, got {errs}"


# ---------------------------------------------------------------------------
# Review shape
# ---------------------------------------------------------------------------

def test_review_spoiler_free_empty_fails(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "spoiler_free": ""}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("spoiler_free empty" in e for e in errs)


def test_review_the_moment_over_25_words_fails(tmp_path):
    mod = _load_mod()
    long_tm = " ".join(["word"] * 26)
    rev = {**VALID_REVIEW, "the_moment": long_tm}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("the_moment" in e and "25" in e for e in errs)


def test_review_the_moment_null_passes(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "the_moment": None}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    assert mod.validate_file(p) == []


def test_review_bollymeter_out_of_range_fails(tmp_path):
    mod = _load_mod()
    for bad in (11, -1, "high", []):
        rev = {**VALID_REVIEW, "bollymeter": bad}
        p = _write(tmp_path, {**VALID_FILM, "review": rev})
        errs = mod.validate_file(p)
        assert any("bollymeter" in e for e in errs), f"expected bollymeter error for {bad!r}"


def test_review_bollymeter_valid_float_passes(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "bollymeter": 7.5}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    assert mod.validate_file(p) == []


def test_review_critic_note_missing_fields_fails(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "critic_note": {"text": "Good film.", "source": "HT"}}  # missing url
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("critic_note" in e for e in errs)


def test_review_critic_note_text_over_25_words_fails(tmp_path):
    mod = _load_mod()
    long_quote = " ".join(["word"] * 26)
    rev = {**VALID_REVIEW, "critic_note": {"text": long_quote, "source": "HT", "url": "https://example.com"}}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("critic_note" in e and "25" in e for e in errs)


def test_review_critic_note_valid_passes(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "critic_note": {
        "text": "A heist film that earns its finale.",
        "source": "HT", "url": "https://example.com"
    }}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    assert mod.validate_file(p) == []


# ---------------------------------------------------------------------------
# Fence checks
# ---------------------------------------------------------------------------

def test_em_dash_in_review_fails(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "spoiler_free": "Great film—really great."}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("em/en-dash" in e for e in errs)


def test_em_dash_in_logline_fails(tmp_path):
    mod = _load_mod()
    d = {**VALID_FILM, "logline": "A film—about something."}
    p = _write(tmp_path, d)
    errs = mod.validate_file(p)
    assert any("em/en-dash" in e for e in errs)


def test_viewing_claim_in_review_fails(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "spoiler_free": "When I watched this film, I noticed the pacing."}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("viewing-claim" in e for e in errs)


def test_viewing_claim_in_the_moment_fails(tmp_path):
    mod = _load_mod()
    rev = {**VALID_REVIEW, "the_moment": "The scene I watched twice in the theatre."}
    p = _write(tmp_path, {**VALID_FILM, "review": rev})
    errs = mod.validate_file(p)
    assert any("viewing-claim" in e for e in errs)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def test_cli_pass(tmp_path):
    import subprocess, sys
    p = _write(tmp_path, VALID_FILM)
    r = subprocess.run([sys.executable, str(VALIDATE_SCRIPT), str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 0
    assert "PASS" in r.stdout


def test_cli_fail(tmp_path):
    import subprocess, sys
    d = {**VALID_FILM, "review": {**VALID_REVIEW, "spoiler_free": ""}}
    p = _write(tmp_path, d)
    r = subprocess.run([sys.executable, str(VALIDATE_SCRIPT), str(p)],
                       capture_output=True, text=True)
    assert r.returncode == 1
    assert "FAIL" in r.stderr
