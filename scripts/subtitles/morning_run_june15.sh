#!/bin/bash
# Morning dossier run — run after 05:30 IST June 15 (UTC midnight = orfree quota reset)
# Usage: bash scripts/subtitles/morning_run_june15.sh
# Runbook: rm QUOTA_HALT, run 3 batches in parallel, report each when done

set -e
cd /home/aditya/bollyai

echo "=== Morning run started $(date) ==="

# Safety: confirm quota has reset
if [ -f data/subtitles/_engine/QUOTA_HALT ]; then
  echo "ERROR: QUOTA_HALT still present. Run after 05:30 IST June 15."
  exit 1
fi

# Ensure STOP is absent (moved to /tmp in previous session)
if [ -f data/subtitles/_engine/STOP ]; then
  mv data/subtitles/_engine/STOP /tmp/STOP.morning_run.bak
  echo "Moved STOP to /tmp/STOP.morning_run.bak"
fi

echo "Starting Wave 1: breaking-bad + the-boys + better-call-saul in parallel"
echo "Budget: ~900 req/day | BB=~240 TB=~60 BCS=~512 = ~812 req"

# Wave 1 — parallel
python3 scripts/subtitles/run_batch.py breaking-bad >> data/subtitles/_engine/ground-dossiers.log 2>&1 &
PID_BB=$!
echo "breaking-bad PID: $PID_BB"

python3 scripts/subtitles/run_batch.py the-boys >> data/subtitles/_engine/ground-dossiers.log 2>&1 &
PID_TB=$!
echo "the-boys PID: $PID_TB"

python3 scripts/subtitles/run_batch.py better-call-saul >> data/subtitles/_engine/ground-dossiers.log 2>&1 &
PID_BCS=$!
echo "better-call-saul PID: $PID_BCS"

# Wait for all wave 1 to finish
wait $PID_BB && echo "breaking-bad DONE" || echo "breaking-bad exited with error"
wait $PID_TB && echo "the-boys DONE" || echo "the-boys exited with error"
wait $PID_BCS && echo "better-call-saul DONE" || echo "better-call-saul exited with error"

echo "Wave 1 complete at $(date)"

# Report milestones
BB_COUNT=$(ls data/subtitles/breaking-bad/_dossiers/*.json 2>/dev/null | wc -l)
TB_COUNT=$(ls data/subtitles/the-boys/_dossiers/*.json 2>/dev/null | wc -l)
BCS_COUNT=$(ls data/subtitles/better-call-saul/_dossiers/*.json 2>/dev/null | wc -l)

echo "Dossier counts: BB=$BB_COUNT TB=$TB_COUNT BCS=$BCS_COUNT"

# Wave 2 — check remaining quota before starting
CURRENT_REQ=$(grep 'requests_today' data/subtitles/_engine/ground-dossiers.log | tail -5 | grep -o '"requests_today": [0-9]*' | tail -1 | grep -o '[0-9]*' || echo "unknown")
echo "Estimated requests used: $CURRENT_REQ"

if [ "$CURRENT_REQ" -lt 800 ] 2>/dev/null; then
  echo "Starting Wave 2: stranger-things + peaky-blinders"
  python3 scripts/subtitles/run_batch.py stranger-things >> data/subtitles/_engine/ground-dossiers.log 2>&1 &
  python3 scripts/subtitles/run_batch.py peaky-blinders >> data/subtitles/_engine/ground-dossiers.log 2>&1 &
  wait
  echo "Wave 2 complete at $(date)"
else
  echo "Quota running low ($CURRENT_REQ/900) — deferring Wave 2 to next day"
fi

# Restore STOP
if [ -f /tmp/STOP.morning_run.bak ]; then
  mv /tmp/STOP.morning_run.bak data/subtitles/_engine/STOP
  echo "STOP restored"
fi

echo "=== Morning run complete $(date) ==="
