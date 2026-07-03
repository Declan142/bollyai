# BLUEPRINT 07 - QA gates, commit, push, deploy (the ship runbook)

The gates ARE the approval (standing grant, Aditya 2026-06-13): tests green = push allowed;
tests + build green (+ design-review >= 7.5 for frontend) = deploy allowed. Skip a gate =
no ship, no exceptions. Prompt: `prompts/P08` (independent gatekeeper session).

## Gate ladder (in order; each gate names its owner)

| # | Gate | Command | Pass condition | Owner |
|---|---|---|---|---|
| 1 | Fence validator (series) | `python3 scripts/batch/validate_series.py <slugs>` (or `--since <iso>` / `--all`) | every file PASS | worker |
| 2 | Fence validator (films) | `python3 scripts/batch/validate_films.py <slugs>` | every file PASS | worker |
| 3 | Dash strip | `python3 scripts/batch/fix_series.py <slugs>` then re-validate | 0 files changed on the re-run | worker |
| 4 | Content test suite | `python3 -m pytest tests/ -q` | 0 failures | floor / gatekeeper |
| 5 | Build + prebuild guards | `cd site && npm run build` | exit 0 (Western allowlist guard, no-AggregateRating check, `postbuild:filecap` under 20k files) | floor ONLY (cores) |
| 6 | Design gate (frontend changes only) | design-reviewer agent on the rendered change | score >= 7.5 | floor |
| 7 | Commit | descriptive message + trailer `Co-Authored-By: Claude <noreply@anthropic.com>` | only on green above | worker/floor |
| 8 | Push | `git pull --rebase && git push` | gate 4 green THIS tree; never --force; never branches you didn't create | floor |
| 9 | Deploy | `npx wrangler pages deploy site/out --project-name=bollyai-in --branch=main` | gates 4+5 (+6) green | floor, interactive only |
| 10 | Post-deploy verify | curl live URLs (below) | all 200 + content sane | floor |
| 11 | IndexNow | `scripts/indexnow_ping.sh` (hash-gated) | <= 85 URLs/wave, changed URLs only | floor |

Deploy creds: `~/.claude/vault/cloudflare-master.md` (god token; the plain `cloudflare.md`
Pages token does NOT scope bollyai-in - auth error 10000). ACCOUNT_ID
`18c1d9f76c2153a2dde6efa561116b17`. NEVER put the god token in GH secrets; the daily-refresh
Action has its own working token.

## Post-deploy verification (minimum set)

```bash
for u in / /browse /box-office /ott/calendar /series/mad-men /series/mad-men/where-to-watch; do
  echo "== $u"; curl -s -o /dev/null -w "%{http_code}\n" "https://bollyai.in$u"; done
# spot-check one page THIS ship changed, full-render:
curl -s https://bollyai.in/<changed-page> | grep -c -i -E 'bollywood|kollywood|tollywood'  # expect 0 on Western surfaces
```
Also confirm: newly shipped pages actually present in `site/out/` before deploy
(`ls site/out/series/<new-slug>/` for a sample).

## Who may do what (hard authority map)

- **Headless/unattended lanes**: validate + fix + commit ONLY. Never build (cores), never
  push, never deploy, never IndexNow, never wrangler, never secrets, never `--no-verify`.
- **Interactive floor (Opus 4.8)**: everything, in ladder order, with outputs pasted.
- Force-push, history rewrite, branch deletion: DENIED for everyone, always.
- The tree may carry OTHER sessions' uncommitted work: `git add` SPECIFIC paths you touched,
  never `git add -A`. If pytest fails on files you did not touch, STOP and report - do not
  "fix" another lane's WIP and do not push around it.

## Velocity + rollback

- NEW-page deploy waves are throttled (site-age spam-signal caution); confirm cadence
  against `data/_state/library-buildout.md` / Aditya before a large wave. Updates uncapped.
- Rollback = redeploy the previous green build: `git checkout <last-good-sha> -- .` is
  FORBIDDEN (history rules); instead `git revert` the bad commit, rebuild, redeploy. CF
  Pages also keeps prior deployments for instant restore from the dashboard (Aditya action).

## Red rules

Never commit red. Never push red. Never deploy on a stale build (rebuild after ANY data
change). Never claim "shipped" without gate 10 output in the report.
