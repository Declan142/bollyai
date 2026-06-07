# BollyAI — pickup state (2026-06-08, post series-scale-up)

**30-sec snapshot:** bollyai.in LIVE (CF Pages Direct Upload, **noindex pre-launch gate ON**). 21 films + **135 series / 322 seasons / 557 static pages** across 6 desks + Series + What-to-Watch. Wikidata spine (QID keys, NO TMDB). Deployed 15dc9a3 → https://95aad4ca.bollyai-in.pages.dev (apex verified 200).

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
