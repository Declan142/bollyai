#!/usr/bin/env bash
set -uo pipefail
# ONE tick of the BollyAI buildout loop, launched FRESH by cron each hour.
# A new `claude` process per fire = the "self-clear context every hour" the loop needs;
# all state is carried by the ledger. Does exactly one batch (via claude -p), then exits.
#
# Guards: single-flight lock, STOP flag, target self-disable, never deploys.
# Usage: loop_tick.sh [--dry]   (--dry = run guards only, do not launch claude)

export PATH="$HOME/.local/bin:$PATH"
ROOT=/home/aditya/bollyai
LEDGER="$ROOT/data/_state/library-buildout.md"
PROMPT_FILE="$ROOT/scripts/batch/LOOP_TICK_PROMPT.md"
LOCK=/tmp/bollyai-buildout.lock
STOP="$ROOT/data/_state/BUILDOUT_STOP"
LOG="$ROOT/data/_state/buildout-loop.log"
MODEL="${BOLLYAI_LOOP_MODEL:-sonnet}"
DRY=0; [ "${1:-}" = "--dry" ] && DRY=1

ts() { date '+%F %T'; }
log() { echo "$(ts) $*" >>"$LOG"; }

count() { ls "$ROOT"/data/series/*.json 2>/dev/null | wc -l | tr -d ' '; }
target() { grep -oiE 'target[^0-9]*[0-9]+' "$LEDGER" 2>/dev/null | grep -oE '[0-9]+' | head -1; }

C=$(count); T=$(target); T=${T:-500}

if [ -f "$STOP" ]; then log "STOP flag present -> exit"; exit 0; fi
if [ "$C" -ge "$T" ]; then
  log "target reached ($C >= $T) -> self-disable (touch STOP + remove crontab line)"
  touch "$STOP"
  (crontab -l 2>/dev/null | grep -v 'loop_tick.sh' | crontab -) 2>/dev/null || true
  exit 0
fi

# single-flight: skip if a tick (or an in-session wave holding this lock) is running
exec 9>"$LOCK"
if ! flock -n 9; then log "another tick is running -> skip"; exit 0; fi

if [ "$DRY" = 1 ]; then
  log "DRY ok: count=$C target=$T model=$MODEL stop=no lock=acquired"
  echo "DRY ok: count=$C target=$T model=$MODEL prompt=$( [ -f "$PROMPT_FILE" ] && echo present || echo MISSING )"
  exit 0
fi

[ -f "$PROMPT_FILE" ] || { log "prompt file missing -> abort"; exit 1; }

log "tick START (count=$C target=$T model=$MODEL)"
cd "$ROOT" || exit 1
claude --model "$MODEL" --dangerously-skip-permissions -p "$(cat "$PROMPT_FILE")" >>"$LOG" 2>&1
log "tick END (rc=$?, count now=$(count))"
exit 0
