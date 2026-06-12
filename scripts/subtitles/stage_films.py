#!/usr/bin/env python3
"""stage_films.py — stage each film SRT from ~/bollyai-subs/films/ as its own
single-episode corpus: data/subtitles/<film-slug>/<film-slug>.srt
(Stage B uses the filename stem as ep_id; crosspass auto-skips <3 eps.)

Usage: python3 stage_films.py [all|<film-slug>]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

FILMS = Path.home() / "bollyai-subs" / "films"
ROOT = Path.home() / "bollyai" / "data" / "subtitles"
HERE = Path(__file__).parent

# scene name -> (slug, quote_lang). en-sub = translated subtitle rendering.
KNOWN = {
    "maharaja": ("maharaja-2024", "en-sub"),
    "jawan": ("jawan", "en-sub"),
    "manjummel": ("manjummel-boys", "en-sub"),
    "inception": ("inception", "en"),
}


def film_slug(fname: str) -> tuple[str, str]:
    low = fname.lower()
    for key, (slug, ql) in KNOWN.items():
        if key in low:
            return slug, ql
    # generic: Title.Year from scene name
    m = re.match(r"^(.+?)\.((?:19|20)\d{2})\.", fname)
    base = m.group(1) if m else fname.rsplit(".", 1)[0]
    slug = re.sub(r"[^a-z0-9]+", "-", base.lower()).strip("-")
    return slug, "en-sub"


def main() -> int:
    want = sys.argv[1] if len(sys.argv) > 1 else "all"
    staged = []
    for srt in sorted(FILMS.glob("*.srt")):
        slug, ql = film_slug(srt.name)
        if want not in ("all", slug):
            continue
        dst = ROOT / slug
        dst.mkdir(parents=True, exist_ok=True)
        tgt = dst / f"{slug}.srt"
        if not tgt.exists():
            shutil.copy2(srt, tgt)
        (dst / "quote_lang.txt").write_text(ql)
        r = subprocess.run([sys.executable, str(HERE / "subtitle_stats.py"), slug],
                           capture_output=True, text=True)
        ok = r.returncode == 0
        print(f"{'OK' if ok else 'FAIL'} {slug} ({ql})")
        if ok:
            staged.append(slug)
    print(json.dumps({"staged": staged}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
