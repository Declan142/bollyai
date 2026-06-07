#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/lib/hc_ping.sh [uuid-or-url] [success|start|fail|log] [message]

Environment fallback:
  HC_UUID=<uuid>
  HC_URL=<full healthchecks URL>

Missing UUID/URL is treated as a no-op so local dry-runs do not fail.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

TARGET="${1:-${HC_URL:-${HC_UUID:-}}}"
STATUS="${2:-success}"
MESSAGE="${3:-}"

if [[ -z "$TARGET" ]]; then
  printf 'hc_ping.sh: HC target missing; skipping.\n' >&2
  exit 0
fi

case "$TARGET" in
  http://*|https://*) URL="$TARGET" ;;
  *) URL="https://hc-ping.com/$TARGET" ;;
esac

case "$STATUS" in
  success|ok) SUFFIX="" ;;
  start) SUFFIX="/start" ;;
  fail|failure) SUFFIX="/fail" ;;
  log) SUFFIX="/log" ;;
  *) printf 'hc_ping.sh: unknown status: %s\n' "$STATUS" >&2; exit 1 ;;
esac

if ! command -v curl >/dev/null 2>&1; then
  printf 'hc_ping.sh: curl is required to ping healthchecks.\n' >&2
  exit 1
fi

curl -fsS --max-time 10 --retry 2 --retry-delay 2 \
  --data-binary "$MESSAGE" \
  "${URL}${SUFFIX}" >/dev/null

printf 'hc_ping.sh: pinged %s.\n' "$STATUS" >&2
