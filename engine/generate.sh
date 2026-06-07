#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage: engine/generate.sh --input <file> [--output <file>] [--min-chars <n>]

PA-clone generation skeleton:
  gen -> adjudicate -> IG-gate -> claim-verify -> em-dash-strip

LLM calls are intentionally stubbed behind shell functions. To plug a real
generator/adjudicator later, set executable hooks:
  BOLLYAI_GENERATE_HOOK=/path/to/gen
  BOLLYAI_ADJUDICATE_HOOK=/path/to/adjudicate

Each hook receives: <input-file> <output-file>
USAGE
}

die() {
  printf 'generate.sh: %s\n' "$*" >&2
  exit 1
}

ENGINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$ENGINE_DIR/.." && pwd)"

INPUT_FILE=""
OUTPUT_FILE=""
MIN_CHARS=240

while (($#)); do
  case "$1" in
    --input|-i)
      INPUT_FILE="${2:-}"
      shift 2
      ;;
    --output|-o)
      OUTPUT_FILE="${2:-}"
      shift 2
      ;;
    --min-chars)
      MIN_CHARS="${2:-}"
      shift 2
      ;;
    --help|-h)
      usage
      exit 0
      ;;
    *)
      die "unknown argument: $1"
      ;;
  esac
done

[[ -n "$INPUT_FILE" ]] || die "--input is required"
[[ -f "$INPUT_FILE" ]] || die "input file not found: $INPUT_FILE"
[[ "$MIN_CHARS" =~ ^[0-9]+$ ]] || die "--min-chars must be an integer"

TMP_DIR="$(mktemp -d)"
cleanup() {
  rm -rf "$TMP_DIR"
}
trap cleanup EXIT

llm_generate() {
  local input="$1"
  local output="$2"

  if [[ -n "${BOLLYAI_GENERATE_HOOK:-}" ]]; then
    [[ -x "$BOLLYAI_GENERATE_HOOK" ]] || die "BOLLYAI_GENERATE_HOOK is not executable"
    "$BOLLYAI_GENERATE_HOOK" "$input" "$output"
    return
  fi

  {
    printf 'BollyAI has not watched this. BollyAI has read everyone who has.\n\n'
    printf 'Draft generated from %s.\n\n' "$(basename "$input")"
    printf 'Source brief:\n'
    sed -n '1,180p' "$input"
    printf '\n\n'
    printf 'What BollyAI thinks: this is a gated draft placeholder. Replace the stub hook with the local Codex or PA generator when prose generation is enabled.\n'
  } >"$output"
}

llm_adjudicate() {
  local input="$1"
  local output="$2"

  if [[ -n "${BOLLYAI_ADJUDICATE_HOOK:-}" ]]; then
    [[ -x "$BOLLYAI_ADJUDICATE_HOOK" ]] || die "BOLLYAI_ADJUDICATE_HOOK is not executable"
    "$BOLLYAI_ADJUDICATE_HOOK" "$input" "$output"
    return
  fi

  {
    printf 'Adjudicated draft. Human editor must review before publication.\n\n'
    cat "$input"
  } >"$output"
}

ig_gate() {
  local input="$1"
  local chars
  chars="$(wc -c <"$input" | tr -d ' ')"

  if (( chars < MIN_CHARS )); then
    printf 'IG-gate rejected: %s chars, need at least %s.\n' "$chars" "$MIN_CHARS" >&2
    return 2
  fi

  printf 'IG-gate passed: %s chars.\n' "$chars" >&2
}

claim_verify() {
  local input="$1"
  python3 "$REPO_ROOT/engine/gates/viewing_claim_regex.py" --input "$input"
}

em_dash_strip() {
  local input="$1"
  local output="$2"
  python3 "$REPO_ROOT/engine/gates/emdash_strip.py" --input "$input" --output "$output"
}

DRAFT="$TMP_DIR/01-generated.txt"
ADJUDICATED="$TMP_DIR/02-adjudicated.txt"
STRIPPED="$TMP_DIR/03-em-dash-stripped.txt"

printf 'stage: gen\n' >&2
llm_generate "$INPUT_FILE" "$DRAFT"

printf 'stage: adjudicate\n' >&2
llm_adjudicate "$DRAFT" "$ADJUDICATED"

printf 'stage: IG-gate\n' >&2
ig_gate "$ADJUDICATED"

printf 'stage: claim-verify\n' >&2
claim_verify "$ADJUDICATED"

printf 'stage: em-dash-strip\n' >&2
em_dash_strip "$ADJUDICATED" "$STRIPPED"

if [[ -n "$OUTPUT_FILE" ]]; then
  mkdir -p "$(dirname "$OUTPUT_FILE")"
  cp "$STRIPPED" "$OUTPUT_FILE"
  printf 'wrote: %s\n' "$OUTPUT_FILE" >&2
else
  cat "$STRIPPED"
fi
