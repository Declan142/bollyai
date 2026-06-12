"""Tests for scripts/subtitles/merge_reviews.py — tmp fixtures only, no real data touched."""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
MERGE_SCRIPT = REPO_ROOT / "scripts" / "subtitles" / "merge_reviews.py"

# Minimal valid series JSON matching validate_series.py requirements
SERIES_TEMPLATE = {
    "slug": "test-series",
    "qid": {"value": "Q999", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "title": {"value": "Test Series", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "canonical_industry": "streaming",
    "origin": "India",
    "original_language": {"value": "hi", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "platform": {"value": "Netflix", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "status": "ended",
    "logline": "A test series for merge validation.",
    "poster": {"src": "/img/series/_fallback.svg", "alt": "Test Series poster", "attribution": "no third-party image"},
    "renewal": {"state": "ended", "note": "Limited series, complete.", "source": "Netflix", "source_url": "https://netflix.com"},
    "seasons": [
        {
            "number": 1,
            "year": 2024,
            "episodes": 5,
            "release_date": {"value": "2024-01-01", "source": "Netflix", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
            "verdict": "WORTH-IT",
            "bollymeter": None,
            "critic": {"positive_pct": None, "sample": None, "pull_quotes": []},
            "audience": None,
            "review_body": "A solid limited series that explores its premise with conviction across five episodes.",
            "season_over_season": None,
            "episode_reviews": []
        }
    ],
    "_quarantine": [],
    "date_modified": "2026-01-01T00:00:00+05:30"
}

STAGING_PASS = [
    {
        "number": 3,
        "title": "Episode 3",
        "bollymeter": None,
        "critic_note": None,
        "spoiler_free": "The third episode slows the pace intentionally, letting two leads occupy a single room. The central argument works because both positions are scripted as correct. Criticism: the subplot introduced here is abandoned by the finale.",
        "the_moment": "The moment a minor character reveals the real motive.",
        "_judge": {"overall": 8, "verdict": "pass", "worst_sentence": None, "fix": None},
        "_writer": {"lane": "gpt-4o-mini", "words": 47, "local_issues": []},
        "voice_pass": True
    }
]

STAGING_NO_VOICE_PASS = [
    {
        "number": 2,
        "title": "Episode 2",
        "bollymeter": None,
        "critic_note": None,
        "spoiler_free": "Episode two raises stakes through escalating confrontations. The pacing is brisk.",
        "the_moment": "The negotiation scene that splits the group.",
        "_judge": {"overall": 8, "verdict": "pass"},
        "_writer": {"lane": "gpt-4o-mini", "words": 16, "local_issues": []},
        # voice_pass deliberately absent
    }
]

STAGING_NO_G3_PASS = [
    {
        "number": 1,
        "title": "Episode 1",
        "bollymeter": None,
        "critic_note": None,
        "spoiler_free": "Episode one is fine.",
        "the_moment": "The opener.",
        "_judge": {"overall": 4, "verdict": "revise"},
        "_writer": {"lane": "gpt-4o-mini", "words": 4, "local_issues": []},
        "voice_pass": True
    }
]


def write_staging(subs_slug_dir: Path, reviews: list) -> Path:
    reviews_dir = subs_slug_dir / "_reviews"
    reviews_dir.mkdir(parents=True, exist_ok=True)
    p = reviews_dir / "episodes.json"
    p.write_text(json.dumps(reviews, ensure_ascii=False), encoding="utf-8")
    return p


def write_dossier_stubs(subs_slug_dir: Path, stubs: list[str]) -> None:
    ddir = subs_slug_dir / "_dossiers"
    ddir.mkdir(parents=True, exist_ok=True)
    for stem in stubs:
        (ddir / f"{stem}.json").write_text("{}", encoding="utf-8")


# ---------------------------------------------------------------------------
# Dry-run tests
# ---------------------------------------------------------------------------

def test_dry_run_no_eligible(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_NO_VOICE_PASS)
    write_dossier_stubs(subs, ["S01E02"])

    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    series_path.write_text(json.dumps(SERIES_TEMPLATE | {"slug": slug}), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=False, force=False)
    assert rc == 0
    # series JSON must be untouched
    assert json.loads(series_path.read_text())["seasons"][0]["episode_reviews"] == []


def test_dry_run_eligible_no_write(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_PASS)
    write_dossier_stubs(subs, ["S01E03"])

    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    series_path.write_text(json.dumps(SERIES_TEMPLATE | {"slug": slug}), encoding="utf-8")

    # Patch paths by monkeypatching via env is complex; instead call merge_series directly
    import importlib, types
    # We'll test the module directly
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    # Temporarily redirect roots
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=False, force=False)
    assert rc == 0
    # dry-run: no write
    result = json.loads(series_path.read_text())
    assert result["seasons"][0]["episode_reviews"] == []


def test_apply_merges_and_validates(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_PASS)
    write_dossier_stubs(subs, ["S01E03"])

    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    d = {**SERIES_TEMPLATE, "slug": slug}
    series_path.write_text(json.dumps(d), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=True, force=False)
    assert rc == 0

    result = json.loads(series_path.read_text())
    eps = result["seasons"][0]["episode_reviews"]
    assert len(eps) == 1
    ep = eps[0]
    assert ep["number"] == 3
    assert "merged_at" in ep
    # internal fields must be stripped
    assert "_judge" not in ep
    assert "_writer" not in ep
    assert "voice_pass" not in ep


def test_gate_refuses_missing_voice_pass(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_NO_VOICE_PASS)
    write_dossier_stubs(subs, ["S01E02"])

    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    series_path.write_text(json.dumps(SERIES_TEMPLATE | {"slug": slug}), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=True, force=False)
    assert rc == 0  # nothing to merge, not an error
    result = json.loads(series_path.read_text())
    assert result["seasons"][0]["episode_reviews"] == []


def test_gate_refuses_failed_g3(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_NO_G3_PASS)
    write_dossier_stubs(subs, ["S01E01"])

    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    series_path.write_text(json.dumps(SERIES_TEMPLATE | {"slug": slug}), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=True, force=False)
    assert rc == 0
    result = json.loads(series_path.read_text())
    assert result["seasons"][0]["episode_reviews"] == []


def test_skip_already_present_without_force(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_PASS)
    write_dossier_stubs(subs, ["S01E03"])

    existing_ep = {
        "number": 3, "title": "Episode 3", "bollymeter": None,
        "spoiler_free": "Already here.", "the_moment": "An earlier take.",
        "critic_note": None
    }
    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    d = {**SERIES_TEMPLATE, "slug": slug}
    d["seasons"][0]["episode_reviews"] = [existing_ep]
    series_path.write_text(json.dumps(d), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=True, force=False)
    assert rc == 0
    result = json.loads(series_path.read_text())
    # original text must be preserved (no overwrite without --force)
    ep = result["seasons"][0]["episode_reviews"][0]
    assert ep["spoiler_free"] == "Already here."


def test_force_overwrites_existing(tmp_path):
    slug = "test-series"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, STAGING_PASS)
    write_dossier_stubs(subs, ["S01E03"])

    existing_ep = {
        "number": 3, "title": "Episode 3", "bollymeter": None,
        "spoiler_free": "Old review.", "the_moment": "Old moment.",
        "critic_note": None
    }
    series_dir = tmp_path / "data" / "series"
    series_dir.mkdir(parents=True)
    series_path = series_dir / f"{slug}.json"
    d = {**SERIES_TEMPLATE, "slug": slug}
    d["seasons"][0]["episode_reviews"] = [existing_ep]
    series_path.write_text(json.dumps(d), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_series(slug, apply=True, force=True)
    assert rc == 0
    result = json.loads(series_path.read_text())
    ep = result["seasons"][0]["episode_reviews"][0]
    assert "merged_at" in ep  # confirms it was replaced by the new one
    assert ep["spoiler_free"] != "Old review."


# ---------------------------------------------------------------------------
# Film path tests
# ---------------------------------------------------------------------------

FILM_TEMPLATE = {
    "qid": {"value": "Q12345", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "slug": "test-film",
    "canonical_industry": "bollywood",
    "title": {"value": "Test Film", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "original_language": {"value": "hi", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "release_date": {"value": "2024-06-01", "source": "wikidata", "fetched_at": "2026-01-01T00:00:00+05:30", "confidence": "verified"},
    "status": "released",
    "logline": "A test film.",
    "poster": {"src": "/img/films/_fallback.svg", "alt": "Test Film poster", "attribution": "none"},
    "budget": None,
    "box_office": {"day_rows": [], "totals": {"india_net_inr_cr": None, "worldwide_gross_inr_cr": None, "as_of": "2026-01-01"}},
    "verdict": {"ladder_rung": None, "tracking": False},
    "bollymeter": None,
    "ott": None,
    "_quarantine": [],
    "date_modified": "2026-01-01T00:00:00+05:30"
}

FILM_STAGING_PASS = [
    {
        "number": 1,
        "title": "Episode 1",
        "bollymeter": None,
        "critic_note": None,
        "spoiler_free": "The film opens on a landscape that frames the central tension before a word is spoken. The first act is precise in establishing the stakes. Criticism: the final stretch overexplains what the visual language already communicated.",
        "the_moment": "The final confrontation that reframes the protagonist's entire arc.",
        "_judge": {"overall": 8, "verdict": "pass"},
        "_writer": {"lane": "gpt-4o-mini", "words": 42, "local_issues": []},
        "voice_pass": True
    }
]


def test_film_dry_run(tmp_path):
    slug = "test-film"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, FILM_STAGING_PASS)

    films_dir = tmp_path / "data" / "films"
    films_dir.mkdir(parents=True)
    film_path = films_dir / "Q12345.json"
    film_path.write_text(json.dumps(FILM_TEMPLATE), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_film(slug, apply=False, force=False)
    assert rc == 0
    result = json.loads(film_path.read_text())
    assert "review" not in result  # dry-run: no write


def test_film_apply_merges(tmp_path):
    slug = "test-film"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, FILM_STAGING_PASS)

    films_dir = tmp_path / "data" / "films"
    films_dir.mkdir(parents=True)
    film_path = films_dir / "Q12345.json"
    film_path.write_text(json.dumps(FILM_TEMPLATE), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_film(slug, apply=True, force=False)
    assert rc == 0

    result = json.loads(film_path.read_text())
    rev = result.get("review")
    assert rev is not None
    assert "spoiler_free" in rev
    assert "merged_at" in rev
    # episode-specific fields stripped for films
    assert "number" not in rev
    assert "title" not in rev
    # internals stripped
    assert "_judge" not in rev
    assert "voice_pass" not in rev


def test_film_skip_existing_without_force(tmp_path):
    slug = "test-film"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, FILM_STAGING_PASS)

    films_dir = tmp_path / "data" / "films"
    films_dir.mkdir(parents=True)
    film_path = films_dir / "Q12345.json"
    existing = {**FILM_TEMPLATE, "review": {"spoiler_free": "Prior take.", "merged_at": "2026-01-01"}}
    film_path.write_text(json.dumps(existing), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_film(slug, apply=True, force=False)
    assert rc == 0
    result = json.loads(film_path.read_text())
    assert result["review"]["spoiler_free"] == "Prior take."


def test_film_gate_refuses_missing_voice_pass(tmp_path):
    slug = "test-film"
    subs = tmp_path / "data" / "subtitles" / slug
    no_voice = [{**FILM_STAGING_PASS[0], "voice_pass": False}]
    write_staging(subs, no_voice)

    films_dir = tmp_path / "data" / "films"
    films_dir.mkdir(parents=True)
    film_path = films_dir / "Q12345.json"
    film_path.write_text(json.dumps(FILM_TEMPLATE), encoding="utf-8")

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    rc = mod.merge_film(slug, apply=True, force=False)
    assert rc == 0  # 0 eligible, not an error
    result = json.loads(film_path.read_text())
    assert "review" not in result


# ---------------------------------------------------------------------------
# Q4: unmatched slug must fail loudly (SystemExit, stderr message)
# ---------------------------------------------------------------------------

def test_unmatched_film_slug_fails_loudly(tmp_path, capsys):
    """_find_film_path must raise SystemExit(2) and print to stderr — never silent skip."""
    slug = "nonexistent-film"
    subs = tmp_path / "data" / "subtitles" / slug
    write_staging(subs, FILM_STAGING_PASS)

    films_dir = tmp_path / "data" / "films"
    films_dir.mkdir(parents=True)
    # Deliberately do NOT create a film JSON with this slug

    import importlib
    spec = importlib.util.spec_from_file_location("merge_reviews", MERGE_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.SUBS_ROOT = tmp_path / "data" / "subtitles"
    mod.SERIES_DIR = tmp_path / "data" / "series"
    mod.FILMS_DIR = tmp_path / "data" / "films"

    with pytest.raises(SystemExit) as exc_info:
        mod.merge_film(slug, apply=True, force=False)
    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert slug in captured.err
