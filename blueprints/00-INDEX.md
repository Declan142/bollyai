# BollyAI Blueprints - the execution layer (read this first)

> Purpose: let ANY Claude session (Sonnet worker, Opus 4.8 conductor, headless cron)
> produce work on this repo at flagship quality WITHOUT rediscovering the rules.
> Every blueprint is grounded in this repo's validators, tests, and shipped specs.
> Where a blueprint and a validator disagree, THE VALIDATOR WINS - then fix the blueprint.

## What BollyAI is (one breath)

Western cinema/TV answer engine at bollyai.in. Disclosed-AI critic: **BollyAI has NOT
watched anything. BollyAI has read everyone who has.** Next.js static export, JSON-in-repo,
CF Pages. Two desks: hollywood (films) + streaming (Western series). 466 series live.
Quality is enforced by build-breaking gates, not by trust.

## The doctrine (why output is outstanding, mechanically)

1. **Ground before you write.** Facts come from Wikipedia/Wikidata, real reviews with URLs,
   or the subtitle dossier. A fact you cannot source does not go on the page. Skip beats
   fabricate, always: a missing file/field is correct, an invented one is a fireable offense.
2. **Mode B honesty.** Most episodes have zero documented per-episode reception. The page is
   still excellent because BollyAI argues its OWN craft read. It never manufactures critics.
   (The 2026-06-14 incident: ~14,700 invented "Critics noted..." attributions, caught at the
   gate, 0 shipped. The attribution gate now breaks the build.)
3. **Two-pass writing.** Draft, then a polish pass that re-reads the full house-style
   contract and sweeps the kill-list. The re-read IS the quality mechanism.
4. **Gates are the approval.** validate -> pytest -> build -> (design-review if frontend)
   -> commit -> push -> deploy. Skip a gate = no ship. Workers validate; the floor builds,
   pushes, deploys.
5. **Fresh sessions, state in files.** Lanes read state from the repo, do one batch, write
   state back, exit. Never trust session memory across batches.

## Routing table

| Task | Blueprint | Prompt | Model | Effort |
|---|---|---|---|---|
| Author NEW series pages (batch) | `02-SERIES-AUTHORING.md` | P01 (conductor) + P02 (workers) | Opus 4.8 + Sonnet workers | medium; xhigh on reconcile |
| Rich episode reviews (expand/upgrade a series) | `03-EPISODE-REVIEWS.md` | P03 (conductor) + P04 (workers) | Opus 4.8 + Sonnet writers | medium; xhigh on spot-review |
| Author film pages (hollywood desk) | `04-FILMS-DESK.md` | P05 | Sonnet, Opus verifies numbers | medium |
| Endings / predictions / recommendation lists | `05-COMPANION-SURFACES.md` | P06 | Sonnet, Opus spot | medium |
| Freshness / returning seasons / calendars | `06-REFRESH-OPS.md` | P07 | Sonnet (headless-safe) | medium |
| Pre-ship QA + deploy | `07-QA-SHIP.md` | P08 | Sonnet mechanical + Opus judgment | xhigh on verdicts |
| Frontend feature / redesign | `07-QA-SHIP.md` + design skills | P09 | Opus 4.8 | xhigh |

Every writing lane ALSO reads `01-QUALITY-BAR.md` - it is the shared constitution.

## Session recipes

- **Interactive floor (Opus 4.8):** open the repo, read the relevant blueprint, paste the
  conductor prompt with placeholders filled. The floor owns build/push/deploy.
- **Headless one-shot:** fill placeholders into a copy of the prompt, then
  `claude -p "$(cat /tmp/filled-prompt.md)" --model sonnet` from the repo root.
  Headless lanes NEVER deploy, NEVER IndexNow, NEVER touch secrets (see fences below).
- **Fleet:** conductor session dispatches workers via the Agent tool, one prompt each,
  disjoint slugs. Fire ONE worker first, wait for its stream to start (cache warm-up),
  THEN fan out the rest in parallel.
- **Placeholders:** `{{LIKE_THIS}}`. A prompt with an unfilled placeholder must abort
  immediately and say so.

## Global fences (every lane inherits these, on top of its own)

1. No first-person viewing claims, any language (gate: `engine/gates/viewing_claim_regex.py`).
2. No unbacked critic/reviewer/audience attribution (gate: `engine/gates/attribution_regex.py`,
   scope-matched - see QUALITY-BAR).
3. No em-dash / en-dash / horizontal bar (U+2014, U+2013, U+2015) anywhere. Spaced hyphen ` - `.
4. No fabricated numbers (Indian OTT view counts, RT% without sample, invented grosses).
   Unsure = null/omit.
5. Western brand lock: series must pass the allowlist guard (`scripts/guard-offbrand-series.mjs`);
   films must be `canonical_industry: "hollywood"`. Never author Korean/Japanese/Indian titles.
6. TMDB = metadata only, never images. No JustWatch scraping, no IMDb datasets, no Letterboxd.
7. Never serve subtitle text. Subtitles are private fuel; dialogue quotes <= 25 words, attributed.
8. Unattended lanes: never deploy, never IndexNow, never wrangler, never push --force, never
   touch `.env` or `~/.claude/vault`, never `git push` (floor pushes after pytest).
9. Mutate JSON via a python json.load -> edit dict -> json.dump script. Never string-edit JSON.
10. Never overwrite an existing data file without reading it first; never delete content you
    did not author in this session.

## Repo source-of-truth map

| What | Where |
|---|---|
| Series schema (types) | `site/lib/series.ts` |
| Film schema (types) | `site/lib/data.ts` |
| Series gold exemplar | `data/series/mad-men.json` |
| Series authoring spec | `scripts/batch/AUTHORING_BRIEF.md` |
| Episode review writer's contract | `scripts/subtitles/REVIEW-HOUSE-STYLE.md` |
| Rich review architecture | `scripts/subtitles/RICH-REVIEW-SPEC.md` |
| Dossier spec (subtitle grounding) | `scripts/subtitles/DOSSIER_SPEC.md` |
| Fence validators | `scripts/batch/validate_series.py`, `scripts/batch/validate_films.py` |
| Mechanical dash fixer | `scripts/batch/fix_series.py` |
| Honesty gates (regex) | `engine/gates/viewing_claim_regex.py`, `engine/gates/attribution_regex.py` |
| Content tests (build gate) | `tests/` (run `python3 -m pytest tests/ -q`) |
| Buildout ledger | `data/_state/library-buildout.md` |
| Batch ingest | `scripts/batch/ingest_batch.sh` |
| Poster harvesters | `scripts/harvest_series_posters.py` + `scripts/harvest_*.py` |
| Staging -> live merge (engine path) | `scripts/subtitles/merge_reviews.py` |
| GHA crons | `.github/workflows/*.yml` |

## Maintenance rule

A fence changes in exactly this order: validator/test first, then `01-QUALITY-BAR.md`,
then any prompt that inlines it. If you find drift between a prompt and a validator,
the validator is right; fix the prompt in the same commit as your content work and say so
in your report.
