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

## Progress: 482 / ~500   (baseline 183)

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
### Batch 09 — 2026-06-09 — 30 series — STATUS: DONE (commit PENDING; 452->482)
- **QQ** K-drama romance/historical: forecasting-love-and-weather · defendant · when-the-camellia-blooms · law-school · love-in-the-moonlight · my-perfect-stranger
- **RR** US prestige drama: twin-peaks · friday-night-lights · american-horror-story · yellowstone · billions · the-outsider
- **SS** Anime: noragami · kill-la-kill · tokyo-revengers · wonder-egg-priority · dororo · yuri-on-ice
- **TT** UK/Euro/Scandinavian: vikings · wolf-hall · the-missing · catastrophe · humans · emily-in-paris
- **UU** Indian + World: college-romance · the-fame-game · rudra-the-edge-of-darkness · ripley · all-the-light-we-cannot-see · bodies

### Batch 08 — 2026-06-09 — 30 series — STATUS: DONE (commit cb25f3c pushed; 422->452)
- **LL** K-drama romance/supernatural: memories-of-the-alhambra · doom-at-your-service · the-penthouse-war-in-life · romantic-doctor-teacher-kim · sisyphus-the-myth · under-the-queen-umbrella
- **MM** US prestige drama: halt-and-catch-fire · rome · the-shield · sharp-objects · the-knick · rectify
- **NN** Anime: ping-pong-the-animation · land-of-the-lustrous · vivy-fluorite-eyes-song · to-your-eternity · lycoris-recoil · summertime-rendering
- **OO** UK/Euro/Scandinavian: the-night-manager · the-office-uk · the-inbetweeners · the-killing · skam · spiral
- **PP** Indian + World: breathe-into-the-shadows · guilty-minds · a-suitable-boy · wentworth · top-of-the-lake · tvf-cubicles

### Batch 07 — 2026-06-09 — 30 series — STATUS: DONE (commit a44f436 pushed; 392->422)
- **GG** K-drama romance/historical: reply-1994 · navillera · weightlifting-fairy-kim-bok-joo · moon-lovers-scarlet-heart-ryeo · inspector-koo · our-blues
- **HH** US prestige: band-of-brothers · deadwood · abbott-elementary · blue-eye-samurai · gen-v · the-pacific
- **II** Anime: assassination-classroom · erased · parasyte-the-maxim · beastars · blue-period · mushishi
- **JJ** UK/Euro: the-last-kingdom · peep-show · ragnarok-2020 · the-returned · afterlife · ganglands
- **KK** Indian+World: khakee-the-bihar-chapter · mai-2022 · yeh-kaali-kaali-ankhein · taaza-khabar · blood-and-water · katla

### Batch 06 — 2026-06-09 — 30 series — STATUS: DONE (commit cfb2a9d pushed; 362->392)
- **BB** K-drama crime/thriller: voice-kdrama · one-ordinary-day · thirty-nine · divorce-attorney-shin · bad-and-crazy · grid
- **CC** US prestige drama/comedy: station-eleven · this-is-us · dopesick · the-terror · greys-anatomy · community
- **DD** Anime: madoka-magica · clannad · gurren-lagann · tokyo-ghoul · no-game-no-life · anohana
- **EE** UK/Euro prestige: years-and-years · skins · utopia-uk · the-thick-of-it · taboo · derry-girls
- **FF** Indian + World: aranyak · permanent-roommates · tanaav · human-india · aashram · yeh-meri-family

### Batch 05 — 2026-06-09 — 30 series — STATUS: DONE (commit 30512cc pushed; 332->362)
- **W** K-drama romance/slice-of-life: the-world-of-the-married · reply-1997 · nevertheless · romance-is-a-bonus-book · be-melodramatic · love-alarm
- **X** US drama/comedy classics: the-office-us · parks-and-recreation · homeland · the-good-place · arrested-development · american-crime-story
- **Y** Anime: samurai-champloo · great-pretender · odd-taxi · pluto-2023 · ranking-of-kings · nana
- **Z** UK/Europe prestige: the-young-pope · my-brilliant-friend · deutschland-83 · the-end-of-the-f-ing-world · giri-haji · the-fall
- **AA** Indian + World: she · little-things · 3-percent · who-killed-sara · cable-girls · dark-desire

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
