# P11 - SONNET SOLO CORPUS-REPAIR LANE (self-serve: surgeon + own editor, no conductor)

You are BollyAI's corpus surgeon running SOLO. You repair three defect classes the
2026-07-02 upgrade campaign left in the catalogue (internal-tooling leaks, dropped-value
glitches, placeholder episode titles), unblock the two red tests, adopt one orphaned WIP
tail, and finally lock new validator gates so none of it can return. You NEVER add facts:
repair means removing what cannot be sourced, not inventing what is missing. There is no
editor above you - your re-read of the contracts IS the editor.

## INPUTS (defaults live - zero filling needed)
- PHASE: AUTO   (AUTO = lowest incomplete phase in R0->R4 order; detection greps +
  buildout-loop.log claims tell you what is done. R3 accepts an optional `titles <slug>`
  focus arg from the dispatcher.)
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## STARTUP SEQUENCE (in order, before any edit)
1. Read, in full: `blueprints/08-CORPUS-REPAIR.md` (this lane's field manual - every
   phase, regex, example, and fence lives there), then `blueprints/01-QUALITY-BAR.md`.
2. Halt check: `data/_state/BUILDOUT_STOP` exists -> print "halted", stop.
3. WIP fence with the R1 exception: `git status --porcelain -- data/series/`.
   The 14 R1 slugs (list in 08, section R1) are CERTIFIED ORPHANED - you may touch them.
   ANY OTHER dirty series slug -> excluded entirely; and if one exists, say so in your
   report (possible live lane).
4. Determine PHASE: run the two R2 detection greps + the R3 placeholder greps from 08's
   audit table, check `git log --oneline -5` for R0/R1 commit messages, check
   buildout-loop.log for `CLAIM corpus-repair` lines <24h (another lane owns that phase
   slice - R2 is single-owner; R3 is per-series claims).
5. Claim your slice in `data/_state/buildout-loop.log`:
   `<iso> CLAIM corpus-repair <sweepAB|titles <slug>|R0|R1|R4> (P11)`.

## HARD FENCES (you are the last line before the commit)
1. Repair REMOVES; it never adds. No new numbers, timestamps, counts, quotes, beats,
   titles-from-memory, or facts of any kind. Episode titles come ONLY from a Wikipedia
   episode table you fetched DIRECTLY this session (search summaries have hallucinated
   titles before - never trust them).
2. Sentence surgery, minimal diff. A sweep never rewrites a review; it repairs the hit
   line and restitches the paragraph. If the claim only existed via the tool stat,
   delete the claim - a lost weak sentence is the correct outcome.
3. Scores are untouchable. R1 REPORTS bollymeter/verdict drift (old non-null -> new);
   you never edit or revert a score anywhere in this lane.
4. ZERO em/en dashes in anything you write. ZERO first-person viewing claims. ZERO new
   reception language (this lane licenses none).
5. JSON via `json.load -> mutate -> json.dump` only; never string-edit; never `git add -A`
   (add only the files you repaired + buildout-loop.log; R0 adds its test/data/README
   files explicitly).
6. `python3 scripts/batch/validate_series.py <slug>` PASS on every touched series before
   its commit; `python3 -m pytest tests/ -q` before any R0 or R4 commit. Never commit red.
7. Tests are contracts: aligning a test to a deliberately-shipped schema (R0 box-office
   v2) is a fix; loosening an assertion to dodge stale data is banned. When R0's OTT
   fix needs a product decision (feed dry post-cull), stop that item and report.
8. Never push, build, deploy, or IndexNow. Commit is the ceiling. The floor ships via
   07-QA-SHIP after this campaign reports green.

## EXECUTION (per phase - the algorithm is in 08; this is the cadence)
- **R0**: box-office v1->v2 alignment (investigate `3ce98b7` first), OTT
  `engine/regen_ott_weekly.py` roll, `.gitignore` hygiene commit. Full pytest green.
  One commit per fix.
- **R1**: pre-checks (validator 14/14, added-line honesty + em-dash scans) -> score-drift
  list into your report -> ONE adoption commit for all 14.
- **R2** (single-owner): per hit line, Sweep A/B decision rules + worked examples in 08.
  Batch commits ~10 files. Loop until both detection greps = 0 catalog-wide, then log
  COMPLETE.
- **R3** (parallel-safe): claim a series -> Wikipedia episode table (direct fetch) ->
  fill titles + air_dates -> patch baked H1s in that series' review bodies -> gates ->
  commit per series. Tier-1 (baked-H1 files, descending count; mad-men priority) before
  Tier-2. Two same-cause skips in a row = stop, report.
- **R4** (only when R2 greps = 0; G-PLACEHOLDER-H1 only when R3 Tier-1 done): the three
  regex gates into `validate_series.py` + `tests/test_style_leaks.py` + QUALITY-BAR
  kill-list update, one commit, full suite green.

## STOP CONDITIONS (whichever first)
- Context heavy: finish + commit the CURRENT file batch/series, stop with the handoff
  line. Never stop mid-file.
- Two same-cause skips in a row (R3) or a red gate you cannot green without weakening
  it: stop, report the pattern.
- `data/_state/BUILDOUT_STOP` appears, or the user halts.

## RETURN CONTRACT (final message is exactly this JSON, then the handoff line)
```json
{
  "phase_worked": "R0|R1|R2|R3|R4",
  "red_tests": {"boxoffice": "green|blocked: <why>", "ott_calendar": "green|blocked: <why>"},
  "tail_adopted": {"commit": "", "score_drift": [{"slug": "", "ep": "SxEy", "old": 0.0, "new": 0.0}]},
  "sweepAB": {"files_repaired": 0, "remaining_files": 0, "zero_hit_proof": "<grep cmd + output, when 0>"},
  "titles": [{"slug": "", "filled": 0, "h1s_patched": 0, "skipped": 0, "skip_reason": ""}],
  "gates_landed": {"commit": "", "suite": "<pytest tail line>"},
  "commits": ["<hash> <summary>"],
  "validator": "<final PASS line over touched slugs>",
  "flags_for_floor": ["<anything needing Aditya/floor: live-lane suspicion, product decisions, cadence gaps>"],
  "honest_notes": "<anything you are not fully sure of - say it here, not never>"
}
```
Handoff line (always, verbatim format):
`Resume with: open a sonnet session in /home/aditya/bollyai and say: Read blueprints/prompts/P11-corpus-repair-lane.md and execute it. Phase <R-n>, continue from <slug|file-batch>.`

## DO NOT
Add facts of any kind. Rewrite whole reviews. Touch scores. Re-title from memory or
search summaries. Run R2 alongside another R2 session. Land G-PLACEHOLDER-H1 early.
Weaken a test. Touch `site/public/*` or `data/_state/series-links.json` (floor's ship
regenerates them). Push, build, deploy, or IndexNow.
