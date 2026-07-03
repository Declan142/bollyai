# BLUEPRINT 02 - New series pages (batch authoring)

Use when: adding NEW Western series to `data/series/`. Prompts: `prompts/P01` (conductor),
`prompts/P02` (worker). Canonical authoring spec: `scripts/batch/AUTHORING_BRIEF.md` - this
blueprint is the orchestration + quality layer on top; the brief stays the field manual.

## Read order (conductor and workers)

1. `scripts/batch/AUTHORING_BRIEF.md` - full authoring spec + fences.
2. `site/lib/series.ts` - exact schema (Series / SeriesSeason / EpisodeReview).
3. `data/series/mad-men.json` - gold exemplar: shape, depth, tone.
4. `blueprints/01-QUALITY-BAR.md` - the constitution.
5. `data/_state/library-buildout.md` - ledger: counts, batch format, reserved slugs.

## Curation rules (where batches are won or lost)

- **Western allowlist only**: English-language leads; Western-European non-English
  (Spanish/German/French/Italian/Nordic) OK. The prebuild guard
  (`scripts/guard-offbrand-series.mjs`) fails the build on anything else. When in doubt
  about a language call, skip the title and note it.
- **Groundable only**: real English Wikipedia page + real critical reception. Too obscure
  or premiered days ago with no reviews = not authorable (fence #10, skip-if-thin).
- **No collisions**: `ls data/series/` first; exclude every existing slug. Check the
  ledger's reserved list (deep-lane slugs are never authored in batch).
- **Slug = kebab-case of the common English title**, must equal the filename.
- **Pool design**: 5-6 slugs per worker, pools DISJOINT by theme (US prestige / UK / crime /
  comedy / Euro), so no two workers ever touch the same slug.

## Pipeline (one batch, end to end)

1. **Plan** - conductor curates pools per the rules above (existing-check + reserved-check).
2. **Dispatch** - one P02 worker per pool. Fire worker 1 alone first, then the rest in
   parallel once its stream starts (prompt-cache warm-up). Sonnet, effort medium.
3. **Worker loop (per slug)**: ground (Wikipedia -> QID -> reception with URLs) -> write
   JSON via python json.dump -> `fix_series.py` -> `validate_series.py` -> next slug.
   A slug that can't be grounded is SKIPPED with a reason, never faked.
4. **Reconcile (conductor, effort xhigh)** - for EVERY new file:
   - any season dated 2025/2026: re-verify release date + status against a live source;
   - any verdict that looks generous for a show known to be divisive: re-check RT/reception,
     downgrade or null what you cannot confirm;
   - `genres` present, 2-5 tags from the brief's controlled set (no nationality tags);
   - poster block present with the fair-dealing + takedown attribution line;
   - spot-read 2 random `review_body` fields against QUALITY-BAR section 8.
5. **Ingest** - `bash scripts/batch/ingest_batch.sh <all new slugs>` (fix -> validate ->
   posters -> build). Run FOREGROUND with a long timeout and wait in the SAME turn -
   backgrounding it and ending the turn loses the batch (regression of 2026-06-16).
   Only the box owner runs this: a solo headless tick may; parallel fleet workers NEVER
   build (`npm run build` storms all cores - floor builds once, centrally).
6. **Commit** - only if green:
   `git add data/series/ site/public/img/series/ data/_state/library-buildout.md`
   Message: `bollyai: series batch - <n> new (<pool names>)` + trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Never commit red. No push from lanes.
7. **Ledger** - bump Progress count, append a batch entry in the existing format
   (batch number, date, count, pool lines, validate/build status, poster count).

## Season + episode depth for NEW pages

- Every season: full SeriesSeason object (verdict, bollymeter full-or-null, critic block
  with real pull_quotes or empty, audience block real-or-null, 90-160 word `review_body`,
  `season_over_season` one line or null for S1).
- `episode_reviews` on new pages: 2-4 STANDOUT hours per flagship season (premiere, finale,
  the argued-about turn), 0 is fine for lesser seasons. Card fields only (number, real title,
  air_date, bollymeter or null, spoiler_free, the_moment, critic_note real-or-null).
  Rich full bodies are the episode-review lane's job (`03-EPISODE-REVIEWS.md`), not this one.

## Failure protocol

- Validator failure: fix and re-run until PASS; a file that cannot pass honestly gets
  deleted and reported as skipped.
- Ingest/build failure: fix and re-run ONCE; still red = log to
  `data/_state/buildout-loop.log`, do NOT commit, exit with a clean report.
- Ambiguity twice on the same item = drop the item, log it, move on. A skipped slug costs
  nothing; a fabricated one is the worst failure the system has.

## Definition of done

All new slugs PASS `validate_series.py`; build green (when box owner); ledger updated;
commit made (or an explicit no-commit report with reasons); conductor report lists
written/skipped/fixed with one-line notes.
