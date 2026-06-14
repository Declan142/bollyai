#!/usr/bin/env bash
# focused_ground.sh — targeted dossier build for refocused lane
# Waits for ground_dossiers.sh to exit, then builds paatal-lok + panchayat
# TRAP pattern: always restore STOP

cd /home/aditya/bollyai
LOG=data/subtitles/_engine/ground-dossiers.log
STOP_PATH=data/subtitles/_engine/STOP
QUOTA_PATH=data/subtitles/_engine/QUOTA_HALT
STOP_BAK=/tmp/STOP.focused.bak

restore_stop() {
  echo "[focused] restoring STOP at $(date -Is)" | tee -a "$LOG"
  mv "$STOP_BAK" "$STOP_PATH" 2>/dev/null || touch "$STOP_PATH"
}
trap restore_stop EXIT

# Wait for ground_dossiers.sh to finish
echo "[focused] waiting for ground_dossiers.sh to exit at $(date -Is)" | tee -a "$LOG"
while pgrep -f "ground_dossiers.sh" > /dev/null 2>&1; do
  sleep 10
done
echo "[focused] ground_dossiers.sh exited at $(date -Is)" | tee -a "$LOG"

# Lift STOP
if mv "$STOP_PATH" "$STOP_BAK" 2>/dev/null; then
  echo "[focused] STOP moved to $STOP_BAK" | tee -a "$LOG"
else
  echo "[focused] STOP was absent (ok)" | tee -a "$LOG"
fi
rm -f "$QUOTA_PATH"

build_one() {
  local slug="$1"
  echo "[focused] START $slug at $(date -Is)" | tee -a "$LOG"
  python3 scripts/subtitles/run_batch.py "$slug" >> "$LOG" 2>&1
  local rc=$?
  local n
  n=$(ls "data/subtitles/$slug/_dossiers/"*.json 2>/dev/null | grep -v '_crosspass' | wc -l)
  if [[ $rc -eq 0 ]]; then
    echo "[focused] DONE $slug: $n dossiers at $(date -Is)" | tee -a "$LOG"
    conductor outcome bollyai partial "ground: $slug dossiers built ($n files)" >> "$LOG" 2>&1 || true
  else
    echo "[focused] FAILED $slug (rc=$rc, dossiers=$n) at $(date -Is)" | tee -a "$LOG"
    conductor outcome bollyai partial "ground: $slug FAILED (rc=$rc, dossiers=$n)" >> "$LOG" 2>&1 || true
  fi
}

# Build in parallel (3 concurrent — the-boys resume + paatal-lok 16 eps + panchayat 24 eps)
build_one the-boys &
build_one paatal-lok &
build_one panchayat &
wait

echo "[focused] all done at $(date -Is)" | tee -a "$LOG"

n_tb=$(ls data/subtitles/the-boys/_dossiers/*.json 2>/dev/null | grep -v '_crosspass' | wc -l)
n_pl=$(ls data/subtitles/paatal-lok/_dossiers/*.json 2>/dev/null | grep -v '_crosspass' | wc -l)
n_pa=$(ls data/subtitles/panchayat/_dossiers/*.json 2>/dev/null | grep -v '_crosspass' | wc -l)
conductor outcome bollyai done "ground focused: the-boys $n_tb, paatal-lok $n_pl, panchayat $n_pa dossiers" >> "$LOG" 2>&1 || true
echo "[focused] DONE at $(date -Is)" | tee -a "$LOG"
# TRAP fires here → restore STOP
