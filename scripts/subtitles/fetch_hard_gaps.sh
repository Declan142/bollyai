#!/usr/bin/env bash
# fetch_hard_gaps.sh — targeted sub fetch for series subliminal missed on default providers
# Tries multiple providers for BB S2-5, The Boys S2-4, Squid Game S3
set -uo pipefail
SUBS_ROOT=~/bollyai-subs/series
SUBLIMINAL=~/.local/bin/subliminal
LOG=~/bollyai/data/subtitles/_engine/ground-dossiers.log

log() { echo "[hard-gaps] $*" | tee -a "$LOG"; }

count_srts() {
  local pattern="$1"
  find "$SUBS_ROOT" -name "$pattern" 2>/dev/null | wc -l
}

try_fetch() {
  local title="$1" season="$2" n_eps="$3" provider="$4"
  local seanum; printf -v seanum "%02d" "$season"
  local outdir="$SUBS_ROOT/$title"
  mkdir -p "$outdir"

  local tmpdir; tmpdir=$(mktemp -d)
  local count=0

  # Create dummies only for missing episodes
  for ep in $(seq 1 "$n_eps"); do
    printf -v epnum "%02d" "$ep"
    local srt_target="$outdir/${title}.S${seanum}E${epnum}.1080p.WEB-DL.en.srt"
    [[ -f "$srt_target" ]] && continue
    touch "$tmpdir/${title}.S${seanum}E${epnum}.1080p.WEB-DL.mkv"
    ((count++)) || true
  done

  if [[ "$count" -eq 0 ]]; then
    rm -rf "$tmpdir"
    log "  ${title} S${seanum}: already complete, skip"
    return 0
  fi

  log "  ${title} S${seanum} ($count missing eps) via $provider ..."
  "$SUBLIMINAL" download -l en -p "$provider" "$tmpdir" 2>&1 \
    | grep -E "Downloaded|No subtitle|Error|subtitle" | head -5 \
    | while IFS= read -r line; do log "    $line"; done || true

  # Copy SRTs found to outdir
  local got=0
  while IFS= read -r srt; do
    local base; base=$(basename "$srt")
    local ep_code; ep_code=$(echo "$base" | grep -oiE "S[0-9]{2}E[0-9]{2}" | head -1 | tr '[:lower:]' '[:upper:]')
    [[ -z "$ep_code" ]] && continue
    local target="$outdir/${title}.${ep_code}.1080p.WEB-DL.en.srt"
    if [[ ! -f "$target" ]]; then
      cp "$srt" "$target"
      log "    ✓ saved $(basename "$target")"
      ((got++)) || true
    fi
  done < <(find "$tmpdir" -name "*.srt" 2>/dev/null)

  rm -rf "$tmpdir"
  log "  → $got new SRTs from $provider"
  return 0
}

PROVIDERS=(podnapisi opensubtitles addic7ed tvsubtitles gestdown)

log "=== Hard-gap harvest start $(date -Is) ==="

# Breaking Bad: S02=13, S03=13, S04=13, S05=16
declare -A BB_EPS=([2]=13 [3]=13 [4]=13 [5]=16)
for season in 2 3 4 5; do
  seanum=$(printf "%02d" "$season")
  already=$(count_srts "Breaking.Bad.S${seanum}*.srt")
  expected=${BB_EPS[$season]}
  if [[ "$already" -ge "$expected" ]]; then
    log "BB S${seanum}: already have $already/$expected, skip"
    continue
  fi
  for provider in "${PROVIDERS[@]}"; do
    try_fetch "Breaking.Bad" "$season" "${BB_EPS[$season]}" "$provider"
    got=$(count_srts "Breaking.Bad.S${seanum}*.srt")
    if [[ "$got" -gt 0 ]]; then
      log "BB S${seanum}: $got SRTs — stopping provider loop"
      break
    fi
  done
done

# The Boys: S02=8, S03=8, S04=7
declare -A TB_EPS=([2]=8 [3]=8 [4]=7)
for season in 2 3 4; do
  seanum=$(printf "%02d" "$season")
  already=$(count_srts "The.Boys.S${seanum}*.srt")
  expected=${TB_EPS[$season]}
  if [[ "$already" -ge "$expected" ]]; then
    log "TB S${seanum}: already have $already/$expected, skip"
    continue
  fi
  for provider in "${PROVIDERS[@]}"; do
    try_fetch "The.Boys" "$season" "${TB_EPS[$season]}" "$provider"
    got=$(count_srts "The.Boys.S${seanum}*.srt")
    if [[ "$got" -gt 0 ]]; then
      log "TB S${seanum}: $got SRTs — stopping provider loop"
      break
    fi
  done
done

# Squid Game S03: ~7 eps
seanum="03"
already=$(count_srts "Squid.Game.S03*.srt")
if [[ "$already" -eq 0 ]]; then
  for provider in "${PROVIDERS[@]}"; do
    try_fetch "Squid.Game" 3 7 "$provider"
    got=$(count_srts "Squid.Game.S03*.srt")
    if [[ "$got" -gt 0 ]]; then
      log "SG S03: $got SRTs — stopping provider loop"
      break
    fi
  done
else
  log "SG S03: already have $already SRTs"
fi

log "=== FINAL COUNTS ==="
log "BB S02-S05: $(count_srts 'Breaking.Bad.S0[2-5]*.srt') SRTs"
log "TB S02-S04: $(count_srts 'The.Boys.S0[2-4]*.srt') SRTs"
log "SG S03: $(count_srts 'Squid.Game.S03*.srt') SRTs"
log "=== Hard-gap harvest done $(date -Is) ==="
