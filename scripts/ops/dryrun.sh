#!/usr/bin/env bash
set -euo pipefail

WORKFLOWS=(daily-refresh friday-surge ott-calendar-roll tentpole-live health-digest)

usage() {
  cat <<'USAGE'
Usage: scripts/ops/dryrun.sh <workflow-name|all> [--report path]

Runs the local core sequence for a workflow with fixture data, temp writes,
no push, no deploy, and IndexNow dry-run mode.
USAGE
}

die() {
  printf 'dryrun.sh: %s\n' "$*" >&2
  exit 1
}

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
WORKFLOW="${1:-}"
REPORT=""
TEMP_PATHS=()

cleanup_temp_paths() {
  local path
  for path in "${TEMP_PATHS[@]:-}"; do
    rm -rf "$path"
  done
}

trap cleanup_temp_paths EXIT

if [[ -z "$WORKFLOW" || "$WORKFLOW" == "--help" || "$WORKFLOW" == "-h" ]]; then
  usage
  exit 0
fi
shift || true

while (($#)); do
  case "$1" in
    --report)
      REPORT="${2:-}"
      [[ -n "$REPORT" ]] || die "--report requires a path"
      shift 2
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

cd "$REPO_ROOT"

run_cmd() {
  printf '\n+'
  printf ' %q' "$@"
  printf '\n'
  "$@"
}

make_temp_data() {
  local tmp
  tmp="$(mktemp -d)"
  TEMP_PATHS+=("$tmp")
  cp -a data "$tmp/data"
  printf '%s\n' "$tmp"
}

build_site() {
  if [[ "${BOLLYAI_DRYRUN_SKIP_BUILD:-0}" == "1" ]]; then
    printf 'dryrun.sh: BOLLYAI_DRYRUN_SKIP_BUILD=1, skipping site build.\n'
    return 0
  fi
  run_cmd bash -lc 'cd site && npm ci && npm run build'
  run_cmd test -s site/out/index.html
}

indexnow_dryrun() {
  local data_dir="$1"
  local state_path="$2/indexnow-state.json"
  run_cmd python3 scripts/lib/indexnow_ping.py \
    --delta "$data_dir/_state/changed-urls.json" \
    --dry-run \
    --force \
    --floor-seconds 0 \
    --state "$state_path"
}

dryrun_data_refresh() {
  local tmp
  tmp="$(make_temp_data)"
  run_cmd python3 engine/fetchers/run_all.py --fixture-mode --live-only --write "$tmp/data"
  run_cmd python3 engine/fetchers/staleness_check.py --data-dir "$tmp/data" --sla-hours 26 --emit "$tmp/data/_state/staleness.json" --now 2026-06-09T12:00:00Z
  build_site
  indexnow_dryrun "$tmp/data" "$tmp"
  printf '\nCommit skipped in local dry-run.\n'
  printf 'Deploy skipped in local dry-run.\n'
}

dryrun_ott_roll() {
  local tmp
  tmp="$(make_temp_data)"
  run_cmd python3 engine/regen_ott_weekly.py --fixture-mode --data-dir "$tmp/data" --today 2026-06-12 --weeks 2
  build_site
  indexnow_dryrun "$tmp/data" "$tmp"
  printf '\nCommit skipped in local dry-run.\n'
  printf 'Deploy skipped in local dry-run.\n'
}

dryrun_tentpole() {
  local tmp
  tmp="$(make_temp_data)"
  run_cmd python3 scripts/ops/tentpole_live.py --fixture-mode --data-dir "$tmp/data" --today 2026-06-12 --force
  run_cmd python3 engine/fetchers/staleness_check.py --data-dir "$tmp/data" --sla-hours 26 --emit "$tmp/data/_state/staleness.json" --now 2026-06-09T12:00:00Z
  build_site
  indexnow_dryrun "$tmp/data" "$tmp"
  printf '\nCommit skipped in local dry-run.\n'
  printf 'Deploy skipped in local dry-run.\n'
}

dryrun_health_digest() {
  local tmp
  tmp="$(mktemp -d)"
  TEMP_PATHS+=("$tmp")
  run_cmd python3 scripts/ops/health_digest.py --dry-run --output "$tmp/health-digest.txt"
  run_cmd test -s "$tmp/health-digest.txt"
  printf '\nResend skipped in local dry-run.\n'
  printf 'Telegram skipped in local dry-run.\n'
}

run_one() {
  case "$1" in
    daily-refresh|friday-surge)
      dryrun_data_refresh
      ;;
    ott-calendar-roll)
      dryrun_ott_roll
      ;;
    tentpole-live)
      dryrun_tentpole
      ;;
    health-digest)
      dryrun_health_digest
      ;;
    *)
      die "unknown workflow: $1"
      ;;
  esac
}

run_all() {
  local report_path="$REPORT"
  local logs_dir
  local failures=0
  logs_dir="$(mktemp -d)"
  TEMP_PATHS+=("$logs_dir")

  if [[ -n "$report_path" ]]; then
    mkdir -p "$(dirname "$report_path")"
    {
      printf '# BollyAI GHA dry-run report\n\n'
      printf 'Generated: %s\n\n' "$(date -u +%FT%TZ)"
      printf 'No push, deploy, or IndexNow network ping was executed.\n\n'
    } > "$report_path"
  fi

  for workflow in "${WORKFLOWS[@]}"; do
    local log_file="$logs_dir/${workflow}.log"
    local status=0
    printf '\n=== %s ===\n' "$workflow"
    if "$0" "$workflow" >"$log_file" 2>&1; then
      status=0
      printf '%s: PASS\n' "$workflow"
    else
      status=$?
      failures=$((failures + 1))
      printf '%s: FAIL (%s)\n' "$workflow" "$status"
    fi
    tail -80 "$log_file"

    if [[ -n "$report_path" ]]; then
      {
        printf '## %s\n\n' "$workflow"
        if [[ "$status" -eq 0 ]]; then
          printf 'Status: PASS\n\n'
        else
          printf 'Status: FAIL (%s)\n\n' "$status"
        fi
        printf 'Evidence:\n\n```text\n'
        { grep -E 'IndexNow dry-run:|Commit skipped|Deploy skipped|Resend skipped|Telegram skipped|BollyAI weekly health digest|Generated:|Snapshot|^- Staleness:|^- Changed URL sidecar:|^\+ test -s site/out/index.html|lint:aggregate|BOLLYAI_DRYRUN_SKIP_BUILD' "$log_file" || true; } \
          | tail -40 \
          | LC_ALL=C tr -cd '\11\12\15\40-\176'
        printf '\n```\n\n'
      } >> "$report_path"
    fi
  done

  if ((failures)); then
    return 1
  fi
}

if [[ "$WORKFLOW" == "all" ]]; then
  run_all
else
  run_one "$WORKFLOW"
fi
