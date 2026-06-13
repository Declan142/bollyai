# Draft Triage Checkpoint — 2026-06-13

## CLOY G4 (completed, conductor task)
- 16/16 voice_pass stamped
- E12 verdict: label: absent from file (pre-stripped)
- Dry-run merge: 12 new eligible (E2-E6, E8-E12, E14-E15), 4 already live (E1/E7/E13/E16 skip)
- Action: floor runs `python3 scripts/subtitles/merge_reviews.py crash-landing-on-you --apply`

## Phase 1 - DONE

### every-year-after
- `data/series/every-year-after.json` authored and validated
- QID: Q138773730, Amazon Prime Video, limited, en, RT 70%/23 critics, Meta 56/100
- Status: validate PASS, 256/256 pytest PASS
- Action: floor runs G4 on 8 drafts (episodes.json exists but no voice_pass yet) then merges

### sweet-magnolias-season-5
- `data/series/sweet-magnolias-season-5.json` authored and validated
- QID: Q56800842, Netflix, running, en, S5 premiered 2026-06-11, verdict null (1 review)
- Status: validate PASS
- Action: floor runs G4 on 10 drafts then merges

## Phase 2 - DEFERRED (quota blown: 1578/900 today, resets 05:30 IST 2026-06-14)

### from (slug: from)
- Series JSON: EXISTS (data/series/from.json)
- Dossiers: 18 (incl meta files), reviews: 0
- Action: draft 16 episode reviews after quota reset

### teach-you-a-lesson
- Series JSON: EXISTS (data/series/teach-you-a-lesson.json)
- Dossiers: 12, reviews: 0
- Action: draft 12 episode reviews after quota reset

### i-will-find-you
- DATA QUALITY FLAG: subtitle directory contains mixed episodes from multiple different shows
  - E01: American comedy (Emet, dance team, sabotage)
  - E02: Chinese drama (Ms. Fang, real estate)
  - E03: Different American comedy (Mike + Molly, scissors)
  - Inconsistent character universe = cannot author coherent series JSON
- Action: Aditya to investigate subtitle collection; skip until resolved

### widows-bay
- Series JSON: MISSING
- Dossiers: 6/9 SRTs, 6 dossiers ready
- Action: fetch 3 remaining SRTs + dossiers after quota reset, then draft + author

### house-of-the-dragon
- Series JSON: EXISTS (data/series/house-of-the-dragon.json)
- HotD dossiers: S01 (9 ep) + S02 (7+ ep) confirmed, S03 status unknown
- Action: check if S03 SRTs exist; draft S3 after quota reset

## Next run checklist (after 05:30 IST 2026-06-14)
1. `python3 scripts/subtitles/merge_reviews.py crash-landing-on-you --apply`  (floor)
2. G4 + merge every-year-after 8 drafts  (floor)
3. G4 + merge sweet-magnolias-season-5 10 drafts  (floor)
4. Draft `from` 16 reviews
5. Draft `teach-you-a-lesson` 12 reviews
6. Check widows-bay SRT completeness; draft+author when complete
7. Investigate i-will-find-you subtitle data quality
