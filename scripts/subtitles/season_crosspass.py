#!/usr/bin/env python3
"""season_crosspass.py — the easter-egg stage. Whole series in ONE 1M context.

Runs TWICE (nemotron lane + deepseek/owl lane = different families), intersects
callbacks: both-found = confidence "high", single-found = "candidate"
(candidates publish only after Fable confirms - FREE_MODEL_RULES.md Part 2).

Input:  data/subtitles/<slug>/_stats/*.json
Output: data/subtitles/<slug>/_dossiers/_crosspass.json

Usage: python3 season_crosspass.py <slug> [--single]   (--single = skip consensus, 1 call)
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import orfree
from extract_dossier import mmss

ROOT = Path.home() / "bollyai" / "data" / "subtitles"

SYSTEM = (
    "You are a forensic continuity analyst. You find cross-episode connections that exist "
    "in the provided dialogue ONLY. Every claim carries episode + timestamp anchors at BOTH "
    "ends. You never use training-memory facts about any show. Output one valid JSON object."
)

PROMPT_TMPL = """FULL SERIES DIALOGUE for {slug} ({neps} episodes). Format: episode header then MM:SS|speaker-or-blank|line (minutes can exceed 59).

{corpus}

DETERMINISTIC RECURRING-PHRASE INDEX (from stats; use as starting leads):
{recurring}

TASK: cross-episode continuity report as STRICT JSON, EXACTLY these keys:
{{
 "callbacks": [{{"setup_ep": "SxxExx", "setup_t": "MM:SS", "payoff_ep": "SxxExx", "payoff_t": "MM:SS",
                "what": "what plants and what pays off, specific", "why_missable": "why viewers miss it"}}],
 "motifs": [{{"motif": "...", "occurrences": [{{"ep": "SxxExx", "t": "MM:SS"}}], "reading": "what it is doing"}}],  // needs 3+ occurrences
 "weak_motifs": [{{"motif": "...", "occurrences": [...]}}],  // 2 occurrences only
 "character_arcs": [{{"who": "Name", "arc": "dialogue-derivable trajectory", "waypoints": [{{"ep": "SxxExx", "t": "MM:SS", "beat": "..."}}]}}],
 "planted_questions": [{{"ep": "SxxExx", "t": "MM:SS", "question": "...", "answered": "SxxExx MM:SS or null"}}],
 "external_ref_candidates": [{{"ep": "SxxExx", "t": "MM:SS", "phrase": "...", "might_reference": "noted for human verification, not asserted"}}],
 "self_check": {{"every_anchor_exists": true, "both_ends_verified": true, "no_training_facts": true}}
}}

HARD RULES:
1. A callback needs BOTH ends anchored. One-ended "feels related" = banned.
2. Start from the recurring-phrase index, then add what statistics cannot see
   (prophecy-to-fulfillment, object handoffs, planted lies, repeated promises).
3. Motifs: 3+ anchored occurrences or they go in weak_motifs.
4. Arcs from what characters SAY and DO in dialogue only - no staging, no cinematography.
5. Mythology/cultural references go in external_ref_candidates as NOTES, never asserted facts.
6. 8-20 callbacks for a multi-season show; quality over count; each must survive a grep.
"""


def build_corpus(slug: str) -> tuple[str, int, str]:
    sdir = ROOT / slug / "_stats"
    eps = sorted(p for p in sdir.glob("*.json") if p.stem != "series")
    blocks = []
    for p in eps:
        st = json.loads(p.read_text())
        lines = [f"=== {st['episode']} ==="]
        for l in st["dialogue"]:
            lines.append(f"{mmss(l['t'])}|{l['speaker'] or ''}|{l['line']}")
        blocks.append("\n".join(lines))
    series_p = sdir / "series.json"
    recurring = "[]"
    if series_p.exists():
        rp = json.loads(series_p.read_text()).get("recurring_phrases", [])[:40]
        recurring = json.dumps(rp, ensure_ascii=False)
    return "\n\n".join(blocks), len(eps), recurring


_CP_STOP = set("the a an and or but to of in on at for with is are was were be been this that "
               "as from his her its their he she it they who when where what while into "
               "about after before then there here both each".split())


def _sig_tokens(text: str) -> set[str]:
    toks = re.findall(r"[a-z']+", (text or "").lower())
    return {t for t in toks if len(t) > 3 and t not in _CP_STOP}


def _same_callback(a: dict, b: dict) -> bool:
    """Two families describe the SAME callback if they agree on the structural
    claim (setup_ep -> payoff_ep) AND their descriptions share content. Timestamps
    are NOT a join key - different models cite the line vs the scene; both ends are
    independently G2-verified anyway, so structural + semantic agreement is the signal."""
    if (a.get("setup_ep"), a.get("payoff_ep")) != (b.get("setup_ep"), b.get("payoff_ep")):
        return False
    ta = _sig_tokens(a.get("what", "")) | _sig_tokens(a.get("why_missable", ""))
    tb = _sig_tokens(b.get("what", "")) | _sig_tokens(b.get("why_missable", ""))
    if not ta or not tb:
        return True  # same ep-pair, no describable content to disagree on
    overlap = ta & tb
    # high bar: >=2 shared content words, or one description >=40% covered by the other
    return len(overlap) >= 2 or (len(overlap) / min(len(ta), len(tb))) >= 0.40


def intersect(primary: dict, secondary: dict) -> dict:
    """Mark callbacks found by BOTH families high-confidence (ep-pair + semantic match)."""
    sec_cbs = list((secondary or {}).get("callbacks", []))
    matched_sec = set()
    for cb in primary.get("callbacks", []):
        hit = next((i for i, s in enumerate(sec_cbs)
                    if i not in matched_sec and _same_callback(cb, s)), None)
        if hit is not None:
            matched_sec.add(hit)
            cb["confidence"] = "high"
        else:
            cb["confidence"] = "candidate"
    # secondary-only callbacks (no primary twin) enter as candidates
    for i, s in enumerate(sec_cbs):
        if i not in matched_sec:
            s["confidence"] = "candidate"
            s["source"] = "secondary_family"
            primary.setdefault("callbacks", []).append(s)
    return primary


def rematch_existing(slug: str) -> int:
    """Zero-cost: re-run the (fixed) intersect on an already-generated _crosspass.json
    by splitting it back into the two families (primary-origin vs secondary_family).
    No LLM calls - repairs consensus on series done before the matching fix."""
    p = ROOT / slug / "_dossiers" / "_crosspass.json"
    if not p.exists():
        print(f"{slug}: no _crosspass.json")
        return 1
    d = json.loads(p.read_text())
    cbs = d.get("callbacks", [])
    prim = {"callbacks": [c for c in cbs if c.get("source") != "secondary_family"]}
    sec = {"callbacks": [c for c in cbs if c.get("source") == "secondary_family"]}
    for c in prim["callbacks"]:
        c.pop("confidence", None)
        c.pop("source", None)
    for c in sec["callbacks"]:
        c.pop("confidence", None)
    merged = intersect(prim, sec)
    d["callbacks"] = merged["callbacks"]
    hi = sum(1 for c in d["callbacks"] if c.get("confidence") == "high")
    d.setdefault("_meta", {})["rematched"] = True
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1))
    print(f"{slug}: rematched -> {len(d['callbacks'])} callbacks, {hi} high-confidence")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--single", action="store_true")
    ap.add_argument("--rematch", action="store_true", help="re-run intersect on existing file, no LLM")
    args = ap.parse_args()

    if args.rematch:
        return rematch_existing(args.slug)

    corpus, neps, recurring = build_corpus(args.slug)
    est_tokens = int(len(corpus.split()) * 1.4)
    print(f"{args.slug}: {neps} eps, ~{est_tokens//1000}K tokens corpus")
    if est_tokens > 550_000:
        print("WARN: corpus near context ceiling - consider per-season split")
    prompt = PROMPT_TMPL.format(slug=args.slug, neps=neps, corpus=corpus, recurring=recurring)
    req_keys = ("callbacks", "motifs", "character_arcs", "self_check")

    primary, meta1 = orfree.call(SYSTEM, prompt, lane="mega", max_tokens=12000,
                                 temperature=0.2, required_keys=req_keys,
                                 ctx=f"crosspass:{args.slug}:primary", total_timeout=900)
    print(f"primary: {meta1['lane_label']} {meta1.get('latency_s')}s, {len(primary.get('callbacks', []))} callbacks")

    if not args.single:
        try:
            secondary, meta2 = orfree.call(SYSTEM, prompt, lane="mega_alt", max_tokens=12000,
                                           temperature=0.2, required_keys=req_keys,
                                           ctx=f"crosspass:{args.slug}:secondary", total_timeout=900)
            print(f"secondary: {meta2['lane_label']} {meta2.get('latency_s')}s, {len(secondary.get('callbacks', []))} callbacks")
            primary = intersect(primary, secondary)
        except Exception as e:
            print(f"consensus partner failed ({str(e)[:120]}) - all callbacks stay candidates")
            for cb in primary.get("callbacks", []):
                cb.setdefault("confidence", "candidate")
    else:
        for cb in primary.get("callbacks", []):
            cb.setdefault("confidence", "candidate")

    out = ROOT / args.slug / "_dossiers"
    out.mkdir(exist_ok=True)
    primary["_meta"] = {"engine": "orfree-v1", "consensus": not args.single,
                        "primary_lane": meta1.get("lane_label"), "eps": neps}
    (out / "_crosspass.json").write_text(json.dumps(primary, ensure_ascii=False, indent=1))
    hi = sum(1 for c in primary.get("callbacks", []) if c.get("confidence") == "high")
    print(f"crosspass written: {len(primary.get('callbacks', []))} callbacks ({hi} high-confidence)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
