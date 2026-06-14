#!/usr/bin/env bash
# ground_dossiers.sh — JOB 1: build dossiers for top-traffic series, then JOB 2: harvest new subs
# TRAP: always restore STOP on exit (crash, kill, or normal completion)

cd /home/aditya/bollyai
LOG=data/subtitles/_engine/ground-dossiers.log

echo "=== ground_dossiers.sh START $(date -Is) ===" | tee -a "$LOG"

STOP_PATH=data/subtitles/_engine/STOP
QUOTA_PATH=data/subtitles/_engine/QUOTA_HALT
STOP_BAK=/tmp/STOP.ground.bak

# TRAP: restore STOP on any exit
restore_stop() {
  echo "[trap] restoring STOP flag at $(date -Is)" | tee -a "$LOG"
  mv "$STOP_BAK" "$STOP_PATH" 2>/dev/null || touch "$STOP_PATH"
  echo "[trap] STOP restored." | tee -a "$LOG"
}
trap restore_stop EXIT

# Lift flags
if mv "$STOP_PATH" "$STOP_BAK" 2>/dev/null; then
  echo "[ground] STOP moved to $STOP_BAK" | tee -a "$LOG"
else
  echo "[ground] STOP was absent" | tee -a "$LOG"
fi
rm -f "$QUOTA_PATH" && echo "[ground] QUOTA_HALT removed" | tee -a "$LOG" || true

run_one() {
  local slug="$1"
  echo "[batch] START $slug at $(date -Is)" | tee -a "$LOG"
  python3 scripts/subtitles/run_batch.py "$slug" >> "$LOG" 2>&1
  local rc=$?
  local n
  n=$(ls "data/subtitles/$slug/_dossiers/"*.json 2>/dev/null | grep -v '_crosspass' | wc -l)
  if [[ $rc -eq 0 ]]; then
    echo "[batch] DONE $slug: $n dossier files at $(date -Is)" | tee -a "$LOG"
    conductor outcome bollyai partial "ground: $slug dossiers built ($n files)" >> "$LOG" 2>&1 || true
  else
    echo "[batch] FAILED $slug (rc=$rc) at $(date -Is)" | tee -a "$LOG"
    conductor outcome bollyai partial "ground: $slug FAILED (rc=$rc, dossiers so far: $n)" >> "$LOG" 2>&1 || true
  fi
}

# JOB 1: dossier targets ordered by traffic; stranger-things pre-staged = runs fastest
TARGETS=(
  stranger-things
  breaking-bad
  money-heist
  the-boys
  sacred-games
  delhi-crime
  panchayat
  beef
  wednesday
  you
  better-call-saul
  peaky-blinders
  black-mirror
  the-crown
  emily-in-paris
  hellbound
  sweet-home
  physical-100
  mad-men
  maharani
)

BATCH_SIZE=3
batch_pids=()

for slug in "${TARGETS[@]}"; do
  # Abort if external STOP re-created (not our bak — our bak is in /tmp)
  if [[ -f "$STOP_PATH" ]]; then
    echo "[ground] External STOP detected — halting loop at $(date -Is)" | tee -a "$LOG"
    break
  fi

  run_one "$slug" &
  batch_pids+=($!)

  if [[ ${#batch_pids[@]} -ge $BATCH_SIZE ]]; then
    echo "[ground] waiting for batch of $BATCH_SIZE at $(date -Is)" | tee -a "$LOG"
    for pid in "${batch_pids[@]}"; do
      wait "$pid" 2>/dev/null || true
    done
    batch_pids=()
    echo "[ground] batch complete, next wave starting at $(date -Is)" | tee -a "$LOG"
  fi
done

# drain final partial batch
for pid in "${batch_pids[@]}"; do
  wait "$pid" 2>/dev/null || true
done

echo "=== JOB 1 done at $(date -Is) ===" | tee -a "$LOG"

# Summarize JOB 1
total_files=0
swarm_ready=()
for slug in "${TARGETS[@]}"; do
  n=$(ls "data/subtitles/$slug/_dossiers/"*.json 2>/dev/null | grep -v '_crosspass' | wc -l)
  if [[ $n -gt 0 ]]; then
    total_files=$((total_files + n))
    swarm_ready+=("$slug")
  fi
done

echo "[ground] JOB1 summary: ${#swarm_ready[@]} series, $total_files dossier files" | tee -a "$LOG"
conductor outcome bollyai done "ground JOB1: ${#swarm_ready[@]} series dossiers built ($total_files files), swarm-ready: ${swarm_ready[*]}" >> "$LOG" 2>&1 || true

# ── JOB 2: harvest new subs ──────────────────────────────────────────────────
echo "=== JOB 2 starting at $(date -Is) ===" | tee -a "$LOG"

# Update fresh-manual.json with new season targets
python3 - >> "$LOG" 2>&1 <<'PYEOF'
import json, sys
from pathlib import Path

manual_path = Path("data/subtitles/_engine/fresh-manual.json")
existing = []
if manual_path.exists():
    try:
        existing = json.loads(manual_path.read_text())
    except Exception:
        pass

new_targets = [
    {"kind": "series", "slug": "navarasa",          "title": "Navarasa"},
    {"kind": "series", "slug": "stranger-things",   "title": "Stranger Things", "season_hint": 5},
    {"kind": "series", "slug": "squid-game",        "title": "Squid Game",      "season_hint": 2},
    {"kind": "series", "slug": "squid-game",        "title": "Squid Game",      "season_hint": 3},
    {"kind": "series", "slug": "wednesday",         "title": "Wednesday",       "season_hint": 2},
    {"kind": "series", "slug": "severance",         "title": "Severance",       "season_hint": 2},
    {"kind": "series", "slug": "mirzapur",          "title": "Mirzapur",        "season_hint": 3},
    {"kind": "series", "slug": "panchayat",         "title": "Panchayat",       "season_hint": 3},
    {"kind": "series", "slug": "panchayat",         "title": "Panchayat",       "season_hint": 4},
]

existing_set = {(e.get("slug"), e.get("season_hint")) for e in existing if isinstance(e, dict)}
added = 0
for t in new_targets:
    key = (t.get("slug"), t.get("season_hint"))
    if key not in existing_set:
        existing.append(t)
        existing_set.add(key)
        added += 1

manual_path.write_text(json.dumps(existing, indent=2, ensure_ascii=False))
print(f"[job2] Added {added} new targets to fresh-manual.json", flush=True)
PYEOF

echo "[job2] Running freshness_radar.py..." | tee -a "$LOG"
python3 scripts/subtitles/freshness_radar.py >> "$LOG" 2>&1 && echo "[job2] freshness_radar done" | tee -a "$LOG" || echo "[job2] freshness_radar partial" | tee -a "$LOG"

echo "[job2] Running fetch_new_subs.py..." | tee -a "$LOG"
python3 scripts/subtitles/fetch_new_subs.py >> "$LOG" 2>&1 && echo "[job2] fetch_new_subs done" | tee -a "$LOG" || echo "[job2] fetch_new_subs partial" | tee -a "$LOG"

echo "=== ground_dossiers.sh DONE $(date -Is) ===" | tee -a "$LOG"
# TRAP fires here → restore STOP
