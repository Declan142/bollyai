"""
archive_offbrand_series.py  --  Phase-2 archive step for the off-brand cull pipeline.

REVERSIBLE: git-mv's culled slugs from data/series/ to data/_archive/indian/.
NEVER deletes files.

Usage:
  python3 scripts/batch/archive_offbrand_series.py --cull-list .cull-list.json [--apply]

  --cull-list   Path to JSON file: {"cull": ["slug-a", "slug-b", ...]}
  --apply       Actually perform the git-mv.  Default is --dry-run.

Without --apply this script is a NO-OP: it only prints what it would do.

To reverse: git-mv data/_archive/indian/<slug>.json data/series/<slug>.json
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SERIES_DIR = REPO_ROOT / "data" / "series"
ARCHIVE_DIR = REPO_ROOT / "data" / "_archive" / "indian"


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Archive off-brand Indian series via git-mv (reversible).")
    p.add_argument("--cull-list", required=True, help="Path to JSON: {\"cull\": [\"slug\", ...]}")
    p.add_argument("--apply", action="store_true", default=False,
                   help="Apply moves.  Default is dry-run (print only).")
    return p.parse_args()


def load_cull_list(path: str) -> list[str]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if isinstance(data, list):
        return data
    if isinstance(data, dict) and "cull" in data:
        return data["cull"]
    raise ValueError(f"Unrecognized cull-list format in {path}. Expected {{\"cull\": [...]}} or a plain list.")


def main() -> None:
    args = parse_args()
    dry_run = not args.apply

    slugs = load_cull_list(args.cull_list)
    if not slugs:
        print("Cull list is empty. Nothing to do.")
        sys.exit(0)

    if not dry_run:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    moved = 0
    skipped = 0

    for slug in slugs:
        src = SERIES_DIR / f"{slug}.json"
        dst = ARCHIVE_DIR / f"{slug}.json"

        if not src.exists():
            print(f"SKIP  {slug}  (source not found: {src})")
            skipped += 1
            continue

        if dst.exists():
            print(f"SKIP  {slug}  (destination already exists: {dst})")
            skipped += 1
            continue

        if dry_run:
            print(f"DRY-RUN  git mv {src.relative_to(REPO_ROOT)}  {dst.relative_to(REPO_ROOT)}")
        else:
            result = subprocess.run(
                ["git", "mv", str(src), str(dst)],
                cwd=REPO_ROOT,
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                print(f"ERROR  {slug}: {result.stderr.strip()}", file=sys.stderr)
                sys.exit(1)
            print(f"MOVED  {src.relative_to(REPO_ROOT)}  ->  {dst.relative_to(REPO_ROOT)}")
        moved += 1

    mode = "DRY-RUN" if dry_run else "APPLIED"
    print(f"\n{mode}: {moved} moves, {skipped} skipped.")
    if dry_run:
        print("Pass --apply to perform the moves.")


if __name__ == "__main__":
    main()
