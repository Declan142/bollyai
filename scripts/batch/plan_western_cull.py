"""
plan_western_cull.py  --  DRY analysis for the "full Western" brand cull.

Classifies data/series/*.json into KEEP (Western allowlist) vs CULL (non-Western),
and reports the dependent blast radius (endings/explainers/episodes/dna/img dirs)
plus list classification. NO file moves. Pure report -> validates the taxonomy
before the mover runs.

Western KEEP allowlist = English + European + (debatable) Latin-American Spanish/Portuguese.
CULL = everything else (Korean, Japanese, Chinese, Thai, Hebrew, Turkish, Arabic, Indian, ...).
"""
from __future__ import annotations
import json, glob, os, collections
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SERIES = REPO / "data" / "series"

# Western languages we KEEP. Allowlist by design (denylist is what let "Hindi"/ko/ja through).
WESTERN_KEEP = {
    "en", "English",           # anglophone core
    "es", "de", "fr", "it",    # major Western European
    "sv", "da", "no", "nb", "nn", "fi", "is",  # Nordic
    "pl", "cs", "sk", "hu", "ro", "el",        # Central/Eastern + Greek (European)
    "nl", "ca", "pt", "gl", "lb", "yi", "ga",  # Dutch/Iberian/misc European
}

def lang_of(d):
    ol = d.get("original_language")
    if isinstance(ol, dict):
        ol = ol.get("value")
    return ol or "??"

def dep_exists(slug):
    deps = {}
    for sub in ("endings", "explainers", "episodes", "series-dna"):
        p = REPO / "data" / sub / f"{slug}.json"
        if p.exists():
            deps[sub] = 1
    img = REPO / "site" / "public" / "img" / "series" / slug
    if img.is_dir():
        deps["img"] = 1
    sub_dir = REPO / "data" / "subtitles" / slug
    if sub_dir.exists():
        deps["subtitles"] = 1
    return deps

def main():
    keep, cull = [], []
    cull_langs = collections.Counter()
    keep_langs = collections.Counter()
    dep_tally = collections.Counter()
    cull_slugs = set()

    for f in sorted(glob.glob(str(SERIES / "*.json"))):
        d = json.load(open(f))
        slug = os.path.basename(f)[:-5]
        lang = lang_of(d)
        if lang in WESTERN_KEEP:
            keep.append(slug); keep_langs[lang] += 1
        else:
            cull.append(slug); cull_langs[lang] += 1; cull_slugs.add(slug)

    # dependent blast radius for cull set
    for slug in cull:
        for k in dep_exists(slug):
            dep_tally[k] += 1

    print(f"=== SERIES: keep={len(keep)}  cull={len(cull)}  total={len(keep)+len(cull)} ===")
    print("CULL by language:", dict(cull_langs.most_common()))
    print("KEEP by language:", dict(keep_langs.most_common()))
    print("\n=== DEPENDENT BLAST RADIUS (files to archive alongside) ===")
    for k, v in dep_tally.most_common():
        print(f"  {k}: {v}")

    # list classification: a list is off-brand if its name flags it OR most of its items are culled
    print("\n=== LISTS (data/recommendations) ===")
    rec_dir = REPO / "data" / "recommendations"
    OFFBRAND_NAME = ("anime", "kdrama", "korean", "-india", "squid-game")
    for f in sorted(glob.glob(str(rec_dir / "*.json"))):
        name = os.path.basename(f)[:-5]
        d = json.load(open(f))
        items = d.get("items") or d.get("entries") or d.get("series") or []
        slugs = []
        for it in items:
            s = it.get("slug") if isinstance(it, dict) else (it if isinstance(it, str) else None)
            if s:
                slugs.append(s)
        culled_in = sum(1 for s in slugs if s in cull_slugs)
        n = len(slugs)
        name_flag = any(tok in name for tok in OFFBRAND_NAME)
        frac = (culled_in / n) if n else 0
        verdict = "ARCHIVE(name)" if name_flag else ("ARCHIVE(thin)" if n and frac >= 0.5 else f"CLEAN drop {culled_in}/{n}")
        print(f"  {name}: items={n} culled_refs={culled_in} -> {verdict}")

    # write the cull slug list for the mover
    out = REPO / "scripts" / "batch" / ".western-cull-list.json"
    json.dump({"cull": cull, "keep_count": len(keep)}, open(out, "w"), indent=0)
    print(f"\nWrote cull list ({len(cull)} slugs) -> {out.relative_to(REPO)}")

if __name__ == "__main__":
    main()
