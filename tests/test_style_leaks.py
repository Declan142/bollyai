"""Gate 6 - style leaks (tooling citations + dropped-value fragments).

Mirrors tests/test_viewing_claim.py. Locks the two corpus-repair R4 patterns
into the suite so a regression breaks pytest, not just the validator: the
2026-07-02 campaign proved validator-clean prose can still violate the bar.
"""

from pathlib import Path
import json
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.gates.style_leak_regex import scan_text


POSITIVE_FIXTURES = [
    # D1: the internal subtitle dossier cited as a source in reader prose
    "The dossier notes dense dialogue broken by three long silences.",
    "Per the dossier, the finale runs fourteen minutes past the season average.",
    "The dossier's counts flag a talky middle stretch.",
    "The subtitles show a script that trusts pauses over punchlines.",
    "The dossier gives only flashes of the B-plot.",
    "the dossier tracks the cold opens getting longer each week.",
    # D2: timestamp templating collapsed to broken English
    "There are long silences from to and again from to, and those gaps are felt.",
    "The argument sequence from to gives the episode its first pressure change.",
    "The episode holds its breath between and never quite exhales.",
    "The chase runs from to.",
]


NEGATIVE_FIXTURES = [
    # legit plot usage of "dossier" (no source-verb after it)
    "MI5 assembles a dossier on the minister within the first act.",
    "The dossier Villanelle stole changes hands twice before the credits.",
    # subtitles as a subject without the source-verb construction
    "Subtitles in three languages shipped on day one.",
    # real from-X-to-Y ranges keep their nouns
    "The stretch from noon to midnight plays as one continuous shot.",
    "The season moves from Boston to Berlin without losing its footing.",
    # real between-X-and-Y
    "The finale swings between ambition and restraint.",
    # ordinary prose
    "BollyAI has not watched this. BollyAI has read everyone who has.",
    "Critics who watched the film call the pacing deliberate.",
]


@pytest.mark.parametrize("text", POSITIVE_FIXTURES)
def test_rejects_tooling_leaks_and_dropped_values(text):
    assert scan_text(text), text


@pytest.mark.parametrize("text", NEGATIVE_FIXTURES)
def test_allows_plot_usage_and_real_ranges(text):
    assert scan_text(text) == [], text


def _walk_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for key, value in node.items():
            if key == "_quarantine":
                continue
            yield from _walk_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from _walk_strings(value)


def test_catalog_has_zero_style_leaks():
    """Suite-level regression lock: the R2 sweeps left the catalog at zero hits
    (COMPLETE 2026-07-05); any reappearance breaks the build, not just review."""
    dirty = []
    for path in sorted((REPO_ROOT / "data" / "series").glob("*.json")):
        doc = json.loads(path.read_text(encoding="utf-8"))
        for text in _walk_strings(doc):
            findings = scan_text(text)
            if findings:
                dirty.append(f"{path.name}: {findings[0].label}: {findings[0].match}")
                break
    assert not dirty, "style leaks re-entered the catalog:\n" + "\n".join(dirty[:20])


def test_cli_exits_two_on_leak(tmp_path):
    target = tmp_path / "draft.txt"
    target.write_text("The dossier notes long silences from to and again.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "engine/gates/style_leak_regex.py"),
            "--input",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "dossier" in result.stderr.lower()


def test_cli_exits_zero_on_clean_prose(tmp_path):
    target = tmp_path / "draft.txt"
    target.write_text(
        "The season moves from Boston to Berlin without losing its footing.",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "engine/gates/style_leak_regex.py"),
            "--input",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
