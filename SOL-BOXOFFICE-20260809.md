# SOL-MAX Box-Office Weekly Source Engine - 2026-08-09

## LANDABLE: YES

The branch is landable as a fail-closed source engine and honest no-current-data
public surface. All required code and build gates pass. Stale, empty, uncleared,
or mismatched source results now stop the owner process with an explicit error,
and stale stored bytes cannot produce box-office rows, rankings, or box-office
structured data on the public page.

`LANDABLE: YES` does not mean that live weekly figures are available. There are
still zero cleared production source adapters and zero qualifying independence
groups. That is an operational data-availability limitation, not a reason to
fabricate a feed or let the job report health. The checked-in board remains
intentionally unchanged, stale, and empty. Until source procurement clears, the
correct production outcome is a loud nonzero fetch plus an honest public
no-current-data state.

Blocking list: none for landing this fail-closed lane.

## STATE AS FOUND

### Repository state

- Branch: `feat/boxoffice-weekly-source-engine`
- Starting HEAD: `8ffb2dc2678cb97904a056185029abc0211d67b6`
- No merge, rebase, push, deployment, or force operation was performed.
- The initial worktree contained the disclosed generated
  `site/public/sitemap.xml` change. The required site build regenerated it via
  the repository's own prebuild script. Its current SHA-256 is
  `29c5ff23b463a70b2a5d9900ffc96176e442f114e6dd616e068ba4a7b6a7dc17`,
  exactly the version at branch HEAD. The pre-build generated version remains
  recoverable in the pre-existing stash
  `codex-preserve-user-sitemap-before-weekly-source-engine`, where its SHA-256
  is `1f572eb878a3382755473f7831164f9b1505827891ceae3326d0a21feba37d96`.
- The required build also regenerated `site/next-env.d.ts`; that incidental
  Next.js change was restored to branch HEAD and is not part of this change.

### Baseline gates, before changes

The branch's existing tests and build were green, but neither gate exercised
the stale-current-board failure condition.

Command:

```text
python3 -m pytest tests/
```

Exit: `0`

Literal result:

```text
collected 319 items
...
tests/test_viewing_claim.py .............................                [100%]
============================= 319 passed in 5.48s ==============================
```

Command:

```text
cd site && npm run build
```

Exit: `0`

Literal relevant output:

```text
> bollyai-site@0.1.0 test:boxoffice
> node --test lib/boxoffice-schema.test.mjs lib/boxoffice-public-state.test.mjs
...
1..18
# tests 18
# suites 0
# pass 18
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 105.834785
[guard-western] OK: all series in data/series/ are Western (or protected).
[guard-films] OK: all 72 films in data/films/ are Western (hollywood).
...
sitemaps: index + 9 children | 2756 URLs (pages 30, films 216, series 480, where-to-watch 342, seasons 1631, endings 45, predictions 1, watch 11) + 301 images

> bollyai-site@0.1.0 build
> next build && npm run lint:aggregate && npm run postbuild:filecap

  ▲ Next.js 14.2.35
...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
...
 ✓ Generating static pages (5661/5661)
   Finalizing page optimization ...
   Collecting build traces ...
...
> bollyai-site@0.1.0 lint:aggregate
> node scripts/assert-no-aggregate-rating.mjs

> bollyai-site@0.1.0 postbuild:filecap
...
filecap: out has 6839 files
```

The baseline build printed this non-fatal warning twice, but completed with
exit `0`:

```text
 ⚠ Found lockfile missing swc dependencies, patching...
 ⨯ Failed to patch lockfile, please try uninstalling and reinstalling next in this workspace
TypeError: Cannot read properties of undefined (reading 'os')
    at fetchPkgInfo (/home/aditya/bollyai/site/node_modules/next/dist/lib/patch-incorrect-lockfile.js:73:25)
```

### Stored data as found

`data/boxoffice/current-week.json` was 262 bytes and contained:

```json
{
  "generated_at": "2026-07-25T23:31:41Z",
  "records": [],
  "schema": "bollyai-boxoffice-week/v3",
  "status": "data_pending",
  "territory": "Worldwide",
  "week": {
    "end": "2026-07-19",
    "label": "13 to 19 July 2026",
    "start": "2026-07-13"
  }
}
```

Its filesystem modification time was `2026-07-27 00:23:41 +0530`. On the task
date, `2026-08-09`, the latest fully closed UTC week was `2026-07-27` through
`2026-08-02`. The stored board was therefore two closed-week slots behind and
empty.

`data/boxoffice/source-candidates.json` contained six candidates:

| Assessment | Count |
|---|---:|
| `scope_mismatch` | 4 |
| `policy_blocked` | 1 |
| `needs_review` | 1 |
| approved | 0 |
| configured adapter | 0 |
| independence attested | 0 |
| fully qualifying | 0 |

The policy-blocked row is the IMDb bulk dataset. It was not activated, read, or
adapted. No JustWatch scraper, IMDb dataset adapter, or Letterboxd dependency
was added.

`data/boxoffice/README.md` already stated that production adapter factories and
production source groups were empty, and that code-owned fixtures could not
authorize a public write. That documentation was accurate: the lane had a
strict schema, source-clearance model, fixture adapters, consensus oracle,
atomic last-good preservation, and substantial tests, but no operational live
weekly source.

### Precisely what was finished, stubbed, and broken

| State | Finding |
|---|---|
| Finished | Strict v3 exact-week schema, conservative consensus, atomic publication, source-clearance registry, two synthetic offline adapters, Python/JavaScript schema parity, and an initial pending-state public projection. |
| Stubbed by policy | `PRODUCTION_ADAPTER_FACTORIES` and `PRODUCTION_SOURCE_GROUPS` were empty; source clearance had 0 of 2 required sources and 0 of 2 independence groups. This remains intentionally closed. |
| Broken | `fetch_boxoffice.py --report` returned exit 0 for the old empty board. |
| Broken | Both fixture adapters could report `SOURCE_PERIOD_STALE`, yet the owner fetch returned exit 0 and collapsed the result to a generic pending code. |
| Broken | An adapter claiming `fresh` could provide an older `observed_week`; the generic boundary relabelled those rows with the requested week. |
| Broken | When no usable observation existed, the adapter batch minted `generated_at` from wall clock, making an empty attempt look freshly generated. |
| Broken | `staleness_check.py` reported `ok: false` and 51 stale film trackers but always returned exit 0; it did not inspect the weekly board at all. |
| Broken | `run_all.py`, the compatibility CLI, the owner fetcher, and the tentpole wrapper masked pending/degraded box-office outcomes as successful process exits. |
| Broken | Python and JavaScript structural validators allowed a tracking record with `sources: []`. |
| Broken | The JavaScript public projector trusted only `board.status`; a structurally valid old `ready` fixture rendered rows, rankings, `Dataset`, and `ItemList` JSON-LD as current. |
| Misleading | The checked-in pending page withheld rows, but displayed the old week as the latest/current week and exposed its old generated date. |

Literal baseline silent-failure evidence:

```text
$ python3 scripts/boxoffice/fetch_boxoffice.py --report
"films": 0,
"status": "data_pending",
"end": "2026-07-19",
EXIT 0

$ python3 engine/fetchers/staleness_check.py --sla-hours 26 --now 2026-08-09T12:00:00Z
"checked_count": 51,
"stale_count": 51,
"ok": false,
EXIT 0
```

That was the live defect: the payload admitted failure while the process
reported health.

## CHANGES

| File:line | What changed | Why | Coverage |
|---|---|---|---|
| `engine/fetchers/boxoffice_source_adapters.py:154` | Added an adapter-result admission contract for identity, requested/observed week equality, nonempty fresh rows, and source timestamp consistency. Batch timestamps now come only from admitted observations; an empty batch has no source payload. | Prevent stale relabelling and wall-clock substitution from entering consensus. | `tests/test_boxoffice_source_adapters.py:92`, `:108`, `:122` |
| `engine/fetchers/boxoffice_week_schema.py:216` | Made the default closed-week reference use the UTC date. | Keep Python freshness boundaries aligned with the declared UTC contract and JavaScript. | Existing deterministic closed-week boundary tests in `tests/test_boxoffice_week_contract.py` |
| `engine/fetchers/boxoffice_week_schema.py:375` | Required at least one observed source envelope on every record. | Every record must carry explicit observation provenance. | `tests/test_boxoffice_week_contract.py:108` |
| `engine/fetchers/boxoffice_week_schema.py:476` | Added `validate_current_board`, which requires the latest fully closed week plus a nonempty ready board. | Keep structural historical validation separate from current operational health. | `tests/test_boxoffice_week_contract.py:88` |
| `engine/fetchers/boxoffice_western.py:83` | Preserved adapter-specific stale/empty/failure codes and refused to build a source payload when no observation was admitted. | Do not collapse source failure into generic pending health. | `tests/test_boxoffice_source_adapters.py:174`, `tests/test_boxoffice_compat_cli.py:103` |
| `engine/fetchers/boxoffice_western.py:232` | Made the owner fetcher log an explicit error and exit 2 for every non-ready outcome. | Empty or stale fetches must alert. | `tests/test_boxoffice_compat_cli.py:103` |
| `engine/fetchers/run_all.py:143` | Classified structurally valid previous bytes as stale when their period differs from the requested latest week. | Do not call an old board pending or last-good for current health. | `tests/test_run_all_boxoffice.py:97` |
| `engine/fetchers/run_all.py:314` | Made the orchestrator's default calendar date UTC. | Avoid a host-timezone freshness split at the Monday boundary. | Full orchestrator suite |
| `engine/fetchers/run_all.py:434` | Propagated adapter state/code and made degraded box office exit 2 with an explicit error. | Workflows must fail on no current box-office data. | `tests/test_run_all_boxoffice.py:274` |
| `engine/fetchers/staleness_check.py:93` | Added a weekly-board item with expected/observed periods, source observation time, stable status code, and stale state. | Monitor the canonical public artifact, not only legacy per-film rows. | `tests/test_staleness_check.py:31`, `:55` |
| `engine/fetchers/staleness_check.py:222` | Added fixture trust mode and exit 1 whenever the emitted payload has `ok: false`, with an explicit weekly error on stderr. | A red monitor result must be a red process result. | `tests/test_staleness_check.py:69` |
| `scripts/boxoffice/fetch_boxoffice.py:39` | Made default dates UTC and added `--board` for fixture-safe report testing. | Deterministic parity and direct adversarial proof without changing public data. | `tests/test_boxoffice_compat_cli.py:72` |
| `scripts/boxoffice/fetch_boxoffice.py:101` | Made source listing, current-board report, and non-ready fetches log explicit errors and exit nonzero. | Remove compatibility paths that hid stale/empty outcomes. | `tests/test_boxoffice_compat_cli.py:55`, `:96`, `:103` |
| `scripts/ops/tentpole_live.py:103` | Propagated the nested degraded/failed box-office state to the wrapper exit. | Prevent the workflow wrapper from swallowing the owner failure. | `tests/test_boxoffice_compat_cli.py:177` |
| `site/lib/boxoffice-schema.mjs:320` | Required at least one source envelope per JavaScript record. | Keep cross-runtime provenance enforcement identical. | `site/lib/boxoffice-schema.test.mjs:143` |
| `site/lib/boxoffice-public-state.mjs:21` | Added the latest fully closed UTC week calculation and stale-board projection to `no_current_data`; stale rows, rankings, and JSON-LD arrays are empty. | The public surface must not present old ready bytes as current. | `site/lib/boxoffice-public-state.test.mjs:74`, `:93`, `:111` |
| `site/lib/boxoffice-public-state.d.mts:1` | Extended public-state types with expected/observed periods and stale/no-current-data flags. | Keep the TypeScript consumer aligned with the runtime projector. | Next.js type check in production build |
| `site/app/box-office/page.tsx:23` | Uses the expected current slot in the hero and conditional metadata. | Never label an observed stale period as the current closed week. | Production build and rendered-artifact checks |
| `site/app/box-office/page.tsx:69` | Added an explicit no-current-data panel, expected-versus-observed explanation, and safe empty-board copy. | Make data unavailability honest and prominent. | `site/lib/boxoffice-public-state.test.mjs`, local desktop/mobile review |
| `site/lib/boxoffice-schema.test.mjs:143` | Added zero-source rejection and one-source tracking acceptance parity tests. | Lock the provenance requirement without incorrectly requiring consensus for tracking. | Node box-office test gate |
| `site/lib/boxoffice-public-state.test.mjs:74` | Added stale ready, stale pending, current pending, and UTC boundary cases. | Prove old rows and structured data remain hidden. | Node box-office test gate |
| `tests/test_boxoffice_compat_cli.py:55` | Added report/list/fetch/tentpole nonzero exit and explicit-error assertions. | Lock every public owner seam fail-closed. | Full pytest gate |
| `tests/test_boxoffice_source_adapters.py:92` | Added lying-fresh, fresh-empty, and wall-clock timestamp mismatch cases. | Prove generic adapters cannot relabel or invent freshness. | Full pytest gate |
| `tests/test_boxoffice_week_contract.py:88` | Added latest-period, empty-current, and per-record provenance contract cases. | Lock current-health semantics independently from historical parsing. | Full pytest gate |
| `tests/test_run_all_boxoffice.py:97` | Added stale-byte classification and degraded CLI exit tests. | Preserve bytes safely without describing them as current health. | Full pytest gate |
| `tests/test_staleness_check.py:1` | Added focused healthy-current, empty-current, stale-week, and nonzero CLI monitor tests. | Directly prove the defect is fixed. | Full pytest gate |
| `data/boxoffice/README.md:51` | Documented the freshness window, source-observation rule, stale preservation state, and nonzero owner behavior. | Keep operational expectations explicit. | Documentation review |
| `blueprints/06-REFRESH-OPS.md:31` | Updated refresh operations to describe loud degraded exits and stale public suppression. | Prevent workflow operators from treating preserved bytes as health. | Documentation review |
| `blueprints/08-CORPUS-REPAIR.md:51` | Updated the repair blueprint to require nonzero missing-source behavior. | Keep future lane work aligned with the fail-closed contract. | Documentation review |
| `SOL-BOXOFFICE-20260809.md:1` | Added this state, evidence, and landability report. | Required auditable handoff. | Manual evidence audit |
| `last.txt:1` | Replaced the prior lane handoff with this task's scoped result and gates. | Required repository handoff convention. | Final status review |

## LOUD-FAILURE PROOF

### 1. Old ready data is rejected as stale

Command:

```text
python3 scripts/boxoffice/fetch_boxoffice.py --report --board tests/fixtures/boxoffice/ready-v3.json --fixture-mode --today 2026-08-09
```

Actual exit: `2`

Literal output:

```json
{
  "board_path": "/home/aditya/bollyai/tests/fixtures/boxoffice/ready-v3.json",
  "code": "STALE_BOXOFFICE_BOARD",
  "error": "board week 2026-07-13 to 2026-07-19 is stale; expected 2026-07-27 to 2026-08-02",
  "expected_week": {
    "end": "2026-08-02",
    "label": "27 July to 2 August 2026",
    "start": "2026-07-27"
  },
  "schema": "boxoffice-report-error/v1",
  "status": "failed"
}
```

### 2. An empty board for the expected week is rejected

Command:

```text
python3 scripts/boxoffice/fetch_boxoffice.py --report --today 2026-07-26
```

Actual exit: `2`

Literal output:

```json
{
  "board_path": "/home/aditya/bollyai/data/boxoffice/current-week.json",
  "code": "NO_CURRENT_BOXOFFICE_DATA",
  "error": "latest closed week has no publishable box-office records: 2026-07-13 to 2026-07-19",
  "expected_week": {
    "end": "2026-07-19",
    "label": "13 to 19 July 2026",
    "start": "2026-07-13"
  },
  "schema": "boxoffice-report-error/v1",
  "status": "failed"
}
```

### 3. The monitor itself exits red on a stale weekly fixture

The temporary data directory contained an exact byte copy of
`tests/fixtures/boxoffice/ready-v3.json` at
`boxoffice/current-week.json` and no film documents.

Command:

```text
python3 engine/fetchers/staleness_check.py --data-dir /tmp/bollyai-stale-proof-20260809 --fixture-mode --now 2026-08-09T12:00:00Z
```

Actual exit: `1`

Literal stderr:

```text
ERROR: staleness check failed: 1 of 1 items stale; weekly_boxoffice=STALE_BOXOFFICE_BOARD
```

Literal stdout:

```json
{
  "checked_count": 1,
  "generated_at": "2026-08-08T22:09:06Z",
  "items": [
    {
      "age_hours": 484.42,
      "code": "STALE_BOXOFFICE_BOARD",
      "expected_week": {
        "end": "2026-08-02",
        "label": "27 July to 2 August 2026",
        "start": "2026-07-27"
      },
      "kind": "weekly_boxoffice",
      "latest_boxoffice_at": "2026-07-20T07:35:00Z",
      "observed_week": {
        "end": "2026-07-19",
        "label": "13 to 19 July 2026",
        "start": "2026-07-13"
      },
      "path": "/tmp/bollyai-stale-proof-20260809/boxoffice/current-week.json",
      "reason": "stale_week",
      "stale": true
    }
  ],
  "ok": false,
  "schema": "bollyai-staleness/v1",
  "sla_hours": 26,
  "stale_count": 1
}
```

### 4. The real uncleared-source seam is loud and preserves bytes

Command:

```text
python3 scripts/boxoffice/fetch_boxoffice.py --today 2026-08-09
```

Actual exit: `2`

Literal stderr:

```text
ERROR: box-office fetch did not produce current data [SOURCE_CLEARANCE_PENDING] status=preserved_stale source_readings=0
```

Literal decisive stdout fields:

```json
{
  "adapter_states": [],
  "changed": false,
  "code": "SOURCE_CLEARANCE_PENDING",
  "preserved_previous_bytes": true,
  "previous_board_status": "stale",
  "published_records": 0,
  "source_readings": 0,
  "status": "preserved_stale"
}
```

The canonical board SHA-256 after this command was
`357d0af9d3043a1bee6b246b9b20856d4cbf8338945d108b5925b9779eeb370a`,
exactly equal to `HEAD:data/boxoffice/current-week.json`.

## GATES

### Before

| Command | Exit | Literal result |
|---|---:|---|
| `python3 -m pytest tests/` | 0 | `319 passed in 5.48s` |
| `cd site && npm run build` | 0 | `18` box-office tests passed; `Compiled successfully`; `Generating static pages (5661/5661)`; `node scripts/assert-no-aggregate-rating.mjs`; `filecap: out has 6839 files` |
| `python3 scripts/boxoffice/fetch_boxoffice.py --report` | 0 | `status: data_pending`, `films: 0`, week ending `2026-07-19` |
| `python3 engine/fetchers/staleness_check.py --sla-hours 26 --now 2026-08-09T12:00:00Z` | 0 | `checked_count: 51`, `stale_count: 51`, `ok: false` |

### After

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
collected 333 items

tests/test_boxoffice_compat_cli.py .........                             [  2%]
tests/test_boxoffice_publish_rule.py .......                             [  4%]
tests/test_boxoffice_source_adapters.py ...........                      [  8%]
tests/test_boxoffice_source_clearance.py ..............                  [ 12%]
tests/test_boxoffice_week_contract.py .................................. [ 22%]
.............                                                            [ 26%]
tests/test_brand_lock.py .........                                       [ 29%]
tests/test_common_atomic_json.py ....                                    [ 30%]
tests/test_draft_reviews_gates.py ...................................... [ 41%]
....................                                                     [ 47%]
tests/test_ending_explained.py ......................................... [ 60%]
.....                                                                    [ 61%]
tests/test_fetcher_degrade.py ....                                       [ 62%]
tests/test_merge_reviews.py ............                                 [ 66%]
tests/test_ops_workflows.py .....                                        [ 67%]
tests/test_ott_calendar.py ....                                          [ 69%]
tests/test_ott_western.py ..............                                 [ 73%]
tests/test_predictions.py ..                                             [ 73%]
tests/test_run_all_boxoffice.py ...........                              [ 77%]
tests/test_staleness_check.py ...                                        [ 78%]
tests/test_style_leaks.py .....................                          [ 84%]
tests/test_validate_films.py .................                           [ 89%]
tests/test_verify_grounding.py ......                                    [ 91%]
tests/test_viewing_claim.py .............................                [100%]

============================= 333 passed in 6.03s ==============================
```

Command:

```text
cd site && npm run build
```

Exit: `0`

Literal relevant output:

```text
> bollyai-site@0.1.0 test:boxoffice
> node --test lib/boxoffice-schema.test.mjs lib/boxoffice-public-state.test.mjs
...
1..24
# tests 24
# suites 0
# pass 24
# fail 0
# cancelled 0
# skipped 0
# todo 0
# duration_ms 105.864
...
 ✓ Compiled successfully
   Linting and checking validity of types ...
   Collecting page data ...
...
 ✓ Generating static pages (5661/5661)
   Finalizing page optimization ...
   Collecting build traces ...
...
> bollyai-site@0.1.0 lint:aggregate
> node scripts/assert-no-aggregate-rating.mjs

> bollyai-site@0.1.0 postbuild:filecap
...
filecap: out has 6839 files
```

The same non-fatal Next.js lockfile-patching warning shown in the baseline
appeared during the final build. Compilation, type checking, static generation,
`assert-no-aggregate-rating`, and the file-cap gate all completed; the command
exited `0`.

Additional gates:

| Command or check | Result |
|---|---|
| `python3 -m pytest -q tests/test_boxoffice_week_contract.py tests/test_boxoffice_source_adapters.py tests/test_run_all_boxoffice.py tests/test_boxoffice_compat_cli.py tests/test_staleness_check.py` | `81 passed in 3.37s` |
| `cd site && npm run test:boxoffice` | `24` passed, `0` failed |
| `git diff --check` | exit `0`, no output |
| `git diff --name-only -- data/series` | exit `0`, no output |
| `rg -q "Fixture Alpha|100000000|\\$100M" site/out/box-office/index.html` | exit `1`, no stale fixture row/value found |
| `rg -q '"@type":"(Dataset|ItemList|AggregateRating)"' site/out/box-office/index.html` | exit `1`, no box-office dataset/list/rating structured data found |
| Rendered copy check | `No current box-office data`, `Current Closed-Week Availability`, expected week `27 July to 2 August 2026`, and observed-vs-expected explanation all present |
| Desktop/mobile local artifact review | PASS, `8.2/10` against required `7.5`; 1440x1000 and real 390x844 CSS viewport checks; no horizontal overflow at 390 or 320 px |
| Canonical board integrity | Worktree SHA-256 equals HEAD: `357d0af9d3043a1bee6b246b9b20856d4cbf8338945d108b5925b9779eeb370a` |
| Generated sitemap integrity | Worktree SHA-256 equals HEAD after repo prebuild regeneration: `29c5ff23b463a70b2a5d9900ffc96176e442f114e6dd616e068ba4a7b6a7dc17` |

`python3 scripts/batch/validate_series.py` does not apply: no
`data/series/*.json` file changed. The command intentionally requires at least
one series target, so running it with no target would report `no target files`
rather than validate this box-office-only change. Series-related repository
tests remained green inside the full 333-test gate.

## NOT DONE / UNVERIFIED

- `UNVERIFIED`: No live exact-week source fetch was possible because there are
  zero cleared/configured production adapters and zero qualifying independent
  source groups. The clearance gate stopped before any source network request.
- `UNVERIFIED`: The legal, redistribution, period, currency, timezone, and
  lineage suitability of candidate commercial feeds remains procurement work.
  No candidate was approved in this task.
- `UNVERIFIED`: No live `bollyai.in` deployment or production HTTP check was
  performed. Deployment was explicitly forbidden.
- `UNVERIFIED`: No integration/rebase against the current `origin/main` was
  performed. At completion this feature branch was 28 commits behind and 1
  commit ahead before the task commit. The eventual integrator must preserve
  both main's newer `site/package.json` static-asset lint addition and this
  lane's box-office test wiring if that file conflicts.
- The current public data file is still stale and empty by design. It was not
  edited, refreshed with a plausible number, or replaced with fixture data.
- No budget, salary, first-hand viewing claim, TMDB image, `AggregateRating`,
  banned-source adapter, credential, token, or environment file was added.
- Non-blocking visual polish: the small `Worldwide` pill overlaps the empty
  board border by about 6 CSS pixels on desktop. It does not obscure content,
  affect mobile overflow, or weaken the no-current-data message.
- Non-blocking toolchain warning: Next.js could not patch missing SWC lockfile
  metadata, but the exact required build and every chained build gate exited
  successfully.
