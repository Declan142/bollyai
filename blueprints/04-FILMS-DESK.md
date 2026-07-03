# BLUEPRINT 04 - Films desk (hollywood)

Use when: authoring or refreshing film pages in `data/films/`. Prompt: `prompts/P05`.
Films are Western theatrical/OTT releases. Desk lock: `canonical_industry: "hollywood"`
(prebuild guard `scripts/guard-offbrand-films.mjs` fails the build otherwise).

## Schema + naming (films differ from series - read before writing)

- **Type SOT**: `Film` in `site/lib/data.ts`. Do not write fields from memory; open it.
- **Filename = `<QID>.json`** (e.g. `Q101112656.json`); the `slug` field inside is the
  kebab title (e.g. `the-brutalist`). Both matter; the validator checks internal shape.
- Core fields: `qid` (SourceValue, verified), `slug`, `canonical_industry: "hollywood"`,
  `title` / `original_language` / `release_date` (SourceValue envelopes), `status`,
  `logline`, `budget` (null unless multi-sourced; never auto-publish), `box_office`,
  `verdict` ({ladder_rung, tracking} - rung values from `site/lib/data.ts`, never invented),
  `bollymeter` (full-or-null), `ott` (platform/date/source_url/source_type, real-or-null),
  `poster` (null until harvested), `_quarantine: []`, `date_modified`.
- Exemplar: `data/films/Q101112656.json` (the-brutalist) - mirror its envelope discipline,
  including the honest `box_office` pending shape.

## Grounding spine

1. **Wikidata first** (keyless): QID, title, release date (P577), box office (P2142),
   language. QID is the primary key - if you cannot confirm the QID, you cannot author the
   film (no QID-guessing, and no file without a confirmed QID).
2. Wikipedia for status/plot/logline context.
3. Reception (for bollymeter basis): RT/Metacritic + named outlets, real URLs.
4. TMDB: metadata only, and only where an API key is already wired (Actions). Never images.

## Box office publish rule (build-tested: `tests/test_boxoffice_publish_rule.py`)

- Publish a figure ONLY when >= 2 INDEPENDENT sources agree within 10% -> label
  "trade estimate".
- 10-25% divergence -> publish the LOWER figure with an explicit caveat.
- Over 25% or single-source or PR-only pairs -> publish NOTHING (honest pending row:
  `published: false`, `reason`, `framing: "awaited"`, sources listed).
- Same metric + same territory only (never mix net/gross or territories in a pair).
- Budgets and salaries: never auto-published, no exceptions.
- Western board = worldwide gross USD "as of <date>" (cumulative), per
  `engine/fetchers/boxoffice_western.py`. No day-wise fabrication.

## Film prose review

`review` field on Film JSON is a PROPOSAL (`scripts/subtitles/FILM_REVIEW_PROPOSAL.md`,
status draft). Do NOT mass-author film review bodies until the floor locks that shape.
If a film review is explicitly commissioned: `validate_films.py` already gates
`review.spoiler_free` (non-empty), `the_moment` <= 25 words, `bollymeter` 0-10 or null,
`critic_note` real-or-null <= 25 words - same honesty fences as episodes, and
QUALITY-BAR applies in full.

## Posters

`site/public/img/films/<slug>-<year>/` (e.g. `project-hail-mary-2026/`). Harvest =
self-hosted official press only (Sec 52(1)(a) + attribution + /takedown). Fallback SVG
until harvested; JSON may carry `poster: null` (site degrades safely).

## Gates

```bash
python3 scripts/batch/validate_films.py <slug-or-path> ...   # or --all
python3 -m pytest tests/test_validate_films.py tests/test_boxoffice_publish_rule.py -q
node scripts/guard-offbrand-films.mjs                        # runs in prebuild too
```
Commit format: `bollyai: films - <n> authored/refreshed` + the standard trailer. No push
from lanes.

## Skip rules (same spine as series)

Unconfirmable QID, no real reception AND no confirmable release data, or non-Western
title = no file, with a one-line reason in the report.
