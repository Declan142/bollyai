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

WRITER_TMPL = """VERIFIED DOSSIER for {slug} {ep} (every quote and beat here already passed a grounding gate - you may rely on it; you may NOT add facts beyond it):

{dossier}

SERIES CONTEXT (one line, factual): {context}

TASK: draft this episode's review as STRICT JSON:
{{
 "number": {num},
 "title": "Episode {num}",
 "bollymeter": null,
 "critic_note": null,
 "spoiler_free": "110-160 words. BollyAI reads what the record shows. Structure: cold-open hook from a specific story moment (never a generic setup sentence) / what this hour does / what elevates it - grounded in a contradiction, character decision, or earned payoff from the dossier / what drags - mandatory, a review with zero criticism fails; criticism must be about story, structure, or character (unearned payoff, repetition, contradiction ignored or dropped) / a one-line verdict that says something falsifiable.",
 "the_moment": "One clean sentence, <=25 words. The beat people will remember, named spoiler-carefully. No parentheticals.",
 "_evidence": ["2-4 dossier anchors you used, by type: 'contradiction: Sunny wants X but does Y', 'payoff: planted desire pays off in confrontation', 'character_beat: Firoz terror shows at climax'"],
 "_self_check": {{"viewing_claims": 0, "words_spoiler_free": <int>, "every_claim_in_dossier": true, "banned_phrases": 0}}
}}

HARD RULES (a strict judge on a different model auto-fails any violation - no bluffing):
1. Zero first-person viewing claims, any language.
2. spoiler_free 110-160 words; must contain at least one concrete criticism with dossier evidence.
3. Dialogue quotes land naked in quotation marks, <=25 words total. BANNED: any attribution to process or source ('as the subtitles render it', 'as the dialogue has it', 'as the English subtitles render', 'the subtitles show').
4. NO timestamps, beat refs (e.g. 'beat 05:20', 'at 38:02'), or second/minute counts anywhere in spoiler_free or the_moment. Evidence citations belong ONLY in _evidence.
5. NO silence or gap durations as criticism. If the dossier's tone_notes mention silence seconds, gap lengths, or quiet periods - IGNORE THEM ENTIRELY, they are subtitle file artifacts (songs, action, non-verbal scenes). Criticism MUST come from story events, character decisions, or structural repetition that you can name. Never write "long silences", "lingering quiet", "stretches of silence/pause", "long pause", or any variant.
6. No banned register: {banned}. No em-dash. No sentence over 35 words.
7. No inline 'Verdict:' label. No stock opener ('The hour thrusts', 'The episode thrusts', 'The hour opens', 'This hour cranks', 'The hour begins'). Cold-open on a character action or story turn.
8. bollymeter and critic_note stay exactly null.
9. the_moment: one clean sentence, no parentheticals, no timestamps, names the beat without resolving it."""

JUDGE_SYS = "You are a strict editorial judge. You score against a rubric and return only JSON."

JUDGE_TMPL = """Score this BollyAI episode review against the dossier it was drawn from. Be hard.

DOSSIER (ground truth):
{dossier}

REVIEW DRAFT:
{draft}

AUTOMATIC FAIL (set overall=0, verdict=fail) if ANY of these are present in spoiler_free or the_moment:
- Any timestamp or beat-ref (e.g. "beat 05:20", "at 38:02", "2882 s", "12:01")
- Any meta-reference to subtitles or production process ("as the English subtitles render it", "as the dialogue has it", "the subtitles show")
- Any silence, gap, or pause used as pacing criticism. Variants that ALWAYS fail: numbered duration + silence/pause/gap/stretch ("143-second silent stretch", "29-minute pause", "48-second gap"); weighted adjective + silence/pause noun ("long silences", "relentless silence", "extended pause", "dead silence"); "silent stretch"; silence/pause noun followed by a pacing-consequence verb ("silences stall momentum", "long silences, which, though atmospheric, stall momentum", "pause drags", "silence hampers pacing"). Only criticism anchored in story events, character decisions, or structural repetition is allowed.
- Any first-person viewing claim ("I watched", "we saw")

If no auto-fail, score rubric (each 0-2):
- grounding: spot 3 specific claims vs dossier beats/contradictions/payoffs. All traceable=2, 1 uncited=1, fabricated claim=0.
- specificity: would this review be FALSE for a different episode? Generic=0, episode-specific=2.
- honesty: any invented number or uncited quote = 0. Clean = 2.
- register: no banned phrases, no sentence over 35 words, no stock opener, no 'Verdict:' label. Violations = 0.
- verdict_courage: the criticism names a real story/character problem with dossier evidence=2. Vague or absent=0.

Return STRICT JSON: {{"scores": {{"grounding": n, "specificity": n, "honesty": n, "register": n, "verdict_courage": n}}, "overall": <sum 0-10>, "verdict": "pass|revise|fail", "worst_sentence": "...", "fix": "one line"}}. pass requires overall>=7 AND honesty=2 AND no auto-fail."""


def mmss_ep(stem: str) -> int:
    """Episode identifier. S01=flat (S01E03->3). S02+=compound (S02E03->203). Keeps backward compat."""
    m = re.search(r"S(\d+)E(\d+)", stem, re.I)
    if m:
        season, episode = int(m.group(1)), int(m.group(2))
        return episode if season == 1 else season * 100 + episode
    m = re.search(r"E(\d+)", stem)
    return int(m.group(1)) if m else 1


def dossier_digest(d: dict) -> str:
    """Compact, the writer doesn't need the _stripped/meta noise."""
    keep = {k: d[k] for k in ("beats", "character_beats", "key_lines", "open_loops",
                              "payoffs", "contradiction", "tone_notes", "quote_lang") if k in d}
    return json.dumps(keep, ensure_ascii=False)


def series_context(slug: str) -> str:
    p = SERIES_DIR / f"{slug}.json"
    if not p.exists():
        return "(no catalogue entry yet)"
    d = json.loads(p.read_text())
    def sv(x): return x.get("value") if isinstance(x, dict) else x
    title = sv(d.get("title")) or slug
    lang = sv(d.get("original_language")) or ""
    plat = sv(d.get("platform")) or ""
    return f"{title}, {lang} on {plat}, status {d.get('status','?')}".strip(", ")


def sanitize_prose(text: str) -> str:
    """Strip em/en-dashes and Verdict: label. Called before G3 judging so the judge sees clean text."""
    if not text:
        return text
    # Replace em-dash (U+2014) and en-dash (U+2013) with spaced hyphen
    text = text.replace("—", " - ").replace("–", " - ")
    # Strip trailing "Verdict:" / "verdict:" label — case-insensitive, any capitalisation
    text = re.sub(r"\s*[Vv]erdict:\s+[^\n]+$", "", text.rstrip()).rstrip()
    return text


# Regex patterns that flag silence/gap/pause criticism.
# Rule: subtitle silence is songs, action, reaction - not pacing evidence.
# Any of these patterns in spoiler_free or the_moment = local FAIL (forces regen, no G3 call).
_GAP_PATTERNS: list[re.Pattern] = [
    # numbered duration + silence/pause/gap/stretch noun (either order)
    re.compile(r'\b\d+[\s\-](?:second|minute|sec|min)s?\b.{0,40}\b(?:silence|pause|gap|stretch|lull)\b', re.I),
    re.compile(r'\b(?:silence|pause|gap|stretch|lull)s?\b.{0,40}\b\d+[\s\-](?:second|minute|sec|min)', re.I),
    # weighted-adjective + silence/pause/quiet noun — includes "lingering quiet" variant
    re.compile(r'\b(?:long|relentless|extended|prolonged|dead|protracted|lengthy|overlong|lingering)\s+(?:silence|silences|pause|pauses|gap|gaps|quiet)\b', re.I),
    # "silent stretch" and "stretches of silence/pause/quiet" — both orderings
    re.compile(r'\bsilent\s+stretch\b', re.I),
    re.compile(r'\bstretches?\s+of\s+(?:silence|pause|pauses|quiet)\b', re.I),
    # silence/pause/quiet noun followed by a pacing-consequence verb within 80 chars
    # "quiet" included to catch "lingering quiet...stagnant/stretches" variants
    re.compile(r'\b(?:silence|silences|pause|pauses|quiet)\b.{0,80}\b(?:stalls?|drags?|hampers?|bogs?\s+down|slows?\s+(?:the\s+)?(?:pace|pacing|momentum)|kills?\s+(?:the\s+)?(?:pace|pacing|momentum)|undermines?|wastes?|pacing\s+suffers|stagnant|stretches\s+without)\b', re.I),
]


def gap_criticism_hit(text: str) -> bool:
    """Return True if text uses silence/gap/pause as pacing criticism."""
    if not text:
        return False
    return any(p.search(text) for p in _GAP_PATTERNS)


# MM:SS timestamp pattern — any digit-colon-digit-digit sequence in prose is a subtitle
# artifact leak (e.g. "at 23:54", "planted at 00:26"). Evidence citations belong only
# in _evidence, never in spoiler_free or the_moment.
_TIMESTAMP_RE = re.compile(r'\b\d{1,2}:\d{2}\b')


def timestamp_hit(text: str) -> bool:
    """Return True if text contains an inline MM:SS timestamp."""
    if not text:
        return False
    return bool(_TIMESTAMP_RE.search(text))


def banned_hit(text: str) -> list[str]:
    low = (text or "").lower()
    return [b for b in BANNED if b in low] + (["em-dash"] if re.search(r"[—–]", text or "") else [])


def draft_one(slug: str, ep_stem: str, dossier: dict, ctx: str) -> dict | None:
    num = mmss_ep(ep_stem)
    prompt = WRITER_TMPL.format(
        slug=slug, ep=ep_stem, dossier=dossier_digest(dossier), context=ctx, num=num,
        banned=", ".join(BANNED[:8]))
    obj, meta = orfree.call(WRITER_SYS, prompt, lane="json", max_tokens=2500,
                            temperature=0.55, required_keys=("spoiler_free", "the_moment", "number"),
                            ctx=f"review:{slug}:{ep_stem}")
    # sanitize before local checks and G3 judging
    obj["spoiler_free"] = sanitize_prose(obj.get("spoiler_free", ""))
    obj["the_moment"] = sanitize_prose(obj.get("the_moment", ""))
    # local pre-judge mechanical checks
    sf = obj.get("spoiler_free", "")
    wc = len(sf.split())
    issues = []
    if banned_hit(sf) or banned_hit(obj.get("the_moment", "")):
        issues.append(f"banned: {banned_hit(sf) + banned_hit(obj.get('the_moment',''))}")
    if gap_criticism_hit(sf) or gap_criticism_hit(obj.get("the_moment", "")):
        issues.append("gap-criticism: silence/pause/gap used as pacing criticism")
    if timestamp_hit(sf) or timestamp_hit(obj.get("the_moment", "")):
        issues.append("timestamp: inline MM:SS timestamp in prose")
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


def _save(reviews: list, out_p: "Path") -> None:
    reviews.sort(key=lambda r: r.get("number", 0))
    out_p.write_text(json.dumps(reviews, ensure_ascii=False, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()
    slug = args.slug
    ddir = ROOT / slug / "_dossiers"
    if not ddir.exists():
        print(f"no dossiers for {slug}", flush=True)
        return 1
    out_dir = ROOT / slug / "_reviews"
    out_dir.mkdir(exist_ok=True)
    out_p = out_dir / "episodes.json"

    # Load existing - keep only episodes that already passed G3, retry everything else.
    existing: dict[int, dict] = {}
    if out_p.exists() and not args.force:
        try:
            for e in json.loads(out_p.read_text()):
                if isinstance(e, dict) and e.get("_judge", {}).get("verdict") == "pass":
                    existing[e["number"]] = e
        except Exception:
            pass

    ctx = series_context(slug)
    # Seed in-memory list with already-passed reviews so incremental saves preserve them.
    reviews: list[dict] = list(existing.values())
    failures: list[str] = []
    dossiers = sorted(p for p in ddir.glob("*.json") if not p.stem.startswith("_"))
    for p in dossiers:
        d = json.loads(p.read_text())
        num = mmss_ep(p.stem)
        if num in existing:
            print(f" keep {p.stem} (already passed)", flush=True)
            continue
        try:
            draft = draft_one(slug, p.stem, d, ctx)
            judge = judge_one(slug, p.stem, d, draft)
            if judge.get("verdict") != "pass" and judge.get("overall", 0) < 7:
                # one regen on the next writer lane via temperature nudge
                draft = draft_one(slug, p.stem, d, ctx)
                judge = judge_one(slug, p.stem, d, draft)
            draft["_judge"] = {k: judge.get(k) for k in ("overall", "verdict", "worst_sentence", "fix", "_judge_lane")}
            reviews.append(draft)
            v = judge.get("verdict"); o = judge.get("overall")
            print(f"{'PASS' if v=='pass' else v.upper():>6} {p.stem}  G3={o}  lane={draft['_writer']['lane']}", flush=True)
        except orfree.QuotaExhausted:
            print("QUOTA_HALT", flush=True)
            (ROOT / "_engine" / "QUOTA_HALT").touch()
            _save(reviews, out_p)
            break
        except Exception as e:
            failures.append(p.stem)
            print(f" SKIP {p.stem}: {str(e)[:120]}", flush=True)
        finally:
            # Incremental write: every episode survives even if the next one crashes.
            _save(reviews, out_p)
    _save(reviews, out_p)
    npass = sum(1 for r in reviews if r.get("_judge", {}).get("verdict") == "pass")
    suffix = f"  failures={failures}" if failures else ""
    print(f"\n{slug}: {len(reviews)} written, {npass} passed G3{suffix} -> {out_p}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
