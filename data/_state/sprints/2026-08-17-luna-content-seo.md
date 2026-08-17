# U4-BollyAI content and SEO tranche, 2026-08-17

## Result

The Aug 17-30 window now has three verified Apple TV entries: Stillwater Season
5 and The Dynasty: UConn Huskies on Aug 21, 2026, plus Dark Matter Season 2 on
Aug 28, 2026. Each release uses an official Apple press announcement for its
date plus an Apple TV title page that lists Original Audio as English and Region
of Origin as United States. The Dark Matter entry maps to the existing
`data/series/dark-matter.json` slug and renders `/series/dark-matter/`. No
existing series or film metadata was changed.

Baseline before regeneration: `data/ott/calendar/2026-W34.json` and
`2026-W35.json` each had `entries: []`; the registry contained 13 entries and
the active two-week window had no verified releases. The live generator could
write that empty result with exit code 0 when every fetcher returned zero.

## Official sources

- https://www.apple.com/tv-pr/news/2026/05/apple-tvs-the-dynasty-uconn-huskies-featuring-the-legendary-university-of-connecticut-womens-college-basketball-team-set-to-premiere-globally-august-21-2026/
- https://tv.apple.com/us/show/the-dynasty-uconn-huskies/umc.cmc.38cvggceyd4sn4sfgl3kus89b
- https://www.apple.com/tv-pr/news/2026/08/apple-tv-unveils-heartwarming-trailer-for-season-five-of-award-winning-series-stillwater-premiering-friday-august-21/
- https://tv.apple.com/us/show/stillwater/umc.cmc.3czcagetjq31vvbgkkyp1xiao
- https://www.apple.com/tv-pr/news/2026/04/apples-acclaimed-sci-fi-hit-dark-matter-starring-golden-globe-nominee-joel-edgerton-and-academy-award-winner-jennifer-connelly-returns-for-season-two-on-august-28-2026/
- https://tv.apple.com/us/show/dark-matter/umc.cmc.4luj45vtqpmjsvb6sc2675oeg

## Automation audit and fix

`.github/workflows/ott-calendar-roll.yml` already provides the Mon/Thu
schedule, manual dispatch, regeneration, build, and downstream delivery. No
new workflow or cadence change was needed. `engine/regen_ott_weekly.py` now
fails closed with exit code 2 before writing any calendar whenever an
unexpected live refresh fetches zero announcements, even if the local registry
still contains entries. `--no-fetch` remains the explicit registry-only rebuild
mode. The scheduled workflow does not use that bypass. This prevents a
network/source outage from relabelling stale registry data as a successful
fetched calendar.

## Verification

- `npm ci --ignore-scripts` from `site/` -> lockfile install succeeded; 38 packages added, 3 audit findings reported (2 moderate, 1 high); no lockfile or dependency edits.
- `npm run build` from `site/` -> passed; 5,664 static pages generated, 6,850 output files under cap, 0 missing static assets.
- `python3 engine/regen_ott_weekly.py --data-dir data --today 2026-08-17 --weeks 2 --no-fetch` -> exit 0, `entries: 3`, window 2026-08-17 through 2026-08-30, archives W34/W35 regenerated.
- `python3 scripts/batch/validate_series.py dark-matter` -> PASS, 1/1 clean.
- `pytest -q tests/test_ott_calendar.py tests/test_ott_regen.py tests/test_ott_western.py` -> 22 passed.
- The focused regression test monkeypatches `refresh_registry` to return zero -> guard returns 2 and no calendar is written.
- Alias regression coverage proves an incoming `Apple TV+` record updates the existing `Apple TV` registry row without duplication. Missing requested-season coverage proves that older season metadata is not reused and the release verdict stays neutral.
- `pytest -q` -> 320 passed.
- `git diff --check` -> pass.
- Build-generated sitemap timestamp changes were discarded after verification; no frontend files remain changed.
- Existing workflow audit -> `ott-calendar-roll`, cron `0 3 * * 1,4`; no duplicate automation added.

The registry's older `Cobra` Wikidata URL remains untouched because it is
outside this tranche and was not used as evidence for the new entries.
