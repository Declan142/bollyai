"""Tests for draft_reviews.py pre-judge gates: gap_criticism_hit, banned_hit, sanitize_prose."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "subtitles"))
from draft_reviews import gap_criticism_hit, banned_hit, sanitize_prose


# ---------------------------------------------------------------------------
# gap_criticism_hit — sentences that MUST trigger (silence as pacing criticism)
# ---------------------------------------------------------------------------

class TestGapCriticismShouldFail:
    # Exact sentences from farzi v2 triage that slipped through the G3 judge
    def test_farzi_v2_e04_long_silent_stretch_stalls(self):
        assert gap_criticism_hit("long silent stretch stalls momentum")

    def test_farzi_v2_e06_long_silent_stretch_rather_than(self):
        assert gap_criticism_hit("long silent stretch stalls momentum rather than heightening tension")

    # scam-1992 E01 — "relentless silence...feels like filler" slipped through with G3=10
    def test_scam_e01_relentless_silence(self):
        assert gap_criticism_hit("Yet the relentless silence after Harshad's reveal feels like filler")

    # scam-1992 E02 — the key missed variant: long silences + stall + atmospheric qualifier
    def test_scam_e02_long_silences_atmospheric_stall(self):
        assert gap_criticism_hit(
            "The pacing swings between manic trading chatter and long silences, "
            "which, though atmospheric, stall momentum."
        )

    # Numbered duration variants (original rule — must still pass)
    def test_numbered_duration_second_silence(self):
        assert gap_criticism_hit("a 143-second silent stretch dominates the third act")

    def test_numbered_duration_minute_pause(self):
        assert gap_criticism_hit("a 29-minute pause breaks the tension")

    def test_numbered_duration_gap(self):
        assert gap_criticism_hit("a 48-second gap follows the confrontation")

    def test_numbered_seconds_before_noun(self):
        assert gap_criticism_hit("the silence for 87 seconds after the loan scene")

    # Other adjective variants
    def test_extended_silence(self):
        assert gap_criticism_hit("extended silence after the reveal slows the pace")

    def test_prolonged_pause(self):
        assert gap_criticism_hit("a prolonged pause breaks the episode's momentum")

    def test_dead_silence(self):
        assert gap_criticism_hit("dead silence drags the third act")

    # Pacing consequence verb variants
    def test_silence_hampers(self):
        assert gap_criticism_hit("The silence hampers the urgency of the confrontation")

    def test_pauses_drag(self):
        assert gap_criticism_hit("repeated pauses drag the climactic scene")

    def test_silence_undermines(self):
        assert gap_criticism_hit("The silence undermines the episode's pacing")

    # "long silences" without an explicit consequence verb — adjective gate catches it
    def test_long_silences_alone(self):
        assert gap_criticism_hit("long silences punctuate the second half")


# ---------------------------------------------------------------------------
# gap_criticism_hit — sentences that must NOT trigger (legit story criticism)
# ---------------------------------------------------------------------------

class TestGapCriticismShouldPass:
    def test_structural_repetition_criticism(self):
        assert not gap_criticism_hit(
            "The script circles the same revelation twice without earning the second visit"
        )

    def test_character_arc_criticism(self):
        assert not gap_criticism_hit(
            "Harshad's flip from certainty to desperation lands too quickly, "
            "skipping the internal debate that would sell it"
        )

    def test_repetition_scene_criticism(self):
        assert not gap_criticism_hit(
            "A second interrogation scene plays out with identical beats to the first, adding nothing"
        )

    def test_silence_as_character_moment(self):
        # silence used as a character decision, not a pacing stat
        assert not gap_criticism_hit(
            "His silence after the accusation is the episode's best moment"
        )

    def test_silence_between_characters(self):
        # relational silence, not pacing criticism
        assert not gap_criticism_hit(
            "The silence between Harshad and Ashwin speaks to a friendship already fracturing"
        )

    def test_silences_with_intent(self):
        # positive characterisation of silence - no pacing consequence verb
        assert not gap_criticism_hit(
            "The actors fill even the silences with intent"
        )

    def test_silence_earns_weight(self):
        assert not gap_criticism_hit(
            "The silence before the final reveal earns its weight"
        )

    def test_unrelated_pacing_verb(self):
        # "drags" present but not linked to silence
        assert not gap_criticism_hit(
            "A subplot about the broker's family drags the episode without advancing anything"
        )


# ---------------------------------------------------------------------------
# sanitize_prose — em/en-dash stripping + Verdict label removal
# ---------------------------------------------------------------------------

class TestSanitizeProse:
    def test_em_dash_replaced(self):
        result = sanitize_prose("contradiction — claiming he is innocent")
        assert "—" not in result
        assert " - " in result

    def test_en_dash_replaced(self):
        result = sanitize_prose("fallout – the removed tracker")
        assert "–" not in result
        assert " - " in result

    def test_verdict_label_stripped(self):
        result = sanitize_prose("Great episode with real stakes. Verdict: A taut hour.")
        assert "Verdict:" not in result

    def test_clean_text_unchanged(self):
        text = "Harshad's gamble pays off when the debt is cleared early."
        assert sanitize_prose(text) == text

    def test_empty_string(self):
        assert sanitize_prose("") == ""

    def test_none_returns_none(self):
        assert sanitize_prose(None) is None


# ---------------------------------------------------------------------------
# banned_hit — slop phrase + em-dash detection
# ---------------------------------------------------------------------------

class TestBannedHit:
    def test_delve_caught(self):
        assert "delve" in banned_hit("Let us delve into the backstory")

    def test_tapestry_caught(self):
        assert "tapestry" in banned_hit("a rich tapestry of characters")

    def test_em_dash_caught(self):
        assert "em-dash" in banned_hit("great scene — very good")

    def test_clean_text_empty(self):
        assert banned_hit("Strong writing and a sharp performance.") == []

    def test_none_safe(self):
        assert banned_hit(None) == []
