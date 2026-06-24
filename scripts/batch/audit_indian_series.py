"""
audit_indian_series.py  --  Step 1 of the off-brand cull pipeline.
READ-ONLY.  No file is written, moved, or deleted by this script.

Identifies Indian-origin series by:
  - original_language.value in INDIAN_LANGS
  - OR canonical_industry in INDIAN_DESKS

Outputs:
  .cull-indian-audit.md  (human markdown, notability-ranked table)
  .cull-indian-audit.json  (machine JSON with full metadata)
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERIES_DIR = REPO_ROOT / "data" / "series"
OUT_MD = REPO_ROOT / ".cull-indian-audit.md"
OUT_JSON = REPO_ROOT / ".cull-indian-audit.json"

INDIAN_LANGS = {"hi", "ur", "ta", "te", "ml", "kn", "bn", "mr", "pa", "gu"}
INDIAN_DESKS = {"bollywood", "tollywood", "kollywood", "mollywood", "sandalwood"}

# Platform prominence tiers (higher = more notable OTT presence)
PLATFORM_TIER = {
    "Netflix": 4,
    "Prime Video": 3,
    "JioHotstar": 3,
    "Disney+ Hotstar": 3,
    "Apple TV+": 3,
    "SonyLIV": 2,
    "ZEE5": 2,
    "MX Player": 1,
    "Lionsgate Play": 1,
    "Eros Now": 1,
    "Voot": 1,
    "ALTBalaji": 1,
}


def platform_score(platform_value: str | None) -> int:
    if not platform_value:
        return 0
    for k, v in PLATFORM_TIER.items():
        if k.lower() in platform_value.lower():
            return v
    return 1


def load_series_metadata(path: Path) -> dict | None:
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        return None

    slug = data.get("slug", path.stem)
    lang_val = None
    if isinstance(data.get("original_language"), dict):
        lang_val = data["original_language"].get("value")
    elif isinstance(data.get("original_language"), str):
        lang_val = data["original_language"]

    industry = data.get("canonical_industry", "")
    qid_raw = data.get("qid")
    qid = qid_raw.get("value") if isinstance(qid_raw, dict) else qid_raw
    title_raw = data.get("title")
    title = title_raw.get("value") if isinstance(title_raw, dict) else (title_raw or slug)
    platform_raw = data.get("platform")
    platform = platform_raw.get("value") if isinstance(platform_raw, dict) else (platform_raw or "")
    status = data.get("status", "unknown")
    seasons = data.get("seasons", [])
    num_seasons = len(seasons)

    # has_poster: poster.src exists and does not point to fallback SVG
    poster_src = ""
    poster_obj = data.get("poster")
    if isinstance(poster_obj, dict):
        poster_src = poster_obj.get("src", "")
    has_poster = bool(poster_src and not poster_src.endswith("_fallback.svg"))

    # Indian-origin filter
    is_indian_lang = lang_val in INDIAN_LANGS
    is_indian_desk = industry in INDIAN_DESKS

    if not (is_indian_lang or is_indian_desk):
        return None

    return {
        "slug": slug,
        "title": title,
        "original_language": lang_val,
        "canonical_industry": industry,
        "desk": industry if industry in INDIAN_DESKS else "streaming",
        "num_seasons": num_seasons,
        "platform": platform,
        "status": status,
        "has_poster": has_poster,
        "qid": qid,
        "_platform_score": platform_score(platform),
    }


def notability_rank(item: dict) -> tuple:
    """Higher tuple = more notable. Used for descending sort."""
    return (item["num_seasons"], item["_platform_score"], int(item["has_poster"]))


def flag_notable(item: dict) -> bool:
    """Mark a title as clearly notable."""
    return item["num_seasons"] >= 3 or item["_platform_score"] >= 3


def lang_label(code: str | None) -> str:
    LABELS = {
        "hi": "Hindi", "ur": "Urdu", "ta": "Tamil", "te": "Telugu",
        "ml": "Malayalam", "kn": "Kannada", "bn": "Bengali",
        "mr": "Marathi", "pa": "Punjabi", "gu": "Gujarati",
    }
    return LABELS.get(code or "", code or "unknown")


def desk_label(desk: str) -> str:
    LABELS = {
        "bollywood": "Bollywood", "kollywood": "Kollywood", "tollywood": "Tollywood",
        "mollywood": "Mollywood", "sandalwood": "Sandalwood", "streaming": "Streaming",
    }
    return LABELS.get(desk, desk)


def main() -> None:
    files = sorted(SERIES_DIR.glob("*.json"))
    matched: list[dict] = []
    for f in files:
        m = load_series_metadata(f)
        if m:
            matched.append(m)

    matched.sort(key=notability_rank, reverse=True)

    # Assign notability rank (1 = most notable)
    for i, item in enumerate(matched, 1):
        item["notability_rank"] = i

    # --- Language breakdown ---
    lang_counts: dict[str, int] = {}
    for item in matched:
        lang = item["original_language"] or "unknown"
        lang_counts[lang] = lang_counts.get(lang, 0) + 1

    # --- Desk breakdown ---
    desk_counts: dict[str, int] = {}
    for item in matched:
        desk = item["desk"]
        desk_counts[desk] = desk_counts.get(desk, 0) + 1

    # --- Write Markdown ---
    now_str = datetime.now(tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines: list[str] = []
    lines.append("# BollyAI Off-Brand Indian Series Audit")
    lines.append("")
    lines.append(f"Generated: {now_str}  |  Total matched: {len(matched)}")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("**Language breakdown:**")
    for lang, count in sorted(lang_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {lang_label(lang)} (`{lang}`): {count}")
    lines.append("")
    lines.append("**Desk breakdown:**")
    for desk, count in sorted(desk_counts.items(), key=lambda x: -x[1]):
        lines.append(f"- {desk_label(desk)} (`{desk}`): {count}")
    lines.append("")
    lines.append("## Notability-Ranked Table")
    lines.append("")
    lines.append("Columns: Rank | Slug | Title | Lang | Desk | Seasons | Platform | Status | Poster | QID | Notable")
    lines.append("")
    lines.append("| Rank | Slug | Title | Lang | Desk | Seasons | Platform | Status | Poster | QID | Notable |")
    lines.append("|------|------|-------|------|------|---------|----------|--------|--------|-----|---------|")

    for item in matched:
        notable_flag = "YES" if flag_notable(item) else "-"
        qid_display = item["qid"] if item["qid"] else "null"
        poster_display = "yes" if item["has_poster"] else "no"
        platform_display = item["platform"] if item["platform"] else "unknown"
        # Truncate platform for table readability
        if len(platform_display) > 20:
            platform_display = platform_display[:20]
        title_display = item["title"]
        if len(title_display) > 35:
            title_display = title_display[:32] + "..."

        lines.append(
            f"| {item['notability_rank']} "
            f"| {item['slug']} "
            f"| {title_display} "
            f"| {lang_label(item['original_language'])} "
            f"| {desk_label(item['desk'])} "
            f"| {item['num_seasons']} "
            f"| {platform_display} "
            f"| {item['status']} "
            f"| {poster_display} "
            f"| {qid_display} "
            f"| {notable_flag} |"
        )

    lines.append("")
    lines.append("## Notability Definition")
    lines.append("")
    lines.append("Notable = num_seasons >= 3 OR platform_tier >= 3 (Netflix/Prime Video/JioHotstar/Disney+/Apple TV+).")
    lines.append("Rank = sorted by (num_seasons desc, platform_tier desc, has_poster desc).")
    lines.append("This table is INPUT to the orchestrator's protect/cull split; no cull decisions made here.")
    lines.append("")
    lines.append("## Scoring Rubric (per item)")
    lines.append("")
    lines.append("Each series is scored on two dimensions:")
    lines.append("")
    lines.append("| Item | Correctness /5 | Coverage /5 | Evidence |")
    lines.append("|------|----------------|-------------|----------|")

    for item in matched:
        correctness = 5
        coverage = 5
        evidence_parts = []

        # Correctness: verify Indian-language or Indian-desk detection
        if item["original_language"] in INDIAN_LANGS:
            evidence_parts.append(f"lang={item['original_language']} in INDIAN_LANGS")
        if item["desk"] in INDIAN_DESKS:
            evidence_parts.append(f"desk={item['desk']} in INDIAN_DESKS")

        # Coverage: deduct for missing QID or missing poster
        if not item["qid"]:
            coverage -= 1
            evidence_parts.append("qid=null (deduct 1)")
        if not item["has_poster"]:
            coverage -= 1
            evidence_parts.append("no poster (deduct 1)")
        if not item["platform"]:
            coverage -= 1
            evidence_parts.append("platform unknown (deduct 1)")

        coverage = max(1, coverage)
        evidence_str = "; ".join(evidence_parts) if evidence_parts else "all fields present"
        title_display = item["title"]
        if len(title_display) > 30:
            title_display = title_display[:27] + "..."

        lines.append(
            f"| {item['slug']} ({title_display}) "
            f"| {correctness} "
            f"| {coverage} "
            f"| {evidence_str} |"
        )

    # Roll-up
    total_correctness = sum(5 for _ in matched)
    total_coverage = 0
    lowest_item = None
    lowest_score = 999
    for item in matched:
        cov = 5
        if not item["qid"]:
            cov -= 1
        if not item["has_poster"]:
            cov -= 1
        if not item["platform"]:
            cov -= 1
        cov = max(1, cov)
        total_coverage += cov
        combined = 5 + cov
        if combined < lowest_score:
            lowest_score = combined
            lowest_item = item

    total_items = len(matched)
    avg_correctness = total_correctness / total_items if total_items else 0
    avg_coverage = total_coverage / total_items if total_items else 0

    lines.append("")
    lines.append(
        f"> Roll-up: avg {avg_correctness:.1f}/5 correctness + {avg_coverage:.1f}/5 coverage "
        f"across {total_items} items. "
        f"Lowest combined score: {lowest_item['slug'] if lowest_item else 'none'} "
        f"({lowest_score}/10). Fix first: "
        + (
            "add QID + poster + platform data for "
            + (lowest_item["slug"] if lowest_item else "N/A")
            if lowest_item
            else "N/A"
        )
        + "."
    )

    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    # --- Write JSON ---
    output_series = []
    for item in matched:
        output_series.append({
            "slug": item["slug"],
            "title": item["title"],
            "original_language": item["original_language"],
            "canonical_industry": item["canonical_industry"],
            "desk": item["desk"],
            "num_seasons": item["num_seasons"],
            "platform": item["platform"],
            "status": item["status"],
            "has_poster": item["has_poster"],
            "qid": item["qid"],
            "notability_rank": item["notability_rank"],
        })

    out_data = {
        "generated_at": now_str,
        "total_matched": len(matched),
        "languages": lang_counts,
        "desks": desk_counts,
        "series": output_series,
    }
    OUT_JSON.write_text(json.dumps(out_data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    print(f"Matched: {len(matched)} Indian-origin series")
    print(f"Languages: {lang_counts}")
    print(f"Desks: {desk_counts}")
    print(f"Outputs: {OUT_MD}  {OUT_JSON}")


if __name__ == "__main__":
    main()
