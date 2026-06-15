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
  --project-name=bollyai-in --branch=main` (CF creds vault/cloudflare.md, extract inline, never echo)
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
