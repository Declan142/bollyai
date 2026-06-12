#!/usr/bin/env bash
# review_chain.sh — waits for the dossier batch to finish, then drafts + G3-judges
# reviews for every series/film that has verified dossiers. Staging only; the
# voice-pass (G4) + merge + ship stay with Vyom/Aditya in the morning.
set -u
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
cd "$HOME/bollyai/scripts/subtitles" || exit 1
ENG="$HOME/bollyai/data/subtitles/_engine"
LOG="$ENG/reviews-console.log"

{
  echo "=== review_chain start $(date -Is) ==="
  # wait for any running run_batch.py to finish (poll, max ~6h)
  for i in $(seq 1 360); do
    if pgrep -f "run_batch.py" >/dev/null; then sleep 60; else break; fi
  done
  echo "batch clear at $(date -Is); drafting reviews"

  # every slug that has a _dossiers dir with at least one real dossier
  for ddir in "$HOME"/bollyai/data/subtitles/*/_dossiers; do
    slug=$(basename "$(dirname "$ddir")")
    n=$(find "$ddir" -name "*.json" ! -name "_*" 2>/dev/null | wc -l)
    [ "$n" -ge 1 ] || continue
    [ -f "$ENG/STOP" ] && { echo "STOP flag - halting"; break; }
    [ -f "$ENG/QUOTA_HALT" ] && { echo "QUOTA_HALT - stopping for the day"; break; }
    echo "--- reviews: $slug ($n dossiers) ---"
    python3 draft_reviews.py "$slug" 2>&1 | tail -40
  done
  echo "=== review_chain done $(date -Is) ==="
} >> "$LOG" 2>&1
