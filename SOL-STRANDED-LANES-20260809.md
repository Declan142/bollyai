# SOL-MAX Stranded Lanes Audit - 2026-08-09

## Executive decision

Both requested branch refs should be **ABANDONED as landing vehicles**.

- `codex/bollyai-worldclass-site-20260801` is already contained in the freshly fetched
  `origin/main`. Its site, engine, scripts, tests, blueprints, box-office, and cache code
  is already on the remote main line. Replaying the branch would add no code and risks
  regressing newer rolling data.
- `fix/bollyai-weekly-contract-20260726` has no unique product code after its shared
  foundation. Its two unique commits change only `last.txt`, and that historical handoff
  is stale. The six substantive commits are already in `origin/main` through the
  worldclass lineage and are also the foundation of the separately audited box-office
  lane.
- Both branch diffs fail the categorical banned-source fence because they add an IMDb
  Box Office bulk-dataset candidate and dataset documentation URLs. Marking that row
  `policy_blocked` is not enough, and the clearance code has no immutable IMDb dataset,
  JustWatch, or Letterboxd deny rule.
- The builds are genuinely green after installing the branch lockfile: worldclass passes
  316 Python tests and the Next 15 production build; weekly passes 311 Python tests and
  the Next 15 production build. Green gates do not override the source-policy failure.

The most important unasked risk is already live in version control: fresh
`origin/main` contains the worldclass branch and therefore contains the same IMDb
candidate. Abandoning the old ref is correct, but a new, focused current-main cleanup is
still required.

## 1. VERDICT TABLE

| Lane | Commits and actual status | What it does | Fence audit | Integration health | Recommendation |
|---|---|---|---|---|---|
| `codex/bollyai-worldclass-site-20260801` at `82f6435b` | 21 ahead of stale local `main`; 0 ahead and 14 behind fresh `origin/main`; tip is an ancestor of `origin/main` | Shared exact-week box-office v3 and Next 15 foundation, then full editorial homepage, Browse URL state, canonical redirects, asset safety, sitemap expansion, and rolling OTT/state updates | **FAIL**: banned IMDb bulk-dataset candidate at `data/boxoffice/source-candidates.json:73-108`; all other checked fences clean | **GREEN**: 316/316 pytest; Next 15.5.22 build; 17/17 Node tests; AggregateRating gate; 5,661 pages; 6,847 files; 0 missing static assets | **ABANDON** as a merge vehicle. The value is already in `origin/main`. Do a new current-main banned-source cleanup instead. |
| `fix/bollyai-weekly-contract-20260726` at `5dcccd99` | 8 ahead of stale local `main`; only 2 unique commits after common `5d1b0353`, both changing `last.txt`; 2 ahead and 29 behind fresh `origin/main` | Shared exact-week box-office v3 contract, clearance registry, atomic last-good writer, fail-closed UI, route retirement, and Next 15 migration; no operational live source | **FAIL**: same banned IMDb dataset candidate and missing code-owned deny rule; all other checked fences clean | **GREEN**: 311/311 pytest; Next 15.5.22 build; 17/17 Node tests; AggregateRating gate; 5,661 pages; 6,840 files | **ABANDON**. All substantive code is already on the current main lineage and in the successor box-office lane; only a stale archival handoff would be lost. |

### Reference clock and branch identity

The task's ahead counts are correct relative to the local `main`, but local `main` is not
the current remote main.

```text
local main                            2053f9db6efcba9488648de5610797e5aa87bfcb
fresh origin/main                     81149d15037bcd81225fcea89d147030286645b5
worldclass                            82f6435bcc2291e5bfd2bd461470be7b052bb9a3
weekly contract                       5dcccd99382c8e2db07e5bffd4b8c5637c932b9b
boxoffice source engine               981f51b681db402fae4c0cf483d3b2d3013b230e
subtitles runtime                     18b557695a3788362a45f56c2961d13ec6fa39a4

main...worldclass                     0 21
main...weekly                         0 8
main...boxoffice                      0 8
main...subtitles                      25 0
main...origin/main                    0 35
origin/main...worldclass              14 0, contained
origin/main...weekly                  29 2, not contained
origin/main...boxoffice               29 2, not contained
origin/main...subtitles               60 0, contained
```

`git ls-remote` immediately before the fetch returned remote main `81149d15`, remote
worldclass `82f6435b`, and remote weekly `5dcccd99`. It returned no remote ref for
`feat/boxoffice-weekly-source-engine`; that audited lane currently exists locally at
`981f51b6` but was not advertised by the remote under that name.

The corpus remained 480 series JSON files and 72 film JSON files in both lane tests.
Neither lane changes primary `data/series/*.json` or `data/films/*.json` content.

## 2. PER-LANE DETAIL

### A. `codex/bollyai-worldclass-site-20260801`

#### Real diff shape

Against the mandated local-main base:

```text
94 files changed, 13511 insertions(+), 6437 deletions(-)
74 modified, 19 added, 1 deleted
```

The branch bundles two different programs:

| Segment | Actual delta | Intent |
|---|---:|---|
| Shared foundation through `5d1b0353` | 6 commits; 64 files; 9,761 insertions, 6,043 deletions | Exact-week box-office v3, fail-closed source clearance, atomic writes, public route changes, Next 15 migration, and tests |
| Worldclass-only segment | 15 commits; 49 files; 3,848 insertions, 492 deletions | Editorial homepage and Browse redesign, canonical navigation, static-asset safety, recommendation repair, richer episode discovery, sitemap expansion, and rolling OTT/state outputs |

#### Box-office contract and source clearance

- `engine/fetchers/boxoffice_week_schema.py:26-60` defines v3, Western scope,
  forbidden lifetime/budget/salary field parts, the 10 and 25 percent thresholds, and
  an empty production source-group mapping.
- `engine/fetchers/boxoffice_week_schema.py:276-320` validates exact period, source
  host/group binding, USD, Worldwide scope, timing, and positive values.
- `engine/fetchers/boxoffice_week_schema.py:323-336` requires at least two independent
  groups, publishes the lowest value within 10 percent as `trade estimate`, publishes
  the lowest within 10 to 25 percent as `lower figure`, and withholds wider divergence.
- `site/lib/boxoffice-schema.mjs:1-417` mirrors the contract for the build and public
  loader.
- `engine/fetchers/common.py:83-130` adds same-directory temporary writes, file sync,
  atomic replace, directory sync, and byte-identical no-op behavior.
- `engine/fetchers/run_all.py:143-296` validates prior bytes, preserves last-good or
  pending bytes, validates candidates before replacement, and separates pre-replace
  failures from post-replace durability failures.

The foundation is deliberately incomplete as a live engine:

- `engine/fetchers/boxoffice_source_clearance.py:79` has no production adapter.
- `engine/fetchers/boxoffice_western.py:47-72` returns `data_pending`, zero readings,
  and zero public records for non-fixture execution.
- `data/boxoffice/current-week.json:1-12` is an empty pending board generated on
  2026-07-25 for the closed week ending 2026-07-19.
- The branch parser checks closure and future time but does not enforce that the stored
  week is the latest closed week. The separately audited box-office lane is the
  successor that adds fail-loud stale-board behavior.

#### Next 15 and route migration

- `site/package.json:17,25-32` pins Next 15.5.22, Sharp 0.35.3, and the PostCSS
  override.
- Dynamic pages use the Next 15 async params contract across film, OTT, series,
  season, episode, explainer, prediction, and watch-list routes.
- The old lifetime club route `site/app/box-office/[club]/page.tsx` is deleted.
- `site/public/_redirects:7-19` sends old club and year-scoreboard routes to the
  canonical weekly board.

#### Editorial site rebuild

- `site/app/page.tsx:141-160` derives real catalogue statistics, a current hero,
  current series, sourced releases, recent rich episode reviews, and curated lists.
- `site/app/page.tsx:164-215` presents the disclosed-AI answer desk and explicitly
  reports zero invented ratings.
- `site/app/page.tsx:218-246` renders one grounded cover verdict with score basis.
- `site/app/page.tsx:270-297` uses only sourced upcoming dates and renders an honest
  empty state when nothing clears.
- `site/app/page.tsx:385-405` states the negative viewing disclosure and source
  contract.
- `site/app/page.tsx:413-420` emits `CollectionPage`, not `AggregateRating`.
- `site/lib/home.ts:97-134,181-263,290-318` limits freshness, requires local art,
  ranks from existing grounded fields, and refuses to substitute catalogue dates for
  sourced upcoming dates.
- Two local brand assets are added:
  `site/public/img/brand/friday-verdict-hero.webp` and
  `site/public/img/brand/friday-verdict-hero-960.webp`.

#### Browse, navigation, assets, and discovery

- `site/components/BrowseGrid.tsx:68-132` reads and writes filter/sort state through
  the URL and filters deterministically.
- `site/components/BrowseGrid.tsx:259-297` provides honest zero-result handling and
  poster/verdict cards.
- `/series/` and `/streaming/` are redirected to the canonical `/browse/` surface.
- `site/lib/series.ts:101-130` resolves only existing site-relative images and falls
  back when an asset is absent.
- `site/scripts/assert-static-assets.mjs:20-63` scans the export for missing local
  references; `site/package.json:7,10` makes that scan a hard post-build gate.
- `site/lib/recommendations.ts:49-74` repairs older picks by exact normalized-title
  matching when slugs are missing.

#### Sitemap and generated state

- `site/scripts/build-sitemaps.mjs:123-161` deduplicates embedded and standalone
  episode routes.
- `site/scripts/build-sitemaps.mjs:163-177` derives standalone explainer URLs.
- `site/scripts/build-sitemaps.mjs:189-203` includes only locally present non-fallback
  images.
- `site/scripts/build-sitemaps.mjs:205-227` writes 11 child sitemaps and the generated
  index.
- The branch advertises 2,873 existing episode URLs and 21 existing explainer URLs.
  It adds no page route template and no primary content JSON, so this is discovery of
  existing pages, not a 2,894-page authoring burst.

The branch's rolling data is stale as a landing payload. Fresh `origin/main` differs
from the branch tip only in seven rolling data/state paths:

```text
data/_state/changed-urls.json
data/_state/staleness.json
data/ott/announcements.json
data/ott/calendar.json
data/ott/calendar/2026-W31.json
data/ott/calendar/2026-W32.json
data/ott/calendar/2026-W33.json
```

All code-bearing trees under `site/`, `engine/`, `scripts/`, `tests/`, `blueprints/`,
`data/boxoffice/`, and `data/cache/` are already represented on `origin/main`.

#### Completeness and applicability

- Editorial/frontend portion: complete and already landed.
- Exact-week contract: complete as fail-closed infrastructure and already landed.
- Operational live weekly source: intentionally incomplete, with zero production
  adapters and a stale empty board; superseded by the third lane.
- Current applicability: yes, proven by ancestry and byte identity, but there is
  nothing left to merge from this branch.
- Value lost by abandoning the branch ref: no product value. Its code is already on
  current remote main. Branch history remains available for provenance.

### B. `fix/bollyai-weekly-contract-20260726`

#### Real diff shape

Against the mandated local-main base:

```text
64 files changed, 9758 insertions(+), 6043 deletions(-)
50 modified, 13 added, 1 deleted
```

The misleading part is uniqueness. All three lanes share six substantive commits
through `5d1b0353`. Weekly's two post-fork commits change only `last.txt`:

```text
f1f85adf docs: record BollyAI production deployment
5dcccd99 docs: narrow work memory artefacts

last.txt | 59 lines changed, 28 insertions, 31 deletions
```

There is no weekly-unique implementation, schema, test, route, or dependency change.

#### Shared functional value

The shared six-commit foundation is substantial:

- strict Python and JavaScript v3 exact-week schemas;
- two-independent-source consensus with lowest-value publication;
- generic source-clearance registry and code-owned scope policy;
- isolation of legacy cumulative India data under `_cache/boxoffice/`;
- atomic last-good publication and structured failure states;
- fail-closed public weekly board and retirement of lifetime-club routes;
- Next 15 async-route migration and deterministic generated indexes;
- 50 new Python tests across compatibility, clearance, week contract, atomic JSON,
  and run-all behavior, plus 17 JavaScript schema subtests.

The same incompleteness applies:

- `engine/fetchers/boxoffice_week_schema.py:60` has no production source groups.
- `engine/fetchers/boxoffice_source_clearance.py:79` has no production adapters.
- `engine/fetchers/boxoffice_western.py:57-72` always returns zero live readings and
  `data_pending`.
- `engine/fetchers/run_all.py:258-268` preserves an old pending board rather than
  advancing the public pending week.
- `site/app/box-office/page.tsx:14-17,44-52` can therefore call an increasingly old
  closed week the latest verified board.

#### Completeness and applicability

- Contract scaffold: substantially complete and valuable.
- Working/current weekly feed: incomplete.
- Current applicability: the functional work already applies because it is already in
  current main via the worldclass lineage and is extended by the third lane.
- Unique value lost by abandoning the branch: only stale deployment/handoff wording in
  `last.txt`. That wording remains recoverable in history and should not overwrite a
  current handoff.

## 3. FENCE AUDIT

### Decisive blocker

Both diffs contain the same shared violation:

- `data/boxoffice/source-candidates.json:73-108` adds a licensed IMDb Box Office bulk
  candidate.
- Lines 91 and 97 identify `imdb_box_office_bulk` and `IMDb Box Office bulk data`.
- Lines 100 to 102 store direct IMDb bulk/API dataset documentation URLs.
- `data/boxoffice/README.md:81-91`, `RESUME.md:9-17`,
  `tests/test_boxoffice_source_clearance.py:60-74`, and each historical `last.txt`
  make the candidate part of the lane contract.
- `engine/fetchers/boxoffice_source_clearance.py:75-80` allows a generic `cleared`
  assessment and has no banned-source set.
- `engine/fetchers/boxoffice_source_clearance.py:198-216,257-303` validates and
  qualifies candidates generically. If registry fields and an adapter were later
  changed, there is no code-owned IMDb dataset, JustWatch, or Letterboxd hard stop.

The candidate is currently unapproved, unconfigured, and `policy_blocked`, so it is not
being fetched. That reduces present operational exposure but does not pass the task's
categorical rule that a lane touching a banned source is not mergeable as-is.

### Every fence, every lane

| Fence | Worldclass | Weekly contract | Evidence and conclusion |
|---|---|---|---|
| 1. No first-person viewing claims | **PASS** | **PASS** | Both authoritative pytest runs include all 29 assertions in `tests/test_viewing_claim.py` and finish green. Exact changed-reader scans found zero findings. Worldclass's disclosure at `site/app/page.tsx:388-393` says the system has not watched anything, which is the required negative disclosure, not a viewing claim. |
| 2. No em/en dash glyphs in authored additions | **PASS** | **PASS** | Exact added-line scans for U+2013 and U+2014 returned zero. `engine/fetchers/boxoffice_week_schema.py:192-200` recursively rejects either glyph, with test coverage in `tests/test_boxoffice_week_contract.py:121-129`. |
| 3. No fabricated OTT metrics | **PASS** | **PASS** | Neither diff adds Indian platform view/stream/hour claims. Weekly changes no OTT content beyond generated timestamps. Worldclass uses sourced announcement rows in `site/lib/home.ts:278-318` and renders an explicit empty state at `site/app/page.tsx:288-296`. |
| 4. BollyMeter must be full and grounded or null | **PASS** | **NOT TOUCHED** | No primary score-bearing content JSON changes. Worldclass only consumes existing full score+basis objects at `site/lib/home.ts:197-242` and renders the basis at `site/app/page.tsx:232-243`; null stays absent. Weekly adds no `bollymeter` source field. |
| 5. Pull quotes real, attributed, and at most 25 words | **NOT TOUCHED** | **NOT TOUCHED** | No `pull_quotes` or `pullQuotes` additions and no primary series, film, episode, recommendation, explainer, ending, or prediction content changes. |
| 6. TMDB metadata only; no served TMDB images or ad-revenue implication | **PASS** | **PASS** | Added-line searches found no TMDB image host, remote image URL, `poster_path`, `backdrop_path`, monetization, or ad-revenue use. Worldclass adds only two local brand WebPs and restricts image resolution to existing site-relative paths at `site/lib/series.ts:101-105`. The only new TMDB mention is metadata-path documentation in `blueprints/06-REFRESH-OPS.md:31-32`. |
| 7a. No JustWatch scraping | **PASS** | **PASS** | Added JustWatch hits: zero. No adapter, endpoint, scraper, or ingestion code is added. |
| 7b. No IMDb datasets | **FAIL** | **FAIL** | Direct merge blocker at `data/boxoffice/source-candidates.json:73-108`, plus README, RESUME, test, and handoff references. There is no immutable deny rule in `boxoffice_source_clearance.py`. |
| 7c. No Letterboxd | **PASS** | **PASS** | Added Letterboxd hits: zero. A pre-existing styling reference is outside both added-line diffs. |
| 8. Box-office source agreement | **PASS** | **PASS** | `engine/fetchers/boxoffice_week_schema.py:323-336` requires at least two independent groups and evaluates the full low/high range. Within 10 percent it publishes the low value as trade estimate; 10 to 25 percent publishes the low value with lower-figure framing; wider divergence yields no number. `:376-406` recomputes and rejects dishonest stored values. |
| 9. Budgets and salaries never auto-publish | **PASS** | **PASS** | `engine/fetchers/boxoffice_week_schema.py:47-50,203-213` recursively rejects budget, salary, lifetime, cumulative, opening-weekend, and week-to-date fields. Public copy at `site/app/box-office/page.tsx:98-99` says these are excluded. |
| 10. Never serve subtitle text | **PASS / NOT TOUCHED** | **NOT TOUCHED** | No changed `.srt`, `.vtt`, subtitle, transcript, or subtitle-serving path. Worldclass's generator comment at `site/scripts/build-sitemaps.mjs:146-147` describes analysis-derived episode pages; it does not add subtitle cargo. |
| 11. Wikidata QID is the identity spine; never guess | **PASS for current publication** | **PASS for current publication** | `engine/fetchers/boxoffice_week_schema.py:251-273` validates QID shape and uses QID as primary identity when present, with slug fallback when QID is null to honor the never-guess rule. Duplicate QIDs/slugs are rejected at `:443-465`. The public board is empty. Fake-looking QIDs exist only in deterministic fixtures, and fixture publication is blocked at `engine/fetchers/boxoffice_western.py:154-162`. Before a live adapter is ever enabled, provenance must be stronger than the syntax-only check at `:259-261`. |
| 12. Skip thin or fabricated output | **PASS** | **PASS** | Live execution returns honest `data_pending`, zero readings, and zero records at `engine/fetchers/boxoffice_western.py:57-72`; `data/boxoffice/current-week.json:1-12` is empty rather than fabricated. Worldclass upcoming UI stays blank until sourced dates clear. |
| 13. Never emit `AggregateRating` | **PASS** | **PASS** | Added application/schema-code hits: zero. Both authoritative builds invoke `site/scripts/assert-no-aggregate-rating.mjs` and exit 0. Worldclass uses `CollectionPage`; box-office structured data uses `ItemList`, `Dataset`, `Movie`, and `TVSeries`. |
| 14. New-page velocity capped at 3 to 5/day | **PASS with discovery caution** | **PASS** | Added route templates: zero. Added primary content JSON: zero. Weekly retires one route. Worldclass newly places 2,873 existing episode routes and 21 existing explainer routes in generated sitemaps; this is an indexing update, not new-page authoring, but the large discovery wave deserves an SEO rollout decision. |
| 15. `site/public/sitemap.xml` is generated, never hand-edited | **PASS** | **PASS** | Each lane changes the generator and generated outputs together. Worldclass generator writes all child maps and the index at `site/scripts/build-sitemaps.mjs:205-227`; weekly does the equivalent at `:151-171`. This audit never hand-edited the sitemap, and each production build regenerated it. |
| 16. Western-only brand | **PASS** | **PASS** | `engine/fetchers/boxoffice_week_schema.py:28-33,339-355` allowlists Hollywood/streaming and Western languages, and rejects off-brand rows. Both builds report 480/480 Western series and all 72 Western films. Worldclass strengthens brand/canonical Browse tests. |

### Named remediation for the already-landed shared defect

Do this as a new reviewed change on current main, not by merging either old branch:

1. Remove the IMDb candidate object at
   `data/boxoffice/source-candidates.json:73-108`.
2. Remove the new dataset-specific references from
   `data/boxoffice/README.md:81-91`, `RESUME.md:9-17`, and
   `tests/test_boxoffice_source_clearance.py:60-74`.
3. Add a code-owned deny invariant near
   `engine/fetchers/boxoffice_source_clearance.py:198-216` so IMDb dataset IDs/hosts,
   JustWatch, and Letterboxd can never qualify even if mutable registry fields claim
   full approval and configuration.
4. Add regression tests that mutate a banned candidate to apparently cleared state and
   prove evaluation still fails closed.

## 4. CONFLICT MAP + LANDING ORDER

### Topology

All three feature lanes share `5d1b0353` after local main:

```text
local main 2053f9db
  shared 6-commit exact-week/Next-15 foundation -> 5d1b0353
    worldclass: +15 commits, 49 post-fork files
    weekly:     +2 commits, 1 post-fork file (last.txt only)
    boxoffice:  +2 commits, 30 post-fork files
```

Main-relative file overlap is 64 paths for every pair, but that is shared history rather
than independent edits. Real post-fork overlap is tiny:

| Pair | Independently edited paths | Literal conflicts |
|---|---|---|
| worldclass + weekly | `last.txt` | `last.txt` |
| weekly + boxoffice | `last.txt` | `last.txt` |
| worldclass + boxoffice | `last.txt`, `site/package.json` | `last.txt`, `site/package.json` |

`migrate/subtitles-codex-runtime` is confirmed contained in both local and remote main:
0 ahead of local main and 60 behind fresh `origin/main`. It was not otherwise audited.

### Actual throwaway-branch merges

Each stranded lane merged cleanly by itself into the mandated throwaway branch from
local `main`:

```text
$ git merge --no-ff --no-commit codex/bollyai-worldclass-site-20260801
Automatic merge went well; stopped before committing as requested

$ git merge --no-ff --no-commit fix/bollyai-weekly-contract-20260726
Automatic merge went well; stopped before committing as requested
```

For the real pairwise test, the audited box-office lane was committed only on the
throwaway branch. Merging worldclass into it produced exactly two conflicts:

```text
$ git merge --no-ff --no-commit codex/bollyai-worldclass-site-20260801
Auto-merging last.txt
CONFLICT (content): Merge conflict in last.txt
Auto-merging site/package.json
CONFLICT (content): Merge conflict in site/package.json
Automatic merge failed; fix conflicts and then commit the result.
MERGE_EXIT=1
UNMERGED_PATHS
last.txt
site/package.json
```

Merging weekly into the box-office integration base produced only the handoff conflict:

```text
$ git merge --no-ff --no-commit fix/bollyai-weekly-contract-20260726
Auto-merging last.txt
CONFLICT (content): Merge conflict in last.txt
Automatic merge failed; fix conflicts and then commit the result.
MERGE_EXIT=1
UNMERGED_PATHS
last.txt
```

Both failed test merges were aborted. The temporary box-office merge was then reverted
on the throwaway branch. Before writing this report, its product tree was byte-identical
to local main:

```text
throwaway HEAD tree  fc745727a1bc49ab5023a0837da6018be65589c1
local main tree      fc745727a1bc49ab5023a0837da6018be65589c1
git diff --quiet main -- . -> exit 0
```

Read-only `git merge-tree --write-tree --messages` tested both orientations for every
pair and confirmed the same path matrix. Against freshly fetched `origin/main`:

- worldclass is already contained and produces no conflict;
- weekly conflicts only in `last.txt`;
- boxoffice conflicts in `last.txt` and `site/package.json`.

### Mechanical resolution map for a future box-office integration

`last.txt` should be regenerated for the new integration. Do not choose either stale
historical handoff wholesale.

The package conflict needs the union of independent gates:

```json
"build": "next build && npm run lint:aggregate && npm run postbuild:filecap && npm run lint:static-assets",
"lint:aggregate": "node scripts/assert-no-aggregate-rating.mjs",
"lint:static-assets": "node scripts/assert-static-assets.mjs",
"test:boxoffice": "node --test lib/boxoffice-schema.test.mjs lib/boxoffice-public-state.test.mjs"
```

Taking worldclass wholesale would drop the third lane's public-state test. Taking the
third lane wholesale would drop worldclass's static-asset gate.

Logical, non-text conflicts to remember:

- Worldclass's checked-in `data/_state/staleness.json` uses the older monitor shape;
  the third lane extends staleness monitoring. Regenerate through the owner script if a
  current snapshot is required.
- Sitemap outputs must be regenerated by the selected generator, never hand-composed.
- All three lane lockfiles are byte-identical, so dependency versions themselves do not
  conflict.
- The third lane advances shared box-office engine files; worldclass and weekly do not
  independently edit those files after `5d1b0353`.

### Recommended real landing order

1. Treat fresh `origin/main` at `81149d15` or newer as the base. It already contains
   worldclass. Do not merge the worldclass branch ref.
2. Integrate `feat/boxoffice-weekly-source-engine` at local commit `981f51b6` onto that
   fresh base, preserving the package-script union above. Its separate report remains
   the authority for its source-engine verification.
3. Before that combined tree is eligible for main, remove and permanently deny the
   already-landed banned IMDb dataset candidate. This is current-main policy debt, not
   a reason to replay an old lane.
4. Do not merge `fix/bollyai-weekly-contract-20260726`. Its only unique delta is stale
   `last.txt` text and would create a conflict without adding product value.

If someone intentionally reconstructs from the stale local main instead, the lowest-pain
hypothetical sequence is boxoffice first, worldclass second with the package union, and
weekly never. The actual remote topology makes that reconstruction unnecessary.

## 5. INTEGRATION RESULTS

### Environment and reproducibility correction

```text
Python 3.12.3
pytest 9.0.3
Node v22.22.1
npm 10.9.7
```

The pre-existing `node_modules` initially contained Next 14.2.35 even though both lane
manifests pin Next 15.5.22. Those first build runs were discarded as non-authoritative.
For each authoritative build, `npm ci` was run from the merged lane lockfile:

```text
added 38 packages, and audited 39 packages in 5s

11 packages are looking for funding
  run `npm fund` for details

3 vulnerabilities (2 moderate, 1 high)

bollyai-site@0.1.0 /home/aditya/bollyai/site
├── next@15.5.22 overridden
└── sharp@0.35.3 overridden
```

No `npm audit fix` was run because this task is diagnosis-only and dependency mutation
was out of scope.

### A. Worldclass integration

Merge result against mandated local main: clean, no conflict.

Command:

```text
python3 -m pytest tests/
```

Exit: `0`

Literal output:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/aditya/bollyai
plugins: anyio-4.13.0, respx-0.23.1, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 316 items

tests/test_boxoffice_compat_cli.py .....                                 [  1%]
tests/test_boxoffice_publish_rule.py .......                             [  3%]
tests/test_boxoffice_source_clearance.py ..............                  [  8%]
tests/test_boxoffice_week_contract.py .................................. [ 18%]
...........                                                              [ 22%]
tests/test_brand_lock.py ..............                                  [ 26%]
tests/test_common_atomic_json.py ....                                    [ 28%]
tests/test_draft_reviews_gates.py ...................................... [ 40%]
....................                                                     [ 46%]
tests/test_ending_explained.py ......................................... [ 59%]
.....                                                                    [ 61%]
tests/test_fetcher_degrade.py ....                                       [ 62%]
tests/test_merge_reviews.py ............                                 [ 66%]
tests/test_ops_workflows.py .....                                        [ 67%]
tests/test_ott_calendar.py ....                                          [ 68%]
tests/test_ott_western.py ..............                                 [ 73%]
tests/test_predictions.py ..                                             [ 74%]
tests/test_run_all_boxoffice.py .........                                [ 76%]
tests/test_style_leaks.py .....................                          [ 83%]
tests/test_validate_films.py .................                           [ 88%]
tests/test_verify_grounding.py ......                                    [ 90%]
tests/test_viewing_claim.py .............................                [100%]

============================= 316 passed in 6.54s ==============================
```

Command:

```text
cd site && npm run build
```

Exit: `0`

Literal decisive gate output, copied from the 266-line raw terminal log:

```text
> bollyai-site@0.1.0 test:boxoffice
> node --test lib/boxoffice-schema.test.mjs
# tests 17
# suites 0
# pass 17
# fail 0
# cancelled 0
# skipped 0
# todo 0
[guard-western] OK: all series in data/series/ are Western (or protected).
[guard-films] OK: all 72 films in data/films/ are Western (hollywood).
[links] 480/480 series linked, 4800 edges, avg 10.0/series -> data/_state/series-links.json
[links] 7 curation warning(s):
  - universe "Money Heist" references missing slug "money-heist-korea"
  - universe "Reply" references missing slug "reply-1988"
  - universe "Reply" references missing slug "reply-1994"
  - universe "Reply" references missing slug "reply-1997"
  - watch_next["money-heist"] references missing slug "money-heist-korea"
  - watch_next["the-last-of-us"] references missing slug "all-of-us-are-dead"
  - watch_next["the-last-of-us"] references missing slug "sweet-home"
image variants: processed=162 skipped=0
search-index.json: 613 entries
ask-index.json: 545 records (477 with a grounded BollyMeter score)
sitemaps: index + 11 children | 5654 URLs (pages 34, films 216, series 480, where-to-watch 342, seasons 1631, episodes 2873, explainers 21, endings 45, predictions 1, watch 11) + 301 images
> bollyai-site@0.1.0 build
> next build && npm run lint:aggregate && npm run postbuild:filecap && npm run lint:static-assets
   ▲ Next.js 15.5.22
 ✓ Compiled successfully in 7.1s
 ✓ Generating static pages (5661/5661)
 ✓ Exporting (2/2)
> bollyai-site@0.1.0 lint:aggregate
> node scripts/assert-no-aggregate-rating.mjs
> bollyai-site@0.1.0 postbuild:filecap
filecap: out has 6847 files
> bollyai-site@0.1.0 lint:static-assets
> node scripts/assert-static-assets.mjs
Static asset gate: 778 unique references across 5666 HTML/CSS files, 0 missing.
```

Authoritative build-side-effect check: `git diff --name-status` was empty after the
Next 15 build. Only the intended staged merge and the pre-existing unrelated untracked
file were present. The test merge was then aborted cleanly.

Raw ephemeral log fingerprints:

```text
worldclass-pytest.log             31 lines  sha256 4cd7d6eccfd57a82b4b0536319e6c9524f397b701ee84abce262a44ad8ad68f7
worldclass-build-next15.log      266 lines  sha256 1d56c1685ac4c54ac258975cf698f1e9796ec75fc2ce87039bf896a73112c9cf
```

### B. Weekly-contract integration

Merge result against mandated local main: clean, no conflict.

Command:

```text
python3 -m pytest tests/
```

Exit: `0`

Literal output:

```text
============================= test session starts ==============================
platform linux -- Python 3.12.3, pytest-9.0.3, pluggy-1.6.0
rootdir: /home/aditya/bollyai
plugins: anyio-4.13.0, respx-0.23.1, asyncio-1.3.0
asyncio: mode=Mode.STRICT, debug=False, asyncio_default_fixture_loop_scope=None, asyncio_default_test_loop_scope=function
collected 311 items

tests/test_boxoffice_compat_cli.py .....                                 [  1%]
tests/test_boxoffice_publish_rule.py .......                             [  3%]
tests/test_boxoffice_source_clearance.py ..............                  [  8%]
tests/test_boxoffice_week_contract.py .................................. [ 19%]
...........                                                              [ 22%]
tests/test_brand_lock.py .........                                       [ 25%]
tests/test_common_atomic_json.py ....                                    [ 27%]
tests/test_draft_reviews_gates.py ...................................... [ 39%]
....................                                                     [ 45%]
tests/test_ending_explained.py ......................................... [ 58%]
.....                                                                    [ 60%]
tests/test_fetcher_degrade.py ....                                       [ 61%]
tests/test_merge_reviews.py ............                                 [ 65%]
tests/test_ops_workflows.py .....                                        [ 67%]
tests/test_ott_calendar.py ....                                          [ 68%]
tests/test_ott_western.py ..............                                 [ 72%]
tests/test_predictions.py ..                                             [ 73%]
tests/test_run_all_boxoffice.py .........                                [ 76%]
tests/test_style_leaks.py .....................                          [ 83%]
tests/test_validate_films.py .................                           [ 88%]
tests/test_verify_grounding.py ......                                    [ 90%]
tests/test_viewing_claim.py .............................                [100%]

============================= 311 passed in 5.88s ==============================
```

Command:

```text
cd site && npm run build
```

Exit: `0`

Literal decisive gate output, copied from the 261-line raw terminal log:

```text
> bollyai-site@0.1.0 test:boxoffice
> node --test lib/boxoffice-schema.test.mjs
# tests 17
# suites 0
# pass 17
# fail 0
# cancelled 0
# skipped 0
# todo 0
[guard-western] OK: all series in data/series/ are Western (or protected).
[guard-films] OK: all 72 films in data/films/ are Western (hollywood).
[links] 480/480 series linked, 4800 edges, avg 10.0/series -> data/_state/series-links.json
[links] 7 curation warning(s):
  - universe "Money Heist" references missing slug "money-heist-korea"
  - universe "Reply" references missing slug "reply-1988"
  - universe "Reply" references missing slug "reply-1994"
  - universe "Reply" references missing slug "reply-1997"
  - watch_next["money-heist"] references missing slug "money-heist-korea"
  - watch_next["the-last-of-us"] references missing slug "all-of-us-are-dead"
  - watch_next["the-last-of-us"] references missing slug "sweet-home"
image variants: processed=162 skipped=0
search-index.json: 613 entries
ask-index.json: 545 records (477 with a grounded BollyMeter score)
sitemaps: index + 9 children | 2756 URLs (pages 30, films 216, series 480, where-to-watch 342, seasons 1631, endings 45, predictions 1, watch 11) + 301 images
> bollyai-site@0.1.0 build
> next build && npm run lint:aggregate && npm run postbuild:filecap
   ▲ Next.js 15.5.22
 ✓ Compiled successfully in 9.1s
 ✓ Generating static pages (5661/5661)
 ✓ Exporting (2/2)
> bollyai-site@0.1.0 lint:aggregate
> node scripts/assert-no-aggregate-rating.mjs
> bollyai-site@0.1.0 postbuild:filecap
filecap: out has 6840 files
```

Authoritative build-side-effect check: `git diff --name-status` was empty after the
Next 15 build. Only the intended staged merge and the pre-existing unrelated untracked
file were present. The test merge was then aborted cleanly.

Raw ephemeral log fingerprints:

```text
weekly-pytest.log                 31 lines  sha256 290eb2c38d824356eda4bd13d65ed535e16e87fd396fac7d47b24d921c95fa83
weekly-build-next15.log          261 lines  sha256 7d4dc77154860e3ff84572da7077342006234cac296c644271b27d60d372e9e4
```

## 6. NOT DONE / UNVERIFIED

- No merge was made into `main`. No push, deploy, branch deletion, branch rename,
  force operation, or `--no-verify` was performed.
- No `.env`, vault, Cloudflare token, credential, or protected auth store was read.
- No live HTTP check or deployment check was run. This task was source-control and
  integration due diligence, not production verification.
- No live box-office source was procured or called. Both old lanes remain intentionally
  empty without approved production adapters.
- The combined worldclass plus third-lane tree was not built after its two conflicts,
  because the task prohibits fixing the lanes and the third lane already has a separate
  completed audit. The exact conflicts and required package union are recorded above.
- Local Node 22.22.1 satisfies the installed package engine ranges, but exact GitHub
  workflow parity on Node 20 was not rerun.
- A current integrated-tree design-reviewer score was not rerun. Worldclass changes the
  frontend, so a fresh score of at least 7.5 would be required if it were not already
  landed. Historical branch self-reports were not accepted as current evidence.
- `npm ci` reported 3 dependency vulnerabilities: 2 moderate and 1 high. Detailed
  `npm audit` adjudication and dependency upgrades were outside this diagnosis-only task.
- The 2,873 episode and 21 explainer sitemap discovery wave was build-verified but not
  independently assessed for search-engine rollout impact.
- Ephemeral raw logs under `/tmp/sol-max-bollyai-20260809.qPEvYR/` are not repo
  deliverables and may disappear after reboot. Their decisive literal output and hashes
  are preserved above.
- The pre-existing untracked `SOURCE-PROCUREMENT-20260809.md` was preserved untouched
  and is not an artefact of this audit.

## Final proof: local main untouched

The local `main` ref never moved. The integration branch contains a temporary merge and
its inverse revert only; no product-lane delta remains in its final tree.

```text
$ git branch --show-current
codex/sol-max-bolly-integration-20260809

$ git log --oneline -1 main
2053f9db chore(sitemaps): register the 4 newly merged series

$ git rev-parse main
2053f9db6efcba9488648de5610797e5aa87bfcb

$ git status --short
 M last.txt
?? SOL-STRANDED-LANES-20260809.md
?? SOURCE-PROCUREMENT-20260809.md
```

Fresh remote context, fetched read-only for the landing decision:

```text
$ git log --oneline -1 origin/main
81149d15 data: daily refresh 2026-08-09T05:30:23Z
```
