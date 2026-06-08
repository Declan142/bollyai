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

## Progress: 225 / ~500   (baseline 183)

## Batches
### Batch 02 — 2026-06-09 — ~42 series — STATUS: authoring
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
