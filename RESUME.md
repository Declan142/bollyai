# BollyAI — pickup state (2026-06-12 ~08:00, OVERNIGHT FLEET WAVE — MEGA-DEPLOY LIVE)

**5-lane wave merged + 2 deploys to bollyai.in:** batch-11 +30 South-first series (catalogue 542) · /box-office/ hub + crore-clubs (blueprint namespace, BO publish rule in renderer - 56 honest tracking states live) · /tools/hit-flop-calculator + /tools/box-office-comparator (Seat-08) · poster-harvester v2 engine + attribution manifests (0 posters filled - only 9 SVG gaps, no legit sources; honest) · /ott/calendar verified weekly OTT calendar (Monday-anchored, regen via engine/regen_ott_weekly.py). Tests 157/157. Em-dash purged source-wide (24 strings). MYSTERY SOLVED: dirty-main w2w residue was COUPLED WIP (ogImage og-card stack) - restored from stash, committed 6a98020; stash entry retained. sharp now a real dep (variant generator in prebuild). IndexNow full 2831 one-time + hash-gated delta after. Deploy = wrangler direct (vault cloudflare.md works).
**Evening waves 3+4 (2026-06-12):** box-office DATA live (tracking 56→1, Sacnilk+ToI 2-source envelopes) · 5 GHA workflows authored+dry-run (ARM = secrets pending Aditya/floor) · /ott/calendar verdict lines (grounded-only) · 37 QIDs resolved (14 honest-null) · interactive tools live (/tools/hit-flop-calculator + box-office-comparator) · em-dash source purge. Deploys ed799ab6/c52b959f.

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
