#!/usr/bin/env python3
"""draft_reviews.py — Stage D. Free models DRAFT publishable reviews from VERIFIED
dossiers (FREE_MODEL_RULES.md Part 3), G3-judged on a different model family.

Writer drafts only what the dossier grounds: spoiler_free prose + the_moment.
bollymeter + critic_note stay null (per-hour numeric needs real reception; critic
quotes need a real source+url - both are the voice-pass/verify-or-strip layer, NOT
a free-model job). number from SxxExx; title "Episode N" until a real source enriches.

Output (STAGING, never the live series JSON): data/subtitles/<slug>/_reviews/
  episodes.json   - [EpisodeReview-shaped + _judge block]
  season_body.txt - season-level body draft
These wait for Aditya/Vyom voice-pass (G4) before merge_reviews.py touches data/series.

Usage: python3 draft_reviews.py <slug> [--force]
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import orfree

ROOT = Path.home() / "bollyai" / "data" / "subtitles"
SERIES_DIR = Path.home() / "bollyai" / "data" / "series"

WRITER_SYS = (
    "You are BollyAI, a disclosed-AI critic for an Indian audience. BollyAI has NOT watched "
    "anything; BollyAI reads what the dialogue and the record show, and weighs it. Third "
    "person ALWAYS - never 'I watched/saw' in any language. English spine, light Hinglish "
    "flavour allowed. No em-dashes, no emojis. Every factual sentence traces to the dossier "
    "you are given; opinion is allowed only as a verdict ON that evidence, never as new fact. "
    "Output one valid JSON object."
)

BANNED = ["delve", "tapestry", "rollercoaster", "must-watch", "edge of your seat",
          "masterclass", "elevates the narrative", "a testament to", "binge-worthy",
          "buckle up", "look no further", "in conclusion"]

WRITER_TMPL = """VERIFIED DOSSIER for {slug} {ep} (every timestamp + quote here already passed a grounding gate - you may rely on it; you may NOT add facts beyond it):

{dossier}

SERIES CONTEXT (one line, factual): {context}

TASK: draft this episode's review as STRICT JSON:
{{
 "number": {num},
 "title": "Episode {num}",
 "bollymeter": null,
 "critic_note": null,
 "spoiler_free": "110-160 words. BollyAI's read of what THIS hour does and how well, grounded ONLY in the dossier. Structure: a concrete 1-sentence hook (no rhetorical-question opener) / what the hour does / what elevates it WITH evidence (cite a beat or the contradiction) / what drags WITH evidence (mandatory - a review with zero criticism fails) / a one-line verdict that actually says something falsifiable. Tease the central question, never resolve it.",
 "the_moment": "<=25 words: the beat people will remember, named spoiler-carefully (do NOT reveal its outcome).",
 "_evidence": ["2-4 dossier anchors you leaned on, e.g. 'contradiction: Meera wants X does Y', 'beat 19:08'"],
 "_self_check": {{"viewing_claims": 0, "words_spoiler_free": <int>, "every_claim_in_dossier": true, "banned_phrases": 0}}
}}

HARD RULES (a judge on a different model checks these - don't bluff):
1. Zero first-person viewing claims, any language.
2. spoiler_free 110-160 words; must contain at least one concrete criticism with evidence.
3. Quote at most 25 words total from the dossier's key_lines, attributed naturally ("as the {qlbl} put it"); subtitle text is fuel, never a transcript dump.
4. No banned register: {banned}. No em-dash, no emoji, no sentence over 35 words.
5. bollymeter and critic_note stay exactly null (a later layer fills them from real reception).
6. the_moment names the beat, never its resolution."""

JUDGE_SYS = "You are a strict editorial judge. You score against a rubric and return only JSON."

JUDGE_TMPL = """Score this BollyAI episode review against the dossier it was drawn from. Be hard.

DOSSIER (ground truth):
{dossier}

REVIEW DRAFT:
{draft}

Rubric, each 0-2: grounding (spot 3 claims vs dossier), specificity (would this be false for a different episode? generic=0), honesty (any viewing claim / invented number / uncited quote = overall 0), register (banned-phrase + sentence-length + hook quality), verdict_courage (says something falsifiable with evidence=2, hedge-mush=0).

Return STRICT JSON: {{"scores": {{"grounding": n, "specificity": n, "honesty": n, "register": n, "verdict_courage": n}}, "overall": <sum, 0-10>, "verdict": "pass|revise|fail", "worst_sentence": "...", "fix": "one line"}}. pass requires overall>=7 AND honesty=2."""


def mmss_ep(stem: str) -> int:
    m = re.search(r"E(\d+)", stem)
    return int(m.group(1)) if m else 1


def dossier_digest(d: dict) -> str:
    """Compact, the writer doesn't need the _stripped/meta noise."""
    keep = {k: d[k] for k in ("beats", "character_beats", "key_lines", "open_loops",
                              "payoffs", "contradiction", "tone_notes", "quote_lang") if k in d}
    return json.dumps(keep, ensure_ascii=False)


def series_context(slug: str) -> tuple[str, str]:
    p = SERIES_DIR / f"{slug}.json"
    if not p.exists():
        return ("(no catalogue entry yet)", "English subtitles")
    d = json.loads(p.read_text())
    def sv(x): return x.get("value") if isinstance(x, dict) else x
    title = sv(d.get("title")) or slug
    lang = sv(d.get("original_language")) or ""
    plat = sv(d.get("platform")) or ""
    ctx = f"{title}, {lang} on {plat}, status {d.get('status','?')}".strip(", ")
    qlbl = "English subtitles render it" if (lang and lang.lower() not in ("english", "en")) else "dialogue has it"
    return ctx, qlbl


def banned_hit(text: str) -> list[str]:
    low = (text or "").lower()
    return [b for b in BANNED if b in low] + (["em-dash"] if re.search(r"[—–]", text or "") else [])


def draft_one(slug: str, ep_stem: str, dossier: dict, ctx: str, qlbl: str) -> dict | None:
    num = mmss_ep(ep_stem)
    prompt = WRITER_TMPL.format(
        slug=slug, ep=ep_stem, dossier=dossier_digest(dossier), context=ctx, num=num,
        qlbl=qlbl, banned=", ".join(BANNED[:8]))
    obj, meta = orfree.call(WRITER_SYS, prompt, lane="json", max_tokens=2500,
                            temperature=0.55, required_keys=("spoiler_free", "the_moment", "number"),
                            ctx=f"review:{slug}:{ep_stem}")
    # local pre-judge mechanical checks
    sf = obj.get("spoiler_free", "")
    wc = len(sf.split())
    issues = []
    if banned_hit(sf) or banned_hit(obj.get("the_moment", "")):
        issues.append(f"banned: {banned_hit(sf) + banned_hit(obj.get('the_moment',''))}")
    if not (95 <= wc <= 175):
        issues.append(f"length {wc}")
    if re.search(r"\b(I|we) (watch|saw|watched|see)\b", sf, re.I):
        issues.append("viewing-claim")
    obj["bollymeter"] = None
    obj["critic_note"] = None
    obj["title"] = f"Episode {num}"
    obj["_writer"] = {"lane": meta.get("lane_label"), "words": wc, "local_issues": issues}
    return obj


def judge_one(slug: str, ep_stem: str, dossier: dict, draft: dict) -> dict:
    prompt = JUDGE_TMPL.format(dossier=dossier_digest(dossier),
                              draft=json.dumps({k: draft[k] for k in
                                                ("spoiler_free", "the_moment") if k in draft}, ensure_ascii=False))
    try:
        obj, meta = orfree.call(JUDGE_SYS, prompt, lane="mega_alt", max_tokens=1200,
                                temperature=0.1, required_keys=("overall", "verdict"),
                                ctx=f"judge:{slug}:{ep_stem}")
        obj["_judge_lane"] = meta.get("lane_label")
        return obj
    except Exception as e:
        return {"overall": 0, "verdict": "fail", "fix": f"judge error: {str(e)[:100]}"}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    slug = args.slug
    ddir = ROOT / slug / "_dossiers"
    if not ddir.exists():
        print(f"no dossiers for {slug}")
        return 1
    out_dir = ROOT / slug / "_reviews"
    out_dir.mkdir(exist_ok=True)
    out_p = out_dir / "episodes.json"
    existing = {e["number"]: e for e in json.loads(out_p.read_text())} if out_p.exists() and not args.force else {}

    ctx, qlbl = series_context(slug)
    reviews = []
    dossiers = sorted(p for p in ddir.glob("*.json") if not p.stem.startswith("_"))
    for p in dossiers:
        d = json.loads(p.read_text())
        num = mmss_ep(p.stem)
        if num in existing and existing[num].get("_judge", {}).get("verdict") == "pass":
            reviews.append(existing[num])
            print(f"keep  {p.stem} (already passed)")
            continue
        try:
            draft = draft_one(slug, p.stem, d, ctx, qlbl)
            judge = judge_one(slug, p.stem, d, draft)
            if judge.get("verdict") != "pass" and judge.get("overall", 0) < 7:
                # one regen on the next writer lane via temperature nudge
                draft = draft_one(slug, p.stem, d, ctx, qlbl)
                judge = judge_one(slug, p.stem, d, draft)
            draft["_judge"] = {k: judge.get(k) for k in ("overall", "verdict", "worst_sentence", "fix", "_judge_lane")}
            reviews.append(draft)
            v = judge.get("verdict"); o = judge.get("overall")
            print(f"{'PASS' if v=='pass' else v.upper():>6} {p.stem}  G3={o}  lane={draft['_writer']['lane']}")
        except orfree.QuotaExhausted:
            print("QUOTA_HALT")
            (ROOT / "_engine" / "QUOTA_HALT").touch()
            break
        except Exception as e:
            print(f"FAIL  {p.stem}: {str(e)[:150]}")
    reviews.sort(key=lambda r: r.get("number", 0))
    out_p.write_text(json.dumps(reviews, ensure_ascii=False, indent=1))
    npass = sum(1 for r in reviews if r.get("_judge", {}).get("verdict") == "pass")
    print(f"\n{slug}: {len(reviews)} drafted, {npass} passed G3 -> {out_p}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
