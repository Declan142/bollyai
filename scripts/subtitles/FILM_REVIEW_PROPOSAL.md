# Film Review Shape Proposal

**Status:** Draft - open questions flagged for floor review before merge_reviews `--film --apply` is used on real data.

## Context

Four films are staged as single-episode corpora in the subtitle engine:

| Slug | QID file | Quote lang |
|---|---|---|
| `maharaja-2024` | Q-series (pending) | en-sub |
| `jawan` | Q-series (pending) | en-sub |
| `manjummel-boys` | Q-series (pending) | en-sub |
| `inception` | (pending) | en |

Each produces `data/subtitles/<slug>/_reviews/episodes.json` with one entry (number=1, title="Episode 1") via `draft_reviews.py`. This is the staging source for `merge_reviews.py --film`.

## Current Film JSON shape (data/films/*.json)

The `Film` TypeScript type (site/lib/data.ts:31) has:

```
qid, slug, canonical_industry, title, original_language, release_date,
status, date_modified, logline, poster, backdrop?, box_office,
verdict: { ladder_rung, tracking },
bollymeter: { score, basis } | null,
ott: { platform, date, source_url, source_type } | null,
budget, _quarantine
```

There is NO `review` field. Films on bollyai.in today show box-office tracking data and a verdict ladder - but no prose review body, no the_moment, no critic_note.

## Proposed `review` field

Add a single top-level `review` object to Film JSON:

```json
{
  "review": {
    "spoiler_free": "110-160 word BollyAI read. Same honesty fences as EpisodeReview.",
    "the_moment": "<=25 words naming the beat people remember.",
    "bollymeter": null,
    "critic_note": null,
    "merged_at": "2026-06-13T09:00:00+05:30"
  }
}
```

### Field semantics

| Field | Type | Notes |
|---|---|---|
| `spoiler_free` | string | BollyAI prose, same fences as EpisodeReview |
| `the_moment` | string or null | Short anchor beat, spoiler-careful |
| `bollymeter` | number (0-10) or null | Null until G4 voice-pass fills from real reception |
| `critic_note` | `{text, source, url}` or null | Real critic quote, verify-or-strip, null until G4 |
| `merged_at` | ISO-8601 +05:30 | Stamped by merge_reviews.py |

Note: the film `bollymeter` at top level (`Film.bollymeter`) is the season-level
season-aggregate score (same shape as `SeriesSeason.bollymeter: {score, basis}`).
The `review.bollymeter` here is the per-"episode" (i.e. the whole film) numeric,
parallel to `EpisodeReview.bollymeter` (a plain float, not an object). This is
an intentional asymmetry - the top-level bollymeter carries a basis string for
the SEO page, the review bollymeter is the critic's per-viewing score.

## TypeScript type extension

`site/lib/data.ts` Film type needs one optional field added:

```typescript
export type FilmReview = {
  spoiler_free: string;
  the_moment: string | null;
  bollymeter: number | null;
  critic_note: { text: string; source: string; url: string } | null;
  merged_at: string;
};

export type Film = {
  // ... existing fields ...
  review?: FilmReview;
};
```

This is a backward-compatible addition (optional field). Existing film JSONs without `review` continue to work.

## Open schema questions for floor review

**Q1: Should film.review reuse EpisodeReview or be its own type?**

Reusing `EpisodeReview` directly is clean but pollutes the film type with `number` and `title` (meaningless for a film). The current implementation strips those fields during merge. Proposal: define `FilmReview` as a separate type (shares most fields but omits `number`, `title`, `air_date`).

**Q2: Does the film page need the review to build?**

Currently `site/app/[desk]/[slug]/page.tsx` (film pages) only renders box-office data. If review is added to the Film type, a new "BollyAI Read" section would need to be designed and rendered. Adding the field to JSON without a render surface is harmless - it just waits. Recommendation: ship the field in JSON now; add the render surface as a separate design-reviewer-gated task.

**Q3: validate_films.py does not exist.**

`validate_series.py` has deep fence checks for series JSON. There is no equivalent for films. The `merge_reviews.py --film --apply` currently runs only `fence_check_review()` (em-dash, viewing-claim, spoiler_free non-empty, bollymeter range, critic_note shape) as a post-write check - NOT the full series validator. This is a gap.

Recommendation: create `scripts/batch/validate_films.py` (or extend validate_series.py) covering at least: viewing-claim + em-dash sweep, film review shape if present, bollymeter range. Until that exists, the `--film --apply` path uses the lightweight fence only. Flag this as a follow-up before film reviews ship to the live site.

**Q4: Film slug-to-file matching.**

Film JSON files are named by QID (`Q107105860.json`), not by slug. The subtitle corpus uses the film slug. `merge_reviews.py` resolves this by scanning all film JSONs and matching on `d["slug"]`. This is O(n) over the film catalogue but fine at current scale (~100 films). Note: films without a `slug` field in their JSON will be silently skipped.

**Q5: Multi-film corpus.**

If a multi-film franchise (e.g. a trilogy) is staged under a single slug, the current design merges only the first eligible entry. For real franchises, each film should have its own slug. No change needed to the schema; just a staging convention.

## Implemented

`merge_reviews.py --film` is implemented and gate-tested. It:
- Reads `data/subtitles/<slug>/_reviews/episodes.json`
- Requires both `_judge.verdict == "pass"` (G3) AND `voice_pass == True` (G4)
- Strips `number`, `title`, and all internal staging fields
- Stamps `merged_at`
- Writes to the QID-keyed film JSON under `film.review`
- Runs `fence_check_review()` post-write; rollback on failure
- Default dry-run; `--apply` to commit

Coverage: `tests/test_merge_reviews.py` (test_film_* cases, 5 tests).

No `site/` changes made. No `data/films/` files touched. The TypeScript type extension and render surface are unimplemented pending floor review of the open questions above.
