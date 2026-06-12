#!/usr/bin/env bash
# freshness_tick.sh — daily cron: discover new content -> fetch subs -> engine.
# Cron-safe: PATH exported (pipx subliminal lives in ~/.local/bin).
set -u
export PATH="$HOME/.local/bin:/usr/local/bin:/usr/bin:/bin"
cd "$HOME/bollyai/scripts/subtitles" || exit 1
LOG="$HOME/bollyai/data/subtitles/_engine/freshness.log"
{
  echo "=== tick $(date -Is) ==="
  # never overlap with a running batch or a halted state
  if [ -f "$HOME/bollyai/data/subtitles/_engine/STOP" ]; then
    echo "STOP flag present - skipping tick"; exit 0
  fi
  python3 freshness_radar.py
  python3 fetch_new_subs.py --max-items 8
  echo "=== tick done $(date -Is) ==="
} >> "$LOG" 2>&1
