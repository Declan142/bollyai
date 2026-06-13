#!/usr/bin/env python3
"""
build_blitz_queue.py — bolly-audit P1
Scans all 555 series JSON files, computes per-season/episode coverage + quality flags,
ranks by popularity proxy, outputs data/_state/blitz-queue.json.
"""
import json
import os
import re
import sys
from pathlib import Path

SERIES_DIR = Path(__file__).parent.parent.parent / "data" / "series"
STATE_DIR = Path(__file__).parent.parent.parent / "data" / "_state"
OUT_PATH = STATE_DIR / "blitz-queue.json"

# ── Popularity proxy weights ──────────────────────────────────────────────────

PLATFORM_SCORE = {
    "Netflix": 10,
    "Prime Video": 9,
    "Amazon Prime Video": 9,
    "Disney+": 8,
    "Disney+ Hotstar": 8,
    "Hotstar": 8,
    "Apple TV+": 8,
    "Max": 8,
    "HBO": 8,
    "JioCinema": 7,
    "SonyLIV": 7,
    "Peacock": 6,
    "Paramount+": 6,
    "Hulu": 6,
    "ZEE5": 5,
    "MX Player": 5,
    "Voot": 5,
    "AltBalaji": 4,
    "Lionsgate Play": 4,
    "AMC+": 4,
    "Crunchyroll": 5,
    "Funimation": 4,
}

ORIGIN_BOOST = {
    "India": 3,
    "South Korea": 2,
    "United States": 1,
    "UK": 1,
    "United Kingdom": 1,
    "Japan": 1,
    "Spain": 1,
    "France": 1,
    "Germany": 1,
    "Italy": 1,
    "Israel": 1,
    "Turkey": 1,
    "Denmark": 1,
    "Brazil": 1,
    "Mexico": 1,
    "Colombia": 1,
    "Sweden": 1,
    "Norway": 1,
    "Australia": 1,
}

# High-traffic genre bonus
HIGH_TRAFFIC_GENRES = {
    "Thriller", "Crime", "Action", "Mystery", "Drama", "Horror",
    "Sci-Fi", "Science Fiction", "Fantasy", "Romance", "Comedy",
    "Superhero", "Spy", "Legal Drama", "Medical Drama", "Historical",
    "Survival", "Dark Comedy", "True Crime", "Political Drama",
}

# Review quality thresholds
REVIEW_BODY_MIN_LEN = 400
REVIEW_BODY_GOOD_LEN = 600
VOICE_PASS_MIN_LEN = 500

# Known high-traffic titles (manual boost list based on global impact)
TIER_1_TITLES = {
    "squid-game", "breaking-bad", "better-call-saul", "game-of-thrones",
    "house-of-the-dragon", "the-last-of-us", "stranger-things", "ozark",
    "narcos", "money-heist", "dark", "mindhunter", "the-crown",
    "succession", "the-bear", "white-lotus", "euphoria", "the-witcher",
    "wednesday", "you", "emily-in-paris", "bridgerton", "peaky-blinders",
    "the-boys", "invincible", "loki", "wanda-vision", "wandavision",
    "ted-lasso", "abbott-elementary", "schitts-creek", "fleabag",
    "the-office", "friends", "seinfeld", "arrested-development",
    "sacred-games", "mirzapur", "scam-1992", "delhi-crime", "panchayat",
    "family-man", "pataal-lok", "maharani", "aarya", "apharan",
    "the-wire", "the-sopranos", "mad-men", "the-west-wing",
    "black-mirror", "band-of-brothers", "chernobyl", "true-detective",
    "fargo", "westworld", "altered-carbon", "blade-runner-2049",
    "squid-game-the-challenge", "physical-100", "parasite",
    "attack-on-titan", "demon-slayer", "fullmetal-alchemist-brotherhood",
    "one-piece", "jujutsu-kaisen", "my-hero-academia", "death-note",
    "vinland-saga", "spy-x-family", "blue-lock", "chainsaw-man",
    "kingdom", "all-of-us-are-dead", "sweet-home", "my-mister",
    "crash-landing-on-you", "its-okay-to-not-be-okay", "vincenzo",
    "the-glory", "moving", "mask-girl", "my-name", "hellbound",
    "juvenile-justice", "little-women-2022", "my-liberation-notes",
    "under-the-queen-s-umbrella", "twenty-five-twenty-one",
    "adolescence", "beef", "daisy-jones-and-the-six", "the-diplomat",
    "firefly-lane", "maid", "inventing-anna", "the-dropout",
    "nobody-wants-this", "the-studio", "mr-and-mrs-smith",
}

TIER_1_BOOST = 4
TIER_2_BOOST = 2


def platform_score(series: dict) -> int:
    plat = series.get("platform", {})
    if isinstance(plat, dict):
        plat = plat.get("value", "")
    return PLATFORM_SCORE.get(plat, 3)


def origin_boost(series: dict) -> int:
    origin = series.get("origin", "")
    return ORIGIN_BOOST.get(origin, 0)


def genre_boost(series: dict) -> float:
    genres = series.get("genres", [])
    matches = len(HIGH_TRAFFIC_GENRES & set(genres))
    return min(matches * 0.5, 2.0)


def tier_boost(slug: str) -> int:
    if slug in TIER_1_TITLES:
        return TIER_1_BOOST
    return 0


def status_boost(series: dict) -> int:
    status = series.get("status", "")
    if status in ("ongoing", "returning"):
        return 1
    return 0


def seasons_count_boost(seasons: list) -> float:
    n = len(seasons)
    if n >= 5:
        return 2.0
    elif n >= 3:
        return 1.0
    elif n >= 2:
        return 0.5
    return 0.0


def popularity_score(slug: str, series: dict) -> float:
    seasons = series.get("seasons", [])
    return (
        platform_score(series)
        + origin_boost(series)
        + genre_boost(series)
        + tier_boost(slug)
        + status_boost(series)
        + seasons_count_boost(seasons)
    )


# ── Quality flag helpers ──────────────────────────────────────────────────────

def check_voice_pass(text: str) -> bool:
    """Heuristic: review passes voice bar if long enough and contains vivid language."""
    if len(text) < VOICE_PASS_MIN_LEN:
        return False
    # Penalize flat/generic openers
    flat_openers = [
        "the series follows", "the show follows", "this series is about",
        "is a television series", "premiered on", "this show is"
    ]
    text_lower = text.lower()
    flat_count = sum(1 for p in flat_openers if p in text_lower)
    return flat_count == 0


def audit_season(season: dict, season_num: int) -> dict:
    review_body = season.get("review_body", "") or ""
    bollymeter = season.get("bollymeter")
    critic = season.get("critic", {}) or {}
    pull_quotes = critic.get("pull_quotes", []) or []
    episode_reviews = season.get("episode_reviews", []) or []
    total_eps = season.get("episodes", 0) or 0

    ep_reviewed = len(episode_reviews)
    ep_coverage_pct = round(ep_reviewed / total_eps, 2) if total_eps > 0 else 0.0

    review_len = len(review_body)
    has_review = review_len > 0
    review_ok = review_len >= REVIEW_BODY_MIN_LEN
    review_good = review_len >= REVIEW_BODY_GOOD_LEN
    has_bollymeter = bollymeter is not None
    has_pull_quotes = len(pull_quotes) > 0
    voice_pass = check_voice_pass(review_body)

    # Episode-level audit
    ep_audit = []
    for ep in episode_reviews:
        ep_num = ep.get("number")
        ep_title = ep.get("title", "")
        ep_spoiler_free = ep.get("spoiler_free", "") or ""
        ep_bollymeter = ep.get("bollymeter")
        ep_moment = ep.get("the_moment", "") or ""
        ep_critic_note = ep.get("critic_note")

        ep_len = len(ep_spoiler_free)
        ep_voice_pass = check_voice_pass(ep_spoiler_free)

        ep_audit.append({
            "number": ep_num,
            "title": ep_title,
            "review_len": ep_len,
            "has_bollymeter": ep_bollymeter is not None,
            "has_the_moment": len(ep_moment) > 0,
            "has_critic_note": ep_critic_note is not None,
            "voice_pass": ep_voice_pass,
        })

    # Missing episodes (episodes that should exist but have no review)
    reviewed_ep_nums = {e.get("number") for e in episode_reviews}
    missing_eps = sorted(set(range(1, total_eps + 1)) - reviewed_ep_nums)

    # Quality score for this season (0-10)
    q = 0
    if has_review:
        q += 1
    if review_ok:
        q += 1
    if review_good:
        q += 1
    if has_bollymeter:
        q += 2
    if has_pull_quotes:
        q += 1
    if voice_pass:
        q += 1
    if ep_coverage_pct >= 0.5:
        q += 1
    if ep_coverage_pct >= 0.8:
        q += 1
    # Check if pilot + finale are covered
    if total_eps > 0:
        has_pilot = 1 in reviewed_ep_nums
        has_finale = total_eps in reviewed_ep_nums
        if has_pilot and has_finale:
            q += 1

    # Deficiencies list (what's needed for perfection)
    deficiencies = []
    if not has_review:
        deficiencies.append("NO_REVIEW_BODY")
    elif not review_ok:
        deficiencies.append(f"REVIEW_TOO_SHORT:{review_len}chars")
    elif not review_good:
        deficiencies.append(f"REVIEW_THIN:{review_len}chars")
    if not has_bollymeter:
        deficiencies.append("NO_BOLLYMETER")
    if not has_pull_quotes:
        deficiencies.append("NO_PULL_QUOTES")
    if not voice_pass and has_review:
        deficiencies.append("VOICE_FLAT")
    if ep_coverage_pct < 0.5 and total_eps > 0:
        deficiencies.append(f"EP_COVERAGE_LOW:{ep_reviewed}/{total_eps}")
    elif ep_coverage_pct < 1.0 and total_eps > 0:
        deficiencies.append(f"EP_COVERAGE_PARTIAL:{ep_reviewed}/{total_eps}")
    if total_eps > 0 and 1 not in reviewed_ep_nums:
        deficiencies.append("MISSING_PILOT_REVIEW")
    if total_eps > 0 and total_eps not in reviewed_ep_nums:
        deficiencies.append("MISSING_FINALE_REVIEW")

    return {
        "season": season_num,
        "year": season.get("year"),
        "total_eps": total_eps,
        "ep_reviewed": ep_reviewed,
        "ep_coverage_pct": ep_coverage_pct,
        "missing_ep_numbers": missing_eps,
        "review_len": review_len,
        "review_ok": review_ok,
        "review_good": review_good,
        "has_bollymeter": has_bollymeter,
        "has_pull_quotes": has_pull_quotes,
        "voice_pass": voice_pass,
        "quality_score": q,
        "deficiencies": deficiencies,
        "ep_audit": ep_audit,
    }


def audit_series(slug: str, series: dict) -> dict:
    seasons = series.get("seasons", [])
    title = series.get("title", {})
    if isinstance(title, dict):
        title = title.get("value", slug)

    platform = series.get("platform", {})
    if isinstance(platform, dict):
        platform = platform.get("value", "")

    season_audits = [audit_season(s, s.get("number", i + 1)) for i, s in enumerate(seasons)]

    total_eps_expected = sum(a["total_eps"] for a in season_audits)
    total_eps_reviewed = sum(a["ep_reviewed"] for a in season_audits)
    total_ep_coverage = round(total_eps_reviewed / total_eps_expected, 2) if total_eps_expected > 0 else 0.0

    # Series-level quality aggregate
    season_qs = [a["quality_score"] for a in season_audits]
    avg_season_quality = round(sum(season_qs) / len(season_qs), 1) if season_qs else 0.0

    # Series-level deficiencies (flatten unique)
    all_deficiencies = []
    for sa in season_audits:
        for d in sa["deficiencies"]:
            entry = f"S{sa['season']}: {d}"
            all_deficiencies.append(entry)

    # Completeness gap score (how far from perfect, higher = more work needed)
    gap = 10 - avg_season_quality

    # Popularity / traffic proxy
    pop = popularity_score(slug, series)

    # Priority = popularity * (1 + gap/10) — high pop AND high gap = highest priority
    priority = round(pop * (1 + gap / 10), 2)

    # Work type classification
    work_types = set()
    for sa in season_audits:
        for d in sa["deficiencies"]:
            if "REVIEW" in d or "VOICE" in d or "BOLLYMETER" in d or "PULL_QUOTES" in d:
                work_types.add("season_review")
            if "EP_" in d or "PILOT" in d or "FINALE" in d:
                work_types.add("episode_reviews")

    return {
        "slug": slug,
        "title": title,
        "platform": platform,
        "origin": series.get("origin", ""),
        "status": series.get("status", ""),
        "genres": series.get("genres", []),
        "season_count": len(seasons),
        "total_eps_expected": total_eps_expected,
        "total_eps_reviewed": total_eps_reviewed,
        "total_ep_coverage_pct": total_ep_coverage,
        "avg_season_quality": avg_season_quality,
        "popularity_score": pop,
        "completeness_gap": round(gap, 1),
        "priority_score": priority,
        "work_types": sorted(work_types),
        "deficiencies": all_deficiencies,
        "seasons": season_audits,
    }


def build_queue():
    entries = []
    errors = []

    series_files = sorted(SERIES_DIR.glob("*.json"))
    total = len(series_files)
    print(f"Auditing {total} series files...", flush=True)

    for i, path in enumerate(series_files):
        slug = path.stem
        # Skip backup files
        if ".bak" in slug or slug.startswith("."):
            continue
        try:
            with open(path) as f:
                data = json.load(f)
            entry = audit_series(slug, data)
            entries.append(entry)
        except Exception as e:
            errors.append({"slug": slug, "error": str(e)})

        if (i + 1) % 50 == 0:
            print(f"  {i+1}/{total}...", flush=True)

    # Sort by priority (desc)
    entries.sort(key=lambda x: x["priority_score"], reverse=True)

    # Add rank
    for i, e in enumerate(entries):
        e["rank"] = i + 1

    # Summary stats
    perfect = sum(1 for e in entries if e["avg_season_quality"] >= 9.0)
    needs_ep_reviews = sum(1 for e in entries if "episode_reviews" in e["work_types"])
    needs_season_review = sum(1 for e in entries if "season_review" in e["work_types"])
    no_deficiencies = sum(1 for e in entries if not e["deficiencies"])

    output = {
        "generated_at": "2026-06-13T00:00:00+05:30",
        "total_series": len(entries),
        "errors": errors,
        "summary": {
            "perfect_series": perfect,
            "needs_season_review": needs_season_review,
            "needs_ep_reviews": needs_ep_reviews,
            "no_deficiencies": no_deficiencies,
            "avg_quality_all": round(
                sum(e["avg_season_quality"] for e in entries) / len(entries), 2
            ) if entries else 0,
            "total_eps_expected": sum(e["total_eps_expected"] for e in entries),
            "total_eps_reviewed": sum(e["total_eps_reviewed"] for e in entries),
        },
        "queue": entries,
    }

    with open(OUT_PATH, "w") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    return output


if __name__ == "__main__":
    result = build_queue()
    s = result["summary"]
    print(f"\nDone. {result['total_series']} series audited.")
    print(f"  Perfect (q>=9): {s['perfect_series']}")
    print(f"  Needs season review upgrade: {s['needs_season_review']}")
    print(f"  Needs episode reviews: {s['needs_ep_reviews']}")
    print(f"  No deficiencies: {s['no_deficiencies']}")
    print(f"  Avg quality: {s['avg_quality_all']}/10")
    print(f"  Total eps expected: {s['total_eps_expected']} | reviewed: {s['total_eps_reviewed']}")
    print(f"  Errors: {len(result['errors'])}")
    if result["errors"]:
        for e in result["errors"][:5]:
            print(f"    {e['slug']}: {e['error']}")
    print(f"\nWritten to {OUT_PATH}")
