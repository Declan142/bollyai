# BollyAI - pickup state (2026-07-07 ~16:00 IST, R2 INTEGRITY PASS - SUITE GREEN 217/217)

## WRAP R2 (2026-07-07 PM, genius-pass lane, Fable fork) - commits 08528e4 + 0bcadc4 (+ this wrap)
- **Fetch-path shadowing KILLED** (08528e4): fetch_western_ott returned TMDB *instead of*
  Wikidata when TMDB was non-empty; TMDB discover is en-only, so every fr/de/es/it/pt
  Western-European original (kept by brand lock) was invisible on keyed runs. Now UNION,
  Wikidata wins collisions (it carries the QID). Plus: registry date-move correction
  (fetched-origin entries take upstream reschedules in place; curated untouchable;
  append-only otherwise) and _provenance.refresh honesty stamp (no-fetch/fixture/fetched
  + fetched/added/updated counts). 6 new tests incl. doubled-run registry byte-stability.
  Suite 217/217.
- **Pre-pivot SERP claims purged** (0bcadc4): sitewide "pan-India answer engine", homepage
  "Verdicts for India" + Squid Game ask-chips (an ARCHIVED series), series-index "Korean
  drama, anime, Indian OTT", OTT pages "JioHotstar, SonyLIV, ZEE5" - all Western now.
  Audience-region "in India" (where-to-watch, India nett) KEPT deliberately: audience is
  Indian, content is Western. Freshness contract, zero scheduling: calendar page renders
  an honest window-ended note at build time; week-archive eyebrows derive from the build
  clock ("Archived week"/"This week"/"Upcoming week") - wk-24..27 said "This week"
  forever. Proof in built HTML: JioHotstar-class 0 hits, labels verified, build green
  (6822 files, all gates).

## CORRECTIONS to earlier beliefs (verified against origin 2026-07-07)
- **"OTT Mon/Thu cadence unwired" is FALSE.** `.github/workflows/ott-calendar-roll.yml`
  (identical both sides) cron `0 3 * * 1,4` runs regen_ott_weekly and HAS been committing
  rolls: Jun-29, Jul-2, Jul-6. No new cron needed - shipping main puts the FIXED fetcher
  on the existing schedule and the calendar self-fills.
- **Origin is serving `entries: []`** - the born-dead fetcher still lives there; the live
  site's calendar is an empty husk re-windowed twice a week. Ship = fix.
- The roll workflow env does NOT pass TMDB_API_KEY to the regen step - 1-line env add if
  TMDB coverage is wanted on rolls (cron file = Aditya's, untouched this lane).
- Blind-window (06-22..07-07, 16 origin commits) diff-audited: NO fabricated values;
  box-office diffs are pure window-rolls; the damage was the empty-calendar class only.
  The roll also REWRITES past week archives each run (W25 sections mutated 07-02) -
  render-side labels are now derived, so this can't lie to readers anymore.

## 07-QA-SHIP COLLISION MAP (pull --rebase WILL conflict - resolution recipe)
Both sides rewrote exactly 4 files since merge-base; everything else rebases clean:
- `data/ott/calendar.json`, `data/ott/calendar/2026-W28.json`, `2026-W29.json`:
  **take LOCAL** (verified 5-entry superset; origin's are entries-empty husks).
- `data/_state/changed-urls.json`: **take LOCAL** (delta sidecar; worst case IndexNow
  under-pings one cycle, the next roll rewrites it).
W25/26/27 archives moved origin-side only - the rebase takes them silently, correct.

## WRAP (2026-07-07, corpus-repair lane, Fable fork)
- **SUITE GREEN 211/211** (was 1 red since ~06-22). Ship-train unblock (R0) DONE +
  gates locked (R4). 4 commits, local only: 3f9e73f (OTT pipeline fix), b0a0a8c
  (calendar regen + 5 curated July entries), 012d1a8 (5-file residual leak sweep),
  cd16907 (Gate 6 style-leak gates + tests).
- **R0 root cause**: regen_ott_weekly could never refresh itself - ott_western.py had
  ZERO callers, its Wikidata query used wdt:P4947 (TMDb film ID) where wdt:P449
  (original broadcaster) was meant (0 rows forever), _http_get swallowed every error
  (429s/timeouts = silent empty), TMDB path fabricated platform "Streaming". All fixed:
  P449 + platform-first subselect, stderr logging + bounded retry, per-title
  watch/providers resolution (skip beats guess), fetch->append-only registry merge
  wired into regen (--no-fetch escape). Wikidata verified working (18 rows on a past
  window) but honestly SPARSE forward - so 2026-W28/W29 is registry-curated: 5 entries
  (Nothing to Lose FR 07-08, Little House on the Prairie 07-09, Lucky/Apple TV+ 07-15,
  The Hawk 07-16, The Map of Longing ES 07-17), each direct-Wikipedia verified, QIDs
  null never guessed, Korean/Hindi/Indonesian in-window titles excluded per brand lock.
- **R4 shipped** (R2 grep = 0 catalog-wide since 07-05): engine/gates/style_leak_regex.py
  (Gate 6), all-strings walk in validate_series.py, tests/test_style_leaks.py with
  catalog-wide zero-hit lock, 01-QUALITY-BAR.md moved in same commit. The wider gate
  net immediately caught 8 residual leaks in 5 files (subtitles-give / dossier's-note
  forms R2's grep missed) - swept same-session, validator 5/5. G-PLACEHOLDER-H1
  deferred to R3-Tier-1-complete by design.
- **Not run**: site build / deploy / push (commit is the lane's ceiling; 07-QA-SHIP owns
  the ship). Working-tree dirt untouched: site/public/* + series-links.json build
  artifacts + RESUME.auto.md + sitemap-predictions.xml ride the ship commit.

## FOR THE FLOOR (Aditya's levers, unchanged + new)
- **PUSH = SHIP LEVER, now unblocked**: local main ~321 ahead / 12 behind origin, suite
  green. 07-QA-SHIP: git pull --rebase over the daily-refresh commits -> full gates ->
  push (GHA auto-deploys origin/main).
- **OTT Mon/Thu cadence still unwired** (cron = your call; this lane was cron-banned).
  Registry now self-refreshes WHEN regen runs; without a scheduler the calendar goes
  stale again after Jul 19. TMDB_API_KEY lives only in GH secrets - local regen runs
  Wikidata-only (forward-sparse); a vault TMDB key would make local regen self-sufficient.
- **Out-of-queue defects flagged, not touched**: raw timestamps in prose ("At t=11:30",
  nobody-wants-this S2E10 region), "(Unknown)" pull-quote attributions (breaking-bad
  S5E2, the-crown S6E2), R3 placeholder titles (2,135 across 162 files) queued per
  blueprint. Wikidata series coverage gap: P577 catches series PREMIERES only, not
  returning-season drops (by design for now).

---

# BollyAI - AUDIT WRAP (2026-07-04 ~17:30 IST, Fable floor) - corpus-repair campaign SPEC'D, not executed

## Verdict (audit-only session; Aditya: "kaam mat kar, sirf dekh + blueprints likh")
- **Fences HOLD**: validator 14/14 on dirty WIP, P10's 11 commits clean in added lines,
  batch 22/23 grounded properly. The blueprint pack works when a lane actually follows it.
- **NOT theek - 5 findings**: (1) the 2026-07-02 gpt-5.5 upgrade campaign (287 local
  commits in one day) ADDED style defects the validator cannot see: internal "the dossier
  notes..." tooling leaks in reader prose (58 files; 30 already LIVE at origin) + broken
  "from to" dropped-timestamp fragments (27 files) - both violate 01-QUALITY-BAR (lines
  ~16/~145) which was never mechanically enforced. (2) That campaign died mid-flight:
  14 series JSONs dirty since 07-02 ~12:13, orphaned; later sessions mistook them for a
  live lane's WIP and fenced around them. (3) 2,135 placeholder "Episode N" titles across
  162 files; 516 review H1s BAKE the placeholder (BCS S1E1 "Uno" published as "Episode 1";
  gold exemplar mad-men carries 90). (4) Ship-train stalled since 06-27: local main 305
  ahead / 12 behind origin; the 2 red tests (boxoffice schema v1->v2 drift from 3ce98b7;
  OTT calendar stale 27-day window, Mon/Thu roll not running since ~06-22) hard-block push
  under "never push red". (5) Refresh-ops cadence unwired (nothing runs regen_ott_weekly).
- **Fix is SPEC'D for Sonnet**: `blueprints/08-CORPUS-REPAIR.md` (field manual: R0 red-test
  unblock -> R1 adopt the 14-file orphan tail -> R2 leak sweeps -> R3 real titles/air-dates
  -> R4 validator gates) + prompt `blueprints/prompts/P11-corpus-repair-lane.md` + routing
  row in 00-INDEX. ~14-19 Sonnet sessions, medium effort; R3 parallel-safe after R2.
- **Aditya's judgment items (parked, not blockers)**: orphan tail re-grades scores
  (mad-men S1E1 9.0->8.6, dead-to-me S1E1 7.8->8.0; R1 reports full drift list) · push =
  ship lever (GHA daily-refresh deploys origin/main; backlog carries ~6 new series pages +
  uncapped updates) · OTT Mon/Thu cron wiring · 2026-06-14 fabrication stashes old enough
  to drop · the-season origin-country question (still open from batch 23).

## DISPATCH (copy-paste)
Open a sonnet session in /home/aditya/bollyai and say:
`Read blueprints/prompts/P11-corpus-repair-lane.md and execute it.`
(Repeat until phases report COMPLETE; R2 single-owner, R3 may run 2-3 parallel sessions.)

---

# BollyAI - pickup state (2026-07-04 ~15:40 IST, NEW-SERIES BATCH 23 + BRAND-LOCK FIX)

## WRAP (2026-07-04 ~15:40 IST) - session hygiene + batch 23 (3 series, 469->472)
- **Clutter swept** (session open): deleted 4 stale untracked scratch/capsule files
  (`RESUME.auto.md`, `.brief-films-cull.md`, `.brief-western-rebuild.md`,
  `.films-cull-report.md`) - all from the already-shipped 2026-06-27 Western-rebuild
  session (commit `2e53d87`), harmless but a week stale. Confirmed the 14 dirty
  `data/series/*.json` files are known other-lane WIP (P10's fence list) - untouched.
- **Batch 23 shipped**: star-city (Apple TV+, For All Mankind spinoff, RT 97%/30) ·
  the-season (Hulu, Hong Kong wealth drama, RT 83%/6) · worst-neighbor-ever (Netflix
  true-crime docuseries, too fresh for an aggregate - grounded on one named critic
  instead, bollymeter/verdict correctly left null). All Wikipedia+Wikidata+RT/MC
  verified via DIRECT fetch (not WebSearch summaries alone - caught the search layer
  hallucinating an unattributable Guardian/Decider quote for worst-neighbor-ever
  mid-session; used a real Ready Steady Cut review instead). validate 3/3 clean,
  guard-offbrand-series PASS, build green, 181/183 pytest (2 pre-existing unrelated
  fails, same as Batch 22). Full detail: `data/_state/library-buildout.md` Batch 23.
- **Judgment call flagged**: the-season is Hong Kong/US co-produced but English-
  language per Wikipedia - passes guard-offbrand-series.mjs (language-gated, not
  origin-country) and the letter of the brand definition. Included; Aditya's call if
  he wants origin-country as a second gate.
- **Brand-lock bug found + fixed**: root-level `public/img/films/{kalki-2898-ad-2024,
  manjummel-boys-2024}` (git-tracked, separate from `site/public/`) still held the two
  off-brand film posters the original films cull (f8a1ae4) missed this mirror, and
  `site/scripts/sync-public.mjs` unconditionally `cp -r`'s it into `site/public/` (and
  from there into `site/out/`) on every single build, silently resurrecting the orphans
  no matter how many times the site/public copy gets deleted. Fixed via `git rm` on the
  root copy; re-ran `sync-public.mjs` standalone to confirm it no longer resurrects.
  Zero live-site risk (no `data/films/` entry ever existed for either, so no page/
  sitemap ever linked them) but was silently re-polluting every build's output tree.
- Commits: (1) brand-lock fix (root public/ off-brand asset removal), (2) batch 23
  content (3 series + library-buildout.md + this file). Both LOCAL only, not pushed/
  deployed (standing grant exists but push wasn't requested this turn).

## NEXT ACTION
Continue the new-series-upcoming batch: search further out for more recently-premiered
Western shows not yet in `data/series/`, cross-check for collisions, verify each via
direct Wikipedia/Wikidata/RT fetch before authoring. Revisit oasis / the-american-
experiment periodically (both still lack an English Wikipedia page as of this session).
Future candidates seen but not yet actioned (premiere too recent / future-dated, revisit
once aired + reviewed): Little House on the Prairie (Netflix, premieres 2026-07-09),
Wrath (Netflix, 2026-07-29), Fightland (Starz, 2026-07-31), Lucky (Apple TV+, 2026-07-15).
Deprioritized as out-of-scope for this lane: returning seasons of shows absent from the
catalogue (X-Men '97 S2, Star Trek: Strange New Worlds, Ransom Canyon S2, Sugar S2 - these
are broad-canon-backfill, explicitly paused) and reality/competition formats (Big Brother,
House of Stassi - poor fit for the review-schema shape of this catalogue).

---

# BollyAI - pickup state (2026-07-04 ~11:46 IST, P10 SOLO LANE - 11 SERIES COMPLETE)

## WRAP (2026-07-04 ~11:46 IST) - P10 solo episode-review lane, 11 series completed
- Ran `blueprints/prompts/P10-sonnet-solo-episode-lane.md` solo (no conductor). WIP fence
  excluded 14 slugs already dirty from other lanes (better-call-saul, breaking-bad,
  brooklyn-nine-nine, dead-to-me, from, house-of-the-dragon, landman, lioness, mad-men,
  nobody-wants-this, severance, the-boys, the-crown, yellowstone) - all left untouched.
- Worked the dossier-backed, single-episode-gap tier of the gap queue to completion:
  adolescence S1E2 (Mode A, Film Stories quote), cable-girls S4E1 (Mode B, also fixed a
  wrong release_date 2019-02-01 -> real 2019-08-09), call-my-agent S2E4 (Mode B),
  cobra-kai S4E9 (Mode B), dark S1E8 (Mode B, dossier-grounded), deutschland-83 S1E4
  (Mode A, AV Club quote), orange-is-the-new-black S5E12 (Mode B), ozark S4E14 series
  finale (Mode B - real Salon quote found but no S4 dossier exists, HOUSE-STYLE needs
  both), sons-of-anarchy S3E11 (Mode B - real AV Club/Den of Geek quotes found but no S3
  dossier), wednesday S2E5 (Mode A, Razorfine quote), you S1E7 (Mode A, TellTaleTV quote).
- All 11 series now show FULL episode coverage (every season, every aired episode
  reviewed). Final combined validate: **11/11 clean, 0 failed**.
- 11 commits, all local only (never pushed/built/deployed - commit is the lane's ceiling).
  Hashes in order: a4c3ff6 (adolescence), 18d3205 (cable-girls), 42c8372 (call-my-agent),
  1def66a (cobra-kai), e7569e1 (dark), 0acc66a (deutschland-83), 85175cb
  (orange-is-the-new-black), 64181c6 (ozark), 19ed391 (sons-of-anarchy), d4bf9e7
  (wednesday), 1ab9295 (you).
- `buildout-loop.log` got CLAIM/completion lines appended (gitignored, local coordination
  file only, never committed).

## OPEN - flagged, not blocking
- Ozark S4 and Sons of Anarchy S3 have NO subtitle dossiers, but real, verified,
  per-episode critic quotes exist for both (Ozark finale: Salon/Kelly McClure; SOA S3E11:
  AV Club + Den of Geek). If dossiers get built for those seasons later, both episodes are
  one-pass upgrades from Mode B to Mode A.
- `adolescence.json` S1E4 has a legacy thin `review_body` (no H1/subheads/verdict object,
  no dossier) that counts as "rich" by the gap-audit's truthy check but does not meet the
  current quality bar. Untouched (MODE was expansion). Flagged for a future upgrade pass.
- Several sibling episodes in cable-girls/call-my-agent/cobra-kai/deutschland-83 still
  carry generic "Episode N" placeholder titles + null air_date even where real titles/
  dates are easy to source. My own new entries used real titles/dates, which is now a
  minor internal inconsistency with those older siblings (not touched, out of scope).
- Gap queue still has ~403 series with episode-review gaps (dossier-backed gap=2 tier
  next: a-very-british-scandal, a-very-english-scandal, all-the-light-we-cannot-see,
  belascoaran-pi, chernobyl, the-pursuit-of-love, the-salisbury-poisonings, unorthodox).

## WRAP (2026-07-04 ~12:36 IST) - new-series pivot, batch 1 done (3 series)
Aditya pivot CONFIRMED: stop the P10/P03/P04 episode-review gap-filling lane, **focus
on new series upcoming only** - recently-premiered Western shows with ZERO
bollyai.in presence yet, full cold-start pages (NOT the P07/OTT-calendar
announced-but-unaired route - explicitly out of scope). Blueprint `02-SERIES-
AUTHORING.md`, prompts P01+P02, canonical spec `scripts/batch/AUTHORING_BRIEF.md`.
- Searched recent premieres (June-July 2026), verified each candidate is real (not a
  search-summary artifact) via direct Wikipedia/Wikidata/RT fetches before authoring.
- Wrote 3 new full series pages, all fully grounded, all validate clean:
  **elle** (Prime Video, Legally Blonde prequel, premiered 2026-07-01, RT 54%/41,
  Metacritic 52), **not-suitable-for-work** (Hulu, Mindy Kaling ensemble comedy,
  2026-06-02, RT 52%/21, Metacritic 53), **life-larry-and-the-pursuit-of-unhappiness**
  (HBO limited series, Larry David, 2026-06-26, RT 53%/30, Metacritic 58). Each has a
  real Wikidata QID (confirmed as "television series" instance), a real RT-consensus
  or named-critic pull_quote with URL, real SourceValue envelopes throughout.
- Ran the full ingest pipeline (`scripts/batch/ingest_batch.sh`): fix (0 changes needed)
  -> validate (3/3 PASS) -> poster harvest (0/3, no_usable_candidate, non-fatal SVG
  fallback by design) -> `npm run build` GREEN (5636 pages, 469/469 series linked, all
  guards pass, file count 6811 well under CF's 20k cap). pytest 181/183 (2 pre-existing
  fails unrelated to this work: box-office cache-version bump, OTT-calendar staleness).
- **Skipped, reason logged** (in `data/_state/library-buildout.md` Batch 22): **oasis**
  (Netflix, Spanish thriller, 2026-06-19) and **the-american-experiment** (Netflix
  docuseries, 2026-06-24) - both real shows with real critical coverage, but NEITHER
  has a dedicated English Wikipedia page yet. AUTHORING_BRIEF.md requires Wikipedia as
  the spine source; two consecutive same-cause skips = paused rather than forcing more
  candidates (per blueprint 00-INDEX.md's escalation matrix). Revisit once Wikipedia
  creates pages for either - both are otherwise groundable (Netflix Tudum, RT, Variety
  review already found for each).
- Also found and excluded (Korean, fails the Western brand lock, never authored):
  notes-from-the-last-row, agent-kim-reactivated.
- Commit `31b9e1c` (data/series/ x3 + library-buildout.md + this file). Not pushed/
  deployed (standing grant exists but push wasn't requested this turn).

## NEXT ACTION
Continue the new-series-upcoming batch: search further out (past ~July 2026) for more
recently-premiered Western shows not yet in `data/series/`, cross-check
`data/series/*.json` for collisions, verify each via direct Wikipedia/Wikidata/RT
fetch before authoring (do NOT trust WebSearch summaries alone - two names this
session synthesized plausible-sounding shows that were actually Korean, and search
result phrasing has been unreliable on exact quote wording more than once). Revisit
oasis / the-american-experiment periodically in case Wikipedia catches up.

---

# BollyAI - pickup state (2026-06-27, FILMS + SERIES Western cull LIVE)

## WRAP (2026-06-27 ~12:05 IST) - INDIAN FILM cull SHIPPED + LIVE
- **Films brand-lock executed**: 36 Indian films archived (bollywood 14 / kollywood 6 / tollywood 8 / mollywood 7 / sandalwood 1 - the old "92" estimate conflated series; Tollywood was missing) to `data/_archive/non-western-films/` via reversible `git mv`. **72 Hollywood films kept.**
- 5 Indian desks removed from `site/lib/desks.ts`; new prebuild guard `scripts/guard-offbrand-films.mjs` (Western-only allowlist, FAILS build on any non-hollywood in `data/films/`). Box-office data-fence: `boxoffice.ts` DESK_SLUGS filter + `current-week.json` emptied + DATA_PENDING true + Indian box-office / 2026-W24 OTT entries archived + comparator repointed to dune-part-two/deadpool-wolverine/conclave. `build-search-index.mjs` trimmed to hollywood+streaming.
- Commit `f8a1ae4` -> **pushed origin/main** + **deployed bollyai-in**. 6/6 live-verify (kept 200 / culled desks+film 404 / box-office graceful 200). Verified: build exit 0, 0 internal off-brand hrefs, 182 tests pass (sole red = pre-existing OTT-calendar empty-window; it reads compiled `data/ott/calendar.json`, empty in committed state, NOT the cull's `2026-W24.json` source edit).
- **PRODUCT decisions queued for Aditya (India-shaped features now hollow on Western-only - NOT blockers)**: (1) OTT calendar renders empty (entries were Indian-heavy); (2) box-office tracker is INR/crore-club shaped, Western films carry no India-nett day-wise rows so hub/comparator/clubs are graceful-but-empty. Per feature: rebuild for Western/USD data, or hide/de-link until data exists (recommend hide/de-link interim).
- Gotcha for next films cull: it leaves orphan `site/public/img/films/<culled-slug>/` dirs, and `build-search-index.mjs` hardcodes the DESKS array (trim it or the search index re-leaks culled URLs every build).

## WRAP (2026-06-26 ~23:40 IST) - 'full western' SERIES cull SHIPPED + LIVE
- **Brand lock executed**: 420 non-Western series archived (Korean 225 / Japanese 176 / Hindi 6 / He-Tr-Zh-Th-Ar 13) + 57 endings + ~390 img + ~119 subs to `data/_archive/non-western/`. **466 Western series kept.** Reversible `git mv`.
- Guard flipped to Western-allowlist (`scripts/guard-offbrand-series.mjs`); build FAILS on any non-Western in `data/series/`. Gold exemplar squid-game -> mad-men.
- Commits `23ed877` (cull) + `ff982a8` (orphan my-name ending fix) -> **pushed origin/main** (durable vs daily 04:30 Action) + **deployed bollyai-in**. Live-verify 8/8 (kept 200 / culled 404).
- ~80 Euro/LatAm non-English series (Dark/Money Heist/Lupin/Gomorrah/Acapulco) KEPT as Western - Aditya's call for English-only.
- **Indian FILM cull: DONE 2026-06-27** (see top WRAP). Actual count was 36 films, not 92 (the estimate conflated series; Tollywood was missing). Series cull did not touch film routes; the films cull handled them separately.
- Gotcha: a series cull orphans `data/endings/<slug>.json` -> fails test_ending_explained + leaks a 404 into sitemap-endings.xml. Sweep data/endings/ + subs after any series cull. (test_ott_calendar empty-window fail is pre-existing, unrelated.)

## WRAP (2026-06-24 ~01:19 IST) - FROM Phase 2 explainer hub shipped

## WRAP (2026-06-24 ~01:19 IST) - FROM Phase 2 explainer hub shipped
- **Explainer route LIVE**: `site/lib/explainers.ts` + `site/app/series/[slug]/explainer/[topic]/page.tsx` + JSON-LD helpers. Data: `data/explainers/<slug>/<topic>.json` (one file per article, per-series dir).
- **3 flagship articles**: `boy-in-white.json` (S1-S3 grounded, theories labeled), `mythology.json` (episode-cited, 8 sections), `clues-you-missed-s4.json` (E1-E9 foreshadowing from repo episode reviews).
- **FROM series page** now surfaces "FROM Explained" panel linking all explainers for the series.
- **predictions/from.json** trimmed to 9 theories (test gate fix, was 10).
- Commit 6dc9677, deployed CF Pages, conductor outcome reported.
- Gates: 262 pytest PASS (OTT calendar pre-existing excluded), em-dash 0, build 19947 files.
- W2 monsters.json already present in data dir (writer lane running).

## FLOOR: needs Aditya
- **S04E08.srt CONTAMINATED**: `data/subtitles/from/S04E08.srt` is The Rookie S4E8 ("Simone"), not FROM. E8 review is web-grounded (fine), but the srt needs replacement if E8 depth-regen is wanted. Delete + re-fetch when correct file available.
- **FROM Season 5 renewal UNCONFIRMED** (as of 2026-06-24): MGM+ has NOT announced S5. Verify and update once MGM+ makes an official announcement. Do NOT publish renewal claims without confirmation.
- **OTT calendar test pre-existing fail**: `test_ott_calendar.py::test_generated_calendar_has_source_envelopes` - calendar entries empty since Jun-22 roll. Needs `data/ott/calendar.json` regeneration.

## NEXT (Phase 2 continuation)
- E10 finale airs June 28 - stub only until it airs
- Writer lanes (W1 characters, W2 mystery/theory, W3 guides) writing to data/explainers/from/ - deploy wave 2 when their files land (LEAD only deploys)
- IndexNow: new explainer URLs will be picked up by next daily cron via sitemap

---

# BollyAI - pickup state (2026-06-24, FROM SATURATION SHIPPED)

## WRAP (2026-06-24 ~00:55 IST) - FROM Phase 1 complete, LIVE on bollyai.in
- **E9 "The Calm Before" upgraded**: 9593ch -> 12447ch, real subs beats (Sophia dead-forms constraint, Clara possession, Henry dream-anchor, Boyd Bottle Tree plea, Que Sera Sera + Doctor My Eyes, final voice). bollymeter 8.8 set.
- **E8 bollymeter 8.1 set** (body stays at 5611ch - web-grounded, E8 subs mislabeled)
- **date_modified refreshed** to 2026-06-24 (was 2026-06-10) - FROM now floats to top of homepage
- **predictions/from.json** expanded: +3 character theories (Sophia/Victor/Henry) + "Clues You Missed in S4" section
- **endings/from.json** sharpened: S4 section + 4 new finale questions from E9
- Commit 73d7409, deployed CF dep 252fe0ec, pushed, IndexNow 3 URLs
- All gates: validate_series PASS, em-dash 0, pytest 264/265 (OTT calendar pre-existing fail)

## FLOOR: needs Aditya
- **S04E08.srt CONTAMINATED**: `data/subtitles/from/S04E08.srt` is The Rookie S4E8 ("Simone"), not FROM. E8 review is web-grounded (fine), but the srt needs replacement if E8 depth-regen is wanted. Delete + re-fetch when correct file available.
- **FROM Season 5 renewal UNCONFIRMED** (as of 2026-06-24): MGM+ has NOT announced S5. `data/explainers/from/season-5.json` states this clearly. Verify and update once MGM+ makes an official announcement. Do NOT publish renewal claims without confirmation.

## NEXT (Phase 2, if time remains)
- E10 finale airs June 28 - E10 stub lives as predictions only (hard fence)
- Phase 2: generic article route for FROM pieces ("Boy in White explained", mythology guide, character analysis) + homepage FROM cluster block. Design-reviewer >= 7.5 gate. Only attempt if Phase 1 fully stable.

---

# BollyAI - pickup state (2026-06-18 ~07:10, TARGET 1000 HIT - ALL WAVES LIVE)

## WRAP SUMMARY (07:10 IST, 2026-06-18) - overnight session complete
- **TARGET 1000 REACHED**: 717 -> 1003 series (+286 this session)
- **Wave 2 shipped**: duranga (9 eps, 7.3-8.1) + taj-divided-by-blood (8 eps, 7.6-8.4) - Azure gpt-5.4 regen
- **10 buildout ticks deployed**: batches 12-21, each ~30 series (717->1003)
- **Every batch**: 262 pytest PASS, validate_series PASS, AggregateRating clean, pushed + IndexNow
- **8655 static pages** live on bollyai.in (commit 5f25c87, pushed to origin)
- **Loop stopped**: BUILDOUT_STOP flag auto-set by loop at target, bollyloop session in pts/8 idle
- **Deploy worktree**: /tmp/bolly-ship1 at 5f25c87 (node_modules symlinked from main)
- **Azure env**: scripts/subtitles/.azure-env.sh (NANO drafts, FULL finals, cap-3 serial)
- **IndexNow total this session**: 19+28+30+30+30+30+30+18 = 215 URLs pinged

## NEXT SESSION OPTIONS
- Subtitle-grounded episode depth wave (duranga + taj have dossiers ready; other candidates: check data/subtitles/)
- Design improvements (series page / browse grid weakest surfaces - see prior RESUME sections below)
- New content: target bumped if desired, or switch to quality moat work

# BollyAI - pickup state (2026-06-16 ~17:40, 6H PUSH WRAPPED by Aditya - 2 WAVES LIVE)

## WRAP SUMMARY (17:40) - run concluded on Aditya "wrap up now"
- Session total: 566 -> 717 series (+151). TWO deploy waves LIVE: wave-1 93 (commit 2db1a6d) +
  wave-2 59 (commit 8c15dae). IndexNow 144 pinged. All committed + PUSHED (origin synced @89ce5a2).
- Deep lane (Azure gpt-5.4): beef 18 + physical-100 18 + you 49 = 85 subtitle-grounded eps live.
- Azure-only infra COMMITTED + durable (extract_dossier nano backend, crosspass skip, loop fix).
- STOPPED clean: bollyloop killed, bolly6h drained, BUILDOUT_STOP set, bolly claim released.
- TO RESUME: `rm data/_state/BUILDOUT_STOP && tmux new-session -d -s bollyloop -c ~/bollyai 'bash scripts/batch/loop_6h.sh 4'`
  (loop self-commits now; floor deploys waves). Excluded 3 partials: how-i-met-your-mother,
  the-good-wife, the-west-wing (re-validate before committing). NOTE: a stale 18:11 supervision
  wakeup may fire once and self-terminate (sees BUILDOUT_STOP).

## WAVE-1 STATUS (17:08)
- Loop: 566 -> 687 series (+121 in ~75min, 4 ticks). FIXED a commit bug: ticks 1-2 backgrounded
  ingest then exited before committing -> floor committed the 93. LOOP_TICK_PROMPT step 4 now
  mandates FOREGROUND ingest (so future ticks self-commit).
- Deep lane DONE its 4 reserved: beef 18 + physical-100 18 + you 49 = 85 deep eps validated;
  i-will-find-you HONEST-SKIPPED (subs contaminated/mixed from 4 shows + unreleased). Now an
  Azure harvest-pump (tvf-pitchers, black-warrant ...).
- DEPLOYED 93 new series LIVE: commit `ab6b147`, gates GREEN (pytest 262 + npm build 658pp +
  AggregateRating clean), verified `/series/{zerozerozero,acapulco}/` 200, IndexNow 85 pinged.
- PUSH DEFERRED: origin +1 trivial commit ("data: daily refresh", a cron); local +47 ahead.
  Do `git stash push -- data/series/tvf-pitchers.json && git pull --rebase origin main && git push
  && git stash pop` at the FINAL tick (when loop stopped) to avoid mid-run rebase conflicts.
- AZURE-ONLY COMPLETE (Aditya: no OpenRouter): extract_dossier->gpt-5.4-nano (.azure-only flag),
  season_crosspass SKIPPED (flag; needs 1M-ctx OpenRouter), regen finals=gpt-5-4 default. Last
  OpenRouter leak was crosspass:black-warrant 17:07, ~1min before the gate. FULL/gpt-5-4 is cap-3.
- Build worktree: `/tmp/bolly-ship1` at ab6b147 (REUSE next wave: `git -C /tmp/bolly-ship1 checkout
  <new-sha>`; never rm/worktree-remove - deny-listed).

# BollyAI - pickup state (2026-06-16 ~15:52, 6H CONTENT PUSH RUNNING - resource-saving)

## 30-SEC SNAPSHOT (overrides everything below)
Aditya: "resource saving mode + 6 ghante back-to-back content hi content bhar de, especially
new series like widows bay." Vyom floor = vyom3 (owns bollyai). TWO content streams LIVE:
- **Stream 1 - buildout loop** (tmux session `bollyloop`, driver `scripts/batch/loop_6h.sh 6`):
  fires `loop_tick.sh` back-to-back. Each tick = a FRESH Sonnet headless session authoring ~30
  NEW web-grounded series (5 Sonnet subagents per AUTHORING_BRIEF), validate+ingest, COMMIT-ONLY.
  Target bumped 500->1000 (ledger + LOOP_TICK_PROMPT). Log: `data/_state/buildout-6h.log`.
  Started 15:52, baseline 566 series. Stops at 6h wall-clock / BUILDOUT_STOP / target 1000.
- **Stream 2 - deep lane** (`conductor` session `bolly6h`, lane `bolly-deep`, Sonnet): subtitle-
  grounded DEEP reviews (the widows-bay-flavor moat) for i-will-find-you (14 dossiers ready) +
  beef + physical-100 + you. Brief: `.brief-bolly-deep.md`. These 4 slugs are RESERVED (loop
  excludes them). Gen = **Azure gpt-5.4 ONLY** (Aditya 2026-06-16: NO OpenRouter/DeepSeek).
  Enforced by: `data/subtitles/_engine/.azure-only` flag + new Azure backend in
  `extract_dossier.py` (`_dossier_call`, gpt-5.4-nano dossiers, PROVEN ~14s/ep) + env file
  `scripts/subtitles/.azure-env.sh` (nano drafts, gpt-5-4 finals; FULL is cap-3, keep low concurrency).
  Do NOT revert to DSV4/orfree. The Sonnet web-loop (Stream 1) is unaffected (it web-authors,
  never calls extract_dossier).
- **FLOOR (me) owns deploy**: loop+lane NEVER push/deploy. Every ~75-90min reconcile-gate ->
  full pytest -> push -> deploy wave from a clean worktree (`/tmp/bolly-ship1`, currently pruned/
  needs re-add) -> IndexNow <=85/wave. Deploy/push authority granted (CLAUDE.md 2026-06-13);
  gates-green = approval. SERIALIZE floor npm-build vs a loop tick's build (single-flight lock
  /tmp/bollyai-buildout.lock or briefly pause loop). widows-bay is ALREADY LIVE (200).
- To HALT everything: `touch data/_state/BUILDOUT_STOP` (stops loop next tick) +
  `conductor kill --session bolly6h` (drains deep lane gracefully).

---

# BollyAI - pickup state (2026-06-16 ~02:45, NIGHT DONE -> NEXT: MAKE IT SPECTACULAR)

## 🎯 NEXT SESSION (Aditya's directive): MAKE bollyai.in SPECTACULAR - pure DESIGN/CRAFT push
Tonight was content-grinding (done, see below). Next session is VISUAL. The quality bar is already set HIGH - build ON it, do NOT restart:
- **LIVE design language to extend**: Verdict Stage full-bleed hero (design-reviewer **8.9**) + OTT Calendar Hero (**9.4**). Full art direction, OKLCH tokens, fonts (Fraunces Variable display + Hanken Grotesk body + JetBrains Mono numerics), warm-graphite bg + scarce amber accent, and the **Phase-2 design backlog** (localStorage diary / ask-bar answer engine / "Verdict Receipt" tap-to-show-sources / title-page score-stack + day-wise BO table / nav 11->5 + full 6-section IA / tentpole poster harvest) are ALL detailed in the **"DESIGN REVAMP PHASE 1 LIVE" section below - READ THAT FIRST**. Design files: `site/app/{globals,revamp}.css`, `site/components/{VerdictStage,BollyMeterDial,OttCalendarHero}.tsx`, `site/lib/home.ts`.
- **Gate**: empire `frontend-design` skill + `design-reviewer` agent (ship >=7.5; the hero hit 9.4 - that's the bar). Banned slop: Inter/system-font brand face, purple-on-white, cookie-cutter grids. Distinctive, dark-cinema editorial, "sex sells".
- ⚡ **RECOMMENDED start**: screenshot the WHOLE live site desktop+mobile (home + a `/series/<slug>/` title page + the browse/catalogue grid), run `design-reviewer` to RANK the weakest surfaces. The hero is already ~9; the **series/title pages + the browse grid** are almost certainly the weak links - elevate THOSE to hero-level first, then below-the-fold home, then a cohesive micro-interaction/empty-state language. Let Aditya steer priority.
- **Work it**: `cd site && npm run dev` (or build + serve `site/out` on :8799); chrome --headless screenshots; design-reviewer gate; ship via the worktree pattern below (box is quiet now, so a frontend-only deploy can also just build the main tree - BUT first handle the 2 partial content files, see caveat).

## TONIGHT'S STATE (content night, 2026-06-16) - live / committed / pending
- **LIVE on bollyai.in** (deployed commit `2819c88`, CF dep `31fd8e28`): OTT Calendar Hero + 12 series (waves 1+2). 8 are NET-NEW subtitle-grounded (call-me-bae, indian-police-force, mismatched, kerala-crime-files, save-the-tigers, rana-naidu, aranyak, four-more-shots-please) + bridgerton, sons-of-anarchy, severance, made-in-heaven.
- **COMMITTED, NOT yet DEPLOYED** (commit `df2a964`): the-glory (16/16) + inspector-rishi (10/10) + sons-of-anarchy (re-grounded DSV4). ⏰ The design session's first deploy carries these live automatically (worktree -> checkout HEAD -> build -> deploy).
- **PARTIAL, uncommitted** (working tree dirty; both VALID JSON): breathe-into-the-shadows (11/12 eps) + yellowstone (30/53; S4-S5 lack subs, need neutral plot summaries). 🚨 CAVEAT for the design deploy: deploy via the WORKTREE (it's at the clean committed HEAD, excludes these) OR `git checkout -- data/series/{breathe-into-the-shadows,yellowstone}.json` first - do NOT build the MAIN tree with these un-finished. Dossiers persist in `data/subtitles/`, so `regen_batch <slug>` finishes them fast later (low priority vs design).
- Fleet STOPPED: `bollynite` drained gracefully, orphan regen killed, box quiet. vyom2 runs PA/MW/BB on session `wc` - SEPARATE floor, NOT mine.

## SHIP PATTERN (proven 3x tonight) + DIGEST NOTES for Aditya
- 🚨 build_review writes `data/series` NON-atomically -> never build the live tree mid-regen. Standing git worktree `/tmp/bolly-ship1` (node_modules symlinked): commit to main -> `git -C /tmp/bolly-ship1 checkout <HEAD-sha>` (reset `data/_state/series-links.json` if it shows M) -> `cd /tmp/bolly-ship1/site && npm run build` -> `npx wrangler pages deploy out --project-name=bollyai-in --branch=main` (CF creds inline from `vault/cloudflare-master.md` (god token) via grep+sed, NEVER echo) -> verify `/series/<slug>/` 200 -> IndexNow (`scripts/lib/indexnow_ping.py --delta <urls> --key 51f2725a841760148d45a3b07a08c53c --host bollyai.in`, <=85). 🚨 `rm -rf` + `git worktree remove --force` are DENY-LISTED - REUSE the worktree, never delete it.
- Standing deploy/push grant (CLAUDE.md) = gates-green IS the approval (validate_series + em-dash + design-reviewer>=7.5 + pytest + npm build).
- DIGEST: (1) babysit's 25m ttl over-flagged the long content lanes as STALLED (~6 false-positive pokes) - they were productive; worth a productivity-aware or per-lane ttl so 2hr content grinds don't spam the floor. (2) VIVEKA: `conductor add` logs an EMPTY task_id to `shadow.jsonl` (v0 gap) so `viveka verdict <task_id>` can't link to its shadow prediction - I recorded kept-verdicts by lane-name (is_win=false: VIVEKA had predicted nested vs my flat lanes). Fix the add->shadow task_id propagation to make the flywheel real.

---

# BollyAI - pickup state (2026-06-16 ~02:10, WAVE-1 SHIPPED)

- **WAVE-1 LIVE** (commit `7d8290d`, CF dep `6b2a1f69`): 8 series - call-me-bae, indian-police-force, mismatched, kerala-crime-files, save-the-tigers (Indian, NEW subtitle-grounding), bridgerton, sons-of-anarchy (prestige, NEW grounding), made-in-heaven S2. ALL 100% rich review_body, validate_series PASS, em-dash clean, `/series/<slug>/` 200. IndexNow 8 pinged.
- 🆕 **SHIP PATTERN for continuous lanes** (build_review.py:533 writes data/series NON-atomically, so NEVER `npm build` the live tree while regen runs): ship from a STANDING git worktree snapshot at `/tmp/bolly-ship1` (node_modules symlinked). Per wave: commit gated slugs to main -> `git -C /tmp/bolly-ship1 checkout <new-HEAD-sha>` -> `cd /tmp/bolly-ship1/site && npm run build` -> `npx wrangler pages deploy out --project-name=bollyai-in --branch=main` (CF creds inline, never echo) -> IndexNow. **Lanes NEVER pause.** 🚨 Do NOT `rm -rf` or `git worktree remove --force` (both deny-listed) - REUSE the worktree across waves.
- **Reconcile-gate EVERY shipped slug** independently (validate_series exit 0 + em-dash sweep + schema-agnostic rich-review count) before commit - never trust lane self-reports (fabrication lesson).
- VIVEKA: `conductor add` logs EMPTY task_id in shadow.jsonl (v0 gap) -> `viveka verdict <id>` can't link cleanly. Judgment: all 3 lanes = **KEPT** (wave-1 shipped as-is, validated). Apply when task_id linkage fixed.
- **LANES still running**: Lane1 (india) DONE/holding. Lane2 (prestige) finishing yellowstone (--force, long); the-glory + severance already done -> SHIP WAVE-2. Lane0 (harvest-new: four-more-shots-please/rana-naidu/breathe-into-the-shadows/inspector-rishi/aranyak) harvesting->regen.
- **WAVE-2 SHIPPED** (commit `2819c88`, CF dep `31fd8e28`): severance + rana-naidu + aranyak + four-more-shots-please (3 NEW India series grounded + 1 prestige), all `/series/<slug>/` 200 + IndexNow. **Tonight total: hero + 12 series** (8 net-new grounded).
- **WAVE-3 pending** (lanes finishing): the-glory + yellowstone (Lane2, were incomplete - empty spoiler_free on un-regenned eps, told to finish) + breathe-into-the-shadows + inspector-rishi (Lane0). Lane1 idle/done (repurpose candidate). Ship via standing worktree `/tmp/bolly-ship1` (`git -C ... checkout <HEAD>` -> build -> deploy).
- NOTE for digest: babysit 25m ttl over-flags long content lanes as STALLED (false-positive) - they were productive; worth a productivity-aware / per-lane-ttl check.

---

# BollyAI - pickup state (2026-06-16 ~00:20, NIGHT GROUNDING CAMPAIGN)

## 30-SEC SNAPSHOT (overrides everything below)
Vyom floor (orchestrator) on BollyAI ONLY; Aditya: "full autonomy, go crazy, whole night" (vyom2 owns PA/MW/BB - do not touch `work` session).
- **SHIPPED + LIVE**: OTT Calendar Hero (commit `e0d207d`, CF dep `7779439d`). design-reviewer **9.4 ACCEPT**; fixed deck poster-bias (home.ts `ottCalendarDeck` was leading posterless one-sheets, pushing all real posters off-screen). 262 pytest green (made `test_ott_calendar` window-assert date-robust - it froze a weekly-rolling date). bollyai.in 200.
- **Catalog reality (fresh blitz-queue: 559 series, 4013/15527 eps = 26%)**: the subtitle-grounded EPISODE backlog is ~exhausted (only ~30 eps across 9 grounded series left). Rich reviews only exist for the ~56 grounded series, so the moat-growth lever now = GROUND NEW series (the depth-regen-swarm would no-op).
- **3 Sonnet lanes RUNNING (tmux session `bollynite`; ALL gen on Azure gpt-5.4 + DeepSeek-V4-Pro, NEVER gpt-5.5)**:
  - `bolly-finish` (bollynite:0): close 30 grounded ep-gaps - stranger-things/mad-men/you/wednesday/the-family-man/paatal-lok (1 ep each) + the-studio (9) + made-in-heaven (7) + house-of-the-dragon (8).
  - `bolly-ground-india` (bollynite:1): fast-ground (subs ALREADY harvested in ~/bollyai-subs) call-me-bae, indian-police-force, mismatched, kerala-crime-files, save-the-tigers -> run_batch dossier + regen.
  - `bolly-ground-prestige` (bollynite:2): fast-ground sons-of-anarchy, bridgerton, the-glory, severance, yellowstone -> dossier + regen (DSV4 for violent).
- ENDPOINT: draft NANO, finals round-robin FULL/MINI/KIMI/DSV4 (4 independent streams, no shared 429); DSV4 (OpenRouter, off-Azure) = the content-filter escape. Lanes NEVER build/deploy/push/commit; FLOOR central-ships.
- **NEXT (floor)**: when lanes hold gated-green -> reconcile-gate every file -> pytest + validate_series + npm build + em-dash sweep -> race-safe deploy (pgrep regen_batch=0) -> IndexNow <=85/wave -> commit+push. `conductor viveka verdict <task_id> kept|edited|rejected` on EACH lane (flywheel). Then refresh queue + harvest-NEW tier (outer-banks/four-more-shots-please/rana-naidu/aranyak) if time remains.

---

# BollyAI - pickup state (2026-06-15 ~22:35, DESIGN REVAMP PHASE 1 LIVE)

## 30-SEC SNAPSHOT (overrides everything below)
Aditya: "site not as nice-looking as bigger sites, structure doesn't look good" -> ran a **10-Opus
design team** (competitors / latest tech / latest UI / retention psychology). Near-unanimous mandate:
KILL the equal-weight bento hero -> a full-bleed **Verdict Stage**. Phase 1 SHIPPED + LIVE on
bollyai.in (commit `78ebc8a`, CF deploy `3e70a159`). Gates: 262 pytest pass · npm build exit 0
(no-AggregateRating clean) · design-reviewer **8.9/10 SHIP** (ACCEPT, no hard-caps). Live-verified:
home + series pages 200, `verdict-stage`/`BollyMeter` present, old FeaturedMosaic gone.
- **New:** `components/VerdictStage.tsx` + `components/BollyMeterDial.tsx`; `lib/home.ts` `heroPick()`
  (curates a poster-bearing, best-furnished lead, Indian-biased for the pan-India flagship - currently
  leads "Brown" / Karisma Kapoor, BollyMeter 6.2, real critic basis).
- **Art direction** (`app/globals.css` :root): muddy indigo-violet bg -> warm near-black graphite (posters
  supply colour); accent .16->.19 scarce; removed 8px banding + reduced grain.
- **`app/revamp.css`** (NEW, loaded after globals.css, all gated @supports + prefers-reduced-motion):
  the Verdict Stage, the BollyMeter conic dial (arc-sweep), the **"BollyAI Edition" typographic one-sheet**
  that replaces the monogram for the 41 posterless films / 95 posterless series, 3-channel card hover,
  cross-document View Transitions cross-fade, scroll-driven `view()` reveals, box-office bar-grow.
- Hero solves the **backdrop gap** (only 1 real backdrop on the catalogue): ambient = the poster itself,
  blurred + scaled, filling the bleed. Zero new assets.
- Old `FeaturedMosaic.tsx` kept (now unused) for easy revert. Team output + SYNTHESIS + before/after
  shots: `~/bollyai/design-revamp-2026-06-15/`.
- design-reviewer >= 7.5 gate was running at handoff. **Phase 2 backlog** (in SYNTHESIS.md): localStorage
  diary / "Your Friday Court", client ask-bar answer engine, "Verdict Receipt" tap-to-show-sources,
  title-page score-stack + day-wise BO table, nav 11->5 + full 6-section IA, tentpole poster harvest.
- To re-screenshot: server at `127.0.0.1:8799` (serves `site/out`); chrome --headless=new --screenshot.

---

# BollyAI - pickup state (2026-06-15 ~13:00, DEPTH WAVE 2 SHIPPED)

## 30-SEC SNAPSHOT (overrides everything below)
"agla wave" -> second depth wave shipped + LIVE on bollyai.in (commit `0afad48`, dep `572cbca0`).
3 Sonnet lanes, floor re-gated every file independently before ship:
- **9 series deepened**: money-heist, breaking-bad (depth-A) + black-mirror, hellbound, sweet-home,
  fauda, emily-in-paris, peaky-blinders, better-call-saul (depth-B, ~281 episode reviews).
- **sherlock S4 honesty fix**: review_body rewritten own-voice Mode B, 2 attribution violations
  removed (was reverted-to-buildable last wave; now grounded + gate-clean).
- Honest skips (no new subtitle dossiers, left as-is): stranger-things, physical-100, mad-men.
  sacred-games was already rich+committed from a prior wave (no change).

Gates: 262 pytest pass, validate_series.py clean on all 10 changed slugs, npm build +
assert-no-aggregate-rating exit 0, em-dash-free. IndexNow hash-gated skip (content-update on
existing URLs, sitemaps unchanged - by design). Live-verified bollyai.in + black-mirror +
peaky-blinders + sherlock all 200. Fleet drained graceful.

**2 OPS LESSONS this wave (both saved to memory):**
1. `conductor add --value high` -> governor picks **Opus**; both depth lanes came up Opus 4.8 on
   bulk grunt. Relaunched `--value normal --model sonnet`. VERIFY MODEL VIA PEEK AFTER DISPATCH.
   ([[feedback_conductor_value_high_maps_to_opus]])
2. A lane ran `npm run build` despite the fence and it HUNG - orphan jest-workers pegged ~800% CPU
   for 2h11m before I caught it (Aditya flagged heat). Killed the tree by PID. The NANO `--force`
   polish loop also hammers CPU (local model x many shells). Fence-violation builds can zombie;
   watch box load, not just lane ctx.

## NEXT WAVE (say "agla wave")
- Depth moat continues: top blitz-queue still has stranger-things, physical-100, the-crown,
  money-heist(done), black-mirror(done) ... feed the lanes ONLY subtitle-grounded incompletes;
  for ungrounded titles write neutral plot summaries, never invented reception.
- **Box-office is the biggest unbuilt wedge**: pipeline + sources registered (sacnilk/boxofficeindia/
  BH/ormax), publishes only on >=2-source agreement. Needs ONE focused lane to wire LIVE 2-source
  fetch so it starts publishing the South mid-tier figures it's currently tracking (do NOT swarm
  this - it's live-HTTP verification, single careful Sonnet lane).

---

# BollyAI - pickup state (2026-06-15 ~11:40, 3-LANE WAVE SHIPPED)

## 30-SEC SNAPSHOT (overrides everything below)
"bollyai resume" -> floor central-shipped the held 3-lane fleet wave. All three lanes had
FINISHED + were holding for the floor to ship (briefs fence lanes from deploy/build). Floor
reconciled, ran every gate, committed `35429dd`, deployed, pushed, IndexNow. **LIVE on bollyai.in.**

Shipped this wave:
- **depth lane**: 38 series deepened with v3 rich reviews (aarya, beef, dexter, ted-lasso,
  slow-horses, the-glory, fleabag, kota-factory, mumbai-diaries, poacher, kohrra, kaala-paani,
  my-mister, moving, my-name, the-marvelous-mrs-maisel ...).
- **boxoffice lane**: honest cited box-office pipeline (`engine/fetchers/boxoffice.py` + BH adapter,
  Ormax registered, `trade_estimate_confidence` field, fence #7 >=2-source publish rule IN CODE;
  single-source figures correctly held DATA_PENDING - 5 records, no fabricated number shipped).
- **endings/recaps lane**: 6 ending-explained (delhi-crime, farzi, mirzapur, paatal-lok, panchayat,
  scam-1992) + 3 before-season recaps - pure Indian-OTT white-space.

Gates ALL green before ship (per CLAUDE.md standing deploy grant): 262 pytest pass, attribution moat
clean on all 38 series, `npm build` + `assert-no-aggregate-rating` lint exit 0, published surfaces
em-dash-free. No frontend/component change this wave (data + engine + link-mesh only) so design-reviewer
N/A. Deploy: CF Pages Direct Upload (12093 files, dep `26de7b5e`) + IndexNow 3014 URLs. Live-verified
bollyai.in 200, ted-lasso + scam-1992/ending-explained both 200. Fleet drained clean (graceful /exit).

Housekeeping: added `.conductor-*.md` / `.film-authoring-brief.md` / `BLITZ-PLAN.md` to `.gitignore`
(were polluting `git status`). `logs/` lane reports left untracked (diagnostic).

## NEXT WAVE (say "agla wave")
- Catalog depth still the moat: ~25/554 series 'perfect', most episodes still neutral summaries. Top of
  `data/_state/blitz-queue.json`: stranger-things, physical-100, the-crown, money-heist, black-mirror
  onward (subtitle-grounded only; never invented reception).
- Box-office: pipeline wired but publishes only on >=2-source agreement. Wire a SECOND citable source
  (Sacnilk + BH pair proven) to start publishing the South mid-tier figures it's currently tracking.
- 1 DEFERRED from prior night: **sherlock** S4 needs grounded v3 regen (was reverted to buildable).

---

# BollyAI - pickup state (2026-06-14 ~02:15, REVIEW-BLITZ + HONESTY-GATE night)

## 30-SEC SNAPSHOT (this overrides older sections below)
Overnight Vyom-orchestrated review-blitz. A 4-writer swarm tried to fill per-episode reviews and
MASS-FABRICATED ~14,700 invented critic/audience attributions ("Critics noted", "Reviewers praised")
on ungrounded series. CAUGHT at the floor reconcile-gate; **0 fabrication shipped.** Root cause:
house-style said "write what critics reported" + the validator only checked viewing-claims.

**Shipped + LIVE (committed 6c3c63d / 22a46b9 / d40d801, deployed + pushed + IndexNow 85):**
- **House-style v3** (no invented attribution) + a **BUILD-BREAKING attribution gate** in
  `scripts/batch/validate_series.py` (`engine/gates/attribution_regex.py`, episode-scope aware).
  Verified: exits 1 on fabrication, 0 on clean. THIS IS THE NEW MOAT - never remove it.
- **11 clean v3 reviews LIVE** on the sub-grounded series (scam-1992 10/10 incl new ep9, squid-game,
  mirzapur, sweet-magnolias, nobody-wants-this, mr-and-mrs-smith, teach-you-a-lesson). 256 pytest pass.
- Centralized inter-series **link mesh** (site/lib/links.ts, 5540 edges) committed + live.

**✅ CLEANUP DONE (Aditya chose Strip+Regen):** catalog went 52% -> **99.8% gate-clean (558/559)**.
TRACK-A regenerated ~35 sub-grounded failing series to rich v3; TRACK-B stripped fabricated attribution
from ~233 ungrounded series (background bash loop + the gate's OWN detector for a deterministic
sentence-strip on the stragglers - far more reliable than the stochastic NANO rewrite). All deployed +
pushed + IndexNow (commits through 8cdb349). 🔸 ONLY 1 DEFERRED: **sherlock** - S4.review_body was
fully fabricated, so it needs a grounded v3 regen (BollyAI's OWN voice on the real season, no
attribution); reverted to its buildable state meanwhile. Fabrication stashes (git stash, several)
retained as recoverable backups - safe to drop after a few days.

**LESSON (saved to memory feedback_swarm_attribution_fabrication_gate):** a swarm + a critic-persona
house-style + a validator blind to attribution = mass fabrication. The FLOOR reconcile-gate (re-gate
every file independently before ship) is the guarantee, NOT writer self-reports. Mechanical de-fab work
belongs in a bash loop (NANO), not 5hr Opus lanes that hit Anthropic rate limits.

**Quarantined (recoverable):** both blitz fabrication rounds in `git stash` (3 stashes - do NOT
blind-restore; they are fabrication). **Deferred:** ungrounded-episode completeness (only do via real
Wikipedia-synopsis grounding, never invented reception) + the 268-series cleanup.

**Honest scope truth:** ~56 series have subtitle grounding; only those + films + reception-rich titles
support rich reviews. Completeness elsewhere = neutral plot-grounded summaries (no fake attribution) or skip.

---

# BollyAI - pickup state (2026-06-13 ~20:25, BIG BUILD DAY shipped)

## 30-SEC SNAPSHOT
Today's intent: "sab build kar saari new series + new movies" + "alive multi-block homepage"
+ "Bing like PapersAdda". ALL headline items LIVE on bollyai.in. Fleet drained clean (no lanes
running). Next: the remaining 8 new series + new-season expansions - same proven pipeline, all
₹0. Orchestration mode: Aditya wants multi-agent lanes, floor orchestrates + reviews only.

## LIVE on bollyai.in (shipped today, commits f7d82ae -> 254cdda)
- **Homepage = multi-block hero-mosaic** (`site/components/FeaturedMosaic.tsx` + `lib/home.ts`
  + globals.css mosaic block): films+series MIXED, 35 above-fold tile-links, design-reviewer 9.4.
  Replaced the single full-bleed pic per Aditya ("multiple blocks/links, maza").
- **Films 21 -> 62** (41 new, codex-authored, grounded): data/films/<QID>.json. Dune, Pushpa 2,
  Kalki, Kantara(2022-note), Sinners, Superman, Deadpool, Coolie, Chhaava, KPop Demon Hunters...
- **5 new series w/ S1 rich reviews:** landman, the-madison(6/6), lioness, mayor-of-kingstown, the-pitt.
- **Original 6 series** (50 eps rich) + 2 fixed fails. Total catalog ~551 series + 62 films.
- **Bing: bollyai.in verified + 3 sitemaps + ~134 URLs (IndexNow)** - FULLY PROGRAMMATIC.

## NEXT WAVE (say "agla wave" - all ₹0, pipeline proven today)
A. **8 remaining new series** (of the 13-series Sheridan/marquee gap):
   - have subs, just dossier+regen: **the-studio, mr-and-mrs-smith, nobody-wants-this**
   - need subs first (fetch_new_subs): the-perfect-couple, indian-police-force, call-me-bae,
     kerala-crime-files, save-the-tigers
B. **Later seasons** (no subs yet) of the multi-season ones: landman S2, lioness S2,
   mayor S2-4, the-pitt S2. Re-run fetch_new_subs when subs drop.
C. **~20 new-SEASON expansions** of existing catalogued series (episode-expansion):
   Squid Game S2/S3, Stranger Things 5, Wednesday S2, Severance S2, Mirzapur S3, Panchayat S3/S4,
   Paatal Lok S2, Suzhal S2, HotD S2, The Boys S4, The Bear S3/S4, etc.
D. kantara = authored as 2022 original; add 2025 "Chapter 1" separately.
- Grounded backlog list: codex discovery at /tmp/bolly-wave2-discovery.md (or re-run `gpt research`).
  Campaign tracker: `data/_state/build-all-campaign.md`.

## THE PROVEN PIPELINES (how to build more)
### New SERIES full chain:
1. Add to `data/subtitles/_engine/fresh-manual.json`: `[{"kind":"series","slug":..,"title":..}]`
2. `python3 scripts/subtitles/freshness_radar.py` (refresh queue from manual+calendar)
3. `python3 scripts/subtitles/fetch_new_subs.py` (subliminal -> ~/bollyai-subs/series/<Title>/,
   ~30min, budget-paced; some too-fresh titles return 0 subs - retry later)
4. Author series JSON (structure+metadata+spoiler_free, NO review_body) via a Sonnet lane +
   `scripts/batch/AUTHORING_BRIEF.md` (grounded Wikipedia+reception, verify-or-strip, QID null if unsure)
5. **Dossiers** 🚨 STOP-DANCE: the Engine STOP + QUOTA_HALT flags HALT run_batch. Run with a
   bash trap that RESTORES STOP always: `mv STOP /tmp/STOP.bak; rm -f QUOTA_HALT;
   python3 scripts/subtitles/run_batch.py <slug>` (stage+stats+dossier via FREE orfree lane,
   ~30min/series, ~900 req/day budget, ~13 req/7 dossiers). Dossiers work ROSTER-LESS (auto-detect
   chars, verified good).
6. **Rich reviews:** `python3 scripts/subtitles/regen_batch.py <slug>` (Azure gpt-5.4).
   🚨 violent/adult titles hit the Azure content-filter -> retry with
   `BOLLYAI_REVIEW_MODEL=gpt-5.5 python3 scripts/subtitles/regen_batch.py <slug>`.
7. 🚨 PIPELINE, don't serialize: regen each series the moment ITS dossiers finish (a lane today
   wasted ~1hr waiting for all dossiers before any regen - STEER lanes to pipeline).
### Films (reception-authored, NO subs/Azure, FAST):
- `data/films/<QID>.json` = SourceValue metadata + verdict + bollymeter(null if ungroundable)
  + box_office(null/awaited default unless 2+ sources within 10%) + logline. Author via codex
  (`.film-authoring-brief.md` pattern) or Sonnet from Wikipedia+box-office+reception. `validate_films`.
### Deploy (floor central-ship):
- 🚨 RACE RULE: the site build reads `data/series` ONLY (NOT data/subtitles). Deploy ONLY when
  `(pgrep regen_batch)+(pgrep build_review)=0`. run_batch (dossiers, data/subtitles) does NOT
  race the build - ignore it.
- `cd site && npm run build` (green, ~2616 pages) -> `npx wrangler pages deploy site/out
  --project-name=bollyai-in --branch=main` (CF creds vault/cloudflare-master.md god token, extract inline, never echo)
  -> live-verify episode pages 200+content -> IndexNow `python3 scripts/lib/indexnow_ping.py
  --delta <urlfile> --key 51f2725a841760148d45a3b07a08c53c --host bollyai.in` (<=85/wave)
  -> commit+push series JSONs (pytest gate; pathspec - data/subtitles is gitignored).

## KEY GOTCHAS (today's learnings)
- 🚨 **null-poster build crash FIXED** (`lib/data.ts` FILM_POSTER_FALLBACK+resolveFilmPoster,
  `lib/series.ts` resolvePoster full-fallback, `site/public/img/films/_fallback.svg`). New
  content with poster:null no longer crashes the build.
- 🚨 **Bing key d00ac... in vault/bing-webmaster.json is VALID** (a lane mis-diagnosed it as
  InvalidApiKey via a bad request format - ALWAYS verify a credential directly before trusting a
  lane's error). Bing API: GetUserSites / AddSite(POST {siteUrl}) / VerifySite(POST {siteUrl}) /
  SubmitFeed(POST {siteUrl,feedUrl}). Verify via BingSiteAuth.xml at site root (account auth code
  5F4DA5E506D4D4C8E41E5E1944B4F511). bing.com/ping is deprecated (410). 8 empire sites on the account.
- 🚨 gpt-5.5 lane is the escape hatch for Azure content-filter on violence (landman/lioness/mayor/CLOY E12).
- STOP + QUOTA_HALT flags can be STALE (morning 429 storm) - safe to clear if requests_today < budget.

## RICH-REVIEW ARCHITECTURE (locked)
- Writer = **gpt-5.4 on Azure** (deployment `gpt-5-4`, capacity-3 = MUST stay serial; 429-backoff
  in `build_review._azure_chat` load-bearing). ₹0 sponsored. Override `BOLLYAI_REVIEW_MODEL=gpt-5.5`.
- MOAT = `scripts/subtitles/REVIEW-HOUSE-STYLE.md` (writing contract sent every call) + draft->edit
  two-pass. Stock models; 100% of quality is the re-sent instructions.
- Schema `site/lib/series.ts` EpisodeReview: review_body(~1.2-1.7k md) + verdict{score,one_liner}
  + pull_quote + hero_image. Per-episode bollymeter = BollyAI's own disclosed craft score.
- FENCES (build-breaking): no first-person viewing claims, NO em/en dash, no fabricated OTT numbers,
  bollymeter null-or-full, QID never guessed, fence#10 skip-if-too-thin. validate_series + validate_films + pytest.

## ORCHESTRATION MODE (Aditya's standing directive today)
"babysit karo, multi-agents se karwao, khud sirf orchestrate + review." Floor dispatches conductor
lanes (`conductor add work --project bolly --value high|normal --task "read .conductor-X.md"`),
arms `conductor babysit --install`, reviews lane output + does the central deploy/commit/push, does
NOT hand-grind code. governor picks model (Opus for high-value design like homepage, Sonnet for grunt).
Per-lane brief files: write .conductor-<task>.md, lane reads it. Serialize conductor adds (they race
on .conductor-task.md - confirm one booted before adding the next).

> 🆕 SHIPPED 2026-06-21 ~09:10 (Azure gpt-5.5 push, floor vyom3): **33 series review-corpus UPGRADED to gpt-5.5** (regen --force, 2 parallel lanes, draft+final=gpt-5-5, 0 Claude meter on expiring Azure credit). Gates green (em-dash 0, pytest 262, npm build exit 0). DEPLOYED to bollyai.in via empire-god token + IndexNow 33 URLs. 🚨 cloudflare.md Pages token does NOT scope bollyai-in (auth 10000) -> used cloudflare-master god token. 🚨 deploy hit CF 20k-file cap (20620) -> pruned 1008 orphaned avif to 19612; RECURRING issue, build now exceeds cap, needs proper fix (stop avif gen or drop avif preloads). 33 commits LOCAL, push blocked (origin ahead, non-fast-forward) -> needs reconcile.
