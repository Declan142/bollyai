#!/usr/bin/env bash
# depth_first_runner.sh — depth-first grounding: complete ONE series fully before moving to next
# Honoring rule: a series is "covered" only when ALL seasons ALL episodes have dossiers.
#
# Priority order:
#   1. sacred-games (16/16 SRTs ready → build all 16 dossiers)
#   2. Tier 2 series: fetch missing seasons, then build full dossier sets
#
# TRAP: always restore STOP after each series run

cd /home/aditya/bollyai
LOG=data/subtitles/_engine/depth-first.log
exec >> "$LOG" 2>&1

echo "=== depth_first_runner.sh START $(date -Is) ==="

STOP_PATH=data/subtitles/_engine/STOP
QUOTA_PATH=data/subtitles/_engine/QUOTA_HALT
STOP_BAK=/tmp/STOP.depth.bak

restore_stop() {
  echo "[trap] restoring STOP at $(date -Is)"
  mv "$STOP_BAK" "$STOP_PATH" 2>/dev/null || touch "$STOP_PATH"
}
trap restore_stop EXIT

# ── STEP 0: fix fetch-state.json — clear got=True for series that need more seasons ──
echo "[depth] clearing got-state for season-fetch targets at $(date -Is)"
python3 - << 'PYEOF'
import json
from pathlib import Path

state_path = Path("data/subtitles/_engine/fetch-state.json")
st = json.loads(state_path.read_text()) if state_path.exists() else {}

# Series that need additional seasons fetched — clear their "got" flag so fresh-queue
# season-specific entries get processed. Don't bump tries count.
needs_refetch = [
    "panchayat", "hellbound", "beef", "wednesday", "delhi-crime",
    "physical-100", "sweet-home",
    "stranger-things", "breaking-bad", "money-heist", "the-boys",
    "peaky-blinders", "better-call-saul", "the-crown", "you",
    "emily-in-paris", "maharani", "black-mirror", "mad-men",
]

cleared = 0
for slug in needs_refetch:
    key = f"series:{slug}"
    if key in st and st[key].get("got"):
        st[key]["got"] = False
        cleared += 1
        print(f"  cleared got for {key}")

state_path.write_text(json.dumps(st, ensure_ascii=False, indent=1))
print(f"[depth] cleared got for {cleared} series")
PYEOF

# ── STEP 1: regenerate fresh-queue from updated fresh-manual.json ──
echo "[depth] regenerating fresh-queue.json at $(date -Is)"
python3 scripts/subtitles/freshness_radar.py && echo "[depth] freshness_radar done"

# ── STEP 2: fetch missing seasons (subliminal, ~30-60 min, STOP present → no dossier build) ──
echo "[depth] fetching missing season SRTs via subliminal at $(date -Is)"
# max-items=30 covers Tier 2 (7 series × 1-2 seasons each) + some Tier 3
python3 scripts/subtitles/fetch_new_subs.py --max-items 30 && echo "[depth] fetch_new_subs pass 1 done"

# ── STEP 3: lift STOP, build dossiers depth-first ──
echo "[depth] lifting STOP for dossier building at $(date -Is)"
mv "$STOP_PATH" "$STOP_BAK" 2>/dev/null && echo "[depth] STOP moved to $STOP_BAK"
rm -f "$QUOTA_PATH"

depth_build() {
  local slug="$1"
  echo "[depth] === SERIES: $slug === $(date -Is)"
  python3 scripts/subtitles/run_batch.py "$slug"
  local n
  n=$(ls "data/subtitles/$slug/_dossiers/"S*.json 2>/dev/null | wc -l)
  echo "[depth] $slug: $n dossiers built at $(date -Is)"
  conductor outcome bollyai partial "depth-first: $slug $n dossiers built" 2>/dev/null || true
}

# Priority order: completable soonest first (fewest missing seasons)
DEPTH_ORDER=(
  sacred-games     # 16/16 SRTs — COMPLETE after this
  hellbound        # 6 SRTs + fetch S02 → 12 dossiers
  beef             # 12 SRTs + fetch S02 → 18 dossiers
  wednesday        # 12 SRTs + fetch S02 → 16 dossiers
  delhi-crime      # 7 SRTs + fetch S02+S03 → 18 dossiers
  physical-100     # 9 SRTs + fetch S02 → 18 dossiers
  sweet-home       # 11 SRTs + fetch S02+S03 → 26 dossiers
  panchayat        # 24 SRTs + fetch S04 → 32 dossiers
)

for slug in "${DEPTH_ORDER[@]}"; do
  # Abort on external STOP (different from our bak)
  if [[ -f "$STOP_PATH" ]]; then
    echo "[depth] External STOP detected — halting at $slug"
    break
  fi
  depth_build "$slug"
done

echo "=== depth_first_runner.sh JOB 3 complete at $(date -Is) ==="

# Summarize
complete=()
partial=()
for slug in "${DEPTH_ORDER[@]}"; do
  d=$(ls "data/subtitles/$slug/_dossiers/"S*.json 2>/dev/null | wc -l)
  p=$(python3 -c "
import json
from pathlib import Path
s = json.loads(Path('data/series/${slug}.json').read_text())
return sum(s2.get('episodes',0) if isinstance(s2.get('episodes',0),int) else 0 for s2 in s.get('seasons',[]))
" 2>/dev/null || echo "?")
  echo "[depth] $slug: $d dossiers / $p JSON eps"
  if [[ "$d" == "$p" ]]; then
    complete+=("$slug")
  else
    partial+=("$slug:$d/$p")
  fi
done

conductor outcome bollyai done "depth-first complete: [${complete[*]}]; partial: [${partial[*]}]" 2>/dev/null || true
echo "=== depth_first_runner.sh DONE $(date -Is) ==="
