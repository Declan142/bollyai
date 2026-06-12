# BollyAI — pickup state (2026-06-13 ~01:40, SUBTITLE ENGINE running overnight — Vyom handoff)

## RUNNING RIGHT NOW (session-independent — do NOT relaunch blindly, check pgrep first)
- **Dossier batch** `pgrep -f run_batch.py` (was PID 990268): 13 series ~250 eps, sequential.
  Done so far: crash-landing-on-you(16+CP), every-year-after(8+CP), films(4). In flight: rest.
  Ledger `data/subtitles/_engine/batch-ledger.jsonl`. Console `_engine/batch-console.log`.
  **@reboot cron relaunches it** (resume-safe) unless STOP/QUOTA_HALT present.
- **Freshness fetch** `fetch_new_subs.py`: sweeping the 18-item fresh-queue, pulling subs via
  subliminal, auto-pushing successes through the engine. Got every-year-after + sweet-magnolias.
  Daily **cron 07:30 IST** (`freshness_tick.sh`) re-runs radar+fetch; 10-try retry per item.
- **Review chain** `review_chain.sh`: WAITS for batch to clear, then drafts+G3-judges reviews
  for every series with dossiers. Console `_engine/reviews-console.log`. Staging only.
- HALT everything: `touch data/subtitles/_engine/STOP`. Quota: ~160/900 today, budget guard at 900.

## SHIPPED THIS SESSION (2026-06-13 ~01:36, commit 78fddc0, deployed 167b681a)
- **Homepage "Naye Episode Reviews" rail** — `site/lib/series.ts` `getNewestEpisodeReviews(10)`,
  horizontal-scroll rail between Just Dropped and Binge Verdicts. Sort key: `merged_at` ISO
  (engine will write it) else `date_modified`. Each card: poster thumb, S01E01 badge, episode
  title, series name, 3-line hook. Design-reviewer **PASS 8.3/10** (two runs: 8.3 + 8.1).
  Gates: `npm run build` green, 180 pytest green. Committed 78fddc0, deployed CF Pages
  `167b681a` (bollyai.in live), IndexNow `https://bollyai.in/` HTTP 200.

## FIXED TONIGHT (verified)
- **Consensus matching bug** (was: ALL callbacks "candidate", 0 high). Root cause: `intersect()`
  required setup_t within 20s — two model families cite the SAME callback at DIFFERENT timestamps.
  Fixed to match on (setup_ep,payoff_ep) PAIR + semantic token-overlap of "what"; timestamps are
  G2-verified independently so not a join key. PROVEN via `--rematch` (zero LLM): every-year-after
  0→4 high, CLOY →1. Running batch's remaining crosspasses auto-use the fix.
  ⚠️ caught a missing `import re` at runtime test — would have crashed every remaining crosspass.
  Always RUN-test season_crosspass after edits, compile-check alone misses NameErrors.
- llm_router v2 (dead deepseek:free leg healed, 8/8 smoke, pushed to PA-fresh).
- Engine code committed+pushed (4f28f58); origin HEAD now has 0 subtitle .srt.

## STILL BROKEN / NOT DONE (honest — this is NOT flawless yet; priority order)
1. **No finished review has been READ for quality.** review_chain is generating drafts but
   nobody (not Aditya, not Vyom) has eyeballed one. FIRST morning job: read 3-4 spoiler_free
   drafts, confirm grounded+specific+has-criticism+no-slop. If weak → fix draft_reviews.py prompt.
2. **Speaker-attribution gate gap (Fix 2, NOT built).** key_line.speaker is LLM-INFERRED;
   subs are non-SDH so the gate can't verify WHO said a line (only that the line exists at t).
   Plan: verify_dossier should null any key_line.speaker not backed by an SDH tag in the
   dialogue doc (don't kill the quote, kill the guessed attribution) + count in _verified.
   Reviews already attribute quotes to "the dialogue/subtitles" not characters, so downstream
   is safe — but the dossier field is dishonest until this lands.
3. **merge_reviews.py DOES NOT EXIST (Fix 3).** No path from `_reviews/episodes.json` staging
   → `data/series/<slug>.json` `episode_reviews[]`. Must: match by number, run validate_series,
   only merge G3-passed + Vyom-voice-passed drafts. This is the blocker for shipping anything.
4. **bollymeter + critic_note are null by design.** Per-hour numeric score + real critic quote
   need real reception (verify-or-strip) — that's the Vyom voice-pass (G4), not a free-model job.
5. **Films review/merge path undesigned.** 4 films staged+extracted as 1-episode corpora; the
   EpisodeReview schema is per-episode-of-a-series. Films need a film-review shape + merge target.

## MORNING PLAN (Vyom, ~07:00 — the work Aditya wants: "sab series review + homepage naye reviews")
1. Read drafts (item 1 above). 2. Build Fix 2 + Fix 3 + film path. 3. G4 voice-pass: BollyAI
   voice on passed drafts, fill bollymeter/critic_note from real reception where groundable.
4. merge → `validate_series.py` → `pytest tests/` → `cd site && npm run build`. 5. ~~Homepage
   "Naye Episode Reviews" rail behind design-reviewer ≥7.5~~ **DONE (8.3/10, 78fddc0, deployed)**.
   6. Deploy `wrangler pages deploy site/out --project-name=bollyai-in` + hash-gated IndexNow
   **DONE (167b681a, IndexNow 200)**. Deploy/push = standing grant, GATES are the approval
   (tests+build+design green). Force-push/history stay DENIED.

## GOVERNANCE / CONTEXT
- **Deploy/push grant** to Vyom recorded in CLAUDE.md (2026-06-13): push needs tests green;
  deploy needs tests+build (+design≥7.5 frontend); IndexNow hash-gated; force-push DENIED.
- **Subtitle corpus**: gitignored, untracked, removed from origin HEAD. Aditya ruled NOT a
  violation (fence #8 = don't SERVE, repo-hosting ok). 37 FROM .srt still in git HISTORY;
  only `git filter-repo`+force-push purges that = fenced, Aditya's explicit call only.
  Leak manifest: `~/.claude/state/bollyai-subtitle-leak-manifest-20260612.txt`.
- **Cost proof**: 75% of answers from FREE models (gpt-oss 32 / nemotron 14 wins of 61);
  paid deepseek backstop ~$0.12 total. The MOAT is the gates, not the models.
- **Model-switch annoyance**: Fable 5's safety classifier false-positives on this session's
  copyright+security vocab cocktail (subtitle/leak/criminal-conviction + DLP-bypass/attack/
  ghatak in empire context) and auto-switches to Opus 4.8. Harmless, work unaffected, both
  models equivalent for this. Channel: /feedback. Not Vyom-fixable.
- **BRIEF-INTEGRATOR.md deletion** parked in `git stash@{0}` (foreign fleet residue, untouched).
- Engine docs: `scripts/subtitles/FREE_MODEL_RULES.md` (the 4-gate quality contract — READ FIRST).

---
# BollyAI — pickup state (2026-06-12 ~08:00, OVERNIGHT FLEET WAVE — MEGA-DEPLOY LIVE)

**5-lane wave merged + 2 deploys to bollyai.in:** batch-11 +30 South-first series (catalogue 542) · /box-office/ hub + crore-clubs (blueprint namespace, BO publish rule in renderer - 56 honest tracking states live) · /tools/hit-flop-calculator + /tools/box-office-comparator (Seat-08) · poster-harvester v2 engine + attribution manifests (0 posters filled - only 9 SVG gaps, no legit sources; honest) · /ott/calendar verified weekly OTT calendar (Monday-anchored, regen via engine/regen_ott_weekly.py). Tests 157/157. Em-dash purged source-wide (24 strings). MYSTERY SOLVED: dirty-main w2w residue was COUPLED WIP (ogImage og-card stack) - restored from stash, committed 6a98020; stash entry retained. sharp now a real dep (variant generator in prebuild). IndexNow full 2831 one-time + hash-gated delta after. Deploy = wrangler direct (vault cloudflare.md works).
**Evening waves 3+4 (2026-06-12):** box-office DATA live (tracking 56→1, Sacnilk+ToI 2-source envelopes) · 5 GHA workflows authored+dry-run (ARM = secrets pending Aditya/floor) · /ott/calendar verdict lines (grounded-only) · 37 QIDs resolved (14 honest-null) · interactive tools live (/tools/hit-flop-calculator + box-office-comparator) · em-dash source purge. Deploys ed799ab6/c52b959f.
**Wave-5:** 7 industry box-office yearboards LIVE (/{industry}/box-office/2026/, verified envelopes, 4872cfd).

# BollyAI — pickup state (2026-06-09, LIBRARY BUILDOUT LOOP running)

**LIBRARY BUILDOUT + VIRAL BROWSE (2026-06-09) — LIVE & AUTONOMOUS:** catalogue **183 -> 267** (waves 01+02, commits `26c8ac6` + `7ee927d`). **Viral browse shipped** (`3b80448`): /series faceted filter (genre/platform/country/status/era) + sort + title search, recency-first, home "Just Dropped" rail, 100% genre coverage (Wikidata P136+P31 + seed via `harvest_genres.py`). **DEPLOYED LIVE** to bollyai.in (CF Pages, 2596 files) + IndexNow throttled (85 new-series hubs). Machinery in `scripts/batch/` (AUTHORING_BRIEF, validate_series, fix_series, ingest_batch, harvest_genres) + ledger `data/_state/library-buildout.md`.
**HOURLY FRESH-CONTEXT LOOP INSTALLED** (system cron `17 * * * * loop_tick.sh`): each hour a FRESH `claude -p` (sonnet) reads the ledger, spawns 5 authoring subagents, reconciles, runs ingest_batch, commits+pushes ONE batch, exits = clean context every hour. Guards: single-flight flock, `data/_state/BUILDOUT_STOP` flag, self-stops + self-removes-cron at 500, **NEVER deploys/IndexNow/force**. To STOP: `touch data/_state/BUILDOUT_STOP`. To watch: `tail data/_state/buildout-loop.log`. **Loop commits but does NOT deploy** — new loop series go live only on a manual deploy (velocity-throttled by design). Deploy creds: vault `cloudflare.md` (Pages token + acct), `npx wrangler pages deploy site/out --project-name=bollyai-in --branch=main`.

---
# BollyAI — pickup state (2026-06-08, post SEO-sweep + Ending-Explained)

**30-sec snapshot:** bollyai.in **LAUNCHED & PUBLIC (2026-06-08)** — noindex triple-gate REMOVED, all pages indexable, deployed, CF cache purged, IndexNow pinged 864 URLs. 21 films + **183 series / 457 seasons / 487 episode reviews + 120 Ending-Explained walkthroughs** across 6 desks (Bollywood/Kollywood/Tollywood/Mollywood/Sandalwood/Hollywood/Streaming) + Series + What-to-Watch (18 lists) + site search. Founder schema = Aditya Sharma / @aditya14. Wikidata spine (QID keys, NO TMDB). **sitemap 864 URLs**, robots.txt → sitemap.

**ONLY REMAINING INDEX STONE — Google Search Console (needs Aditya's Google login):** add `bollyai.in` as a Domain property at search.google.com/search-console → verify (CF one-click OR a DNS TXT I can add via CF API once you paste the token) → submit sitemap `https://bollyai.in/sitemap.xml`. IndexNow already covers Bing/Yandex/Seznam/Naver; Google has no programmatic submit for an unverified property (and Google killed the sitemap-ping endpoint in 2023).

**Latest session (commits f3.. → a2cf928):**
- **Site-wide title/description sweep**: whole site was on the root default `<title>` (the real traffic blocker, NOT review length). Every indexable route now has unique search-intent title+desc (series/film/ott/static); fixed /watch double-bar; hub uses peak-season verdict (`peakSeason()`); series-hub "Quick Answers" FAQ from real renewal/platform data.
- **Ending-Explained surface**: `/series/[slug]/ending-explained/`, **120 grounded spoiler walkthroughs** (2 waves × 10 Opus agents, Wikipedia-cited), `data/endings/<slug>.json` + `lib/endings.ts` + gate `tests/test_ending_explained.py` (121/121). Hub CTA + season link gated on `hasEnding()`. Only ended/limited shows; 3 correctly skipped (film / too-recent / contradictory-sources). Essentially the full qualified catalogue is now covered. To extend: drop more `data/endings/*.json` vs the locked schema.

**Latest increment (this session, 3 commits f7d82f8→15dc9a3):**
- **+76 international series** via 6-agent parallel fan-out: US/UK prestige, sci-fi/fantasy, Korean, Japanese anime, European/Spanish/British, Indian. Catalogue 59→135.
- **Episode reviews**: new `episode_reviews[]` schema → "Standout Episodes" panel + TVEpisode/Review JSON-LD. 159 on new series + 33 backfilled on tentpoles (Squid Game, TLOU ep3, The Bear Fishes/Forks…). 192 total.
- **What-to-Watch surface**: `/watch` + `/watch/[slug]`, 10 curated lists / 73 picks (38 linked on-site), ItemList+FAQPage JSON-LD, home rail + nav.
- **118/135 series posters** harvested (Wikipedia REST-summary lead image, 2:3 crop, fair-dealing attributed); 17 on honest fallback SVG (logo/SVG leads). Scripts: scripts/harvest_series_posters.py (+og/infobox fallbacks).
- **sitemap.ts fixed**: was missing the ENTIRE series surface — now 553 URLs (series hubs + seasons + /watch + lists).
- Gates clean: 0 viewing-claim / 1376 prose fields, em-dashes stripped. CriticConsensus hardened null-safe. Graceful poster fallback in series.ts.

**State:**
- Repo: github.com/Declan142/bollyai (public, main). Engine: fetchers (wikidata/boxoffice/ott_announcements/image_harvester), gates (viewing-claim 29 tests, emdash), scripts (indexnow w/ PRELAUNCH no-op, deploy-manual).
- Infra done: zone active, Pages bollyai-in + apex/www, Email Routing takedown@→gmail, SSL strict, www→apex 301 (Page Rule), DMARC. IndexNow key in vault + public/.
- NOINDEX triple gate: layout.tsx robots block + _headers X-Robots-Tag + data/_state/PRELAUNCH_NOINDEX flag. **Launch = remove all 3 + full IndexNow re-ping.**

**Next (Day 2 runbook):** 5 GHA workflows + secrets + hc.io checks + dry-runs + chaos tests (10-ops-infra-build.md §4-7). Then: engine-generated review content (the "half-baked" gap), design polish (design-reviewer ≥7.5 gate pending).

**Blocked on Aditya:** scoped CF token (Pages:Edit + bollyai.in DNS:Edit, dashboard mint) for GH secrets · @bollyai handles claim · "launch" call (removes noindex).

**Watch:** codex weekly pool spent (118%) — gen work routes local/spark till renewal. Backfill verdict rungs all null (no budget data) — render as OPEN/TRACKING; content engine to fill BollyMeter + verdicts with cited basis.
