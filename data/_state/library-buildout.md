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

## Batches
### Batch 01 — 2026-06-09 — 42 series — STATUS: authoring
- **A** K-drama recent: when-life-gives-you-tangerines · the-trauma-code · weak-hero-class-1 · reborn-rich · little-women-2022 · the-devil-judge · my-demon
- **B** K-drama prestige: my-liberation-notes · beyond-evil · flower-of-evil · hotel-del-luna · the-uncanny-counter · the-red-sleeve · our-beloved-summer
- **C** Netflix/Western: the-queens-gambit · beef · the-diplomat · the-night-agent · 3-body-problem · bridgerton · the-gentlemen
- **D** Anime: my-hero-academia · blue-lock · oshi-no-ko · jojos-bizarre-adventure · made-in-abyss · re-zero · the-apothecary-diaries
- **E** UK/Euro: sex-education · line-of-duty · happy-valley · normal-people · 1899 · the-day-of-the-jackal · broadchurch
- **F** Indian/World: heeramandi · mumbai-diaries · tvf-pitchers · poacher · money-heist-korea · suburra · shtisel
