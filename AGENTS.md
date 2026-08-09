# BollyAI — Agent Instructions (Codex / any coding agent)

Claude Code reads the user's global `~/.claude/CLAUDE.md` plus this repo's `CLAUDE.md` (project layer — read that for full depth on the honesty fences). Codex CLI and every other coding agent read this file instead. Same fences, condensed for a cold start with zero prior context.

## ⚠️ Read first

- **You are almost certainly not on `main`.** Verified 2026-08-09: HEAD here sits on `codex/sol-max-bolly-integration-20260809`, a throwaway audit branch (4 ahead / 29 behind `main`; `main` itself is in sync with `origin/main`). Tree is dirty from that audit (`last.txt` modified, `SOL-STRANDED-LANES-20260809.md` + `SOURCE-PROCUREMENT-20260809.md` untracked at root). Run `git branch --show-current` before your first commit. **6 more worktrees** live under `/home/aditya/worktrees/*` — never touch one you didn't create. Two of them (`codex/bollyai-worldclass-site-20260801`, `fix/bollyai-weekly-contract-20260726` / `feat/boxoffice-weekly-source-engine`) were audited today and recommended **ABANDON** — don't resume them without asking first.
- **`site/node_modules` is contaminated right now**: `next/package.json` inside it reports `15.5.22` while `site/package.json` + `package-lock.json` pin `^14.2.30` (leftover from testing an abandoned Next-15 lane in this same tree). Always `npm ci` before `build`/`dev`.
- **Box office is deliberately empty, not broken.** `data/boxoffice/current-week.json` is `DATA_PENDING: true`, `records: []` (last generated 2026-07-25, 51/51 titles stale). Fail-closed by design — see Hard gates.

## What this repo is

Western (English + Western-European) film/TV answer engine at bollyai.in, `github.com/Declan142/bollyai`. Disclosed-AI critic voice: "BollyAI has NOT watched anything. BollyAI has read everyone who has." Brand-locked 2026-06-26 to WESTERN-ONLY (Korean/Japanese/Indian archived, enforced by a build-time allowlist guard). Stack: Next.js **14.2.30** (`site/`, App Router, static export, Cloudflare Pages project `bollyai-in`) + Python 3.12 fetch/gen engine (no requirements.txt — `requests`/`PIL`/`yaml`/`openai` assumed pre-installed ambient) + JSON-in-repo under `data/` (no database). Two desks: Hollywood (films, QID-keyed) + Streaming (series, slug-keyed). Verified counts 2026-08-09: **480 series, 72 films**. The moat is the subtitle-grounded episode recap engine (`scripts/subtitles/`), not the box-office tracker.

## Layout

- `site/` — Next.js static export; build output `site/out/`, **not** `dist/`.
- `data/series/*.json`, `data/films/*.json` — rendered catalogue (schema: `site/lib/series.ts` / `site/lib/data.ts`; gold exemplar `data/series/mad-men.json`).
- `data/_archive/non-western/{korean,japanese,indian,foreign}` — reversible pre-brand-lock archive; never author into these.
- `data/_state/` — ledgers (`library-buildout.md`, `staleness.json`, `changed-urls.json` for IndexNow) — read before batches, never rendered.
- `data/subtitles/` — private subtitle corpus, gitignored, **never** served/committed (legal fence, CLAUDE.md gate #8).
- `engine/fetchers/` — live data pulls (Wikidata/TMDB/box office); `engine/gates/` — honesty-regex build gates.
- `scripts/batch/` — series authoring pipeline + `validate_series.py` (the honesty-fence gate).
- `scripts/subtitles/` — the recap/dossier engine; house-style + spec docs live here.
- `blueprints/` — task-routing pack for writing/refresh/QA lanes; read `00-INDEX.md` first.
- `tests/` — pytest content + gate suite: **234 passed, 3.3s** (verified 2026-08-09, this branch).
- `.github/workflows/` — 5 crons, all LLM-free data refresh.

## Build / dev / test / deploy

```
cd site && npm ci                    # ALWAYS first — see node_modules warning above
cd site && npm run build             # prebuild (brand guards, sitemaps, search/ask index) -> next build -> lint:aggregate -> postbuild:filecap (CF 20k-file cap)
npx next dev                         # no "dev" script in package.json — invoke next directly
python3 -m pytest tests/ -q          # 234 passed, 3.3s
python3 scripts/batch/validate_series.py <slug...>   # must pass before any content commit
```
No `npm run lint` / `npm test` at the JS layer — `lint:aggregate` (inside `build`) is the only JS check; all content/gate testing is pytest.

Deploy is normally automatic: `daily-refresh` (04:30 IST), `friday-surge` (Fri x3), `ott-calendar-roll` (Mon/Thu), `tentpole-live` (every 3h Fri–Mon) each fetch → build → `wrangler pages deploy site/out --project-name=bollyai-in --branch=main` → IndexNow delta, gated on GH secrets `CLOUDFLARE_API_TOKEN`/`CLOUDFLARE_ACCOUNT_ID`/`INDEXNOW_KEY`/`TMDB_API_KEY`. `health-digest` is read-only (no deploy). Manual fallback: `scripts/deploy-manual.sh --execute` (dry-run by default; reads creds from env, not vault — export them yourself, e.g. from `~/.claude/vault/cloudflare-master.md`).

## Hard gates

- 10 honesty fences in `CLAUDE.md` (§"BollyAI honesty fences") — no first-person viewing claims, no em/en-dash, no fabricated Indian OTT numbers, `bollymeter` full-object-or-null, real attributed `pull_quotes`, no TMDB images served, box-office publish rule (≥2 independent sources within 10%), never guess a Wikidata QID, skip beats fabricate.
- Box office is **intentionally** fail-closed: `SOURCE-PROCUREMENT-20260809.md` (repo root) found no off-the-shelf vendor pair clears the "two independent groups" bar at small-site budget — Gower Street/BFI/OpusData all trace back to Comscore or are enterprise-only/unpriced. Don't wire a single-source feed into the board to "fix" the empty state; that violates the publish-rule gate.
- Western brand lock: `guard-offbrand-series.mjs` / `guard-offbrand-films.mjs` fail the build on any non-Western series or non-`hollywood` film in `data/`.
- `assert-no-aggregate-rating.mjs` (via `lint:aggregate`) and the CF 20k-file cap (`postbuild:filecap`) are hard build-breakers. design-reviewer ≥ 7.5 before any frontend ships.

## Non-negotiable safety

- Never `git push --force`, `git reset --hard origin/*`, `--no-verify`, `rm -rf $HOME/*`.
- `git push` (non-force) to `main` is standing-granted (Aditya, 2026-06-13) **only** when validate + pytest + build (+ design-review for frontend) are green — a skipped gate is no push.
- Never commit `.env*`, `.azure-env.sh`, or credentials. Vault is `~/.claude/vault/` (outside this repo) — read only the exact path you're told, never dump or print it.
- Never touch `~/.claude/`, `~/.codex/`, `~/.ssh/`, `~/.aws/`, `~/.gnupg/`, browser profiles.
- Never delete a branch or worktree you didn't create.
- Infra: Cloudflare Pages only, no Docker/Vercel/Supabase/Firebase/Railway/Render/Fly. No paid vendor (see box-office gate) without explicit approval.
- Never claim "done" from a write alone — state the command run, its actual output, and the changed files.

## Do not touch / never commit

- `data/subtitles/` — gitignored legal fence, never a git object.
- `site/out/`, `site/.next/`, `site/node_modules/`, `_cache/`, `data/cache/*` — generated/ignored.
- `.conductor-*.md`, `.briefs/`, `BLITZ-PLAN.md`, `.film-authoring-brief.md` — gitignored scratch.
- `data/_archive/**` — reversible cull storage; don't un-archive without an explicit instruction.
- Never hand-edit `data/series|films/*.json` with sed/substring replace — mutate via `json.load → edit dict → json.dump` (curly-quote corruption precedent); never overwrite without reading first.

## Commits & branches

- Feature branches `{purpose}/{slug}`; trailer `Co-Authored-By:` for the acting agent.
- Confirm `git branch --show-current` before your first commit — see the ⚠️ hazard above.
- Stage explicit paths, never `git add -A` — other lanes' WIP and untracked root docs routinely sit in this tree.
- `RESUME.md` is the pickup log (newest entry at top) — append, don't rewrite history.
