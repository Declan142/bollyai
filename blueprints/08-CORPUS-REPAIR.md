# 08 - CORPUS REPAIR (style-leak sweeps + placeholder titles + ship-train unblock)

> Born from the 2026-07-04 floor audit. The 2026-07-02 gpt-5.5 review-upgrade campaign
> (287 local commits, one day) produced validator-CLEAN but bar-VIOLATING prose at scale,
> died mid-flight leaving a 14-file uncommitted tail, and the ship-train has been stalled
> since 2026-06-27 behind 2 red tests. This blueprint is the repair campaign: adopt the
> tail, sweep 3 defect classes out of the corpus, lock new gates so they can never
> return, and hand a green tree to the ship-train (07-QA-SHIP).
>
> The defects violate rules ALREADY WRITTEN in `01-QUALITY-BAR.md` (line ~16: prose never
> mentions subtitles/dossiers; line ~145: no timestamps in prose). The bar was right; the
> validator just could not see these patterns. Doctrine holds: validator wins, so the fix
> ends by teaching the validator (phase R4).

## Audit facts (2026-07-04, working tree = local main @ 9cba333 + 14 dirty)

| Defect | Detection (grep -E over `data/series/*.json`) | Scope found |
|---|---|---|
| D1 tooling leak: reader-facing prose cites the internal dossier | `[Tt]he dossier('s)? (notes\|marks\|records\|gives\|shows\|has\|logs\|lists\|confirms\|clocks\|counts\|flags\|tracks)\|[Pp]er the dossier\|[Tt]he subtitles? (show\|note\|record\|mark)` | 58 files (30 of them ALSO leaky at origin = live site serves them today) |
| D2 dropped-value glitch: timestamp templating collapsed to broken English ("silences from to and again from to") | `from to( \|,\|\.)\|between and( \|,\|\.)` | 27 files |
| D3 placeholder episode titles: `"title": "Episode N"` + null air_date, with review H1s baking the placeholder (`# Better Call Saul S1E1: "Episode 1" Review` - the real title is "Uno") | titles: `"title": "Episode [0-9]+"` · baked H1s: `: \\"Episode [0-9]+\\" Review` | 2,135 placeholder episodes across 162 files; 516 review H1s baked across 116 files (Tier-1). mad-men (the gold exemplar) has 90 |
| Red test 1, resolved 2026-07-26 | `tests/test_boxoffice_publish_rule.py::test_current_week_schema_and_published_figures_are_source_gated` | strict `bollyai-boxoffice-week/v3` now enforces exact closed-week scope in Python and JavaScript; v1/v2 and lifetime fields fail closed |
| Red test 2 | `tests/test_ott_calendar.py::test_generated_calendar_has_source_envelopes` | `data/ott/calendar.json` window 2026-06-08 -> 2026-07-05 (27 days; must be 13). The Mon/Thu roll (`engine/regen_ott_weekly.py`) has not run since ~Jun-22 |
| Orphan tail | 14 series JSONs dirty since 2026-07-02 ~04:50-12:13 IST, no owning lane alive (no tmux, no loop, no claim) | better-call-saul, breaking-bad, brooklyn-nine-nine, dead-to-me, from, house-of-the-dragon, landman, lioness, mad-men, nobody-wants-this, severance, the-boys, the-crown, yellowstone |
| Ship stall | local main 305 ahead of origin, 12 behind (daily-refresh cron commits); last push = films cull 2026-06-27 | live site is ~a week stale on all content work |

Counts are point-in-time observations. NEVER trust them at session start - re-run the
detection greps; they are the queue.

## Non-negotiables (inherited, restated)

1. `01-QUALITY-BAR.md` governs every rewritten sentence. Read it in full first.
2. Repair NEVER adds facts. Numbers out, no new numbers in. A dropped timestamp is
   deleted, not "restored" from imagination. A dossier citation is removed, not
   re-attributed. If a claim only existed via the tool reference, the claim goes too.
3. Skip beats fabricate. A Wikipedia page without an episode table = log + leave the
   placeholder + move on.
4. Commit is the lane's ceiling. Never push, build, deploy, or IndexNow. The floor
   ships via `07-QA-SHIP.md` after this campaign reports green.
5. `python3 scripts/batch/validate_series.py <slug>` after EVERY file touched; commit
   only green; per-phase commits so work is never lost.
6. JSON via `json.load -> mutate -> json.dump` (see the template in `03-EPISODE-REVIEWS.md`).
   Never string-edit JSON. Preserve key order and 2-space indent (match the file).
7. Em/en dash ban applies to every byte you write, including this campaign's edits.

## Phase R0 - unblock the ship-train (red tests + micro-hygiene)

Do this FIRST; it is small and it un-rots the suite for every other lane.

1. **Box-office schema drift, resolved 2026-07-26.** Do not restore v1 or v2. The public
   file and both runtime readers now use strict v3: one exact closed week, full-set
   independent-source consensus, no lifetime substitution, and atomic last-good
   preservation. The operational exact-week source adapter remains a separate pending
   task; missing live input is honest degraded status with a nonzero owner-process exit,
   not permission to weaken the contract or render stale bytes as current.
2. **OTT calendar staleness.** Read `python3 engine/regen_ott_weekly.py --help`, then run
   it (it is the cron-safe Mon/Thu entrypoint; writes `data/ott/calendar.json`, week
   archives, changed-URL sidecar; never deploys). Verify: window = current Monday ->
   Sunday+13, `python3 -m pytest tests/test_ott_calendar.py -q` green. If the calendar
   regenerates EMPTY and the test still fails on source envelopes, the upstream
   announcements feed (`data/ott/announcements.json` via `engine/fetchers/`) is the real
   patient - diagnose, fix the fetcher if it is a code/data problem, and if it needs a
   product decision (feed genuinely dry post-Western-cull), STOP the phase and flag in the
   report. Weakening the test is banned - it is the difference between "fixed" and "hidden".
3. **Hygiene commits.** Commit the pending `.gitignore` line (`.azure-env.sh`). Leave
   `site/public/*`, `data/_state/series-links.json` build-artifact dirt ALONE - the floor
   regenerates + commits those at ship time (`sitemap-predictions.xml` is new build output;
   it rides the same ship commit).
4. **Gate:** run the current full Python suite. Historical fixed test counts are evidence
   only; do not weaken new gates to match the old 183-test snapshot.
5. **Report the cadence gap:** the Mon/Thu OTT roll has no live scheduler. Wiring a cron is
   the floor's call - flag it, do not build it.

## Phase R1 - adopt the orphan tail (the 14 files)

The 14 slugs above are CERTIFIED ORPHANED (audit 2026-07-04: mtimes 2026-07-02, no lane,
no claim). This phase overrides the usual "dirty = another lane's WIP" fence for EXACTLY
these 14 slugs. If ANY other `data/series/*.json` is dirty beyond these 14, stop and
report - that could be a genuinely live lane.

1. Pre-checks on the dirty set (all 14 at once):
   - `python3 scripts/batch/validate_series.py <all 14>` -> must be 14/14 PASS (it was on
     audit day).
   - Added-line honesty scan: `git diff -- data/series/ | grep '^+' | grep -inE "watched|i saw|i've seen|my screening|maine|humne"` -> 0.
   - Em-dash: `git diff -- data/series/ | grep '^+' | grep -P '[\x{2013}\x{2014}]'` -> 0.
2. **Score-drift report** (Aditya sees every re-grade; you do not judge them):
   for each of the 14, `git show HEAD:data/series/<slug>.json` vs working copy; list every
   episode/season where bollymeter or verdict.score changed from a NON-null old value
   (audit examples: mad-men S1E1 9.0 -> 8.6, dead-to-me S1E1 7.8 -> 8.0). Paste the full
   list into your session report. Do NOT revert them; the campaign re-scored consistently
   and consistency wins pending Aditya's call.
3. Commit all 14 + this ledger note in ONE commit:
   `bollyai: adopt orphaned gpt-5.5 upgrade tail - 14 series (2026-07-02 lane died uncommitted)`.
   The tail still CONTAINS D1/D2/D3 defects - that is fine; R2/R3 sweep the whole corpus
   including these. Adoption preserves the campaign's work as its own honest commit.

## Phase R2 - sweeps A + B (leak surgery; single session, NOT parallel-safe)

Regenerate the queue live: the detection greps above ARE the queue. Claim the whole
sweep in `data/_state/buildout-loop.log`: `<iso> CLAIM corpus-repair sweepAB (P11)`.
Only one Sweep-A/B session may run at a time (file set overlaps).

Per file, per hit line (read every hit in context - these are sentence-level surgeries,
minimal diffs, never a whole-review rewrite):

**Sweep A (D1 tooling leak).** The sentence cites the dossier/subtitles as a source.
Decide which of two shapes it is:
- The paragraph ALREADY argues the point with scene evidence -> delete the tool
  citation, keep the craft claim, restitch. `"The dossier notes dense dialogue broken
  by three long silences" -> "The episode breaks its dense dialogue with long silences"`
  ONLY IF the surrounding prose already establishes that; otherwise:
- The claim exists ONLY via the tool stat (silence lengths, dialogue density, "the
  dossier gives only flashes") -> the CLAIM ITSELF is subtitle-density-derived pacing
  criticism, which `01-QUALITY-BAR.md` bans outright -> delete the claim, restitch the
  paragraph so it reads whole. Losing a weak sentence is the correct outcome.
- Legit plot usage ("MI5 assembles a dossier on the minister") does not match the
  verb-anchored regex; if a hit IS plot usage, leave it and note it.

**Sweep B (D2 dropped values).** `"from to"` / `"between and"` fragments are collapsed
templating. Delete the quantitative fragment; keep the qualitative observation only if
it stands without the numbers AND is not subtitle-density pacing criticism (same test as
Sweep A). NEVER invent replacement numbers. Examples from the corpus:
- `"long top silences from to and again from to, and those gaps are felt as gaps"` ->
  the whole claim is density-derived -> delete sentence, restitch.
- `"the long argument sequence from to gives the episode its first pressure change"` ->
  `"the long argument sequence gives the episode its first pressure change"` (claim
  survives without the range; scene is named in context).

After each file: re-run BOTH detection greps on that file -> 0 hits; validator PASS;
bump nothing else (date_modified only if prose changed, +05:30). Commit in batches of
~10 files: `bollyai: corpus repair sweep A+B - <n> files (tooling leaks + dropped values)`.
Log `<iso> corpus-repair sweepAB files=<n> remaining=<m>`.

Session sizing: 58 + 27 files with overlap = expect 1-2 sessions. Loop until both
detection greps return ZERO files catalog-wide, then log
`<iso> COMPLETE corpus-repair sweepAB`.

## Phase R3 - sweep C (placeholder titles + air dates + baked H1s; parallel-safe per series)

Queue = Tier-1 first: the 116 files where review H1s bake `"Episode N"` (reader-facing
worst; regenerate with the baked-H1 grep). Tier-2 after: remaining files with placeholder
titles only in `season.episodes` metadata. Within a tier, order by descending placeholder
count (better-call-saul 59, brooklyn-nine-nine 151, mad-men 90, the-crown 58 ... the gold
exemplar mad-men is a Tier-1 PRIORITY - the exemplar must meet its own bar).

Per series (claim it: `<iso> CLAIM corpus-repair titles <slug> (P11)` - same 24h-claim
skip rule as P10; parallel sessions are safe because claims are per-series):

1. **Fetch the real episode table**: direct `WebFetch` of the Wikipedia episode-list page
   (`List of <Title> episodes` or the season articles). DIRECT fetch only - search-summary
   titles have hallucinated before (2026-07-04 lesson, RESUME.md). No table on Wikipedia ->
   try the series' main page episode section; still nothing -> SKIP series, log reason.
2. **Fill metadata**: for every `season.episodes[]` entry whose title matches
   `^Episode [0-9]+$`: set the real title; set `air_date` (ISO) when the table gives it;
   leave null when it does not. Episode-count mismatch vs Wikipedia (extra/missing/
   specials) = do NOT force; fix obvious off-by-one alignment only when unambiguous,
   else skip that season + report.
3. **Patch baked prose**: in the same series, every `episode_reviews[].review_body` whose
   H1 quotes the placeholder gets the H1 title replaced with the real title (and scan the
   body for other literal `"Episode N"` self-references - replace only where it names THIS
   episode's title). Nothing else in the review changes.
4. Gates per series: placeholder grep on the file (target: 0 in Tier-1 scope; Tier-2
   metadata may keep nulls where Wikipedia is silent, but no `Episode N` where the table
   had a name), validator PASS, em-dash 0. Commit per series:
   `bollyai: real episode titles + air dates - <slug> (<n> filled)`.
   Log `<iso> corpus-repair titles <slug> filled=<n> skipped=<m>`.
5. Two consecutive series skipped for the same cause = systemic; stop, report (standing
   escalation rule).

## Phase R4 - lock the gates (ONLY when R2 detection greps = 0 catalog-wide)

Teach `scripts/batch/validate_series.py` the three patterns, on every prose field it
already walks (review_body, spoiler_free, the_moment, one_liner, logline, season
review_body):

- `G-TOOLING-LEAK`: `\b[Tt]he (dossier|subtitles?)\b(?:'s)?\s+(notes?|marks?|records?|gives?|shows?|has|have|logs?|lists?|confirms?|clocks?|counts?|flags?|tracks?)\b|\bper the dossier\b`
- `G-DROPPED-VALUE`: `\bfrom to([\s,.])|\bbetween and\b`
- `G-PLACEHOLDER-H1` (review_body first line only): `^#.*: "Episode \d+" Review`

Then:
1. New `tests/test_style_leaks.py` mirroring `tests/test_viewing_claim.py`: synthetic bad
   fixtures rejected, clean prose passes, plus a catalog assertion (0 hits repo-wide) so
   the suite - not just the validator - breaks on regression.
2. `G-PLACEHOLDER-H1` lands with R3 Tier-1 complete (else it reddens the suite; if Tier-1
   is still in flight, ship the other two gates first and this one after).
3. Same commit updates `01-QUALITY-BAR.md` kill-list + regex table with the three gates
   (drift rule: validator and blueprint move together), and adds one line to
   `scripts/batch/AUTHORING_BRIEF.md` if it lists gates.
4. Full `python3 -m pytest tests/ -q` green + `validate_series.py` over a 20-file random
   sample. Commit: `bollyai: style-leak gates in validator (tooling-leak, dropped-value, placeholder-H1) + tests`.

## Phase R5 - report + handoff (the lane does NOT ship)

Final session report must state: red tests green (or exactly what blocks them), tail
adopted (commit hash + score-drift list), sweep A/B zero-hit proof (paste the grep
commands + empty output), sweep C tier progress (filled/skipped counts per series), gates
landed (commit hash), and the standing items for the floor: 305+ local commits to
reconcile (`git pull --rebase` over the ~12 daily-refresh commits, then full gates, then
push - GHA daily-refresh auto-deploys origin/main, so PUSH IS THE SHIP LEVER; backlog
carries ~6 new series pages which is within the velocity throttle's one-time spirit, plus
mass updates which are uncapped), OTT Mon/Thu cadence unwired, fabrication stashes
(stash@{3},{4}, 2026-06-14) old enough to drop pending Aditya nod.

## Session sizing (honest)

R0+R1: one session. R2: 1-2 sessions (serialized). R3 Tier-1: ~8-12 sessions at ~10-15
series/session (big files fewer; parallel-safe, 2-3 lanes fine AFTER R2 is complete so
sweeps do not collide). R3 Tier-2: ~3-4 sessions. R4: half a session. Total ~14-19
Sonnet sessions, effort medium throughout; no Opus needed (detection is deterministic,
surgery is bounded, and the one judgment class - score re-grades - is explicitly parked
for Aditya).

## DO NOT

Rewrite whole reviews (sentence surgery only). Add any number, timestamp, count, or fact
during repair. Touch scores/verdicts (report drift, never edit it). Re-title an episode
without the Wikipedia table in front of you. Run two Sweep-A/B sessions at once. Land
G-PLACEHOLDER-H1 before its corpus is clean. Weaken a test to green it. Push, build,
deploy, or IndexNow - commit is the ceiling; `07-QA-SHIP.md` owns the ship.
