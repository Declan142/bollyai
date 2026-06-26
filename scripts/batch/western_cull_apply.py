"""
western_cull_apply.py  --  "Full Western" brand cull. REVERSIBLE (git-mv only, never rm).

Archives every non-Western series + its dependents (endings / img dir / subtitles),
archives off-brand lists, and strips culled picks from kept lists.

Dry-run by default. Pass --apply to perform git-mv + list edits.
Reverse: git-mv data/_archive/non-western/<lang>/<slug>.json data/series/<slug>.json (etc.)

Usage:
  python3 scripts/batch/western_cull_apply.py --cull-list scripts/batch/.western-cull-list.json [--apply]
"""
from __future__ import annotations
import argparse, json, subprocess, sys, glob, os
from pathlib import Path
from collections import Counter

REPO = Path(__file__).resolve().parents[2]
SERIES = REPO / "data" / "series"
ARCH = REPO / "data" / "_archive"
OFFBRAND_LIST_TOKENS = ("anime", "kdrama", "korean", "-india", "squid-game")

def gitmv(src: Path, dst: Path, apply: bool):
    if not src.exists():
        return False
    dst.parent.mkdir(parents=True, exist_ok=True) if apply else None
    if not apply:
        return True
    r = subprocess.run(["git", "mv", str(src), str(dst)], cwd=REPO, capture_output=True, text=True)
    if r.returncode != 0:
        # fall back to plain move + git add for already-untracked edge cases
        print(f"  ERR git mv {src.name}: {r.stderr.strip()}", file=sys.stderr)
        return False
    return True

def lang_of(d):
    ol = d.get("original_language")
    return (ol.get("value") if isinstance(ol, dict) else ol) or "xx"

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cull-list", required=True)
    ap.add_argument("--apply", action="store_true", default=False)
    args = ap.parse_args()
    apply = args.apply
    cull = json.load(open(args.cull_list))["cull"]
    cull_set = set(cull)

    tally = Counter()
    lang_buckets = {"ko": "korean", "ja": "japanese", "Hindi": "indian", "hi": "indian"}

    # 1. series + dependents
    for slug in cull:
        sf = SERIES / f"{slug}.json"
        if not sf.exists():
            tally["series_missing"] += 1
            continue
        lang = lang_of(json.load(open(sf)))
        bucket = lang_buckets.get(lang, "foreign")
        if gitmv(sf, ARCH / "non-western" / bucket / f"{slug}.json", apply):
            tally["series"] += 1
        if gitmv(REPO / "data" / "endings" / f"{slug}.json", ARCH / "non-western-endings" / f"{slug}.json", apply):
            tally["endings"] += 1
        if gitmv(REPO / "site" / "public" / "img" / "series" / slug, ARCH / "non-western-img" / slug, apply):
            tally["img_dirs"] += 1
        if gitmv(REPO / "data" / "subtitles" / slug, ARCH / "non-western-subtitles" / slug, apply):
            tally["subtitle_dirs"] += 1

    # 2. lists: archive off-brand by name; strip culled picks from the rest
    for f in sorted(glob.glob(str(REPO / "data" / "recommendations" / "*.json"))):
        name = os.path.basename(f)[:-5]
        if any(t in name for t in OFFBRAND_LIST_TOKENS):
            if gitmv(Path(f), ARCH / "non-western-lists" / f"{name}.json", apply):
                tally["lists_archived"] += 1
            continue
        d = json.load(open(f))
        picks = d.get("picks", [])
        kept = [p for p in picks if not (isinstance(p, dict) and p.get("slug") in cull_set)]
        if len(kept) != len(picks):
            tally["lists_cleaned"] += 1
            tally["picks_dropped"] += len(picks) - len(kept)
            if apply:
                d["picks"] = kept
                json.dump(d, open(f, "w"), ensure_ascii=False, indent=2)
                open(f, "a").write("\n")

    mode = "APPLIED" if apply else "DRY-RUN"
    print(f"=== {mode} ===")
    for k, v in tally.most_common():
        print(f"  {k}: {v}")
    if not apply:
        print("\nPass --apply to execute.")

if __name__ == "__main__":
    main()
