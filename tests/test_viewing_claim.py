from pathlib import Path
import subprocess
import sys

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from engine.gates.viewing_claim_regex import scan_text


POSITIVE_FIXTURES = [
    "I watched the film on Friday and the interval landed.",
    "When I saw the climax, the theatre went silent.",
    "I've seen it twice, and the second half still works.",
    "I have watched the trailer in a packed hall.",
    "I caught the film at a press show.",
    "After watching the movie, the opening stretch felt stronger.",
    "While watching the episode, I noticed the edit drag.",
    "My screening was packed from the first scene.",
    "Maine film dekhi kal raat.",
    "maine theatre mein movie dekhi thi.",
    "Jab maine interval block dekha, crowd phat gaya.",
    "Humne FDFS dekha and the mass scenes worked.",
    "hamne picture dekhi thi on release day.",
    "Main theatre gaya tha for the first show.",
    "Theatre mein maine climax dekha.",
    "Mujhe laga film ka climax thoda lamba hai.",
    "First day first show dekha, crowd energy solid thi.",
]


NEGATIVE_FIXTURES = [
    "BollyAI has not watched this. BollyAI has read everyone who has.",
    "BollyAI hasn't watched this. BollyAI has read everyone who has.",
    "Critics who watched the film call it uneven.",
    "The trailer shows a larger canvas than the teaser.",
    "Audience reports suggest the climax lands.",
    "Isha watched the show before joining the panel.",
    "Maine Pyaar Kiya remains a landmark film title.",
    "The source says viewers saw a stronger day-two trend.",
    "Reviewers at the screening noticed a loud second half.",
    "Trade estimates vary, so BollyAI is holding the number.",
]


@pytest.mark.parametrize("text", POSITIVE_FIXTURES)
def test_rejects_first_person_viewing_claims(text):
    assert scan_text(text), text


@pytest.mark.parametrize("text", NEGATIVE_FIXTURES)
def test_allows_non_first_person_or_disclosed_ai_language(text):
    assert scan_text(text) == []


def test_cli_exits_two_on_rejected_claim(tmp_path):
    target = tmp_path / "draft.txt"
    target.write_text("Maine movie dekhi thi and I watched the climax again.", encoding="utf-8")

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "engine/gates/viewing_claim_regex.py"),
            "--input",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "viewing" not in result.stdout.lower()
    assert "maine" in result.stderr.lower() or "i watched" in result.stderr.lower()


def test_cli_exits_zero_on_clean_disclosure(tmp_path):
    target = tmp_path / "draft.txt"
    target.write_text(
        "BollyAI has not watched this. BollyAI has read everyone who has.",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "engine/gates/viewing_claim_regex.py"),
            "--input",
            str(target),
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert result.stderr == ""
