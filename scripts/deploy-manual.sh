#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: scripts/deploy-manual.sh [--execute] [--skip-pull] [--skip-indexnow]

GHA-outage fallback skeleton for BollyAI.

Default mode is dry-run and prints the network/build commands without running
them. Use --execute only when you intentionally want the local fallback to:
  git pull --rebase --autostash origin main
  cd site && npm ci && npm run build
  npx wrangler pages deploy site/out --project-name=bollyai-in --branch=main
  python3 scripts/lib/indexnow_ping.py --all <sitemap>
  scripts/lib/hc_ping.sh ...

No vault files are read. Execute mode requires relevant env vars, especially:
  CLOUDFLARE_API_TOKEN
  CLOUDFLARE_ACCOUNT_ID
  INDEXNOW_KEY
USAGE
}

DRY_RUN=1
SKIP_PULL=0
SKIP_INDEXNOW=0
PROJECT_NAME="${BOLLYAI_CF_PROJECT:-bollyai-in}"
BRANCH="${BOLLYAI_BRANCH:-main}"
SITEMAP="${BOLLYAI_SITEMAP:-site/out/sitemap.xml}"

while (($#)); do
  case "$1" in
    --execute)
      DRY_RUN=0
      shift
      ;;
    --skip-pull)
      SKIP_PULL=1
      shift
      ;;
    --skip-indexnow)
      SKIP_INDEXNOW=1
      shift
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      printf 'deploy-manual.sh: unknown argument: %s\n' "$1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

print_cmd() {
  printf '+ %s\n' "$*"
}

require_env() {
  local name="$1"
  if [[ -z "${!name:-}" ]]; then
    printf 'deploy-manual.sh: %s is required in --execute mode.\n' "$name" >&2
    exit 1
  fi
}

if ((DRY_RUN)); then
  printf 'deploy-manual.sh: dry-run mode. Add --execute to run.\n'
  cd "$REPO_ROOT"
  if (( ! SKIP_PULL )); then
    print_cmd "git pull --rebase --autostash origin main"
  fi
  print_cmd "cd site && npm ci && npm run build"
  print_cmd "test -s site/out/index.html"
  print_cmd "npx wrangler pages deploy site/out --project-name=${PROJECT_NAME} --branch=${BRANCH} --commit-dirty=true"
  if (( ! SKIP_INDEXNOW )); then
    print_cmd "python3 scripts/lib/indexnow_ping.py --all ${SITEMAP}"
  fi
  print_cmd "scripts/lib/hc_ping.sh \"\${HC_DAILY_UUID:-}\" success \"manual deploy done\""
  exit 0
fi

require_env CLOUDFLARE_API_TOKEN
require_env CLOUDFLARE_ACCOUNT_ID

cd "$REPO_ROOT"

if (( ! SKIP_PULL )); then
  git pull --rebase --autostash origin main
fi

(cd site && npm ci && npm run build)
test -s site/out/index.html

npx wrangler pages deploy site/out \
  --project-name="$PROJECT_NAME" \
  --branch="$BRANCH" \
  --commit-dirty=true

if (( ! SKIP_INDEXNOW )); then
  python3 scripts/lib/indexnow_ping.py --all "$SITEMAP"
fi

scripts/lib/hc_ping.sh "${HC_DAILY_UUID:-}" success "manual deploy done"

printf 'deploy-manual.sh: manual deploy complete.\n'
