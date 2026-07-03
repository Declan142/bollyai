# BLUEPRINT 06 - Freshness, returning seasons, calendars, crons

Use when: keeping shipped pages true. Updates are uncapped; NEW-page deploy waves are
velocity-throttled (confirm cadence with the ledger / Aditya before large waves).
Prompt: `prompts/P07` (headless-safe refresh tick).

## Automated layer (GitHub Actions - do not duplicate by hand)

| Workflow | Purpose |
|---|---|
| `daily-refresh.yml` | daily data refresh via `engine/fetchers/run_all.py --live-only`, then build + deploy (has its own CF token secret - leave it alone) |
| `ott-calendar-roll.yml` | Mon/Thu regen of `data/ott/calendar.json` from announcements via `engine/regen_ott_weekly.py` |
| `friday-surge.yml` | Friday release-day refresh |
| `tentpole-live.yml` | tentpole release live-tracking |
| `health-digest.yml` | site health digest |

Schedules live in the YAML - read them there, don't trust memory. The Actions commit from
runners; local sessions MUST `git pull --rebase` before pushing anything.
Western data paths: `engine/fetchers/ott_western.py` + `boxoffice_western.py`. The India
fetcher (`engine/fetchers/boxoffice.py`) is orphaned from `run_all.py` - never rewire it.

## Manual/agent refresh surfaces (the P07 tick)

1. **Staleness scan**: `data/_state/staleness.json` + `engine/fetchers/staleness_check.py`;
   prioritize (a) `renewal.state: "awaiting"` shows, (b) `status: "returning"` shows with a
   season likely announced, (c) pages whose latest season is 2025/2026 (facts still moving).
2. **Verify against live sources** (Wikipedia/Wikidata/official/trade press). Every changed
   fact gets a fresh SourceValue envelope (`fetched_at` now, correct confidence).
3. **Returning-season playbook** (a tracked show dropped or got dated):
   - update `renewal` (state/note/source/source_url) + `status`;
   - append the new SeriesSeason when it has aired or has a confirmed date: real
     release_date envelope; verdict/bollymeter null until reception is real (still
     dropping is honest);
   - queue the season for the episode-review lane (blueprint 03) - do not write rich
     bodies inside a refresh tick;
   - refresh companion surfaces if they exist (predictions page for the new season;
     retire prediction pages for finales that aired - blueprint 05);
   - bump `date_modified` ONLY on files whose content actually changed (recency rails
     feed on it; churn is pollution).
4. **Validate + commit**: `fix_series.py` -> `validate_series.py` on every touched slug ->
   `python3 -m pytest tests/ -q` if anything beyond series JSON changed -> commit
   `bollyai: refresh - <n> series (<reason classes>)` + trailer. No push, no deploy.

## IndexNow + sitemaps (floor-only)

- IndexNow is content-hash-gated re-pings only: `scripts/indexnow_ping.sh`, <= 85 URLs
  per wave, embedded in the flow (tests enforce it stays non-standalone). Never blast.
- Sitemaps regenerate at build. Never hand-edit generated XML.

## The buildout loop (context, so you don't fight it)

Hourly local loop (`scripts/batch/loop_tick.sh` + `LOOP_TICK_PROMPT.md`), single-flight
flock, commits but never deploys. Halt: `touch data/_state/BUILDOUT_STOP`. Target reached
2026-06-18 (1003, pre-cull); catalogue now 466 Western series. New-series batches are
on-demand (blueprint 02), not loop-driven, unless Aditya re-arms the loop.

## Retired lanes (do not resurrect without Aditya)

Azure GPT-5.5 push lanes (`~/.claude/state/azure-push/*.sh`, `scripts/subtitles/build_review.py`
API path): sponsored credit expired 2026-07-02. The scripts stay for reference; episode
review production now runs on Claude lanes per blueprint 03. The staging -> merge path
(`scripts/subtitles/merge_reviews.py`) remains valid if a lane ever stages instead of
writing live.
