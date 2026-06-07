#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: engine/commit.sh -m <message> [-- <path>...]

Serialized writer for BollyAI local generation batches.

Flow, retried up to 3 times:
  git pull --rebase --autostash origin main
  git add ...
  git commit -m ...
  git push origin main

Do not run this script from automation that is already inside another writer
lock. This script contains push logic by design; this build task does not
execute it.
USAGE
}

die() {
  printf 'commit.sh: %s\n' "$*" >&2
  exit 1
}

ENGINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ENGINE_DIR/.." && pwd)"
MESSAGE=""
PATHS=()
MAX_RETRIES=3

while (($#)); do
  case "$1" in
    -m|--message)
      MESSAGE="${2:-}"
      shift 2
      ;;
    --retries)
      MAX_RETRIES="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    --)
      shift
      PATHS=("$@")
      break
      ;;
    *)
      PATHS+=("$1")
      shift
      ;;
  esac
done

[[ -n "$MESSAGE" ]] || die "commit message is required"
[[ "$MAX_RETRIES" =~ ^[1-9][0-9]*$ ]] || die "--retries must be a positive integer"

cd "$REPO_ROOT"
git rev-parse --is-inside-work-tree >/dev/null 2>&1 || die "not inside a git work tree"

LOCK_DIR="$REPO_ROOT/.git/bollyai-writer.lock"
acquire_lock() {
  local waited=0
  until mkdir "$LOCK_DIR" 2>/dev/null; do
    waited=$((waited + 1))
    if (( waited > 300 )); then
      die "timed out waiting for writer lock"
    fi
    sleep 1
  done
}

release_lock() {
  rmdir "$LOCK_DIR" 2>/dev/null || true
}

attempt_commit_push() {
  git pull --rebase --autostash origin main

  if ((${#PATHS[@]})); then
    git add -- "${PATHS[@]}"
  else
    git add -A
  fi

  if ! git diff --cached --quiet; then
    git commit -m "$MESSAGE"
  else
    printf 'commit.sh: no staged changes; attempting push in case branch is ahead.\n' >&2
  fi

  git push origin main
}

acquire_lock
trap release_lock EXIT

for attempt in $(seq 1 "$MAX_RETRIES"); do
  if attempt_commit_push; then
    printf 'commit.sh: writer flow complete on attempt %s.\n' "$attempt" >&2
    exit 0
  fi

  if (( attempt == MAX_RETRIES )); then
    die "writer flow failed after $MAX_RETRIES attempts"
  fi

  sleep_for=$((attempt * 5))
  printf 'commit.sh: attempt %s failed; retrying in %ss.\n' "$attempt" "$sleep_for" >&2
  sleep "$sleep_for"
done
