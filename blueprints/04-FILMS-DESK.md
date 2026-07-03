# BLUEPRINT 04 - Films desk (hollywood)

Use when: authoring or refreshing film pages in `data/films/`. Prompt: `prompts/P05`.
Films are Western theatrical/OTT releases. Desk lock: `canonical_industry: "hollywood"`
(prebuild guard `scripts/guard-offbrand-films.mjs` fails the build otherwise).

## Schema + naming (films differ from series - transcribed from `site/lib/data.ts`)

- **Filename = `<QID>.json`** (e.g. `Q101112656.json`); the `slug` field inside is the
  kebab title (`the-brutalist`). No confirmed QID = no file.
- **Confidence vocabulary differs from series**: films use
  `verified | trade_estimate | editorial | unverified` (the `Confidence` type in data.ts).
  Series use verified/reported. Do not mix them up.
- **`status`**: `upcoming | live | released | ott` (live = currently in theatres;
  ott = now streaming).
- **`verdict`**: `{ ladder_rung, tracking }` where `tracking: true` means the call is
  still moving. `ladder_rung` from the 9-rung trade ladder (or null while tracking):
  `DISASTER | FLOP | BELOW AVERAGE | AVERAGE | SEMI-HIT | HIT | SUPER-HIT | BLOCKBUSTER |
  ALL-TIME BLOCKBUSTER`.
- **`box_office`**: `{ day_rows: DayRow[], totals: { india_net_inr_cr, worldwide_gross_inr_cr, as_of } }`.
  DayRow: `{date, day, net_inr_cr: SourceValue<MoneyRange|null>, sources: [{name,url,as_of}], label}`.
  MoneyRange is `{low, high}` - the schema is BUILT for publishing ranges, use it.
  (The Western BOARD surface is worldwide-USD via `engine/fetchers/boxoffice_western.py`;
  the per-film JSON keeps this shape.)
- **`budget`**: null, or `{value, source, fetched_at, confidence, first_party}` - and the
  publish rule below still says never auto-publish; leave null unless the floor signs off.
- **`ott`**: `{platform: SourceValue, date: SourceValue, source_url, source_type}` where
  `source_type` is `press | official_social | trade`; the whole block null when unsourced.
- **`poster`**: null until harvested (site substitutes a full fallback object safely);
  `bollymeter`: `{score, basis}` or null; `_quarantine: []`; `date_modified` ISO +05:30.
- Exemplar: `data/films/Q101112656.json` (the-brutalist) - mirror its envelope discipline,
  especially the honest pending `day_rows` row:
  `label: "figures not yet pair-verified"`, `framing: "awaited"`, `published: false`,
  `reason: "single_source_or_no_valid_independent_pair"`, value null, sources listed.

## Grounding spine

1. **Wikidata first** (keyless, free):
   - Find the QID:
     `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=<title>&language=en&type=item&format=json`
     - confirm the description says film + the right year. Ambiguous = skip the film.
   - Pull claims:
     `https://www.wikidata.org/w/api.php?action=wbgetclaims&entity=<QID>&format=json`
     - P577 (publication date), P2142 (box office). SPARQL alternative:
     `https://query.wikidata.org/sparql?format=json` with a descriptive User-Agent header.
2. **Wikipedia** for status, plot context, the logline's facts, studio (poster attribution).
3. **Reception** (bollymeter basis): RT/Metacritic + named outlets, real URLs, real
   samples. Same licensing rules as series (QUALITY-BAR gate 2).
4. **TMDB**: metadata only, and only where the API key is already wired (GitHub Actions
   secret; there is NO local key). Never images, never watch-provider scraping.

## Box office publish rule (build-tested: `tests/test_boxoffice_publish_rule.py`)

Worked arithmetic - run this check before publishing ANY figure:

| Case | Sources | Spread | Action |
|---|---|---|---|
| A | $405.9M vs $412.1M | (412.1-405.9)/405.9 = 1.5% (< 10%) | PUBLISH as `{low: 405.9, high: 412.1}`, label "trade estimate", both sources listed |
| B | $180M vs $215M | 19.4% (10-25%) | PUBLISH the LOWER: `{low: 180, high: 180}`, label carries the caveat + both sources |
| C | $95M vs $140M | 47% (> 25%) | DO NOT publish: pending row (`published: false`, reason, sources) |
| D | Studio PR + a site quoting that PR | not independent | DO NOT publish (PR-only pair rejected) |
| E | India net vs worldwide gross | different metric/territory | NOT a valid pair - never mix |

Budgets and salaries: never auto-published, no exceptions. Every published row carries
`as_of` + a real source URL per source.

## `bollymeter` + `verdict` for films

- bollymeter basis: 1-2 sentences of REAL grounding ("Reviews and awards coverage place it
  in elite critical territory" - the-brutalist style), or null.
- ladder_rung: only when the box-office trajectory is defensible from published figures;
  `tracking: true` + rung null is the honest default for anything still moving.
- The film `review` prose field is a PROPOSAL (`scripts/subtitles/FILM_REVIEW_PROPOSAL.md`,
  status draft). Do NOT mass-author film review bodies until the floor locks that shape.
  If one is explicitly commissioned: `validate_films.py` gates `review.spoiler_free`
  (non-empty), `the_moment` <= 25 words, `bollymeter` 0-10/null, `critic_note` <= 25 words
  real-or-null; HOUSE-STYLE + QUALITY-BAR apply in full.

## Posters

`site/public/img/films/<slug>-<year>/` (e.g. `project-hail-mary-2026/`). Harvest =
self-hosted official press only (Sec 52(1)(a) + attribution + /takedown). JSON ships
`poster: null` until harvested; never a TMDB URL, never a hotlink.

## Gates + commit

```bash
python3 scripts/batch/validate_films.py <slug-or-path> ...    # or --all
python3 -m pytest tests/test_validate_films.py tests/test_boxoffice_publish_rule.py -q
node scripts/guard-offbrand-films.mjs                          # also runs in prebuild
```
validate_films checks: JSON parses, qid/slug/canonical_industry present, slug matches the
INTERNAL naming, review shape when present, the four-dash ban, viewing claims in prose.
Commit: `bollyai: films - <n> authored/refreshed` + trailer. No push from lanes.

## Skip rules (same spine as series)

Unconfirmable QID; no real reception AND no confirmable release data; non-Western title;
sources that only circle back to one PR - all of these = no file + a one-line reason in
the report. 72 films exist today; a batch that adds 5 real ones beats one that adds 20
with hollow envelopes.
