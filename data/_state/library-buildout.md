# BollyAI Library Buildout — loop ledger

**Started:** 2026-06-09 · **Baseline:** 183 series
**Target:** provisional 500 (confirm with Aditya) · **Stop:** target reached OR Aditya halts
**Velocity policy:** author+gate+commit AGGRESSIVE (reversible/internal); deploy+IndexNow
THROTTLED — site is 1 day old, avoid spam-velocity signal. (confirm cadence with Aditya)

## Pipeline per batch
1. plan disjoint slugs (filter existing) → 6-8 pools
2. dispatch Sonnet authoring agents (brief: scripts/batch/AUTHORING_BRIEF.md)
3. `validate_series.py` over new files → fix/quarantine failures
4. Opus reconcile spot-pass (fence + score sanity)
5. harvest posters (scripts/harvest_series_posters.py)
6. `cd site && npm run build` → must be green
7. commit
8. (throttled) deploy + IndexNow

## Loop-continuation rule (for any future session)
NEVER end a processing turn without either dispatching the next wave OR scheduling a
wakeup - a wave must always be in flight so completions keep waking the orchestrator.
Read this ledger first, then dispatch the next pending batch's pools. Stop at target
or on Aditya's halt. Deploy+IndexNow stays THROTTLED/held until Aditya's velocity call.

## Progress: 332 / ~500   (baseline 183)

## VIRAL BROWSE shipped 2026-06-09 (commit 3b80448, pushed, NOT deployed)
Genre data 267/267 (Wikidata P136+P31 via harvest_genres.py + curated seed). /series is
now a faceted browse (genre/platform/country/status/era + sort + title search, SSR cards +
hydrated filters). Recency-first: getSeriesByRecency/seriesRecency/isFreshSeries; home "Just
Dropped" rail. NEW + BollyMeter badges. Fixed --font-mono->--font-number. genres in Series
type + AUTHORING_BRIEF (future waves self-tag). validate baseline now 267/267.

## OPEN: (1) DEPLOY held pending Aditya velocity call (nothing live since launch's 183).
## OPEN: (2) hourly fresh-context cron (Aditya asked) - design pending his go.
## Autonomous wave loop PAUSED at 267 (was Opus-in-session; resumes via cron or manual).

## Batches
### Batch 04 — 2026-06-09 — 30 series — STATUS: DONE (commit af8550b pushed; 302->332)
- **R** K-drama romance/fantasy: my-love-from-the-star · secret-garden · pinocchio-kdrama · fight-my-way · vagabond-kdrama · suspicious-partner
- **S** US prestige/FX/HBO: the-americans · atlanta · the-handmaids-tale · boardwalk-empire · justified · six-feet-under
- **T** Anime: violet-evergarden · toradora · 86-eighty-six · fruits-basket-2019 · your-lie-in-april · berserk-1997
- **U** UK/Euro/HBO limited: unorthodox · mare-of-easttown · the-night-of · misfits · downton-abbey · doctor-foster
- **V** Indian OTT: four-more-shots-please · bombay-begums · mismatched · scam-2003-the-telgi-story · sunflower · hostel-daze

### Batch 03 — 2026-06-09 — 30 series — STATUS: DONE (commit 77c64c8 pushed; 267->297)
- **M** K-drama recent/crime: juvenile-justice · through-the-darkness · happiness-kdrama · jirisan · the-silent-sea · celebrity
- **N** Netflix/Western: the-haunting-of-hill-house · midnight-mass · never-have-i-ever · daredevil · outer-banks · suits
- **O** Anime: neon-genesis-evangelion · sword-art-online · that-time-i-got-reincarnated-as-a-slime · golden-kamuy · banana-fish · overlord
- **P** European/British: killing-eve · luther · borgen · the-bureau · the-bridge · vis-a-vis
- **Q** Indian: jamtara · leila · ghoul · ic-814-the-kandahar-hijack · bard-of-blood · undekhi

### Batch 02 — 2026-06-09 — 42 series — STATUS: DONE (commit 7ee927d pushed; 225->267)
### Batch 02 (orig plan) — authoring
- **G** K-drama action: vigilante · song-of-the-bandits · bloodhounds · chicago-typewriter · kill-me-heal-me · the-atypical-family · a-shop-for-killers
- **H** K-drama recent/romance: w-two-worlds · while-you-were-sleeping · doctor-slump · weak-hero-class-2 · light-shop · the-frog · crash-course-in-romance
- **I** Netflix Western: you · cobra-kai · the-lincoln-lawyer · the-sandman · griselda · kaos · the-residence
- **J** HBO/Apple prestige: big-little-lies · the-leftovers · watchmen · barry · euphoria · the-morning-show · for-all-mankind
- **K** Anime: bocchi-the-rock · kaguya-sama-love-is-war · dr-stone · the-promised-neverland · haikyu · mushoku-tensei · delicious-in-dungeon
- **L** Indian/World: bambai-meri-jaan · rana-naidu · inside-edge · the-empress · maxton-hall · 1670 · call-my-agent

### Batch 01 — 2026-06-09 — 42 series — STATUS: DONE (commit 26c8ac6 pushed; 183->225; validate 42/42, build green, 150 pytest)
- **A** K-drama recent: when-life-gives-you-tangerines · the-trauma-code · weak-hero-class-1 · reborn-rich · little-women-2022 · the-devil-judge · my-demon
- **B** K-drama prestige: my-liberation-notes · beyond-evil · flower-of-evil · hotel-del-luna · the-uncanny-counter · the-red-sleeve · our-beloved-summer
- **C** Netflix/Western: the-queens-gambit · beef · the-diplomat · the-night-agent · 3-body-problem · bridgerton · the-gentlemen
- **D** Anime: my-hero-academia · blue-lock · oshi-no-ko · jojos-bizarre-adventure · made-in-abyss · re-zero · the-apothecary-diaries
- **E** UK/Euro: sex-education · line-of-duty · happy-valley · normal-people · 1899 · the-day-of-the-jackal · broadchurch
- **F** Indian/World: heeramandi · mumbai-diaries · tvf-pitchers · poacher · money-heist-korea · suburra · shtisel
