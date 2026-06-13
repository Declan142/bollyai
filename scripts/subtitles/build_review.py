#!/usr/bin/env python3
"""build_review — rich episode review via gpt-5.5.

Reads the dossier + REVIEW-HOUSE-STYLE.md, calls gpt-5.5 for a draft,
then a tighten/edit pass, then extracts verdict JSON.
Merges the result back into data/series/<slug>.json.

Usage:
  python3 scripts/subtitles/build_review.py house-of-the-dragon 1 1

Hard fences:
- No em-dash (U+2014) or en-dash (U+2013) anywhere.
- No first-person viewing claims.
- No fabricated OTT numbers.
- Mutates JSON via json.dump only.
"""
import sys
import os
import json
import re
import subprocess

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HOUSE_STYLE = os.path.join(os.path.dirname(__file__), 'REVIEW-HOUSE-STYLE.md')


def gpt_ask(instruction: str, stdin_text: str, timeout: int = 600) -> tuple[str, int]:
    p = subprocess.run(
        ['gpt', 'ask', instruction],
        input=stdin_text,
        capture_output=True,
        text=True,
        timeout=timeout,
    )
    return p.stdout.strip(), p.returncode


def strip_fences(text: str) -> str:
    text = re.sub(r'^```(?:markdown)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def em_dash_count(text: str) -> int:
    return text.count('—') + text.count('–') + text.count('--')


def strip_em_dashes(text: str) -> str:
    text = text.replace('—', ' - ')
    text = text.replace('–', ' - ')
    return text


def build_draft_prompt(house_style: str, dossier: dict, slug: str) -> str:
    ep_tag = dossier.get('episode', 'S01E01')
    ep_title = dossier.get('title') or ep_tag
    series_name = slug.replace('-', ' ').title()

    beats_lines = []
    for b in dossier.get('beats', []):
        beats_lines.append(f"  [{b['t']}] {b['what']}")

    char_lines = []
    for c in dossier.get('character_beats', []):
        char_lines.append(f"  {c['who']}: {c['beat']} (evidence t={c['evidence_t']})")

    key_lines = []
    for k in dossier.get('key_lines', []):
        sp = k.get('speaker') or 'Unknown'
        key_lines.append(f"  [{k['t']}] {sp}: \"{k['line']}\" — {k['why']}")

    open_loops = []
    for q in dossier.get('open_loops', []):
        open_loops.append(f"  - {q}")

    contradiction = dossier.get('contradiction', {})
    contra_text = (
        f"  {contradiction.get('who','')}: wants {contradiction.get('wants','')} "
        f"but does {contradiction.get('does','')} (t={contradiction.get('line_t','')})"
        if contradiction else "  (none)"
    )

    tone = dossier.get('tone_notes', '')

    dossier_text = f"""SERIES: {series_name}
EPISODE: {ep_tag} - "{ep_title}"

EPISODE BEATS (chronological):
{chr(10).join(beats_lines)}

CHARACTER BEATS (internal contradiction maps):
{chr(10).join(char_lines)}

KEY LINES (verbatim from subtitles, <=25 words each; use at most 1-2 in the review, attributed to character):
{chr(10).join(key_lines)}

OPEN LOOPS (questions the episode plants for later):
{chr(10).join(open_loops)}

CENTRAL CONTRADICTION:
{contra_text}

TONE NOTES: {tone}"""

    return (
        house_style
        + "\n\n---\n\n# YOUR TASK\n"
        f"Write the episode review for **{series_name} {ep_tag}** following the HOUSE STYLE contract above EXACTLY.\n"
        "The dossier arrives via stdin. Write ONLY from the dossier. Every claim must trace to a dossier entry.\n"
        "At the END of the review (after the disclosure line), emit on its own line:\n"
        "VERDICT_JSON: {\"score\": <float 0-10 one decimal>, \"one_liner\": \"<15-25 words, the review in one sharp sentence, no em-dash>\"}\n\n"
        "Output ONLY: H1 title, italic spoiler-care line, cold-open paragraphs, 3-5 ## act-block sections, ## The Verdict section, "
        "the disclosure footer, then the VERDICT_JSON line. No code fences, no preamble, no notes."
    ), dossier_text


EDIT_INSTR = """You are a ruthless editor enforcing house style on a TV episode review. Tighten the draft you receive via stdin.

HARD TARGETS:
- 1,200-1,700 words total. Be ruthless but keep all analysis.
- KILL on sight: aphoristic closers; "X is both A and B" couplets; "not X; it's Y" hinges; over-editorializing instead of stating; padding; generic intensifiers (truly/deeply/masterfully/stunning); em-dashes (replace with period or comma or restructure); en-dashes; first-person viewing claims (I watched/I saw/I read).
- KEEP: factual accuracy (never alter events); the structure (H1, italic spoiler line, ## act-subheads with **bold** first-mention names, ## The Verdict, footer disclosure, VERDICT_JSON line); the 1-2 genuinely best lines.
- Sharpen rhythm: break any metronomic stretch with short punchy sentences. No listing-in-threes reflex.
- Preserve the VERDICT_JSON line exactly as-is at the end.

Output ONLY the tightened review. No notes, no preamble, no code fences."""


def parse_verdict_json(text: str) -> dict | None:
    m = re.search(r'VERDICT_JSON:\s*(\{.*?\})', text, re.DOTALL)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def strip_verdict_line(text: str) -> str:
    return re.sub(r'\nVERDICT_JSON:.*', '', text).rstrip()


def main():
    if len(sys.argv) < 4:
        print("usage: build_review.py <slug> <season> <episode>", file=sys.stderr)
        sys.exit(1)

    slug = sys.argv[1]
    season_n = int(sys.argv[2])
    ep_n = int(sys.argv[3])
    ep_tag = f"S{season_n:02d}E{ep_n:02d}"

    dossier_path = os.path.join(REPO, 'data', 'subtitles', slug, '_dossiers', f'{ep_tag}.json')
    series_path = os.path.join(REPO, 'data', 'series', f'{slug}.json')

    if not os.path.exists(dossier_path):
        print(f"ERROR: dossier not found: {dossier_path}", file=sys.stderr)
        sys.exit(1)
    if not os.path.exists(series_path):
        print(f"ERROR: series JSON not found: {series_path}", file=sys.stderr)
        sys.exit(1)

    house_style = open(HOUSE_STYLE).read()
    dossier = json.load(open(dossier_path))
    series_data = json.load(open(series_path))

    # Find matching EpisodeReview in series JSON
    season_obj = next((s for s in series_data.get('seasons', []) if s['number'] == season_n), None)
    if season_obj is None:
        print(f"ERROR: season {season_n} not found in {series_path}", file=sys.stderr)
        sys.exit(1)

    ep_review = next((e for e in season_obj.get('episode_reviews', []) if e['number'] == ep_n), None)
    if ep_review is None:
        print(f"ERROR: episode {ep_n} not found in season {season_n} of {series_path}", file=sys.stderr)
        sys.exit(1)

    # Use series JSON episode title (more reliable than dossier title which may be null)
    if ep_review.get('title') and dossier.get('title') is None:
        dossier['title'] = ep_review['title']

    # --- DRAFT ---
    print(f"Drafting review for {slug} {ep_tag} via gpt-5.5...")
    draft_instr, dossier_text = build_draft_prompt(house_style, dossier, slug)
    draft, rc = gpt_ask(draft_instr, dossier_text, timeout=600)
    draft = strip_fences(draft)
    if rc != 0 or len(draft.split()) < 400:
        print(f"ERROR: draft failed (rc={rc}, words={len(draft.split())})", file=sys.stderr)
        sys.exit(1)
    print(f"  Draft: {len(draft.split())} words | em-dash={em_dash_count(draft)}")

    # --- EDIT PASS ---
    print(f"Edit pass...")
    edited, rc2 = gpt_ask(EDIT_INSTR, draft, timeout=480)
    edited = strip_fences(edited)
    if rc2 != 0 or len(edited.split()) < 400:
        print(f"  WARNING: edit pass failed (rc={rc2}), using draft")
        edited = draft

    # Strip em-dashes as final safety
    edited = strip_em_dashes(edited)

    wc = len(edited.split())
    print(f"  Final: {wc} words | em-dash={em_dash_count(edited)}")

    # --- PARSE VERDICT ---
    verdict = parse_verdict_json(edited)
    if not verdict:
        # Try from draft if edit pass lost it
        verdict = parse_verdict_json(draft)
    if verdict:
        print(f"  Verdict: score={verdict.get('score')} | one_liner={verdict.get('one_liner','')[:60]}...")
    else:
        print("  WARNING: could not parse VERDICT_JSON, using existing bollymeter")

    # Strip the VERDICT_JSON line from the body
    review_body = strip_verdict_line(edited)

    # Validate no em-dash
    remaining_em = em_dash_count(review_body)
    if remaining_em > 0:
        print(f"  WARNING: {remaining_em} em/en-dashes remain after strip — stripping again")
        review_body = strip_em_dashes(review_body)

    # --- MERGE INTO SERIES JSON ---
    ep_review['review_body'] = review_body
    ep_review['hero_image'] = f"/img/series/{slug}/poster.jpg"

    if verdict:
        ep_review['verdict'] = {
            'score': float(verdict['score']),
            'one_liner': verdict['one_liner'],
        }
        # Sync bollymeter with verdict score (per spec: per-episode bollymeter = BollyAI craft score)
        ep_review['bollymeter'] = float(verdict['score'])

    # Pull quote: promote from existing critic_note if present and <=25 words
    if not ep_review.get('pull_quote') and ep_review.get('critic_note'):
        cn = ep_review['critic_note']
        if cn and len(cn.get('text', '').split()) <= 25:
            ep_review['pull_quote'] = {
                'text': cn['text'],
                'source': cn['source'],
                'url': cn['url'],
            }

    # Write back
    with open(series_path, 'w', encoding='utf-8') as f:
        json.dump(series_data, f, ensure_ascii=False, indent=2)
        f.write('\n')

    print(f"  Merged into {series_path}")
    print(f"DONE: {slug} {ep_tag} | {wc} words | verdict={verdict}")


if __name__ == '__main__':
    main()
