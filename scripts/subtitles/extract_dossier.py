#!/usr/bin/env python3
"""extract_dossier.py — Stage C on the free-model lane (per FREE_MODEL_RULES.md).

Input:  data/subtitles/<slug>/_stats/SxxExx.json   (Stage B output, has full dialogue)
Output: data/subtitles/<slug>/_dossiers/SxxExx.json (+ _meta block)

Resume-safe: skips episodes whose dossier exists unless --force.
--repair <ep> re-runs one episode feeding verify_grounding errors back (1 round max).

Usage:
  python3 extract_dossier.py <slug> [--limit N] [--eps S01E01,S01E02] [--force]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import orfree

ROOT = Path.home() / "bollyai" / "data" / "subtitles"

SYSTEM = (
    "You are a forensic dialogue analyst for an editorial engine. You extract ONLY what "
    "the provided dialogue doc supports. You never use training-memory facts about any "
    "show. Anchor or omit. Null beats guess. Output a single valid JSON object, nothing else."
)

PROMPT_TMPL = """EPISODE DIALOGUE DOC for {slug} {ep} (format MM:SS|speaker-or-blank|line; minutes can exceed 59; non-English originals are English subtitle renderings):

{dialogue}

STATS HINTS (deterministic, from the same subtitles):
- top silences (start-end seconds): {silences}
- name mentions this hour: {mentions}
- phrases recurring across the series that appear in this episode: {recurring}

TASK: produce the Episode Evidence Dossier as STRICT JSON with EXACTLY these keys:
{{
 "episode": "{ep}",
 "title": null,
 "beats": [{{"t": "MM:SS", "what": "specific one-line event grounded in dialogue at that timestamp"}}],   // 5-8 beats spanning the whole episode
 "character_beats": [{{"who": "Name-or-null", "beat": "what they want vs what they do this hour", "evidence_t": "MM:SS"}}],  // 2-4
 "key_lines": [{{"t": "MM:SS", "speaker": "Name-or-null", "line": "VERBATIM substring of the line at t, <=15 words", "why": "why load-bearing"}}],  // max 6
 "open_loops": ["the exact question the viewer is left holding"],  // 2-5
 "payoffs": [{{"plants_from": "earlier MM:SS this episode", "pays_here": "MM:SS", "what": "the connection"}}],  // 0-3, within-episode only
 "contradiction": {{"who": "...", "wants": "...", "does": "...", "line_t": "MM:SS"}},
 "tone_notes": "pacing observation grounded in the stats (silences, density)",
 "speaker_attribution_confidence": "high|medium|low",
 "quote_lang": "{quote_lang}",
 "self_check": {{"every_t_exists": true, "quotes_verbatim": true, "quote_words_total": 0, "no_training_facts": true}}
}}

HARD RULES (violations get mechanically stripped, so don't bother):
1. Every t / evidence_t / line_t is COPIED from the doc. No timestamp in doc = claim does not exist.
2. key_lines.line is a character-exact substring of the line at that t. Max 6 lines, <=15 words each, <=80 quoted words total.
3. Unknown speaker = null (subtitles are non-SDH; speakers are inferences - mark confidence honestly).
4. title stays null. No actor names, air dates, or any fact from training memory.
5. Specificity bar: a beat that could describe any episode of any show is banned.
6. contradiction is MANDATORY - the character whose want-vs-do gap drives the hour.
7. Fill self_check only after re-verifying: count the quoted words yourself.
{repair_block}"""


def mmss(t: float) -> str:
    return f"{int(t // 60):02d}:{int(t % 60):02d}"


def build_dialogue_doc(stats: dict) -> str:
    lines = []
    for l in stats["dialogue"]:
        sp = l["speaker"] or ""
        lines.append(f"{mmss(l['t'])}|{sp}|{l['line']}")
    return "\n".join(lines)


def episode_recurring(series_stats: dict, ep: str) -> list[str]:
    out = []
    for rp in series_stats.get("recurring_phrases", []):
        if any(e["ep"] == ep for e in rp["eps"]):
            out.append(rp["phrase"])
    return out[:12]


def extract_one(slug: str, ep: str, *, force: bool = False, repair_errors: list | None = None,
                quote_lang: str = "en") -> dict | None:
    sdir = ROOT / slug
    stats_p = sdir / "_stats" / f"{ep}.json"
    out_dir = sdir / "_dossiers"
    out_dir.mkdir(exist_ok=True)
    out_p = out_dir / f"{ep}.json"
    if out_p.exists() and not force and not repair_errors:
        return None
    stats = json.loads(stats_p.read_text())
    series_stats_p = sdir / "_stats" / "series.json"
    series_stats = json.loads(series_stats_p.read_text()) if series_stats_p.exists() else {}

    repair_block = ""
    if repair_errors:
        repair_block = ("\nREPAIR ROUND - your previous output failed mechanical verification. "
                        "Fix EXACTLY these and change nothing else:\n"
                        + "\n".join(f"- {e}" for e in repair_errors[:12]))

    prompt = PROMPT_TMPL.format(
        slug=slug, ep=ep,
        dialogue=build_dialogue_doc(stats),
        silences=json.dumps(stats.get("top_silences", [])[:4]),
        mentions=json.dumps(stats.get("name_mentions", {})),
        recurring=json.dumps(episode_recurring(series_stats, ep)),
        quote_lang=quote_lang,
        repair_block=repair_block,
    )
    obj, meta = orfree.call(
        SYSTEM, prompt, lane="json", max_tokens=6000, temperature=0.2,
        required_keys=("episode", "beats", "key_lines", "contradiction", "self_check"),
        ctx=f"dossier:{slug}:{ep}",
    )
    obj["_meta"] = {"engine": "orfree-v1", "model": meta.get("model"),
                    "lane_label": meta.get("lane_label"), "latency_s": meta.get("latency_s"),
                    "repair_round": bool(repair_errors)}
    out_p.write_text(json.dumps(obj, ensure_ascii=False, indent=1))
    return obj


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--eps", default="")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--quote-lang", default="en", help="en for English originals, en-sub for translated subs")
    args = ap.parse_args()

    sdir = ROOT / args.slug / "_stats"
    eps = sorted(p.stem for p in sdir.glob("*.json") if p.stem != "series")  # SxxExx or film stem
    if args.eps:
        want = set(args.eps.split(","))
        eps = [e for e in eps if e in want]
    if args.limit:
        eps = eps[: args.limit]
    done = skipped = failed = 0
    for ep in eps:
        try:
            r = extract_one(args.slug, ep, force=args.force, quote_lang=args.quote_lang)
            if r is None:
                skipped += 1
                print(f"SKIP {ep} (exists)")
            else:
                done += 1
                print(f"OK   {ep}  lane={r['_meta']['lane_label']}  {r['_meta']['latency_s']}s")
        except orfree.QuotaExhausted:
            print("QUOTA_HALT - daily budget reached, resume tomorrow")
            (ROOT / "_engine" / "QUOTA_HALT").touch()
            return 3
        except Exception as e:
            failed += 1
            print(f"FAIL {ep}: {str(e)[:200]}")
    print(f"\n{args.slug}: {done} extracted, {skipped} skipped, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
