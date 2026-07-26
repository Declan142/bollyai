# BollyAI Weekly Box Office

This directory feeds only `/box-office/`, the Western worldwide weekly board.
The board reports gross earned inside one exact, fully closed
Monday-to-Sunday period. It does not contain lifetime totals.

The old club and year-scoreboard selectors are intentionally retired. Those
routes require a separately sourced lifetime dataset and must not be derived
from weekly readings.

## Public contract

`current-week.json` uses `schema: bollyai-boxoffice-week/v3`.

The root object has these exact fields:

- `schema`: always `bollyai-boxoffice-week/v3`.
- `status`: `ready` or `data_pending`.
- `generated_at`: an ISO timestamp with a timezone.
- `territory`: always `Worldwide`.
- `week`: the exact closed week with canonical `start`, `end`, and `label`.
- `records`: Western `hollywood` or `streaming` rows only.

Each record has one publishable metric, `week_gross_usd`. Its measurement is
`exact_week`, its currency is USD, and its period and territory must equal the
board. A source reading carries the same scope plus a public HTTPS URL, stable
independence group, `as_of`, `fetched_at`, and positive numeric value.
Production independence groups are code-owned and currently empty because no
operational exact-week adapter is approved. Fixture-only host mappings are
passed explicitly by offline tests and cannot authorize a public write.

The shared Python and JavaScript validators reject:

- v1, v2, unexpected, lifetime, cumulative, opening-weekend, and
  week-to-date fields;
- period, territory, currency, metric, or canonical-route mismatches;
- non-Western rows, invalid source timing, duplicate films, sources, or
  source groups;
- future provenance, sub-millisecond timestamp ambiguity, literal/private
  hosts, URL fragments, and unregistered source-group claims;
- budgets, salaries, and forbidden dash glyphs;
- a stored value or label that does not match recomputed consensus.

A `data_pending` board is valid only with an empty `records` array. A `ready`
board needs at least one record with a publishable number.

## Consensus rule

Consensus considers the full range across every independent source group for
a film. It never chooses a convenient agreeing pair while ignoring a third
divergent reading.

- Two or more groups within 10 percent publish the lowest reading as
  `trade estimate`.
- A full-source spread above 10 and at most 25 percent publishes only the
  lowest reading as `lower figure`.
- A single source, a repeated group, or spread above 25 percent publishes no
  number and remains `tracking`.

## Source clearance gate

`source-candidates.json` is a sanitized, machine-readable assessment registry.
It contains no endpoint, credential, fee, or licensing-term assumptions. The
offline evaluator is `engine/fetchers/boxoffice_source_clearance.py`.

The evaluator compares the registry to a code-owned policy that the JSON
cannot weaken. A source qualifies only when all of these are true:

- its coverage is proven as Worldwide gross in USD for one exact, closed
  Monday-to-Sunday period on the UTC calendar;
- its independence group is attested with a reviewed reference;
- coverage, legal, terms, and license reviews are complete;
- activation has a reviewed approval reference and an adapter registered in
  code.

The gate opens only with at least two qualifying sources from two distinct
independence groups. Opening this gate does not itself create or enable an
adapter. Until both source clearance and an operational adapter exist, the
board remains `data_pending`.

The 2026-07-26 research snapshot is intentionally non-authorizing:

| Candidate | Verified public signal | Current assessment |
| --- | --- | --- |
| Box Office Mojo public weekly chart | Domestic, Friday to Thursday | Scope mismatch |
| The Numbers public charts | Domestic | Scope mismatch; exact period not proven |
| IMDb Box Office bulk data | Licensed candidate documents Weekly and Worldwide options | Policy blocked by the project rule against IMDb datasets; exact weekdays and currency not proven |
| Comscore Global Box Office | Commercial global reporting candidate | Needs review; exact period and currency not proven |

Every candidate remains unapproved and unconfigured. Candidate documentation
links record only the public pages used for this assessment.

Procurement and activation checklist:

1. Obtain provider documentation proving the requested exact closed period,
   territory, measurement, and currency without relabelling.
2. Complete legal, terms, license, robots, and rate-limit review as applicable.
3. Attest the estimation and ownership independence of each source group.
4. Record sanitized review references only. Keep credentials and commercial
   terms outside this repository.
5. Implement an offline-testable adapter with captured fixtures and strict
   provenance timestamps.
6. Change a candidate to `cleared`, approved, configured, and code-registered
   only in a separately reviewed activation change.
7. Pass source-clearance, parser-parity, consensus, last-good, full test, and
   production-build gates before enabling a live write.

## Last-good publication

`engine/fetchers/run_all.py` owns the public write. It validates a complete
candidate before writing and uses a same-directory atomic replacement. The
writer preserves file mode, syncs file and directory state, and treats
byte-identical output as a no-op.

A missing live adapter, missing consensus, or invalid candidate does not
replace a validated existing file. Pre-replacement write failures also
preserve it. If the destination replacement succeeds but the final directory
sync fails, the job reports a durability failure plus the measured
`changed`/`preserved_previous_bytes` state instead of falsely claiming the
old bytes survived. The box-office job reports one structured status:

- `updated` or `unchanged` for a validated write;
- `dry_run` for a validated fixture candidate without `--write`;
- `preserved_last_good` when a pending live result leaves existing bytes
  untouched and those bytes validate as a ready v3 board;
- `preserved_pending` when existing bytes validate only as `data_pending`;
- `data_pending` when no prior board exists;
- `failed` for a contract or write error.

Existing bytes are parsed and validated before receiving any "last good"
label. Invalid JSON or a non-v3 document returns `INVALID_EXISTING_BOARD`,
stays byte-identical, and fails the wider refresh.

The top-level `overall_status` is `ok`, `degraded`, or `failed`. Intentional
live `data_pending` is degraded but does not fail the wider refresh process.
A hard contract or writer error exits nonzero.

## Offline verification

The fixture is `data/cache/fixtures/boxoffice_week_exact.json`. It contains
only invented names, example.com URLs, and deterministic exact-week readings.
Fixture mode never calls a network source.
Owner CLIs reject fixture writes into the canonical public data directory.
Temporary fixture output remains available for tests and dry-run workflows.

```bash
python3 engine/fetchers/boxoffice_western.py \
  --fixture-mode --today 2026-07-26
python3 engine/fetchers/run_all.py \
  --fixture-mode --today 2026-07-26
python3 engine/fetchers/boxoffice_source_clearance.py
python3 scripts/boxoffice/fetch_boxoffice.py --list-sources
python3 scripts/boxoffice/fetch_boxoffice.py --report
python3 -m pytest -q tests/test_boxoffice_week_contract.py \
  tests/test_run_all_boxoffice.py tests/test_common_atomic_json.py
cd site && node --test lib/boxoffice-schema.test.mjs
```

The standalone clearance command exits 2 while candidates remain pending.
That is the activation gate's expected closed state, not a source failure.
The Python and JavaScript readers share
`tests/fixtures/boxoffice/ready-v3.json` as a cross-runtime contract fixture.

## Operational adapter status

No live exact-week source adapter is enabled yet. Live runs evaluate the
checked-in registry, return `SOURCE_CLEARANCE_PENDING`, publish no substitute,
and preserve the last-good bytes. This is deliberate. If two sources and their
adapter references are eventually cleared and code-registered before adapter
execution is wired, the result remains pending with
`NO_OPERATIONAL_SOURCE_ADAPTER`.

Before enabling an operational adapter, it must:

1. pass the source-clearance gate;
2. prove that each provider reading is gross for the requested exact week,
   not a lifetime, cumulative, opening-weekend, or week-to-date total;
3. map source independence through the reviewed code-owned registry;
4. emit the strict source payload without relabelling a stale period;
5. pass the full offline, parser-parity, last-good, and production-build
   gates.

## Legacy India pipeline

`engine/fetchers/boxoffice.py` remains only for the separate day-wise India
publish-rule tests and historical adapters. It is not imported by
`run_all.py`. Its optional fill command can read or write only
`_cache/boxoffice/legacy-india-current-week-v1.json`; it cannot overwrite the
public v3 board. Its generic `--emit` is also confined beneath
`_cache/boxoffice/`. The compatibility script
`scripts/boxoffice/fetch_boxoffice.py` delegates to the strict Western job and
forbids fixture publication.
