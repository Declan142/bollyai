# BLUEPRINT 06 - Freshness, returning seasons, calendars, crons

Use when: keeping shipped pages true. Updates are uncapped; NEW-page deploy waves are
velocity-throttled (confirm cadence with the ledger / Aditya before large waves).
Prompt: `prompts/P07` (headless-safe refresh tick).

## Automated layer (GitHub Actions - schedules transcribed 2026-07-04; YAML wins on drift)

| Workflow | Cron (UTC) | IST | Purpose |
|---|---|---|---|
| `daily-refresh.yml` | `30 4 * * *` | 10:00 daily | `engine/fetchers/run_all.py --live-only` refresh, then build + deploy (own CF token secret - leave it) |
| `ott-calendar-roll.yml` | `0 3 * * 1,4` | 08:30 Mon/Thu | regen `data/ott/calendar.json` via `engine/regen_ott_weekly.py --weeks 2` |
| `friday-surge.yml` | `0 4,7,11 * * 5` | 09:30/12:30/16:30 Fri | release-day refresh bursts |
| `tentpole-live.yml` | `0 */3 * * 5,6,0,1` | every 3h Fri-Mon | tentpole live tracking |
| `health-digest.yml` | `0 2 * * 0` | 07:30 Sun | site health digest |

All have `workflow_dispatch` for manual runs. The Actions COMMIT FROM RUNNERS: local
sessions must `git pull --rebase` before pushing anything, and local copies of generated
files go stale between pulls (this is why generated-data tests can be red locally while
green on origin).

## Generated-file clobber map (never hand-edit; the crons own these)

| File | Owner |
|---|---|
| `data/ott/calendar.json` (+ `data/ott/calendar/` archive) | ott-calendar-roll |
| `data/boxoffice/current-week.json` | daily-refresh / friday-surge through the strict v3 last-good writer in run_all.py |
| `site/public/sitemap*.xml` | build |
| `data/_state/*.log`, `staleness.json`, `changed-urls.json` | engine/scripts |

Western OTT fetch path: `engine/fetchers/ott_western.py` (TMDB-key-on-Actions, keyless
Wikidata fallback). `engine/fetchers/boxoffice_western.py` is the strict exact-week
boundary, but has no operational live source adapter yet. Live box-office runs report
structured degraded status, preserve the existing v3 file byte for byte, and exit nonzero
so missing current data alerts instead of passing as health. The public projector withholds
stale rows. Lifetime or cumulative sources are not a fallback. The India fetcher
(`engine/fetchers/boxoffice.py`) is fully orphaned from `run_all.py`, and its optional
fill path is isolated under `_cache/boxoffice/`. Never rewire it to the public board.
To add a real OTT announcement by hand, append to `data/ott/announcements.json` (the
curated source the roll consumes), never to calendar.json.

## The refresh tick (P07) - what it actually does

1. **Build the worklist** (cap N), priority order:
   a. `renewal.state == "awaiting"` (renewal news likely);
   b. `status == "returning"` (new-season dates move);
   c. latest season year is 2025/2026 (facts still settling);
   tie-break with `data/_state/staleness.json` (oldest first) when present.
   ```bash
   python3 - <<'PY'
   import json, glob
   for f in sorted(glob.glob('data/series/*.json')):
       d = json.load(open(f))
       ren = (d.get('renewal') or {}).get('state')
       yrs = [s.get('year') or 0 for s in d['seasons']]
       if ren == 'awaiting' or d.get('status') == 'returning' or max(yrs or [0]) >= 2025:
           print(f"{d['slug']}\t{d.get('status')}\t{ren}\t{max(yrs or [0])}")
   PY
   ```
2. **Verify against live sources** (Wikipedia/official/trade press). Every changed fact
   gets a fresh envelope (source, fetched_at now +05:30, verified|reported honestly).
3. **Returning-season playbook** - the exact delta when a show gets dated/drops:
   - `renewal`: `{"state": "renewed", "note": "Season 3 premieres February 12, 2027 on HBO.", "source": "Variety", "source_url": "<the article>"}`
     (state moves awaiting -> renewed -> after the finale of a final season -> ended);
   - `status`: returning (dated/announced) or running (currently airing);
   - append the SeriesSeason ONLY when aired or officially dated: number/year/episodes
     (announced count or best sourced), release_date envelope, `verdict: null`,
     `bollymeter: null`, `critic: {positive_pct: null, sample: null, pull_quotes: []}`,
     `audience: null`, review_body = a 60+ char honest holding read ("Season 3 arrives
     February 12, 2027; BollyAI's verdict opens once real reception lands."),
     `season_over_season: null`, no episode_reviews;
   - queue the season for the episode-review lane (blueprint 03) in your report - never
     write rich bodies inside a tick;
   - companion surfaces: new season on a show with a predictions/endings page = flag the
     refresh/retire in the report (blueprint 05 lifecycle);
   - `date_modified` bumps ONLY on files whose content actually changed (recency rails
     feed on it; churn is pollution).
4. **Gate + commit**: `fix_series.py` -> `validate_series.py` on every touched slug ->
   commit `bollyai: refresh - <n> series (<reason classes>)` + trailer. One tick, exit.

## IndexNow + sitemaps (floor-only)

Content-hash-gated re-pings only: `scripts/indexnow_ping.sh`, <= 85 URLs/wave, embedded in
the flow (tests enforce it stays non-standalone, relative URLs accepted). Never blast the
catalogue; never ping from an unattended lane.

## The buildout loop (context, so you don't fight it)

Hourly local loop (`scripts/batch/loop_tick.sh` + `LOOP_TICK_PROMPT.md`), single-flight
flock, commits but never deploys. Halt: `touch data/_state/BUILDOUT_STOP`. Its 1000 target
was hit 2026-06-18 (pre-cull); the catalogue now sits at ~466 Western series. New-series
batches are on-demand (blueprint 02) unless Aditya re-arms the loop.

## Retired lanes (do not resurrect without Aditya)

Azure GPT-5.5 push lanes (`~/.claude/state/azure-push/*.sh` driving
`scripts/subtitles/build_review.py`): the sponsored credit expired 2026-07-02. Scripts
stay for reference; episode-review production runs on Claude lanes per blueprint 03.
The staging -> merge path (`scripts/subtitles/merge_reviews.py`, g3_pass + voice_pass
gated, dry-run by default, `--apply` validates + rolls back on failure) remains the
write-path if a lane ever stages instead of writing live.
