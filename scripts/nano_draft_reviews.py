#!/usr/bin/env python3
"""
BollyAI BLITZ — NANO draft episode review generator.
Floods gpt-5.4-nano (250 RPM) with DRAFT episode reviews for incomplete series.
NEVER clobbers existing reviews. Drafts only - P2 will polish.

Usage:
    python3 scripts/nano_draft_reviews.py [--slugs slug1 slug2 ...] [--limit N] [--workers N]
"""

import json
import os
import re
import sys
import time
import argparse
import concurrent.futures
from datetime import datetime
from pathlib import Path
from typing import Optional

from openai import AzureOpenAI

# ── NANO endpoint (250 RPM / 250K TPM) ─────────────────────────────────────
NANO_ENDPOINT = "https://adity-mnuhhdt9-eastus2.cognitiveservices.azure.com/"
NANO_KEY = os.environ.get("AZURE_FOUNDRY_KEY", "").strip()
NANO_DEPLOYMENT = "gpt-5.4-nano"

DATA_DIR = Path(__file__).parent.parent / "data" / "series"
LOG_FILE = Path(__file__).parent.parent / "data" / "_state" / "nano_draft.log"

EM_DASH_RE = re.compile(r"[—–]")
VIEWING_CLAIM_RE = re.compile(
    r"\b(I watched|I saw|I screened|I witnessed|I noticed|maine dekhi|humne dekha|when I saw|my screening)\b",
    re.IGNORECASE,
)

# ── High-traffic priority queue (ordered: smallest missing first within tier) ──
HIGH_TRAFFIC_TARGETS = [
    # Tier 1: <10 missing (fast wins)
    "adolescence", "scam-1992", "avatar-the-last-airbender", "fallout",
    "baby-reindeer", "ripley", "years-and-years", "blue-eye-samurai",
    "station-eleven", "tvf-pitchers", "kingdom", "all-of-us-are-dead",
    "fleabag", "wednesday", "the-last-of-us", "sacred-games", "paatal-lok",
    "shogun", "aspirants", "bocchi-the-rock", "chainsaw-man",
    "the-diplomat", "arcane",
    # Tier 2: 10-25 missing
    "beef", "mindhunter", "bandish-bandits", "delhi-crime", "my-mister",
    "vincenzo", "severance", "the-witcher", "the-boys", "bridgerton",
    "sex-education", "never-have-i-ever", "andor", "euphoria",
    "college-romance", "the-family-man", "squid-game", "house-of-the-dragon",
    "sweet-home", "mr-sunshine",
    # Tier 3: 25-50 missing (high-traffic despite more work)
    "aarya", "dark", "hacks", "ted-lasso", "barry", "shrinking",
    "only-murders-in-the-building", "you", "the-crown", "money-heist",
    "fargo", "succession", "peaky-blinders", "narcos", "mirzapur",
    "panchayat", "true-detective", "alchemy-of-souls", "the-marvelous-mrs-maisel",
    "the-bear", "invincible", "black-mirror", "emily-in-paris",
    "stranger-things", "mob-psycho-100", "one-punch-man", "vinland-saga",
    "spy-x-family", "jujutsu-kaisen",
    # Tier 4: 50+ missing but massive traffic
    "breaking-bad", "better-call-saul", "the-wire", "the-sopranos",
    "mad-men", "game-of-thrones", "ozark", "westworld",
    "the-handmaids-tale", "cobra-kai", "attack-on-titan",
    "abbott-elementary",
]


def _get_client() -> AzureOpenAI:
    return AzureOpenAI(
        api_version="2024-12-01-preview",
        azure_endpoint=NANO_ENDPOINT,
        api_key=NANO_KEY,
    )


def _log(msg: str):
    ts = datetime.now().strftime("%H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line, flush=True)
    try:
        with open(LOG_FILE, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def _clean(text: str) -> str:
    text = EM_DASH_RE.sub(" - ", text)
    text = VIEWING_CLAIM_RE.sub("[BollyAI note: viewing claim removed]", text)
    return text.strip()


def _load_series(slug: str) -> Optional[dict]:
    path = DATA_DIR / f"{slug}.json"
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def _get_missing_episodes(season: dict) -> list[int]:
    """Return episode numbers that have no spoiler_free review (>100 chars)."""
    eps_field = season.get("episodes")
    if isinstance(eps_field, int):
        total = eps_field
        all_nums = list(range(1, total + 1))
    elif isinstance(eps_field, list):
        all_nums = [e.get("number", i + 1) if isinstance(e, dict) else i + 1
                    for i, e in enumerate(eps_field)]
    else:
        all_nums = []

    reviewed = set()
    for er in season.get("episode_reviews", []):
        sf = er.get("spoiler_free", "").strip()
        if len(sf) > 100:
            reviewed.add(er["number"])

    return [n for n in all_nums if n not in reviewed]


def _get_ep_title(season: dict, ep_num: int) -> str:
    eps = season.get("episodes")
    if isinstance(eps, list):
        for e in eps:
            if isinstance(e, dict) and e.get("number") == ep_num:
                return e.get("title") or e.get("name") or f"Episode {ep_num}"
    return f"Episode {ep_num}"


def _series_context(d: dict) -> str:
    title = d.get("title", {})
    if isinstance(title, dict):
        title = title.get("value", "Unknown")

    platform = d.get("platform", {})
    if isinstance(platform, dict):
        platform = platform.get("value", "streaming")

    origin = d.get("origin", "")
    logline = d.get("logline", "")
    genres = d.get("genres", [])
    genre_str = ", ".join(genres) if genres else ""

    return (
        f'Series: "{title}" | Platform: {platform} | Origin: {origin} | '
        f'Genres: {genre_str}\nLogline: {logline}'
    )


def _season_context(season: dict) -> str:
    n = season.get("number", 1)
    year = season.get("year", "")
    ep_count = season.get("episodes", 0)
    if not isinstance(ep_count, int):
        ep_count = len(ep_count) if isinstance(ep_count, list) else 0
    verdict = season.get("verdict", "")
    review_body = (season.get("review_body", "") or "")[:400]
    return (
        f"Season {n} ({year}, {ep_count} episodes). "
        f"Season verdict: {verdict}.\n"
        f"Season overview: {review_body}"
    )


SYSTEM_PROMPT = """You are a BollyAI editorial researcher. BollyAI has NOT watched anything.
BollyAI writes in third person about what critics and audiences reported.

HARD RULES (violating any of these fails our build gate):
1. NO first-person viewing claims. Never: "I watched / I saw / when I saw / my screening". Always third person.
2. NO em-dashes (—) or en-dashes (–). Use a spaced hyphen " - " instead.
3. NO fabricated Indian OTT viewership numbers (Indian platforms do not publish them).
4. bollymeter: set to null for drafts (grounding will happen in the polish pass).
5. critic_note: set to null for drafts.
6. Output ONLY valid JSON, no markdown fences, no preamble.

You write spoiler-light episode review drafts. Each review is grounded in what critics
and audiences broadly noted about this series and this episode's place in the season arc."""


def _generate_episode_reviews(
    client: AzureOpenAI,
    series_ctx: str,
    season_ctx: str,
    episodes: list[dict],  # [{"number": N, "title": "..."}]
    retry: int = 2,
) -> list[dict]:
    """Generate draft episode reviews for a batch of episodes in one call."""
    ep_list = "\n".join(
        f'  - Episode {e["number"]}: "{e["title"]}"' for e in episodes
    )
    user_prompt = (
        f"{series_ctx}\n{season_ctx}\n\n"
        f"Generate draft episode reviews for these episodes:\n{ep_list}\n\n"
        "For EACH episode, output a JSON object with exactly these fields:\n"
        '{\n'
        '  "number": <integer>,\n'
        '  "title": "<episode title>",\n'
        '  "air_date": null,\n'
        '  "bollymeter": null,\n'
        '  "spoiler_free": "<3-4 sentences, third-person, spoiler-light. What critics noted about '
        'this episode\'s role in the season arc, key performances, craft. No viewing claims.>",\n'
        '  "the_moment": "<1 sentence: the beat audiences remember from this episode, spoiler-careful>",\n'
        '  "critic_note": null\n'
        "}\n\n"
        "Output a JSON ARRAY of all episode objects. No markdown, no code blocks, no preamble."
    )

    for attempt in range(retry + 1):
        try:
            resp = client.chat.completions.create(
                model=NANO_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                max_completion_tokens=1500,
                temperature=0.7,
            )
            raw = resp.choices[0].message.content.strip()
            # Strip markdown fences if present
            raw = re.sub(r"^```json\s*", "", raw)
            raw = re.sub(r"\s*```$", "", raw)
            parsed = json.loads(raw)
            if not isinstance(parsed, list):
                parsed = [parsed]
            # Clean each review
            result = []
            for er in parsed:
                if not isinstance(er, dict):
                    continue
                if "spoiler_free" in er:
                    er["spoiler_free"] = _clean(er["spoiler_free"])
                if "the_moment" in er and er["the_moment"]:
                    er["the_moment"] = _clean(er["the_moment"])
                # Enforce null fields for drafts
                er["bollymeter"] = None
                er["critic_note"] = None
                result.append(er)
            return result
        except json.JSONDecodeError as e:
            if attempt < retry:
                time.sleep(2)
                continue
            _log(f"  JSON parse error (attempt {attempt+1}): {e}")
            return []
        except Exception as e:
            if attempt < retry:
                time.sleep(5)
                continue
            _log(f"  API error (attempt {attempt+1}): {e}")
            return []
    return []


def process_series(slug: str, client: AzureOpenAI, dry_run: bool = False) -> dict:
    """Process one series: find missing episodes, generate drafts, merge back."""
    result = {"slug": slug, "drafted": 0, "skipped": 0, "errors": []}

    d = _load_series(slug)
    if d is None:
        result["errors"].append("file not found")
        return result

    series_ctx = _series_context(d)
    modified = False

    for season in d.get("seasons", []):
        missing_nums = _get_missing_episodes(season)
        if not missing_nums:
            continue

        season_ctx = _season_context(season)
        episodes = [
            {"number": n, "title": _get_ep_title(season, n)}
            for n in missing_nums
        ]

        _log(f"  {slug} S{season['number']}: generating {len(missing_nums)} drafts "
             f"[ep {missing_nums[0]}..{missing_nums[-1]}]")

        if dry_run:
            result["drafted"] += len(missing_nums)
            continue

        # Batch calls: up to 8 episodes per call (token budget)
        batch_size = 8
        new_reviews = []
        for i in range(0, len(episodes), batch_size):
            batch = episodes[i:i + batch_size]
            reviews = _generate_episode_reviews(client, series_ctx, season_ctx, batch)
            new_reviews.extend(reviews)
            if len(episodes) > batch_size:
                time.sleep(0.3)  # brief pause between batches for same season

        if not new_reviews:
            result["errors"].append(f"S{season['number']}: no reviews generated")
            continue

        # Merge: add new, fill gaps in existing entries with empty spoiler_free (never clobber good reviews)
        existing_map = {er["number"]: er for er in season.get("episode_reviews", [])}
        for nr in new_reviews:
            num = nr.get("number")
            if not num:
                continue
            if num not in existing_map:
                existing_map[num] = nr
                result["drafted"] += 1
            elif len((existing_map[num].get("spoiler_free") or "").strip()) <= 100:
                existing_map[num]["spoiler_free"] = nr.get("spoiler_free", "")
                existing_map[num]["the_moment"] = nr.get("the_moment")
                result["drafted"] += 1

        season["episode_reviews"] = sorted(existing_map.values(), key=lambda x: x.get("number", 0))
        modified = True

    if modified and not dry_run:
        d["date_modified"] = datetime.now().strftime("%Y-%m-%dT%H:%M:%S+05:30")
        path = DATA_DIR / f"{slug}.json"
        with open(path, "w") as f:
            json.dump(d, f, indent=2, ensure_ascii=False)
        _log(f"  {slug}: wrote {result['drafted']} new draft reviews")
    elif not modified:
        result["skipped"] = 1
        _log(f"  {slug}: already complete - skipped")

    return result


def main():
    parser = argparse.ArgumentParser(description="BollyAI NANO draft review generator")
    parser.add_argument("--slugs", nargs="+", help="Specific series slugs to process")
    parser.add_argument("--limit", type=int, default=50, help="Max series to process (default 50)")
    parser.add_argument("--workers", type=int, default=20, help="Parallel workers (default 20)")
    parser.add_argument("--dry-run", action="store_true", help="Count missing but don't call API")
    parser.add_argument("--tier", type=int, default=None, help="Only process tier 1-4 (by missing count)")
    args = parser.parse_args()

    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    _log(f"=== NANO DRAFT RUN START — {datetime.now().isoformat()} ===")

    if args.slugs:
        slugs = args.slugs
    else:
        slugs = HIGH_TRAFFIC_TARGETS

    # Filter to only those with missing episodes
    def has_missing(slug: str) -> bool:
        d = _load_series(slug)
        if not d:
            return False
        for s in d.get("seasons", []):
            if _get_missing_episodes(s):
                return True
        return False

    slugs = [s for s in slugs if has_missing(s)]
    _log(f"Slugs with missing episodes: {len(slugs)}")

    if args.tier:
        tier_bounds = {1: (0, 10), 2: (10, 25), 3: (25, 50), 4: (50, 9999)}
        lo, hi = tier_bounds.get(args.tier, (0, 9999))
        def in_tier(slug):
            d = _load_series(slug)
            if not d:
                return False
            total_missing = sum(len(_get_missing_episodes(s)) for s in d.get("seasons", []))
            return lo <= total_missing < hi
        slugs = [s for s in slugs if in_tier(s)]
        _log(f"After tier {args.tier} filter: {len(slugs)} slugs")

    slugs = slugs[:args.limit]
    _log(f"Processing {len(slugs)} series with {args.workers} workers")

    client = _get_client()

    total_drafted = 0
    total_errors = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as executor:
        futures = {
            executor.submit(process_series, slug, client, args.dry_run): slug
            for slug in slugs
        }
        for fut in concurrent.futures.as_completed(futures):
            slug = futures[fut]
            try:
                r = fut.result()
                total_drafted += r.get("drafted", 0)
                if r.get("errors"):
                    total_errors += 1
                    _log(f"  ERRORS in {slug}: {r['errors']}")
            except Exception as e:
                total_errors += 1
                _log(f"  EXCEPTION {slug}: {e}")

    _log(f"=== DONE: {total_drafted} drafts written, {total_errors} errors ===")

    if args.dry_run:
        print(f"\nDRY RUN: would generate ~{total_drafted} episode review drafts")
    else:
        print(f"\nDone: {total_drafted} draft reviews written across {len(slugs)} series")

    return 0 if total_errors == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
