"""Regression tests for the free-tier bare-string list-item bug.

Free-tier/codex lanes occasionally emit a bare string (e.g. a stray schema key
name like "plants_from") inside an otherwise-valid JSON list field. Historically
that crashed verify_grounding (p.get() on a str) mid-batch.

Root-cause layer: llm_bridge.drop_malformed_list_items normalizes at ingestion
(extract_dossier._dossier_call / season_crosspass._crosspass_call), so persisted
documents are well-typed. Belt-and-braces layer: verify_grounding.keep() strips
plus logs instead of crashing, for old on-disk dossiers.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts" / "subtitles"))

import extract_dossier
import verify_grounding as vg
from llm_bridge import drop_malformed_list_items


def make_index() -> vg.EpisodeIndex:
    return vg.EpisodeIndex({"dialogue": [
        {"t": 62, "speaker": None, "line": "we bury it tonight"},
        {"t": 300, "speaker": None, "line": "you said we buried it"},
    ]})


def base_dossier() -> dict:
    return {
        "episode": "S01E01",
        "title": None,
        "beats": [{"t": "01:02", "what": "burial pact made"}],
        "character_beats": [],
        "key_lines": [{"t": "05:00", "speaker": None,
                       "line": "you said we buried it", "why": "callback spine"}],
        "open_loops": ["what was buried"],
        "payoffs": [
            "plants_from",  # the free-tier bug shape: bare string in a dict list
            {"plants_from": "01:02", "pays_here": "05:00", "what": "pact pays off"},
        ],
        "contradiction": {"who": "Sara", "wants": "silence", "does": "talks",
                          "line_t": "05:00"},
        "tone_notes": "",
        "speaker_attribution_confidence": "low",
        "self_check": {"every_t_exists": False, "quotes_verbatim": False,
                       "quote_words_total": 5, "no_training_facts": True},
    }


class TestNormalizeAtIngestion:
    def test_bare_string_dropped_from_payoffs(self):
        d = base_dossier()
        dropped = drop_malformed_list_items(d, extract_dossier.DICT_LIST_FIELDS)
        assert d["payoffs"] == [
            {"plants_from": "01:02", "pays_here": "05:00", "what": "pact pays off"}]
        assert len(dropped) == 1
        assert dropped[0].startswith("payoffs:")

    def test_string_item_lists_untouched(self):
        d = base_dossier()
        drop_malformed_list_items(d, extract_dossier.DICT_LIST_FIELDS)
        assert d["open_loops"] == ["what was buried"]

    def test_non_list_and_missing_fields_ignored(self):
        d = {"payoffs": "not-a-list"}
        assert drop_malformed_list_items(d, ("payoffs", "beats")) == []
        assert d["payoffs"] == "not-a-list"

    def test_dossier_call_persist_path_is_well_typed(self, monkeypatch):
        """The producer seam itself: a bridge reply carrying a bare-string
        payoff must come out of _dossier_call with dict-only list items."""
        reply = json.dumps(base_dossier())
        monkeypatch.setattr(extract_dossier, "gpt_ask", lambda *a, **k: (reply, 0))
        monkeypatch.setattr(extract_dossier, "configured_model", lambda: "gpt-5.6-luna")
        obj, meta = extract_dossier._dossier_call(
            "sys", "user", required_keys=("episode", "payoffs"), ctx="test")
        assert all(isinstance(p, dict) for p in obj["payoffs"])
        assert len(obj["payoffs"]) == 1
        assert meta["malformed_items_dropped"] == 1


class TestKeepGuardBeltAndBraces:
    def test_verify_dossier_survives_bare_string_payoff(self):
        """Old on-disk dossiers written before ingestion normalization must
        strip plus log, never raise AttributeError."""
        errs, out = vg.verify_dossier("S01E01", base_dossier(), make_index())
        assert all(isinstance(p, dict) for p in out["payoffs"])
        assert len(out["payoffs"]) == 1
        assert any("not an object" in e for e in errs)
        assert any(s.get("why") == "not an object" for s in out.get("_stripped", []))

    def test_verify_dossier_keeps_valid_claims(self):
        errs, out = vg.verify_dossier("S01E01", base_dossier(), make_index())
        assert out["beats"] == [{"t": "01:02", "what": "burial pact made"}]
        assert len(out["key_lines"]) == 1
