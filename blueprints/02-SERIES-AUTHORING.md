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
  (`scripts/guard-offbrand-series.mjs`) checks `original_language.value` against an
  allowlist and FAILS THE BUILD on anything else. When in doubt about a language call,
  skip the title and note it.
- **Groundable only**: real English Wikipedia page + real critical reception. Too obscure
  or premiered days ago with no reviews = not authorable (fence #10, skip-if-thin).
- **No collisions**: `ls data/series/ | sed 's/\.json//'` first; exclude every existing
  slug. Check the ledger's reserved list (deep-lane slugs are never authored in batch).
- **Slug = kebab-case of the common English title**, must equal the filename exactly
  (validator checks). Disambiguate remakes with the year only when Wikipedia does
  (`the-office-us` style only if needed for a real collision).
- **Pool design**: 5-6 slugs per worker, pools DISJOINT by theme (US prestige / UK /
  crime / comedy / Euro), so no two workers ever touch the same slug.

## Grounding playbook (per slug - the order matters)

1. **Wikipedia page** (the spine): `https://en.wikipedia.org/wiki/<Title>` - WebFetch it.
   Capture: official title, original language, country, network/platform, status
   (ended/returning/running), season count, episodes per season, premiere date per season,
   renewal/cancellation facts with dates. The infobox is your envelope source
   (`source: "Wikipedia"`, confidence `verified`).
2. **QID**: the page's "Wikidata item" sidebar link, or
   `https://www.wikidata.org/w/api.php?action=wbsearchentities&search=<title>&language=en&type=item&format=json`.
   Confirm the entity is the TV series (description says "television series"). Cannot
   confirm = `qid: null`. Never guess.
3. **Reception per season**: Rotten Tomatoes season pages
   (`rottentomatoes.com/tv/<rt-slug>/s01`), Metacritic, IMDb rating (audience block).
   Capture the REAL critic %, the REAL sample count, and 1-2 quotable critic lines with
   their exact URLs (the RT "critics consensus" line, attributed to
   `"Rotten Tomatoes (critics consensus)"` with the season URL, is a reliable licensed
   pull_quote - see mad-men). Named outlets for deeper quotes: Variety, THR, Guardian,
   NYT, Vulture, AV Club, IndieWire, Collider, Decider.
4. **Platform for India framing**: what the show streams on NOW (the platform field drives
   the where-to-watch mesh). Combined platforms write as the primary ("JTBC / Netflix"
   tokenizes fine, but prefer the single primary Western platform).
5. Everything you could not capture goes null/omitted - not approximated.

## Annotated skeleton (structure = law; ALL-CAPS placeholders = replace or the page is wrong)

```json
{
  "slug": "SLUG-MATCHES-FILENAME",
  "qid": { "value": "Q000000", "source": "wikidata", "fetched_at": "NOW+05:30", "confidence": "verified" },
  "title": { "value": "OFFICIAL TITLE", "source": "Wikipedia", "fetched_at": "NOW+05:30", "confidence": "verified" },
  "canonical_industry": "streaming",
  "origin": "United States",
  "original_language": { "value": "en", "source": "Wikipedia", "fetched_at": "NOW+05:30", "confidence": "verified" },
  "platform": { "value": "Netflix", "source": "Wikipedia", "fetched_at": "NOW+05:30", "confidence": "verified" },
  "status": "ended",
  "genres": ["Drama", "Crime"],
  "logline": "ONE SPOILER-FREE SENTENCE: premise + hook, sharp and specific, never generic.",
  "poster": {
    "src": "/img/series/SLUG/poster.jpg",
    "alt": "TITLE series poster",
    "attribution": "Poster (c) STUDIO / PLATFORM. Used for criticism and review under fair dealing (Sec 52(1)(a)). Takedown: bollyai.in/takedown"
  },
  "renewal": {
    "state": "ended",
    "note": "ONE FACTUAL LINE, e.g. 'Series concluded May 17, 2015 after seven seasons and 92 episodes on AMC.'",
    "source": "Wikipedia",
    "source_url": "https://en.wikipedia.org/wiki/PAGE"
  },
  "seasons": [
    {
      "number": 1, "year": 2007, "episodes": 13,
      "release_date": { "value": "2007-07-19", "source": "Wikipedia", "fetched_at": "NOW+05:30", "confidence": "verified" },
      "verdict": "MUST-WATCH",
      "bollymeter": { "score": 9.0, "basis": "1-2 sentences of REAL grounding: awards won, the RT shape you captured, the named consensus you can license. Specific, never vibes." },
      "critic": {
        "positive_pct": 94, "sample": 52,
        "pull_quotes": [ { "text": "REAL QUOTE, <= 25 words.", "source": "Rotten Tomatoes (critics consensus)", "url": "https://www.rottentomatoes.com/tv/RT-SLUG/s01" } ]
      },
      "audience": { "rating": 8.3, "scale": 10, "source": "IMDb", "source_url": "https://www.imdb.com/title/tt0000000/" },
      "review_body": "90-160 WORDS per the recipe below.",
      "season_over_season": null,
      "episode_reviews": []
    }
  ],
  "_quarantine": [],
  "date_modified": "NOW+05:30"
}
```

Field notes the skeleton can't carry:
- `positive_pct` / `sample` / `audience` may be null (mad-men S1 ships null pct with a
  real pull_quote - that is legal). What is NOT legal: a pct without its sample, or any
  filled value you didn't fetch.
- `genres`: 2-5 tags from the brief's controlled set ONLY: Drama, Thriller, Comedy, Crime,
  Romance, Fantasy, Sci-Fi, Action, Mystery, Horror, Historical, Adventure, Coming of Age,
  Teen, Supernatural, Medical, Legal, Biographical, Documentary, Sports, Superhero, Spy,
  Psychological, Slice of Life, Musical, Family, War, LGBTQ. No nationality tags, ever.
- `status`: running | returning | ended | limited. `renewal.state`: renewed | awaiting |
  ended | final-season | limited (validator also tolerates returning/running in old data;
  do not write those two on new pages).
- Poster image is harvested later; you write the JSON block only. Use `(c)` not the
  copyright symbol if unsure; the exemplar uses the real symbol - both are fine, dashes
  are not.

## Season `review_body` recipe (90-160 words, five sentence-slots)

1. What the season IS + its engine, with one concrete craft detail (a character, a device,
   a setting used well). Not the premise restated - the mechanism.
2. Reception shape ONLY as licensed: if you captured a season pull_quote and/or RT%+sample,
   you may name what clustered ("Critics in 2007 were stunned by..." works because the RT
   quote backs it). NO quote captured = skip this slot entirely and write BollyAI's own
   read instead. This is the season-level Mode A/B split.
3. What works at its best: one specific dynamic or hour, spoiler-careful.
4. The honest wobble: one real criticism (pacing lull, arc that stalls, a cast imbalance).
5. Optional close: where it leaves the viewer / who it is for. No aphorism, no "in the end".

## Verdict calibration (OTT ladder, anti-inflation)

| Rung | Reception shape that earns it |
|---|---|
| MUST-WATCH | Broad, durable critical consensus + audience holds; awards or era-defining status you can cite |
| WORTH-IT | Clearly good with caveats; strong majority reception, some real flaws |
| ONE-TIME WATCH | Watchable, disposable; hook outruns the follow-through |
| SKIP | The weight of real reception says broken or pointless |
| DISASTER DROP | Notorious failure, documented |
| null | Still dropping / reception unformed - honest and common for current seasons |

Torn between two rungs = take the lower. The rung must survive the reception you actually
captured, not your affection for the show.

## Pipeline (one batch, end to end)

1. **Plan** - conductor curates pools per the rules above (existing-check + reserved-check).
2. **Dispatch** - one P02 worker per pool. Fire worker 1 alone first, then the rest in
   parallel once its stream starts. Sonnet, effort medium.
3. **Worker loop (per slug)**: ground -> write via python json.dump -> `fix_series.py` ->
   `validate_series.py` -> QUALITY-BAR rubric -> next slug. Ungroundable = skip + reason.
4. **Reconcile (conductor, effort xhigh)** - for EVERY new file:
   - re-run the validator yourself;
   - any season dated 2025/2026: re-verify release date + status live;
   - any verdict generous for a show known to be shaky: re-check reception, downgrade or null;
   - `genres` present + controlled-set only; poster attribution carries the takedown line;
   - spot-read 2 random review_body fields against QUALITY-BAR sections 4-6 + 10.
5. **Ingest** - `bash scripts/batch/ingest_batch.sh <all new slugs>`:
   `[1/4] fix -> [2/4] validate (exit 1 stops everything) -> [3/4] harvest posters
   (non-fatal, SVG fallback by design) -> [4/4] cd site && npm run build`.
   Run FOREGROUND with a long timeout (1800000 ms) and wait in the SAME turn -
   backgrounding it and ending the turn loses the batch (2026-06-16 regression).
   Only the box owner runs it; parallel fleet workers never build.
6. **Commit** - only if green:
   `git add data/series/ site/public/img/series/ data/_state/library-buildout.md`
   Message: `bollyai: series batch - <n> new (<pool names>)` + trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Never commit red. No push from lanes.
7. **Ledger** - bump Progress, append the batch entry:
   ```
   ### Batch <n> - <YYYY-MM-DD> - <k> series - STATUS: DONE (<from>-><to>)
   - **A <Pool name>:** slug · slug · slug
   - **B <Pool name>:** ...
   - <k>/<k> validate clean · build green (<pages>pp) · <p>/<k> posters (<f> SVG fallback)
   ```

## Validator error -> fix table (every message `validate_series.py` emits)

| Error | Fix |
|---|---|
| `invalid JSON` | You string-edited or truncated. Rewrite via python json.dump |
| `slug field 'x' != filename 'y'` | Make them identical (rename file or fix field) |
| `missing top-level field: F` | Add F per the skeleton |
| `canonical_industry must be 'streaming'` | Literal string, always |
| `status '...' not in [...]` | Use running/returning/ended/limited |
| `qid present but not a SourceValue envelope (or null)` | Wrap in envelope or set null |
| `<f> is not a SourceValue envelope` | Wrap title/original_language/platform |
| `poster.src / poster.alt missing` | Fill both |
| `poster.attribution missing fair-dealing/takedown line` | Use the skeleton's line |
| `renewal.state '...' not in [...]` / `renewal.note / source missing` | Fill per skeleton |
| `viewing-claim in <where>: <match>` | REWRITE the sentence (QUALITY-BAR gate 1). Not auto-fixable |
| `SN: missing field f` | Every season needs number/year/episodes/release_date/verdict/bollymeter/critic/review_body |
| `SN: release_date not a SourceValue envelope` | Wrap it |
| `SN: verdict '...' not in OTT ladder` | Exact rung strings or null |
| `SN: bollymeter must be null OR {score,basis}` / score 0-10 / basis empty | Full object or null; basis is real prose |
| `SN: review_body too thin (<60 chars)` | Write the real 90-160 word review |
| `FABRICATED-attribution in <where> (no backing pull_quote w/ url at this scope)` | Rewrite as BollyAI's own read, OR add the real quote you actually captured (QUALITY-BAR gate 2) |
| `SN: pull_quote missing text/source/url` / `> 25 words` | Complete it or drop it; trim without altering words |
| `SNEM: episode missing number/title` / `missing bollymeter` / `bollymeter must be 0-10 or null` / `spoiler_free empty` / `critic_note missing text/source/url` | Complete per the EpisodeReview shape |
| `em/en-dash in <path>` | `python3 scripts/batch/fix_series.py <slug>` then re-validate |

## Edge-case decision tree

- **Miniseries/limited**: `status: "limited"`, `renewal.state: "limited"`, one season,
  `season_over_season: null`.
- **Anthology (new cast per season)**: normal multi-season file; each season carries its
  own verdict/review; the logline names the anthology format.
- **Split season (Part 1/2)**: ONE season object per numbered season; `release_date` =
  Part 1 date; note the split inside `review_body`. Never invent "Season 4B".
- **Cancelled mid-story**: `status: "ended"`, `renewal.state: "ended"`, note says
  cancelled + date + source.
- **Platform moved**: `platform` = current primary with a fresh envelope; the old home can
  live in `review_body`/`renewal.note` if it matters.
- **Upcoming announced season, no date**: do NOT add a season object; note it in
  `renewal` (state `renewed`, note + source).
- **Episode count disputes** (specials, episode 0): follow Wikipedia's canonical count;
  specials are not episodes unless Wikipedia numbers them.

## Episode depth on NEW pages

2-4 STANDOUT hours per flagship season (premiere, finale, the argued-about turn), card
fields only (`number`, real `title`, `air_date`, `bollymeter` or null, `spoiler_free`,
`the_moment`, `critic_note` real-or-null). 0 for lesser seasons is fine. Rich full bodies
are the episode-review lane's job (`03-EPISODE-REVIEWS.md`), never this one - do not
half-write them here.

## Failure protocol + definition of done

Validator red -> fix -> re-run until PASS; a file that cannot pass honestly is deleted and
reported as skipped. Ingest red -> fix -> ONE re-run -> still red = log to
`data/_state/buildout-loop.log`, no commit, clean report. Done = all new slugs PASS,
build green (box owner), ledger updated, commit made (or explicit no-commit + reasons),
report lists written/skipped/fixed with one-line notes.
