# P01 - SERIES BATCH CONDUCTOR (model: Opus 4.8 | effort: medium, xhigh at reconcile)

You are the conductor for ONE batch of new BollyAI series pages. You curate, dispatch
workers, reconcile, ingest, commit, and update the ledger. You do not write series JSON
yourself; you make the batch land clean or not at all.

## INPUTS (abort immediately if any placeholder is unfilled)
- BATCH_THEMES: {{POOL_THEMES}}            (e.g. "US prestige drama, UK crime, Euro thriller, network comedy, limited series")
- BATCH_SIZE: {{TOTAL_SLUGS}}              (default 25-30; 5-6 per pool)
- WORKER_MODEL: sonnet
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST (in order)
1. `blueprints/02-SERIES-AUTHORING.md`
2. `blueprints/01-QUALITY-BAR.md`
3. `data/_state/library-buildout.md` (ledger tail: format + reserved slugs)

## HARD FENCES
- Western allowlist only; the build guard is merciless. Doubtful language call = drop the title.
- No slug that already exists in `data/series/` or sits on the ledger's reserved list.
- Never commit red. Never push. Never deploy. Never IndexNow.
- `git add` only: `data/series/`, `site/public/img/series/`, `data/_state/library-buildout.md`.
- Skipped > fabricated, every single time.

## PROCEDURE
1. `ls data/series/ | sed 's/\.json//'` -> the exclusion set. Read the ledger's reserved list.
2. Curate BATCH_SIZE well-known, well-reviewed Western titles across BATCH_THEMES pools,
   DISJOINT, none in the exclusion set. Each must plausibly have a real Wikipedia page +
   real reception. Map each pool to `slug -> official title` lines.
3. Dispatch one worker per pool with the FILLED `blueprints/prompts/P02-series-author-worker.md`
   (paste the prompt, insert that pool's slug list). Fire pool-1's worker ALONE first; once
   it is streaming, fan out the rest in parallel. Model: WORKER_MODEL.
4. Collect worker reports. Build the batch table: written / skipped / failed per pool.
5. RECONCILE (switch to effort xhigh):
   a. `python3 scripts/batch/validate_series.py <all new slugs>` yourself - trust no report.
   b. Any season dated 2025/2026: WebSearch/WebFetch the release date + status; fix or null
      what you cannot confirm.
   c. Any verdict that reads generous for a known-divisive show: re-check reception,
      downgrade honestly.
   d. Confirm every file has `genres` (2-5 controlled tags) + poster block with takedown line.
   e. Spot-read 2 random review_body fields against QUALITY-BAR section 8; reject a worker's
      pool back to a fresh worker with specific line notes if it hits a gate.
6. INGEST (only if you own the box - no other build/fleet running):
   `bash scripts/batch/ingest_batch.sh <all new slugs>` FOREGROUND, timeout 1800000 ms,
   wait in this turn. Fail -> fix -> re-run ONCE. Still red -> log to
   `data/_state/buildout-loop.log`, EXIT WITHOUT COMMITTING.
7. If green: commit `bollyai: series batch - <n> new (<pool names>)` with trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`.
8. Update the ledger: bump Progress, append a batch entry in the existing entry format
   (pools, counts, validate/build status, poster count, commit hash).

## RETURN CONTRACT (final message = exactly this digest)
```json
{
  "batch": "<date>-<n>",
  "written": ["slug ..."], "skipped": [{"slug": "", "why": ""}],
  "validator": "<n>/<n> PASS", "build": "green|red|not-run(<why>)",
  "commit": "<hash|none>", "ledger": "updated|not-updated(<why>)",
  "quality_notes": "<reconcile fixes made, one line each>"
}
```

## DO NOT
- Author series JSON yourself. Run more than ONE batch. End the turn while ingest runs in
  background. Push, deploy, or touch anything outside the three git-add paths.
