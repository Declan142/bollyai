#!/usr/bin/env bash
set -euo pipefail
# Per-batch closer for the BollyAI library buildout loop.
#   fix (em-dash) -> validate (hard fences) -> harvest posters -> build
# Exit 0 = green, safe to commit. Non-zero = STOP, do not commit.
#
# Usage: ingest_batch.sh <slug> [<slug> ...]
ROOT=/home/aditya/bollyai
cd "$ROOT"
[ $# -ge 1 ] || { echo "usage: ingest_batch.sh <slug>..."; exit 2; }

echo "== [1/4] fix (mechanical em-dash) =="
python3 scripts/batch/fix_series.py "$@"

echo "== [2/4] validate (hard fences) =="
if ! python3 scripts/batch/validate_series.py "$@"; then
  echo ">> VALIDATION FAILED - not building, not committing." >&2
  exit 1
fi

echo "== [3/4] harvest posters (non-fatal; SVG-logo leads fall back by design) =="
python3 scripts/harvest_series_posters.py "$@" || echo "(poster harvest had misses - ok)"

echo "== [4/4] build =="
cd site && npm run build

echo "== GREEN: $# slugs validated + site build passed - safe to commit =="
