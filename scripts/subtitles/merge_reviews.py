#!/usr/bin/env python3
"""merge_reviews.py — merge staged episode reviews into live series/film JSON.

Reads:  data/subtitles/<slug>/_reviews/episodes.json  (staging, never served)
Writes: data/series/<slug>.json  seasons[N].episode_reviews[]     (series path)
        data/films/<slug>.json   review                             (films path)

Gate: only entries carrying BOTH g3_pass AND voice_pass are eligible.
  g3_pass  = _judge.verdict == "pass"
  voice_pass = entry["voice_pass"] == True  (stamped by the G4 Opus voice-pass)

Default mode: DRY-RUN (prints plan, touches nothing).
--apply: writes and runs validate_series.py (series) or validate_films.py (films)
         on each touched file; rolls back on validator failure.
--force: overwrite episodes already present in the live JSON.

Usage:
  python3 merge_reviews.py <slug>                  # dry-run
  python3 merge_reviews.py <slug> --apply          # merge + validate
  python3 merge_reviews.py <slug> --apply --force  # overwrite existing
  python3 merge_reviews.py <slug> --film --apply   # film path
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SUBS_ROOT = REPO_ROOT / "data" / "subtitles"
SERIES_DIR = REPO_ROOT / "data" / "series"
FILMS_DIR = REPO_ROOT / "data" / "films"
VALIDATE_SERIES = REPO_ROOT / "scripts" / "batch" / "validate_series.py"
VALIDATE_FILMS = REPO_ROOT / "scripts" / "batch" / "validate_films.py"

IST = timezone(timedelta(hours=5, minutes=30))
EMDASH = ("—", "–", "―")

# Fields from staging that must NOT appear in the live JSON
_INTERNAL_FIELDS = {"_judge", "_writer", "_evidence", "_self_check", "voice_pass",
                    "g3_pass"}


def now_ist() -> str:
    return datetime.now(IST).isoformat(timespec="seconds")


def is_eligible(entry: dict) -> tuple[bool, str]:
    """Returns (eligible, reason). Both g3_pass AND voice_pass must be true."""
    j = entry.get("_judge") or {}
    g3_pass = j.get("verdict") == "pass"
    voice_pass = entry.get("voice_pass") is True
    if not g3_pass and not voice_pass:
        return False, "missing both g3_pass and voice_pass"
    if not g3_pass:
        return False, "g3_pass missing (_judge.verdict != 'pass')"
    if not voice_pass:
        return False, "voice_pass missing (G4 voice-pass not yet run)"
    return True, "ok"


def clean_for_publish(entry: dict) -> dict:
    """Strip staging internals; add merged_at."""
    out = {k: v for k, v in entry.items() if k not in _INTERNAL_FIELDS}
    out["merged_at"] = now_ist()
    return out


def ep_to_season_map(slug: str) -> dict[int, int]:
    """Build {episode_number: season_number} from dossier filenames (S01E03 -> {3: 1})."""
    ddir = SUBS_ROOT / slug / "_dossiers"
    mapping: dict[int, int] = {}
    if not ddir.exists():
        return mapping
    for p in sorted(ddir.glob("S*.json")):
        m = re.match(r"S(\d+)E(\d+)", p.stem, re.I)
        if m:
            snum, enum = int(m.group(1)), int(m.group(2))
            # Compound key mirrors draft_reviews.mmss_ep: S01 stays flat, S02+ = season*100+episode
            key = enum if snum == 1 else snum * 100 + enum
            mapping[key] = snum  # unique compound keys - no collision
    return mapping


def load_staging(slug: str) -> list[dict]:
    p = SUBS_ROOT / slug / "_reviews" / "episodes.json"
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))


def fence_check_prose(text: str) -> list[str]:
    """Minimal fence: no em-dash, no first-person viewing claim."""
    issues = []
    if any(d in (text or "") for d in EMDASH):
        issues.append("em/en-dash")
    if re.search(r"\b(I|we)\s+(watch|saw|watched|see)\b", text or "", re.I):
        issues.append("viewing-claim")
    return issues


def fence_check_review(entry: dict) -> list[str]:
    issues = []
    for field in ("spoiler_free", "the_moment"):
        issues += [f"{field}: {i}" for i in fence_check_prose(entry.get(field) or "")]
    if not (entry.get("spoiler_free") or "").strip():
        issues.append("spoiler_free empty")
    bm = entry.get("bollymeter")
    if bm is not None and not (isinstance(bm, (int, float)) and 0 <= bm <= 10):
        issues.append(f"bollymeter {bm!r} not 0-10 or null")
    cn = entry.get("critic_note")
    if cn is not None and not (cn.get("text") and cn.get("source") and cn.get("url")):
        issues.append("critic_note missing text/source/url")
    return issues


# ---------------------------------------------------------------------------
# Series merge path
# ---------------------------------------------------------------------------

def merge_series(slug: str, *, apply: bool, force: bool) -> int:
    staging = load_staging(slug)
    if not staging:
        print(f"[{slug}] no staging file at data/subtitles/{slug}/_reviews/episodes.json")
        return 1

    ep_season = ep_to_season_map(slug)

    eligible = []
    for entry in staging:
        ok, reason = is_eligible(entry)
        num = entry.get("number", "?")
        if ok:
            eligible.append(entry)
            print(f"  ELIGIBLE  ep {num}")
        else:
            print(f"  SKIP      ep {num}  ({reason})")

    if not eligible:
        print(f"[{slug}] 0 eligible reviews - nothing to merge")
        return 0

    series_path = SERIES_DIR / f"{slug}.json"
    if not series_path.exists():
        print(f"[{slug}] series JSON not found: {series_path}")
        return 1

    series = json.loads(series_path.read_text(encoding="utf-8"))
    seasons_by_num: dict[int, dict] = {s["number"]: s for s in series.get("seasons", [])}

    plan: list[tuple[int, int, int, dict]] = []  # (season_num, staging_num, ep_for_json, cleaned)
    for entry in eligible:
        staging_num = entry.get("number")
        if staging_num is None:
            print(f"  WARN  entry missing 'number', skipping")
            continue
        issues = fence_check_review(entry)
        if issues:
            print(f"  FENCE-FAIL  ep {staging_num}: {'; '.join(issues)}")
            continue
        season_num = ep_season.get(staging_num, 1)
        if season_num not in seasons_by_num:
            print(f"  WARN  ep {staging_num}: season {season_num} not in series JSON, defaulting to 1")
            season_num = 1
        if season_num not in seasons_by_num:
            print(f"  SKIP  ep {staging_num}: no matching season {season_num}")
            continue
        # Decode episode-within-season from compound staging number (S02E03 -> 203 -> ep 3)
        ep_for_json = staging_num % 100 if staging_num > 100 else staging_num
        existing_eps = {e["number"] for e in (seasons_by_num[season_num].get("episode_reviews") or [])}
        if ep_for_json in existing_eps and not force:
            print(f"  SKIP  ep {staging_num} (already in S{season_num} - use --force to overwrite)")
            continue
        cleaned = clean_for_publish(entry)
        cleaned["number"] = ep_for_json  # use episode-within-season, not compound staging number
        plan.append((season_num, staging_num, ep_for_json, cleaned))
        print(f"  PLAN  S{season_num}E{ep_for_json} -> seasons[{season_num}].episode_reviews")

    if not plan:
        print(f"[{slug}] nothing to merge after gates")
        return 0

    if not apply:
        print(f"\n[{slug}] DRY-RUN: {len(plan)} review(s) would merge. Pass --apply to write.")
        return 0

    # Apply: build updated seasons, write, validate, rollback on failure
    original_text = series_path.read_text(encoding="utf-8")
    try:
        for season_num, staging_num, ep_for_json, cleaned in plan:
            s = seasons_by_num[season_num]
            reviews = list(s.get("episode_reviews") or [])
            reviews = [e for e in reviews if e.get("number") != ep_for_json]  # remove old if force
            reviews.append(cleaned)
            reviews.sort(key=lambda e: e.get("number", 0))
            s["episode_reviews"] = reviews

        series["date_modified"] = now_ist()
        series_path.write_text(json.dumps(series, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{slug}] wrote {len(plan)} review(s) to {series_path}")
    except Exception as e:
        series_path.write_text(original_text, encoding="utf-8")
        print(f"[{slug}] ROLLBACK: write failed: {e}")
        return 1

    # Validate - pass full path so the script finds the file regardless of its SERIES_DIR
    r = subprocess.run([sys.executable, str(VALIDATE_SERIES), str(series_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        series_path.write_text(original_text, encoding="utf-8")
        print(f"[{slug}] ROLLBACK: validator failed:")
        print(r.stderr or r.stdout)
        return 1

    print(f"[{slug}] validate_series PASS")
    return 0


# ---------------------------------------------------------------------------
# Film merge path
# ---------------------------------------------------------------------------

def _find_film_path(slug: str) -> Path:
    """Films are keyed by QID filename; scan for the slug match.

    Raises SystemExit with a loud stderr message if not found — a missing
    film JSON is always a caller error, never a silent skip.
    """
    for p in FILMS_DIR.glob("*.json"):
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            if d.get("slug") == slug:
                return p
        except Exception:
            continue
    print(f"ERROR: no film JSON with slug={slug!r} found in {FILMS_DIR}", file=sys.stderr)
    print(f"  Staged film slugs must match a data/films/*.json 'slug' field exactly.", file=sys.stderr)
    print(f"  Run: python3 -c \"import json,pathlib; "
          f"[print(json.load(open(p)).get('slug')) for p in pathlib.Path('{FILMS_DIR}').glob('*.json')]\"",
          file=sys.stderr)
    raise SystemExit(2)


def merge_film(slug: str, *, apply: bool, force: bool) -> int:
    staging = load_staging(slug)
    if not staging:
        print(f"[{slug}] no staging file")
        return 1

    # Film corpus is a single-episode dossier; take the first eligible entry
    eligible_entries = [e for e in staging if is_eligible(e)[0]]

    skipped = [e for e in staging if not is_eligible(e)[0]]
    for e in skipped:
        _, reason = is_eligible(e)
        print(f"  SKIP      ep {e.get('number', '?')}  ({reason})")
    for e in eligible_entries:
        print(f"  ELIGIBLE  ep {e.get('number', '?')}")

    if not eligible_entries:
        print(f"[{slug}] 0 eligible reviews")
        return 0

    entry = eligible_entries[0]
    issues = fence_check_review(entry)
    if issues:
        print(f"[{slug}] FENCE-FAIL: {'; '.join(issues)}")
        return 1

    film_path = _find_film_path(slug)  # raises SystemExit(2) if not found

    film = json.loads(film_path.read_text(encoding="utf-8"))
    if film.get("review") and not force:
        print(f"[{slug}] review already present - use --force to overwrite")
        return 0

    cleaned = clean_for_publish(entry)
    # Films don't have episode_number semantics; strip the number field
    cleaned.pop("number", None)
    cleaned.pop("title", None)  # "Episode 1" is meaningless for a film

    print(f"  PLAN  {slug} -> film.review")
    if not apply:
        print(f"\n[{slug}] DRY-RUN: film review would merge. Pass --apply to write.")
        return 0

    original_text = film_path.read_text(encoding="utf-8")
    try:
        film["review"] = cleaned
        film["date_modified"] = now_ist()
        film_path.write_text(json.dumps(film, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[{slug}] wrote film review to {film_path}")
    except Exception as e:
        film_path.write_text(original_text, encoding="utf-8")
        print(f"[{slug}] ROLLBACK: write failed: {e}")
        return 1

    # Validate with validate_films.py (full fence, rollback on failure)
    r = subprocess.run([sys.executable, str(VALIDATE_FILMS), str(film_path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        film_path.write_text(original_text, encoding="utf-8")
        print(f"[{slug}] ROLLBACK: validate_films failed:")
        print(r.stderr or r.stdout)
        return 1
    print(f"[{slug}] validate_films PASS")

    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("slug", help="series or film slug")
    ap.add_argument("--apply", action="store_true",
                    help="write changes (default is dry-run)")
    ap.add_argument("--force", action="store_true",
                    help="overwrite episodes already present")
    ap.add_argument("--film", action="store_true",
                    help="use the film merge path (data/films/)")
    args = ap.parse_args()

    if args.film:
        return merge_film(args.slug, apply=args.apply, force=args.force)
    return merge_series(args.slug, apply=args.apply, force=args.force)


if __name__ == "__main__":
    sys.exit(main())
