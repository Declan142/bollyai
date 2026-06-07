#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/lib/tg_alert.sh [message]

Environment:
  TG_BOT_TOKEN   Telegram bot token
  TG_CHAT_ID     Telegram chat id
  TG_SEVERITY    Optional label, default: INFO

Missing Telegram env is treated as a no-op so local dry-runs do not fail.
USAGE
}

if [[ "${1:-}" == "--help" || "${1:-}" == "-h" ]]; then
  usage
  exit 0
fi

TOKEN="${TG_BOT_TOKEN:-}"
CHAT_ID="${TG_CHAT_ID:-}"
SEVERITY="${TG_SEVERITY:-INFO}"

if (($#)); then
  MESSAGE="$*"
else
  MESSAGE="$(cat)"
fi

if [[ -z "$TOKEN" || -z "$CHAT_ID" ]]; then
  printf 'tg_alert.sh: TG_BOT_TOKEN or TG_CHAT_ID missing; skipping.\n' >&2
  exit 0
fi

if [[ -z "$MESSAGE" ]]; then
  printf 'tg_alert.sh: message is empty; skipping.\n' >&2
  exit 0
fi

if ! command -v curl >/dev/null 2>&1; then
  printf 'tg_alert.sh: curl is required to send Telegram alerts.\n' >&2
  exit 1
fi

curl -fsS --max-time 10 --retry 2 --retry-delay 2 \
  -X POST "https://api.telegram.org/bot${TOKEN}/sendMessage" \
  -d "chat_id=${CHAT_ID}" \
  -d "disable_web_page_preview=true" \
  --data-urlencode "text=[${SEVERITY}] ${MESSAGE}" >/dev/null

printf 'tg_alert.sh: sent Telegram alert.\n' >&2
