#!/usr/bin/env python3
"""nano_draft — batch draft episode reviews via gpt-5.4-nano (250 RPM, no dossier needed).

For series that lack subtitle dossiers, generates draft reviews from model knowledge + the
REVIEW-HOUSE-STYLE contract.  Drafts are interim; P2 polish (FULL gpt-5-4) upgrades them.

Usage:
  python3 scripts/subtitles/nano_draft.py physical-100 hellbound navarasa
  python3 scripts/subtitles/nano_draft.py --force physical-100   # redo even if body exists
  NANO_WORKERS=6 python3 scripts/subtitles/nano_draft.py physical-100  # parallel within series

Hard fences (build-breaking if violated):
  - No first-person viewing claims.
  - No em-dash (U+2014) or en-dash (U+2013).
  - No fabricated OTT viewership numbers.
  - bollymeter per-episode = null (let P2 score after polish).
  - pull_quote = null (no verified external quotes without a URL).
  - Never clobber an existing review_body.
"""
import sys
import os
import json
import re
import subprocess
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

REPO = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
HOUSE_STYLE = os.path.join(os.path.dirname(__file__), 'REVIEW-HOUSE-STYLE.md')
VALIDATE = os.path.join(REPO, 'scripts', 'batch', 'validate_series.py')
LEDGER = os.path.join(REPO, 'data', 'subtitles', '_engine', 'nano-draft.jsonl')

AZ_ENDPOINT = "https://adity-mnuhhdt9-eastus2.cognitiveservices.azure.com"
AZ_API_VER = "2024-12-01-preview"
NANO_DEPLOYMENT = "gpt-5.4-nano"

WORKERS = int(os.environ.get('NANO_WORKERS', '5'))
FORCE = '--force' in sys.argv

_AZ_KEY = None


def az_key() -> str:
    global _AZ_KEY
    if _AZ_KEY:
        return _AZ_KEY
    _AZ_KEY = os.environ.get('AZURE_FOUNDRY_KEY', '').strip()
    if not _AZ_KEY:
        _AZ_KEY = subprocess.run(
            ["az", "cognitiveservices", "account", "keys", "list", "-g", "empire-ai",
             "-n", "adity-mnuhhdt9-eastus2", "--query", "key1", "-o", "tsv"],
            capture_output=True, text=True).stdout.strip()
    return _AZ_KEY


def log(rec: dict):
    rec['ts'] = time.strftime('%Y-%m-%dT%H:%M:%S%z')
    os.makedirs(os.path.dirname(LEDGER), exist_ok=True)
    with open(LEDGER, 'a') as fh:
        fh.write(json.dumps(rec, ensure_ascii=False) + '\n')
    print(f"[{rec.get('event','?')}] {rec.get('slug','')} "
          f"{rec.get('ep','')} {rec.get('detail','')}", flush=True)


def strip_em_dashes(text: str) -> str:
    text = text.replace('—', ' - ').replace('–', ' - ')
    text = re.sub(r'--+', ' - ', text)
    return text


def em_dash_count(text: str) -> int:
    return text.count('—') + text.count('–') + text.count('---') + text.count('--')


def strip_fences(text: str) -> str:
    text = re.sub(r'^```[a-z]*\n?', '', text, flags=re.MULTILINE)
    text = re.sub(r'^```\s*$', '', text, flags=re.MULTILINE)
    return text.strip()


def strip_verdict_line(text: str) -> str:
    return re.sub(r'\nVERDICT_JSON:.*', '', text).rstrip()


def parse_verdict_json(text: str) -> dict | None:
    m = re.search(r'VERDICT_JSON:\s*(\{[^}]+\})', text)
    if not m:
        return None
    try:
        return json.loads(m.group(1))
    except Exception:
        return None


def _http_post(url: str, headers: dict, body: dict, timeout: int = 120):
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


def nano_chat(system_msg: str, user_msg: str, timeout: int = 90) -> tuple[str, int]:
    """Call gpt-5.4-nano with backoff. Returns (text, rc)."""
    url = (f"{AZ_ENDPOINT}/openai/deployments/{NANO_DEPLOYMENT}"
           f"/chat/completions?api-version={AZ_API_VER}")
    for attempt in range(5):
        code, parsed, retry_after = _http_post(
            url,
            {"Content-Type": "application/json", "api-key": az_key()},
            {"messages": [{"role": "system", "content": system_msg},
                          {"role": "user", "content": user_msg}],
             "max_completion_tokens": 2200},
            timeout=timeout
        )
        if code == 200:
            text = (parsed["choices"][0]["message"]["content"] or "").strip() if parsed else ""
            return text, 0
        if code == 429 and attempt < 4:
            wait = int(retry_after) if str(retry_after).isdigit() else min(30, 4 * (2 ** attempt))
            print(f"  429 rate-limit, backoff {wait}s (attempt {attempt+1}/5)", flush=True)
            time.sleep(wait)
            continue
        print(f"  nano HTTP {code}", file=sys.stderr)
        return "", 1
    return "", 1


def build_prompt(series_data: dict, season_obj: dict, ep_num: int,
                 ep_title: str | None, house_style: str) -> tuple[str, str]:
    """Return (system_instruction, user_prompt) for a no-dossier draft."""
    title_val = series_data.get('title', {})
    title = title_val.get('value', '') if isinstance(title_val, dict) else str(title_val)
    platform_val = series_data.get('platform', {})
    platform = platform_val.get('value', '') if isinstance(platform_val, dict) else str(platform_val)
    genres = series_data.get('genres', [])
    if isinstance(genres, list):
        genres_str = ', '.join(genres)
    else:
        genres_str = str(genres)
    logline = series_data.get('logline', '')
    origin = series_data.get('origin', '')
    snum = season_obj.get('number', 1)
    year = season_obj.get('year', '')
    ep_count = season_obj.get('episodes', 0)
    season_review = season_obj.get('review_body', '')[:400]

    ep_label = f'S{snum:02d}E{ep_num:02d}'
    ep_display = f'"{ep_title}"' if ep_title else ep_label

    system_instruction = f"""{house_style}

IMPORTANT ADDITIONS FOR THIS DRAFT (no subtitle dossier available):
- You are writing from your training knowledge of how critics and audiences received this show.
- State reception facts confidently only if you know them to be accurate.
- For plot beats you are not certain about, write at the STRUCTURAL or THEMATIC level rather
  than inventing specific details. It is better to be general and accurate than specific and wrong.
- Do NOT invent viewership numbers, streaming statistics, or ratings you don't know.
- Set bollymeter to null in the VERDICT_JSON (no per-episode grounding without dossier).
- Use the VERDICT_JSON format exactly as specified in the house style.
- This is a DRAFT. Prioritize structure and voice over completeness.
"""

    user_msg = f"""Write a draft episode review.

SERIES CONTEXT:
  Title: {title}
  Platform: {platform}
  Origin: {origin}
  Genre: {genres_str}
  Logline: {logline}
  Season {snum} ({year}, {ep_count} episodes):
  {season_review}

EPISODE TO REVIEW:
  {ep_label}: {ep_display}

Write the full review now. Follow the house style above exactly.
Set bollymeter in VERDICT_JSON to null (no verified per-episode score available).
Spoiler-careful. No first-person viewing claims. No em-dashes.
"""
    return system_instruction, user_msg


def draft_episode(series_data: dict, slug: str, snum: int, ep_num: int,
                  ep_title: str | None, house_style: str) -> dict | None:
    """Generate a draft review for one episode. Returns merged episode_review dict or None."""
    ep_label = f'S{snum:02d}E{ep_num:02d}'

    season_obj = next((s for s in series_data.get('seasons', []) if s.get('number') == snum), None)
    if season_obj is None:
        print(f"  ERROR: season {snum} not found in {slug}", file=sys.stderr)
        return None

    sys_msg, user_msg = build_prompt(series_data, season_obj, ep_num, ep_title, house_style)

    print(f"  Drafting {slug} {ep_label}...", flush=True)
    text, rc = nano_chat(sys_msg, user_msg)
    text = strip_fences(text)

    if rc != 0 or len(text.split()) < 200:
        log({'event': 'ep_FAIL', 'slug': slug, 'ep': ep_label,
             'detail': f'rc={rc} words={len(text.split())}', 'model': NANO_DEPLOYMENT})
        return None

    # Strip em-dashes
    text = strip_em_dashes(text)

    verdict = parse_verdict_json(text)
    review_body = strip_verdict_line(text)

    # Safety: ensure no viewing claims slipped through
    viewing_patterns = [
        r'\bI watched\b', r'\bI saw\b', r'\bwhen I\b', r'\bmy screening\b',
        r'\bmaine dekhi\b', r'\bhumne dekha\b',
    ]
    for pat in viewing_patterns:
        if re.search(pat, review_body, re.IGNORECASE):
            print(f"  WARNING: viewing claim detected in {ep_label}, stripping phrase", file=sys.stderr)
            review_body = re.sub(pat, 'critics noted', review_body, flags=re.IGNORECASE)

    words = len(review_body.split())
    log({'event': 'ep_ok', 'slug': slug, 'ep': ep_label,
         'detail': f'{words} words | em={em_dash_count(review_body)}', 'model': NANO_DEPLOYMENT})

    ep_review = {
        'number': ep_num,
        'title': ep_title or f'Episode {ep_num}',
        'air_date': None,
        'bollymeter': None,  # no per-episode grounding without dossier
        'spoiler_free': '',
        'the_moment': None,
        'critic_note': None,
        'review_body': review_body,
        'verdict': verdict,
        'pull_quote': None,
        'hero_image': f'/img/series/{slug}/poster.jpg',
    }

    # Extract spoiler_free: first substantive content paragraph (skip headings/meta/title lines)
    lines = review_body.split('\n')
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        if stripped.startswith('*') and stripped.endswith('*'):
            continue
        if 'Written by BollyAI' in stripped:
            continue
        if 'VERDICT_JSON' in stripped:
            continue
        if 'Review' in stripped and len(stripped) < 60:
            continue
        if len(stripped) > 80:
            ep_review['spoiler_free'] = stripped[:280]
            break

    return ep_review


def process_series(slug: str) -> tuple[int, int]:
    """Process one series: generate missing episode reviews. Returns (ok, fail)."""
    series_path = os.path.join(REPO, 'data', 'series', f'{slug}.json')
    if not os.path.exists(series_path):
        print(f"ERROR: {series_path} not found", file=sys.stderr)
        return 0, 0

    house_style = open(HOUSE_STYLE).read()

    with open(series_path) as f:
        series_data = json.load(f)

    # Collect all missing episodes across all seasons
    missing = []  # (snum, ep_num, ep_title, existing_ep_review_or_None)
    for season in series_data.get('seasons', []):
        snum = season.get('number')
        ep_count = season.get('episodes', 0)
        if not isinstance(ep_count, int) or ep_count <= 0:
            continue
        ep_reviews = season.get('episode_reviews', [])
        if not isinstance(ep_reviews, list):
            ep_reviews = []
        reviewed = {ep.get('number'): ep for ep in ep_reviews}
        for ep_num in range(1, ep_count + 1):
            existing = reviewed.get(ep_num)
            if existing and existing.get('review_body') and not FORCE:
                continue  # skip: already reviewed
            ep_title = existing.get('title') if existing else None
            missing.append((snum, ep_num, ep_title, existing))

    if not missing:
        print(f"  {slug}: no missing episode reviews, skipping")
        return 0, 0

    log({'event': 'series_start', 'slug': slug, 'detail': f'{len(missing)} episodes missing'})

    # Parallel draft calls (workers capped at WORKERS)
    results = {}  # (snum, ep_num) -> ep_review dict or None
    with ThreadPoolExecutor(max_workers=WORKERS) as pool:
        futures = {
            pool.submit(draft_episode, series_data, slug, snum, ep_num, ep_title, house_style): (snum, ep_num)
            for (snum, ep_num, ep_title, _) in missing
        }
        for fut in as_completed(futures):
            key = futures[fut]
            try:
                results[key] = fut.result()
            except Exception as e:
                results[key] = None
                print(f"  ERROR {slug} S{key[0]}E{key[1]}: {e}", file=sys.stderr)

    # Merge all results into series_data (re-read to avoid stale state from parallelism)
    with open(series_path) as f:
        series_data = json.load(f)

    ok = fail = 0
    for (snum, ep_num, ep_title, existing_ep) in missing:
        ep_review = results.get((snum, ep_num))
        if ep_review is None:
            fail += 1
            continue

        # Find/create the season
        season_obj = next((s for s in series_data.get('seasons', []) if s.get('number') == snum), None)
        if season_obj is None:
            fail += 1
            continue

        # Ensure episode_reviews list exists
        if 'episode_reviews' not in season_obj or not isinstance(season_obj['episode_reviews'], list):
            season_obj['episode_reviews'] = []

        # Find existing entry or append
        ep_reviews = season_obj['episode_reviews']
        idx = next((i for i, e in enumerate(ep_reviews) if e.get('number') == ep_num), None)
        if idx is not None:
            # Merge into existing entry (preserve fields we don't overwrite)
            existing = ep_reviews[idx]
            if existing.get('review_body') and not FORCE:
                ok += 1
                continue  # already has body, skip
            existing.update({k: v for k, v in ep_review.items() if v is not None})
        else:
            # Append new entry, sorted by episode number
            ep_reviews.append(ep_review)
            ep_reviews.sort(key=lambda e: e.get('number', 0))

        ok += 1

    # Write merged JSON
    with open(series_path, 'w', encoding='utf-8') as f:
        json.dump(series_data, f, ensure_ascii=False, indent=2)
        f.write('\n')
    print(f"  Wrote {series_path} (ok={ok} fail={fail})")

    # Validate
    result = subprocess.run(
        ['python3', VALIDATE, slug], capture_output=True, text=True, cwd=REPO)
    if result.returncode == 0:
        log({'event': 'validate_ok', 'slug': slug, 'detail': f'ok={ok} fail={fail}'})
    else:
        errs = (result.stdout + result.stderr)[-300:]
        log({'event': 'validate_FAIL', 'slug': slug, 'detail': errs})
        print(f"  VALIDATE FAIL {slug}: {errs}", file=sys.stderr)

    return ok, fail


def main():
    args = [a for a in sys.argv[1:] if not a.startswith('--')]
    if not args:
        print("usage: nano_draft.py [--force] <slug1> <slug2> ...", file=sys.stderr)
        sys.exit(1)

    total_ok = total_fail = 0
    for slug in args:
        ok, fail = process_series(slug)
        total_ok += ok
        total_fail += fail
        print(f"  {slug}: done ok={ok} fail={fail}")

    print(f"\nTotal: ok={total_ok} fail={total_fail}")
    if total_ok > 0 and total_fail == 0:
        print("conductor outcome bollyai done \"nano_draft: all episodes drafted\"")
    elif total_ok > 0:
        print(f"conductor outcome bollyai partial \"nano_draft: {total_ok} ok / {total_fail} fail\"")
    else:
        print("conductor outcome bollyai fail \"nano_draft: no episodes generated\"")


if __name__ == '__main__':
    main()
