# BollyAI Box Office Data

This directory feeds the `/box-office/` namespace. It is separate from `data/films/` so the weekly board can be updated without touching film or series authoring lanes.

Blueprint namespace:

- `/box-office/` - current cross-industry board.
- `/box-office/<tier>-crore-club/` - cross-industry club trackers.
- `/{industry}/box-office/{YYYY}/` - industry year scoreboards.

## Schema

`current-week.json` is live on `schema: bollyai-boxoffice-week/v2` (Western rebuild,
commit `3ce98b7`, 2026-06-27). It is written by `engine/fetchers/boxoffice_western.py`,
not by the India pipeline below.

Each v2 record includes:

- `film`: `{title, type, qid, slug, url}`. Use `qid: null` when not verified. Never guess a QID.
- `language` and `industry` (`hollywood` or `streaming` - Western brand only, no South-first list).
- `territory`: always `Worldwide`.
- `release_date`.
- `worldwide_gross_usd`: `{value, sources, label}`. `value` is `null` or a plain USD number
  (not an INR crore range). `sources` must be visible public URLs.

Note on IDs: the master blueprint has an earlier `tmdb_id` spine ruling, but its 2026-06-07 amendment drops TMDB and promotes Wikidata QID as primary. This repo follows the amendment and the active project guide: QID primary, no TMDB images, no guessed IDs.

**Known gap (flagged 2026-07-04, unresolved):** `worldwide_gross_usd` is filled directly
from a single Wikidata or TMDB reading (see `fetch_wikidata_boxoffice` /
`fetch_tmdb_boxoffice`) and is never run through the two-source `publish_rule` gate below -
the frontend (`getPublishedWorldwideGrossUsd` in `site/lib/boxoffice.ts`) renders whatever
`value` is in the file. This is a real gap against the pair-verify honesty fence
(`01-QUALITY-BAR.md` Gate 4) and needs a product decision (add a second independent source
before publish, or badge single-source figures as `trade estimate` more visibly) - not
silently fixed inside a test-alignment pass.

## Publish Rule (legacy India pipeline, `engine/fetchers/boxoffice.py`)

`india_net_inr_cr` / `worldwide_gross_inr_cr` / `india_gross_inr_cr` figures (not part of
the live v2 record shape, but the dataclasses and rule below are still exercised by
`tests/test_boxoffice_publish_rule.py`) go through this hard rule in Python and its
TypeScript mirror:

- Two independent source readings within 10 percent render the lower reading as `trade estimate`.
- Independent readings 10 to 25 percent apart render only the lower figure with a caveat.
- Single-source rows, PR-only pairs, and readings more than 25 percent apart render as `tracking`.
- Budgets and salaries are not part of this schema and must never be auto-published.

## Current Status

The Western v2 board (`current-week.json`) is filled by `boxoffice_western.py`'s TMDB/Wikidata
fetch, wired into `engine/fetchers/run_all.py`'s daily-refresh Action.

The legacy India fill mode below is decoupled from `run_all.py` (2026-06-27) so the daily
Action cannot re-add Indian data; it remains only as dormant code + test fixtures.

## Legacy Fill Steps (India pipeline, dormant)

1. Gather raw readings for the same metric and territory, such as India nett in crore for week `2026-06-08` to `2026-06-14`.
2. Add each reading to the relevant figure's `sources` array with `name`, `url`, `as_of`, optional `group`, and numeric `value`.
3. Keep `value: null` unless the renderer computes a publishable figure from the source readings.
4. Run `python3 -m pytest tests/`.
5. Run `cd site && npm run build`.
6. Flip `DATA_PENDING` to `false` only after at least one row has a renderer-publishable figure and the page still shows attribution.
