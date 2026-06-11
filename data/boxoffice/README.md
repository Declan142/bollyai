# BollyAI Box Office Data

This directory feeds the `/box-office/` namespace. It is separate from `data/films/` so the weekly board can be updated without touching film or series authoring lanes.

Blueprint namespace:

- `/box-office/` - current cross-industry board.
- `/box-office/<tier>-crore-club/` - cross-industry club trackers.
- `/{industry}/box-office/{YYYY}/` - industry year scoreboards.

## Schema

Weekly files use `schema: bollyai-boxoffice-week/v1`.

Each record must include:

- `film`: `{title, type, qid, slug, url}`. Use `qid: null` when not verified. Never guess a QID.
- `language` and `industry`. Keep rows South-first: Tollywood, Kollywood, Mollywood, Sandalwood, Bollywood, Hollywood, Streaming.
- `week`: `{start, end, label}`.
- `territory`: usually `India`.
- `india_net_inr_cr` and `worldwide_gross_inr_cr`, each as `{value, sources, label}`.

`value` is either `null` or a `{low, high}` crore range. `sources` must be visible public URLs. Source objects may include a private-to-renderer `value` field for source readings, but the page will not show any amount unless the renderer-side publish rule passes.

Note on IDs: the master blueprint has an earlier `tmdb_id` spine ruling, but its 2026-06-07 amendment drops TMDB and promotes Wikidata QID as primary. This repo follows the amendment and the active project guide: QID primary, no TMDB images, no guessed IDs.

## Publish Rule

The page enforces the hard box-office rule in TypeScript:

- Two independent source readings within 10 percent render as `trade estimate`.
- Independent readings 10 to 25 percent apart render only the lower figure with a caveat.
- Single-source rows, PR-only pairs, and readings more than 25 percent apart render as `tracking`.
- Budgets and salaries are not part of this schema and must never be auto-published.

## Current Status

`current-week.json` is intentionally `DATA_PENDING: true`.

Live search on 2026-06-12 found current pointers for Peddi, Karuppu, Drishyam 3, and Hai Jawani Toh Ishq Hona Hai, but not enough same-metric independent readings to publish a weekly figure. The hub therefore ships with tracked rows and source attribution, not amounts.

## Fill Steps

1. Gather raw readings for the same metric and territory, such as India nett in crore for week `2026-06-08` to `2026-06-14`.
2. Add each reading to the relevant figure's `sources` array with `name`, `url`, `as_of`, optional `group`, and numeric `value`.
3. Keep `value: null` unless the renderer computes a publishable figure from the source readings.
4. Run `python3 -m pytest tests/`.
5. Run `cd site && npm run build`.
6. Flip `DATA_PENDING` to `false` only after at least one row has a renderer-publishable figure and the page still shows attribution.
