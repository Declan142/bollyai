#!/usr/bin/env python3
"""Safe mechanical auto-fix for BollyAI series JSON.

Only touches STRING LEAVES (never structure), so it can never corrupt JSON:
  * replaces em/en/bar-dash with a spaced hyphen ' - '
  * collapses the double-spaces a replacement can create
Re-dumps indent=2, UTF-8. Viewing-claims and schema errors are NOT auto-fixable
here by design - validate_series.py hard-fails those for human/agent rework.

Usage: fix_series.py <slug|path> [<slug|path> ...]
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

SERIES_DIR = Path("/home/aditya/bollyai/data/series")
DASHES = {"—": " - ", "–": " - ", "―": " - "}

_dirty = False


def fix_str(s: str) -> str:
    global _dirty
    out = s
    for d, r in DASHES.items():
        out = out.replace(d, r)
    while "  " in out:
        out = out.replace("  ", " ")
    if out != s:
        _dirty = True
    return out


def walk(node):
    if isinstance(node, str):
        return fix_str(node)
    if isinstance(node, dict):
        return {k: walk(v) for k, v in node.items()}
    if isinstance(node, list):
        return [walk(v) for v in node]
    return node


def main() -> int:
    global _dirty
    changed = 0
    for a in sys.argv[1:]:
        p = Path(a)
        if p.suffix != ".json":
            p = SERIES_DIR / f"{a}.json"
        if not p.exists():
            print(f"skip {p.stem}: not found")
            continue
        _dirty = False
        fixed = walk(json.loads(p.read_text(encoding="utf-8")))
        # Only rewrite when an actual dash/space replacement happened, so clean
        # files are never reformatted (no churn).
        if _dirty:
            p.write_text(json.dumps(fixed, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"fixed {p.stem}")
            changed += 1
    print(f"{changed} files changed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
