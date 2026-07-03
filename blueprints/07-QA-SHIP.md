# BLUEPRINT 07 - QA gates, commit, push, deploy (the ship runbook)

The gates ARE the approval (standing grant, Aditya 2026-06-13): tests green = push allowed;
tests + build green (+ design-review >= 7.5 for frontend) = deploy allowed. Skip a gate =
no ship, no exceptions. Prompt: `prompts/P08` (independent gatekeeper session).

## Gate ladder (in order; each gate names its owner)

| # | Gate | Command | Pass condition | Owner |
|---|---|---|---|---|
| 1 | Fence validator (series) | `python3 scripts/batch/validate_series.py <slugs>` (or `--since <iso>` / `--all`) | every file PASS | worker |
| 2 | Fence validator (films) | `python3 scripts/batch/validate_films.py <slugs>` | every file PASS | worker |
| 3 | Dash sweep | `grep -rlP '[\x{2012}-\x{2015}]' data/ --include='*.json'` then `fix_series.py` on in-scope hits | zero hits after fix | worker |
| 4 | Content test suite | `python3 -m pytest tests/ -q` | 0 failures | floor / gatekeeper |
| 5 | Build + prebuild guards | `cd site && npm run build` | exit 0 | floor ONLY (cores) |
| 6 | Design gate (frontend only) | design-reviewer agent on the rendered change | score >= 7.5 | floor |
| 7 | Commit | specific paths + trailer `Co-Authored-By: Claude <noreply@anthropic.com>` | only on green above | worker/floor |
| 8 | Push | `git pull --rebase && git push` | gate 4 green on THIS tree; never --force | floor |
| 9 | Deploy | `npx wrangler pages deploy site/out --project-name=bollyai-in --branch=main` | gates 4+5 (+6) green, build FRESH | floor, interactive only |
| 10 | Post-deploy verify | script below | all 200 + content sane | floor |
| 11 | IndexNow | `scripts/indexnow_ping.sh` | hash-gated, <= 85 URLs/wave | floor |

What gate 5 actually enforces inside `npm run build`: the Western original-language
allowlist guard (`guard-offbrand-series.mjs` + films guard) - one off-brand file kills the
build; the no-AggregateRating hard check; `postbuild:filecap` (strips avif variants and
hard-fails at >= 20k output files - CF Pages cap). A build after ANY data change must be
re-run before deploy; deploying a stale `site/out` ships yesterday's data.

## Per-gate failure playbooks

- **Gate 1/2 red**: blueprint 02 carries the full validator error -> fix table. Content
  errors (viewing-claim, FABRICATED-attribution) are rewrites, never mechanical strips.
- **Gate 3 hits outside your scope**: report only - another lane's WIP is not yours to fix.
- **Gate 4 red**: read the failing test file's docstring first (each states its fence).
  Classify: IN-SCOPE (your wave caused it - fix at the source) vs PRE-EXISTING (name the
  likely owner; the wave is still blocked per the red rules - say so plainly).
  KNOWN pre-existing reds as of 2026-07-04: `test_boxoffice_publish_rule::
  test_current_week_schema_and_published_figures_are_source_gated` and
  `test_ott_calendar::test_generated_calendar_has_source_envelopes` - both over
  cron-generated files that are stale/diverged locally (origin runners rewrite them).
  Triage belongs to the floor: pull the runner commits or regenerate, THEN re-run. Do not
  hand-edit generated files to silence tests.
- **Gate 5 red**: paste the exact failing guard line. Off-brand guard = a data file must
  move to `data/_archive/`, never a guard edit. Filecap = the wave is too big; split it.
- **Gate 6 < 7.5**: iterate execution (direction stays), re-review; two failed rounds =
  stop and surface the reviewer's notes.
- **Gate 8 conflicts on pull --rebase**: if OTHER lanes' uncommitted work blocks the
  rebase, STOP - the floor resolves divergence by hand. Never autostash someone else's WIP
  into a conflict.

## Deploy + post-deploy (floor, interactive)

Creds: `~/.claude/vault/cloudflare-master.md` (god token; the plain `cloudflare.md` Pages
token does NOT scope bollyai-in - auth error 10000). ACCOUNT_ID
`18c1d9f76c2153a2dde6efa561116b17`. NEVER put the god token in GH secrets (the
daily-refresh Action has its own working token). Expected wrangler success shape: upload
summary (n files), then `Deployment complete!` + a `*.pages.dev` preview URL - paste both
lines in the ship report.

```bash
# post-deploy verify (minimum set; add every route THIS wave changed)
for u in / /browse /box-office /ott/calendar /series/mad-men /series/mad-men/where-to-watch; do
  printf "%-45s %s\n" "$u" "$(curl -s -o /dev/null -w '%{http_code}' https://bollyai.in$u)"; done
# a changed page, full render sanity + off-brand sweep (expect 0):
curl -s https://bollyai.in/<changed-page> | grep -c -i -E 'bollywood|kollywood|tollywood|sandalwood' || true
# new slugs actually present in the build before deploy:
ls site/out/series/<new-slug>/ 
```

## Who may do what (hard authority map)

- **Headless/unattended lanes**: validate + fix + commit ONLY. Never build (cores), never
  push, never deploy, never IndexNow, never wrangler, never secrets, never `--no-verify`.
- **Interactive floor (Opus 4.8)**: everything, in ladder order, outputs pasted.
- Force-push, history rewrite, deleting branches you didn't create: DENIED, always.
- The tree may carry OTHER sessions' uncommitted work: `git add` SPECIFIC paths you
  touched, never `-A`. pytest red on files you didn't touch = STOP and report.

## Velocity + rollback

- NEW-page deploy waves are throttled (site-age spam-signal caution); confirm cadence
  against the ledger / Aditya before a big wave. Updates uncapped.
- Rollback, exactly this sequence (history rules forbid reset/force):
  1. `git revert <bad-sha>` (or a range revert) -> a NEW commit;
  2. gates 4-5 on the reverted tree;
  3. redeploy `site/out`;
  4. CF Pages dashboard also keeps prior deployments for instant restore (Aditya action)
     while the revert builds.

## Red rules

Never commit red. Never push red. Never deploy a stale build. Never claim "shipped"
without gate 10 output pasted. A false PASS from the gatekeeper is the most expensive
mistake this repo can make - when unsure, FAIL with the question attached.
