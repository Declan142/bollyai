#!/usr/bin/env python3
"""strip_attribution.py - TRACK B cleanup (CLEANUP-PLAN.md).

For each prose field that FAILS the attribution gate, NANO-rewrite (gpt-5.4-nano) to REMOVE
every critic / reviewer / audience attribution while KEEPING BollyAI's own disclosed analysis
of the real beats. Grammatical, no dangling fragments, NO invented reception, no em-dash. Then
re-gate; iterate once; NULL the field only as a last resort (optional fields only - required
fields are never nulled or left failing).

This is for the ~73 "naked" series (zero url-backed pull_quotes) where the fix is pure
phrasing: "Critics noted that X" -> "X" stated in BollyAI's own editorial voice.

Usage:
  python3 scripts/cleanup/strip_attribution.py <slug> [<slug> ...] [--dry-run] [--quiet]

Honesty: only REMOVES attribution; never adds reception, quotes, or numbers. The rewrite is
gate-verified before it is kept; a field that still fails after two tries is reported, not
silently written. NEVER leaves a file that fails validate_series.
NO commit/deploy - the floor reconciles.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, REPO)

# Reuse the model router + text-normalizers from build_review (5-endpoint routing, NANO lane,
# em-dash / timestamp strippers) instead of duplicating them.
_spec = importlib.util.spec_from_file_location(
    "build_review", os.path.join(REPO, "scripts", "subtitles", "build_review.py"))
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

from engine.gates.attribution_regex import scan_text as scan_attr  # noqa: E402
from engine.gates.viewing_claim_regex import scan_text as scan_view  # noqa: E402

# Required prose fields can never be nulled (the validator requires them non-empty); they must
# be rewritten to passing prose. Optional fields may be nulled as a last resort.
REQUIRED = {"review_body", "spoiler_free"}
OPTIONAL = {"season_over_season", "the_moment"}

STRIP_INSTR = (
    "You are a precise editor cleaning a single BollyAI TV-review prose field. The text wrongly "
    "attributes opinions to critics, reviewers, or audiences. BollyAI has NOT surveyed any "
    "critics or audiences, so those attributions are fabrication and must go.\n\n"
    "REWRITE the text so it makes the SAME observations in BollyAI's OWN editorial voice, but "
    "with EVERY external attribution removed. Rules:\n"
    "- Delete every subject like 'Critics', 'Reviewers', 'Commentators', 'Audiences', 'Viewers', "
    "'Fans', 'the press'. Turn 'Critics noted that the finale lands' into 'The finale lands'. "
    "Turn 'Audiences remember the elevator scene' into 'The elevator scene lingers'.\n"
    "- Delete reception phrasing with no source: 'widely praised', 'widely discussed', 'often "
    "cited', 'critically acclaimed', 'fan-favorite', 'drew acclaim', 'sparked debate', "
    "'received praise'. State the underlying craft point directly as BollyAI's own read.\n"
    "- Do NOT invent any reception, consensus, quotes, ratings, or numbers. Do NOT add 'BollyAI "
    "thinks' framing - just state the observation.\n"
    "- Keep it grammatical and roughly the same length. No dangling fragments, no orphaned "
    "clauses, no leftover 'that' or 'for' from a deleted subject.\n"
    "- No em-dashes or en-dashes. No first-person ('I watched'). Third person about the show.\n"
    "Output ONLY the rewritten prose. No preamble, no notes, no quotes around it, no code fences."
)


def _rewrite(text: str) -> tuple[str, int]:
    out, rc = br.gpt_ask(STRIP_INSTR, text, timeout=180, model="NANO")
    if rc != 0:
        return "", rc
    out = br.strip_fences(out)
    out = br.strip_em_dashes(out)
    out = br.strip_timestamps(out)
    return out.strip(), 0


def _passes(text: str) -> bool:
    """A rewritten field is acceptable only if it is free of BOTH attribution and viewing claims."""
    return not scan_attr(text) and not scan_view(text)


def clean_field(text, field: str):
    """Return (new_value, status). status in {clean, rewritten, nulled, UNRESOLVED}.
    new_value is the text to store (or None to null). UNRESOLVED keeps the best attempt but
    signals the file is not yet gate-clean."""
    if not text or not scan_attr(text):
        return text, "clean"
    orig_wc = len(text.split())
    best = None
    for attempt in range(2):
        out, rc = _rewrite(text)
        if rc != 0 or not out:
            continue
        # accept only if gate-clean AND it did not gut the field to a stub
        if _passes(out) and len(out.split()) >= max(15, int(orig_wc * 0.45)):
            return out, f"rewritten(try{attempt + 1})"
        if _passes(out):
            best = out  # clean but short - hold as fallback
    if best is not None:
        return best, "rewritten(short)"
    if field in OPTIONAL:
        return None, "nulled(last-resort)"
    return text, "UNRESOLVED"  # required field, could not clean - do NOT write a passing claim


def process(slug: str, dry: bool, quiet: bool) -> dict:
    path = os.path.join(REPO, "data", "series", f"{slug}.json")
    if not os.path.exists(path):
        return {"slug": slug, "error": "file not found"}
    d = json.load(open(path, encoding="utf-8"))
    changes = []
    unresolved = []
    for s in d.get("seasons", []) or []:
        sn = s.get("number", "?")
        for fk in ("review_body", "season_over_season"):
            if fk not in s:
                continue
            new, st = clean_field(s.get(fk), fk)
            if st == "clean":
                continue
            changes.append((f"S{sn}.{fk}", st))
            if st == "UNRESOLVED":
                unresolved.append(f"S{sn}.{fk}")
            else:
                s[fk] = new
        for ep in (s.get("episode_reviews") or []):
            en = ep.get("number", "?")
            for fk in ("spoiler_free", "the_moment"):
                if fk not in ep:
                    continue
                new, st = clean_field(ep.get(fk), fk)
                if st == "clean":
                    continue
                changes.append((f"S{sn}E{en}.{fk}", st))
                if st == "UNRESOLVED":
                    unresolved.append(f"S{sn}E{en}.{fk}")
                else:
                    ep[fk] = new
    rewritten = [c for c in changes if c[1].startswith("rewritten")]
    nulled = [c for c in changes if c[1].startswith("nulled")]
    if changes and not dry and not unresolved:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(d, f, ensure_ascii=False, indent=2)
            f.write("\n")
    if not quiet:
        for where, st in changes:
            print(f"    {where}: {st}")
    return {"slug": slug, "fields_touched": len(changes), "rewritten": len(rewritten),
            "nulled": len(nulled), "unresolved": unresolved, "wrote": bool(changes and not dry and not unresolved)}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slugs", nargs="+")
    ap.add_argument("--dry-run", action="store_true", help="scan + rewrite but do not write the file")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    bad = 0
    for slug in args.slugs:
        print(f"== {slug} ==")
        r = process(slug, args.dry_run, args.quiet)
        if r.get("error"):
            print(f"  ERROR: {r['error']}"); bad += 1; continue
        tag = "DRY-RUN" if args.dry_run else ("WROTE" if r["wrote"] else "no-write")
        print(f"  {tag}: {r['fields_touched']} fields ({r['rewritten']} rewritten, "
              f"{r['nulled']} nulled){' UNRESOLVED:' + ','.join(r['unresolved']) if r['unresolved'] else ''}")
        if r["unresolved"]:
            bad += 1
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
