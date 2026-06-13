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
import time
import urllib.request
import urllib.error

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HOUSE_STYLE = os.path.join(os.path.dirname(__file__), 'REVIEW-HOUSE-STYLE.md')

# Model routing (bake-off 2026-06-13: gpt-5.4-Azure won on analysis density + in-target
# length + ZERO marginal cost on sponsored credits; frees the ChatGPT weekly pool).
# Override with BOLLYAI_REVIEW_MODEL=gpt-5.5 to use the codex/gpt-5.5 sampler.
REVIEW_MODEL = os.environ.get('BOLLYAI_REVIEW_MODEL', 'gpt-5-4')
AZ_ENDPOINT = "https://adity-mnuhhdt9-eastus2.cognitiveservices.azure.com"
AZ_API_VER = "2024-12-01-preview"
_AZ_KEY = None


def _az_key() -> str:
    global _AZ_KEY
    if _AZ_KEY is None:
        _AZ_KEY = subprocess.run(
            ["az", "cognitiveservices", "account", "keys", "list", "-g", "empire-ai",
             "-n", "adity-mnuhhdt9-eastus2", "--query", "key1", "-o", "tsv"],
            capture_output=True, text=True).stdout.strip()
    return _AZ_KEY


def _azure_chat(deployment: str, instruction: str, user: str, budget: int = 9000,
                timeout: int = 600) -> tuple[str, int]:
    """OpenAI-compatible Azure call. gpt-5.x = max_completion_tokens (reasoning, no temp).
    Exponential backoff on 429 (the gpt-5-4 deployment is low-capacity; respect Retry-After)."""
    url = f"{AZ_ENDPOINT}/openai/deployments/{deployment}/chat/completions?api-version={AZ_API_VER}"
    body = {"messages": [{"role": "system", "content": instruction},
                         {"role": "user", "content": user}],
            "max_completion_tokens": budget}
    data = json.dumps(body).encode()
    for attempt in range(6):
        req = urllib.request.Request(url, data=data,
            headers={"Content-Type": "application/json", "api-key": _az_key()})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                d = json.loads(r.read())
            return (d["choices"][0]["message"]["content"] or "").strip(), 0
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 5:
                wait = int(e.headers.get('Retry-After', 0)) or min(60, 8 * (2 ** attempt))
                print(f"  429 rate-limited, backoff {wait}s (attempt {attempt+1}/6)", flush=True)
                time.sleep(wait); continue
            print(f"  azure HTTP {e.code}: {e.read()[:160]!r}", file=sys.stderr); return "", 1
        except Exception as e:
            print(f"  azure call failed: {e!r}", file=sys.stderr); return "", 1
    return "", 1


def gpt_ask(instruction: str, stdin_text: str, timeout: int = 600) -> tuple[str, int]:
    """Route to the chosen review model. Default gpt-5.4-Azure (sponsored, ~$0)."""
    if REVIEW_MODEL == 'gpt-5.5':
        p = subprocess.run(['gpt', 'ask', instruction], input=stdin_text,
                           capture_output=True, text=True, timeout=timeout)
        return p.stdout.strip(), p.returncode
    return _azure_chat(REVIEW_MODEL, instruction, stdin_text, timeout=timeout)


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


def strip_timestamps(text: str) -> str:
    """Belt-and-suspenders: house-style bans inline subtitle timestamps; some models
    still leak 'At 62:49,' type tokens. Strip them, keep the sentence readable."""
    # "At 62:49, " / "around 1:23:45 " / "(62:49)" / bare " 62:49"
    text = re.sub(r'\s*\(?\b(?:[Aa]t|[Aa]round|by)\s+\d{1,2}:\d{2}(?::\d{2})?\)?,?', '', text)
    text = re.sub(r'\s*\(\d{1,2}:\d{2}(?::\d{2})?\)', '', text)
    text = re.sub(r'\s+\b\d{1,2}:\d{2}(?::\d{2})?\b', '', text)
    text = re.sub(r'  +', ' ', text)            # collapse double spaces
    text = re.sub(r' ([,.])', r'\1', text)      # fix orphaned punctuation spacing
    return text


def timestamp_count(text: str) -> int:
    return len(re.findall(r'\b\d{1,2}:\d{2}\b', text))


def build_draft_prompt(house_style: str, dossier: dict, slug: str) -> str:
    ep_tag = dossier.get('episode', 'S01E01')
    ep_title = dossier.get('title') or ep_tag
    series_name = slug.replace('-', ' ').title()

    beats_lines = []
    for b in dossier.get('beats', []):
        beats_lines.append(f"  [{b['t']}] {b['what']}")

    char_lines = []
    for c in dossier.get('character_beats', []):
        who = c.get('who')
        beat = c.get('beat')
        if not who or not beat:
            continue  # skip malformed dossier entries instead of crashing the build
        char_lines.append(f"  {who}: {beat} (evidence t={c.get('evidence_t', '?')})")

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
    print(f"Drafting review for {slug} {ep_tag} via {REVIEW_MODEL}...")
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

    # Hard timestamp strip (house-style bans them; models leak 'At 62:49,' type tokens)
    ts_before = timestamp_count(review_body)
    if ts_before > 0:
        review_body = strip_timestamps(review_body)
        print(f"  timestamps stripped: {ts_before} -> {timestamp_count(review_body)}")

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
