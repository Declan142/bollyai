#!/usr/bin/env python3
"""build_review - rich episode review via the multi-endpoint model router.

Reads the dossier + REVIEW-HOUSE-STYLE.md, drafts the review, runs a tighten/edit
polish pass (the polish pass re-sends the upgraded house-style contract = the quality
mechanism), then extracts verdict JSON. Draft and polish can target different endpoints
(FULL/NANO/MINI/KIMI/DSV4) via env; default = gpt-5-4 on both, fully backward-compatible.
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

# =============================================================================
# MULTI-ENDPOINT MODEL ROUTING (BLITZ, 2026-06-13)
# =============================================================================
# The REVIEW-BLITZ runs many writer lanes IN PARALLEL across 5 endpoints with
# SEPARATE rate limits, so no single 429 throttles the swarm:
#
#   key   | model id (canonical)          | endpoint family       | rate niche
#   ------+-------------------------------+-----------------------+------------------
#   FULL  | gpt-5-4                       | azure-cog (eastus2)   | cap-3, QUALITY finals
#   NANO  | gpt-5.4-nano                  | azure-cog (eastus2)   | 250 RPM, bulk DRAFTS
#   MINI  | gpt-5-4-mini                  | azure-cog (eastus2)   | cap-3, 2nd quality
#   KIMI  | kimi-k2-6                     | azure-foundry (eastus2)| cap-3, THINKING, 3rd quality
#   DSV4  | deepseek/deepseek-v4-pro      | openrouter            | OFF-Azure, diff corpus, 4th quality
#
# BACKWARD-COMPATIBLE: with NO env overrides this behaves EXACTLY as before -
# REVIEW_MODEL defaults to gpt-5-4 and both draft + edit go to the azure-cog
# eastus2 deployment with max_completion_tokens. work:5 and the buildout loop are
# unaffected. New knobs (all optional):
#   BOLLYAI_REVIEW_MODEL  - default model for both passes (alias OR canonical id)
#   BOLLYAI_DRAFT_MODEL   - override the draft pass only (e.g. NANO for bulk)
#   BOLLYAI_FINAL_MODEL   - override the edit/polish pass only (e.g. FULL or KIMI)
# Aliases (FULL/NANO/MINI/KIMI/DSV4) and canonical ids both accepted everywhere.
# Keys are read from env first, vault second; a key is NEVER printed or logged.

AZ_ENDPOINT = "https://adity-mnuhhdt9-eastus2.cognitiveservices.azure.com"
AZ_API_VER = "2024-12-01-preview"
FOUNDRY_URL = "https://adity-mnuhhdt9-eastus2.services.ai.azure.com/models/chat/completions"
FOUNDRY_API_VER = "2024-05-01-preview"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
VAULT_DIR = os.path.expanduser("~/.claude/vault")

# Friendly routing keys -> canonical model id.
MODEL_ALIASES = {
    'FULL': 'gpt-5-4',
    'NANO': 'gpt-5.4-nano',
    'MINI': 'gpt-5-4-mini',
    'KIMI': 'kimi-k2-6',
    'DSV4': 'deepseek/deepseek-v4-pro',
}

# Canonical model id -> which transport to use. Anything NOT listed (an arbitrary
# Azure deployment string) falls through to azure-cog, preserving legacy behavior.
MODEL_KIND = {
    'gpt-5-4': 'azure-cog',
    'gpt-5.4-nano': 'azure-cog',
    'gpt-5-4-mini': 'azure-cog',
    'kimi-k2-6': 'azure-foundry',
    'deepseek/deepseek-v4-pro': 'openrouter',
}

# Thinking-prone models (Kimi, DeepSeek V4 Pro) leak chain-of-thought into the content
# field unless told to emit prose only - we have seen DSV4 return "We are asked to tighten
# a review..." plus a word-counting scratchpad as the body. This guard suppresses that.
KIMI_THINK_GUARD = ("\n\nOutput ONLY the finished prose (the review text and the VERDICT_JSON "
                    "line). Do NOT include reasoning, planning, notes, word-counts, self-edits, "
                    "compliance checks, or any meta-commentary in the output.")
PROSE_ONLY_GUARD = KIMI_THINK_GUARD  # shared by foundry (Kimi) + openrouter (DSV4)
KIMI_MIN_TOKENS = 32000


def resolve_model(name: str) -> str:
    """Map a friendly alias (FULL/NANO/...) to its canonical model id; pass others through."""
    return MODEL_ALIASES.get((name or '').strip().upper(), (name or '').strip())


_AZ_KEY = None


def _az_key() -> str:
    """Azure account key: env AZURE_FOUNDRY_KEY first (lets a swarm skip 200 az subprocesses),
    else the az CLI. Same account-level key works for cog + foundry deployments."""
    global _AZ_KEY
    if _AZ_KEY is None:
        _AZ_KEY = os.environ.get('AZURE_FOUNDRY_KEY', '').strip()
    if not _AZ_KEY:
        _AZ_KEY = subprocess.run(
            ["az", "cognitiveservices", "account", "keys", "list", "-g", "empire-ai",
             "-n", "adity-mnuhhdt9-eastus2", "--query", "key1", "-o", "tsv"],
            capture_output=True, text=True).stdout.strip()
    return _AZ_KEY


_OR_KEY = None


def _or_key() -> str:
    """OpenRouter key: env OPENROUTER_API_KEY first, else parse ~/.claude/vault/openrouter.md.
    Handles both '- **API Key:**' (bold) and '- API Key:' (plain) line conventions."""
    global _OR_KEY
    if _OR_KEY is None:
        _OR_KEY = os.environ.get('OPENROUTER_API_KEY', '').strip()
    if not _OR_KEY:
        path = os.path.join(VAULT_DIR, 'openrouter.md')
        try:
            for line in open(path):
                low = line.strip().lower()
                if low.startswith('- **api key:**'):
                    _OR_KEY = line.split('**API Key:**', 1)[1].strip().split()[0]; break
                if low.startswith('- api key:'):
                    _OR_KEY = line.split('API Key:', 1)[1].strip().split()[0]; break
        except FileNotFoundError:
            pass
    if not _OR_KEY:
        raise RuntimeError("no OpenRouter key (set OPENROUTER_API_KEY or vault/openrouter.md)")
    return _OR_KEY


def _http_json(url: str, headers: dict, body: dict, timeout: int) -> tuple[int, dict | None, str]:
    """POST JSON, return (http_code, parsed_or_None, retry_after). code 0 = transport error."""
    data = json.dumps(body).encode()
    req = urllib.request.Request(url, data=data, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return 200, json.loads(r.read()), ''
    except urllib.error.HTTPError as e:
        return e.code, None, str(e.headers.get('Retry-After', '') or '')
    except Exception as e:
        print(f"  call failed: {e!r}", file=sys.stderr)
        return 0, None, ''


def _backoff_loop(call, label: str):
    """Run call() with exponential backoff on 429. call() -> (code, parsed, retry_after, text).
    Returns (text, rc). The low-capacity cap-3 deployments need this; respect Retry-After."""
    for attempt in range(6):
        code, parsed, retry_after, text = call()
        if code == 200:
            return text, 0
        if code == 429 and attempt < 5:
            wait = int(retry_after) if str(retry_after).isdigit() else min(60, 8 * (2 ** attempt))
            print(f"  429 rate-limited [{label}], backoff {wait}s (attempt {attempt+1}/6)", flush=True)
            time.sleep(wait); continue
        print(f"  {label} HTTP {code}", file=sys.stderr)
        return "", 1
    return "", 1


def _azure_chat(deployment: str, instruction: str, user: str, budget: int = 9000,
                timeout: int = 600) -> tuple[str, int]:
    """azure-cog transport: OpenAI-compatible, gpt-5.x = max_completion_tokens (no temp)."""
    url = f"{AZ_ENDPOINT}/openai/deployments/{deployment}/chat/completions?api-version={AZ_API_VER}"

    def _call():
        code, parsed, ra = _http_json(
            url, {"Content-Type": "application/json", "api-key": _az_key()},
            {"messages": [{"role": "system", "content": instruction},
                          {"role": "user", "content": user}],
             "max_completion_tokens": budget}, timeout)
        text = ((parsed["choices"][0]["message"]["content"] or "").strip()
                if parsed else "")
        return code, parsed, ra, text

    return _backoff_loop(_call, f"azure-cog/{deployment}")


def _foundry_chat(model: str, instruction: str, user: str, budget: int = 9000,
                  timeout: int = 600) -> tuple[str, int]:
    """azure-foundry transport (Kimi): thinking model, max_tokens >= 32K + prose-only guard.
    Falls back to reasoning_content if the content field comes back empty."""
    budget = max(budget, KIMI_MIN_TOKENS)
    sys_prompt = instruction + KIMI_THINK_GUARD
    url = f"{FOUNDRY_URL}?api-version={FOUNDRY_API_VER}"

    def _call():
        code, parsed, ra = _http_json(
            url, {"Content-Type": "application/json", "api-key": _az_key()},
            {"model": model,
             "messages": [{"role": "system", "content": sys_prompt},
                          {"role": "user", "content": user}],
             "max_tokens": budget}, timeout)
        text = ""
        if parsed:
            msg = parsed["choices"][0]["message"]
            text = (msg.get("content") or "").strip()
            if not text:  # thinking-ate-the-content fallback (vault: feedback_kimi_k26_...)
                reasoning = msg.get("reasoning_content") or msg.get("reasoning") or ""
                idx = reasoning.find("Full draft assembly:")
                if idx >= 0:
                    text = reasoning[idx + len("Full draft assembly:"):].split("---\n\nLet me")[0].strip()
        return code, parsed, ra, text

    return _backoff_loop(_call, f"foundry/{model}")


def _openrouter_chat(model: str, instruction: str, user: str, budget: int = 9000,
                     timeout: int = 600) -> tuple[str, int]:
    """openrouter transport (DeepSeek V4 Pro): off-Azure, different corpus, 1M ctx.
    DSV4 is thinking-prone, so we append the prose-only guard. We do NOT fall back to the
    `reasoning` field on empty content - for a chat model that field is raw chain-of-thought,
    and emitting it as the review is exactly the leak we are guarding against."""
    url = OPENROUTER_URL
    sys_prompt = instruction + PROSE_ONLY_GUARD

    def _call():
        code, parsed, ra = _http_json(
            url, {"Authorization": f"Bearer {_or_key()}",
                  "Content-Type": "application/json",
                  "HTTP-Referer": "https://bollyai.in",
                  "X-Title": "bollyai-review-blitz"},
            {"model": model,
             "messages": [{"role": "system", "content": sys_prompt},
                          {"role": "user", "content": user}],
             "max_tokens": budget, "stream": False}, timeout)
        text = ""
        if parsed:
            text = (parsed["choices"][0]["message"].get("content") or "").strip()
        return code, parsed, ra, text

    return _backoff_loop(_call, f"openrouter/{model}")


def gpt_ask(instruction: str, stdin_text: str, timeout: int = 600,
            model: str | None = None, budget: int = 9000) -> tuple[str, int]:
    """Route a single chat turn to the chosen model across any of the 5 endpoints.
    `model` may be a friendly key (FULL/NANO/MINI/KIMI/DSV4) or a canonical id;
    defaults to REVIEW_MODEL (today's gpt-5-4) -> fully backward-compatible."""
    canon = resolve_model(model or REVIEW_MODEL)
    if canon == 'gpt-5.5':  # codex/gpt-5.5 sampler (legacy escape hatch)
        p = subprocess.run(['gpt', 'ask', instruction], input=stdin_text,
                           capture_output=True, text=True, timeout=timeout)
        return p.stdout.strip(), p.returncode
    kind = MODEL_KIND.get(canon, 'azure-cog')  # unknown id -> legacy azure-cog deployment
    if kind == 'azure-foundry':
        return _foundry_chat(canon, instruction, stdin_text, budget=budget, timeout=timeout)
    if kind == 'openrouter':
        return _openrouter_chat(canon, instruction, stdin_text, budget=budget, timeout=timeout)
    return _azure_chat(canon, instruction, stdin_text, budget=budget, timeout=timeout)


# Default model for both passes (alias or canonical). Per-pass overrides below.
REVIEW_MODEL = resolve_model(os.environ.get('BOLLYAI_REVIEW_MODEL', 'gpt-5-4'))
DRAFT_MODEL = resolve_model(os.environ.get('BOLLYAI_DRAFT_MODEL', REVIEW_MODEL))
FINAL_MODEL = resolve_model(os.environ.get('BOLLYAI_FINAL_MODEL', REVIEW_MODEL))


def strip_fences(text: str) -> str:
    text = re.sub(r'^```(?:markdown)?\s*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'\n?```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def em_dash_count(text: str) -> int:
    return text.count('—') + text.count('–') + text.count('--')


def strip_em_dashes(text: str) -> str:
    # em / en / horizontal-bar = clause separators -> spaced hyphen
    text = text.replace('—', ' - ')   # em dash
    text = text.replace('–', ' - ')   # en dash
    text = text.replace('―', ' - ')   # horizontal bar
    # in-word dash look-alikes -> plain hyphen (never spaced: "Gi-hun", "debt-soaked")
    text = text.replace('‐', '-')     # hyphen (unicode)
    text = text.replace('‑', '-')     # non-breaking hyphen
    text = text.replace('‒', '-')     # figure dash
    text = text.replace(' ', ' ')     # non-breaking space -> normal space
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


_REASONING_HEAD = re.compile(
    r"\s*(we are asked|we need to|we must|we should|let me|let's|the (current )?draft|okay,|"
    r"first,? (i|we|let)|i (will|need to|should|am going)|the user (wants|asks)|"
    r"here('?s| is) (the|my) (tightened|edited|revised|final))", re.IGNORECASE)


def looks_like_reasoning_leak(text: str) -> bool:
    """Thinking models (DSV4, Kimi) sometimes dump chain-of-thought into the content field:
    a reasoning preamble ('We are asked to tighten...') and/or a word-counting scratchpad
    ('storyline(2) threads(3) directly(4)'). Detect both so we can fall back to a clean pass."""
    if _REASONING_HEAD.match(text[:300] or ""):
        return True
    if re.search(r"\w\(\d+\)\s+\w+\(\d+\)", text):   # numbered-word counting scratchpad
        return True
    return False


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
        key_lines.append(f"  [{k['t']}] {sp}: \"{k['line']}\" - {k['why']}")

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
    print(f"Drafting review for {slug} {ep_tag} via {DRAFT_MODEL} (final: {FINAL_MODEL})...")
    draft_instr, dossier_text = build_draft_prompt(house_style, dossier, slug)
    draft, rc = gpt_ask(draft_instr, dossier_text, timeout=600, model=DRAFT_MODEL)
    draft = strip_fences(draft)
    if rc != 0 or len(draft.split()) < 400 or looks_like_reasoning_leak(draft):
        print(f"ERROR: draft failed (rc={rc}, words={len(draft.split())}, "
              f"leak={looks_like_reasoning_leak(draft)})", file=sys.stderr)
        sys.exit(1)
    print(f"  Draft: {len(draft.split())} words | em-dash={em_dash_count(draft)}")

    # --- EDIT PASS (the polish pass: where the upgraded house style does its work) ---
    print(f"Edit pass via {FINAL_MODEL}...")
    edited, rc2 = gpt_ask(EDIT_INSTR, draft, timeout=480, model=FINAL_MODEL)
    edited = strip_fences(edited)
    draft_wc = len(draft.split())
    edit_wc = len(edited.split())
    leak = looks_like_reasoning_leak(edited)
    too_long = edit_wc > max(2200, int(draft_wc * 1.6))   # editor should TIGHTEN, not bloat
    if rc2 != 0 or edit_wc < 400 or too_long or leak:
        print(f"  WARNING: edit pass rejected (rc={rc2} words={edit_wc} draft={draft_wc} "
              f"leak={leak} too_long={too_long}) - using clean draft")
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
        print(f"  WARNING: {remaining_em} em/en-dashes remain after strip - stripping again")
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
            # normalize the one_liner too (models leak em/en/nbsp-hyphen here, not just the body)
            'one_liner': strip_em_dashes(verdict['one_liner']),
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
