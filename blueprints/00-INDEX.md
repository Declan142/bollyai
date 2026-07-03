# BollyAI Blueprints - the execution layer (read this first)

> Purpose: let ANY Claude session (Sonnet worker, Opus 4.8 conductor, headless cron)
> produce work on this repo at flagship quality WITHOUT rediscovering the rules.
> Every blueprint is grounded in this repo's validators, tests, and shipped specs.
> Where a blueprint and a validator disagree, THE VALIDATOR WINS - then fix the blueprint.

## What BollyAI is (one breath)

Western cinema/TV answer engine at bollyai.in. Disclosed-AI critic: **BollyAI has NOT
watched anything. BollyAI has read everyone who has.** Next.js static export, JSON-in-repo
(no database), Cloudflare Pages. Two desks: hollywood (films, QID-keyed) + streaming
(Western series, slug-keyed). ~466 series live, ~72 films. Quality is enforced by
build-breaking gates, not by trust.

## How to use this pack

1. Find your task in the routing table below.
2. Read the blueprint (the WHY + the full procedure + the worked examples).
3. Copy the matching prompt from `blueprints/prompts/`, fill every `{{PLACEHOLDER}}`,
   launch the session. The prompt is the mission brief; the blueprint is the field manual
   it points back into.
4. Writing lanes ALWAYS read `01-QUALITY-BAR.md` before producing prose. No exceptions.
   It is the distilled constitution of every honesty gate and style rule in the repo.

## The doctrine (why output is outstanding, mechanically)

1. **Ground before you write.** Facts come from Wikipedia/Wikidata, real reviews with URLs,
   or the subtitle dossier. A fact you cannot source does not go on the page. Skip beats
   fabricate, always: a missing file/field is correct, an invented one is a fireable offense.
2. **Mode B honesty.** Most episodes have zero documented per-episode reception. The page is
   still excellent because BollyAI argues its OWN craft read. It never manufactures critics.
   (The 2026-06-14 incident: ~14,700 invented "Critics noted..." attributions, caught at the
   gate, 0 shipped. The attribution gate now breaks the build.)
3. **Two-pass writing.** Draft, then a polish pass that re-reads the full house-style
   contract and sweeps the kill-list. The contract re-read IS the quality mechanism.
4. **Gates are the approval** (standing grant, Aditya 2026-06-13): validate -> pytest ->
   build -> (design-review >= 7.5 if frontend) -> commit -> push -> deploy. Skip a gate =
   no ship. Workers validate; the floor builds, pushes, deploys.
5. **Fresh sessions, state in files.** Lanes read state from the repo, do one batch, write
   state back (ledger/log), exit. Never trust session memory across batches.
6. **Judge before accept.** Conductors spot-read worker output against the rubric before
   committing it. Trust no self-report; re-run the validator yourself.

## Routing table

| Task | Blueprint | Prompt | Model | Effort |
|---|---|---|---|---|
| Author NEW series pages (batch) | `02-SERIES-AUTHORING.md` | P01 (conductor) + P02 (workers) | Opus 4.8 + Sonnet workers | medium; xhigh on reconcile |
| Rich episode reviews (expand/upgrade a series) | `03-EPISODE-REVIEWS.md` | P03 (conductor) + P04 (workers) | Opus 4.8 + Sonnet writers; Opus writes flagships | medium; xhigh on spot-review |
| Author film pages (hollywood desk) | `04-FILMS-DESK.md` | P05 | Sonnet, Opus verifies numbers | medium |
| Endings / predictions / recommendation lists | `05-COMPANION-SURFACES.md` | P06 | Sonnet, Opus spot | medium |
| Freshness / returning seasons / calendars | `06-REFRESH-OPS.md` | P07 | Sonnet (headless-safe) | medium |
| Pre-ship QA + deploy | `07-QA-SHIP.md` | P08 | Sonnet mechanical + Opus judgment | xhigh on verdicts |
| Frontend feature / redesign | `07-QA-SHIP.md` + design skills | P09 | Opus 4.8 | xhigh |

## Model + effort discipline (why the split)

- **Sonnet = the volume engine.** Drafting, grounding fetches, mechanical gates, refresh
  ticks. Effort medium. Sonnet with a filled prompt + the QUALITY-BAR produces shippable
  drafts; the system's honesty lives in the gates, not in model heroics.
- **Opus 4.8 = the scarce judgment layer.** Batch curation, reconcile passes, spot-reviews,
  verdict/score sanity, design direction, anything ambiguous. Effort xhigh ONLY on those
  judgment turns, medium otherwise. Never spend Opus on bulk typing.
- **Flagship exception:** series the site trades on (top-searched, homepage rails) get
  Opus-written rich reviews (P04 with Opus) because the ceiling matters there.
- **Cache warm-up rule:** when fanning out parallel workers, fire ONE first, wait for its
  stream to start, then launch the rest together.
- **Box capacity rule:** `npm run build`, design-reviewer (headless Chrome), and pytest over
  the full catalogue are FLOOR-ONLY, run serially. Parallel workers never build; they
  validate their own slugs only (cheap). More remote calls per lane beats more lanes.

## Lifecycle walkthroughs (which lanes fire, in order)

**A new season of a tracked show drops:**
1. P07 refresh tick (or the daily Action) catches it -> series JSON gets the new season
   shell (real release_date envelope, verdict/bollymeter null, renewal updated).
2. Floor queues the season in P03 -> P04 writes rich episode reviews as episodes air
   (depth-first within the season).
3. Pre-finale: P06 predictions page. Post-finale: P06 ending-explained; retire/refresh the
   predictions page in the same pass.
4. P08 gatekeeper -> floor ships the wave.

**Cold-start a new show (not in catalogue):**
P01/P02 batch (or a single P02 with one pool) -> poster harvest via ingest -> then the
season lifecycle above. New-page deploys are velocity-throttled; updates are not.

**Weekly rhythm (steady state):**
Daily Action refreshes data (10:00 IST). P07 tick for facts the Action can't verify.
P03/P04 grind the episode-review gap queue. P06 fills companion gaps for finished shows.
P08 + floor ship in waves. `06-REFRESH-OPS.md` has the cron map.

## Global fences (every lane inherits these, on top of its own)

1. No first-person viewing claims, any language (gate: `engine/gates/viewing_claim_regex.py`).
2. No unbacked critic/reviewer/audience attribution (gate: `engine/gates/attribution_regex.py`,
   scope-matched - see QUALITY-BAR section 2).
3. No fancy dashes anywhere, FOUR codepoints: em (U+2014), en (U+2013), figure (U+2012),
   horizontal bar (U+2015). Use a spaced hyphen ` - ` or restructure. (Tests gate all four;
   sweep with `grep -rP '[\x{2012}-\x{2015}]'`.)
4. No fabricated numbers (Indian OTT view counts, RT% without sample, invented grosses).
   Unsure = null/omit.
5. Western brand lock: series must pass the original-language allowlist guard
   (`scripts/guard-offbrand-series.mjs`); films must be `canonical_industry: "hollywood"`
   (`scripts/guard-offbrand-films.mjs`). Never author Korean/Japanese/Indian titles.
6. TMDB = metadata only, never images (ToS). No JustWatch scraping, no IMDb datasets,
   no Letterboxd. Served images = self-hosted press under Sec 52(1)(a) + attribution +
   /takedown route.
7. Never serve subtitle text. Subtitles are private fuel; dialogue quotes <= 25 words,
   attributed to the character, sourced from the dossier only.
8. Unattended lanes: never deploy, never IndexNow, never wrangler, never push --force,
   never touch `.env` or `~/.claude/vault`, never `git push` (floor pushes after pytest).
9. Mutate JSON via a python `json.load -> edit dict -> json.dump` script. Never string-edit
   JSON with sed or substring Edits (curly-quote corruption incident).
10. Never overwrite an existing data file without reading it first; never delete content
    you did not author in this session; `git add` specific paths, never `-A`.

## Escalation matrix (what to do when it goes sideways)

| Situation | Action |
|---|---|
| A slug/episode cannot be grounded | Skip it, one-line reason in the report. Never pad |
| Validator red twice on the same item after honest fixes | Drop the item, log to `data/_state/buildout-loop.log`, continue the batch |
| Two consecutive items dropped for the same cause | Systemic - stop the lane, report the pattern instead of grinding |
| pytest red on files you did NOT touch | STOP. Classify as pre-existing, name the likely owner, do not fix another lane's WIP, do not push |
| Conductor finds a worker fabricating | Reject the whole pool to a FRESH worker; note the failure pattern in the report |
| Anything needs deploy/IndexNow/secrets in an unattended lane | Refuse, log, leave it for the floor |
| Placeholder unfilled in your prompt | Abort immediately, say which one |

## Repo source-of-truth map

| What | Where |
|---|---|
| Series schema (types) | `site/lib/series.ts` |
| Film schema (types + verdict ladder + confidence vocab) | `site/lib/data.ts` |
| Series gold exemplar | `data/series/mad-men.json` |
| Series authoring spec | `scripts/batch/AUTHORING_BRIEF.md` |
| Episode review writer's contract | `scripts/subtitles/REVIEW-HOUSE-STYLE.md` (v4) |
| Rich review architecture | `scripts/subtitles/RICH-REVIEW-SPEC.md` |
| Dossier spec (subtitle grounding) | `scripts/subtitles/DOSSIER_SPEC.md` |
| Fence validators | `scripts/batch/validate_series.py`, `scripts/batch/validate_films.py` |
| Mechanical dash fixer | `scripts/batch/fix_series.py` |
| Honesty gates (regex) | `engine/gates/viewing_claim_regex.py`, `engine/gates/attribution_regex.py` |
| Content tests (build gate) | `tests/` - run `python3 -m pytest tests/ -q` |
| Companion exemplars | `data/endings/from.json`, `data/predictions/from.json`, `data/recommendations/best-british-mysteries.json` |
| Buildout ledger | `data/_state/library-buildout.md` |
| Batch ingest (fix -> validate -> posters -> build) | `scripts/batch/ingest_batch.sh` |
| Poster harvesters | `scripts/harvest_series_posters.py` + `scripts/harvest_*.py` |
| Staging -> live merge (engine path) | `scripts/subtitles/merge_reviews.py` |
| GHA crons | `.github/workflows/*.yml` (schedule table in `06-REFRESH-OPS.md`) |

## Pack maintenance

A fence changes in exactly this order: validator/test first, then `01-QUALITY-BAR.md`,
then any blueprint/prompt that inlines it - same commit. If you find drift between this
pack and a validator, the validator is right; fix the pack in the same commit as your
content work and say so in your report. Never "improve" a fence from inside a content
lane; propose it to the floor.
