# Draft Triage Checkpoint — 2026-06-13 (updated)

## Completed this session

### sweet-magnolias-season-5 G4 voice-pass (conductor task)
- 7/10 PASS, 3 FAIL (E01: 37w sentence; E06: vague hook; E07: cinematography violation)
- bollymeter null all 10, critic_note null all 10
- Dry-run merge: 7 eligible (E02-E05, E08-E10) -> seasons[1].episode_reviews
- Action: floor runs `python3 scripts/subtitles/merge_reviews.py sweet-magnolias-season-5 --apply`

### CLOY G4 (prior session, completed)
- Dry-run merge: 12 new eligible (E2-E6, E8-E12, E14-E15), 4 already live skip
- Action: floor runs `python3 scripts/subtitles/merge_reviews.py crash-landing-on-you --apply`

### every-year-after (prior session, authored + validated)
- QID Q138773730, Amazon Prime Video, limited, en, RT 70%/23, Meta 56/100
- Action: floor G4 on 8 drafts then merge

## i-will-find-you - 11/12 episodes staged
- Series JSON: SKIPPED (mixed subtitle data - see below; honesty fence blocks authoring)
- Dossiers: 12 (S01E01-S01E12)
- episodes.json: 11 reviews written (E01-E11), E07 verdict=fail, E12 missing
- DATA FLAG: SRT files appear to be from multiple different shows (E01 = American comedy,
  E02/E04 = Chinese real estate drama with "Fang Si Jin", E03 = "Mike & Molly"-style content).
  Best Wikidata match Q134412018 premieres June 18 with only 8 episodes - does not match.
  QID cannot be confidently assigned. Series JSON skipped per honesty fence.
- On next run (new draft_reviews.py fix): will keep E01-E06/E08-E11 (pass), retry E07 + draft E12
- Action (after 05:30 reset): `python3 scripts/subtitles/draft_reviews.py i-will-find-you`
  Then G4 voice-pass + dry-run merge (floor applies)

## Engineering fix committed (7c86e43)
- draft_reviews.py: incremental writes after every episode (finally block), per-episode
  try/except with failures list, re-runnable dedup (keeps only verdict=pass), flush=True
- orfree.py: requests_today() fixed to exclude phantom entries (winner events + g1_schema_fail
  re-logs that were inflating count 2x)
- Real quota metric: use `grep -c $(date -u +%Y-%m-%d) data/subtitles/_engine/orfree-log.jsonl`
  for raw count, or the python3 orfree.requests_today() which is now accurate

## QUOTA HALT - 2026-06-13
- Real API calls today: 1107 / 1000 OpenRouter free tier
- Blown by: multiple parallel background re-runs during diagnosis (blind re-runs before fix)
- Reset: 05:30 IST 2026-06-14

## ACTIVE QUEUE (resume after 05:30 reset, dedup first each time)
### Priority order (full-season coverage program):
1. i-will-find-you: `draft_reviews.py i-will-find-you` (retry E07 + draft E12, then G4)
2. teach-you-a-lesson: `draft_reviews.py teach-you-a-lesson` (E02-E09 missing, E01+E10 live)
3. widows-bay: fetch S01E07-S01E09 SRTs + dossiers; author series JSON; draft all
4. fauda: check existing reviews in data/series/fauda.json; draft missing only
5. berlin: check existing reviews; draft missing only
6. mirzapur: check existing reviews; draft missing only
7. kingdom: check existing reviews; draft missing only
8. house-of-the-dragon: check S03 SRTs exist; draft missing S01/S02/S03
9. 4 films: `draft_reviews.py --film <slug>` (check --film flag exists first)

### DEDUP RULE (mandatory, wasted a full run on 'from'):
Before any draft run, python3 -c "import json; d=json.load(open('data/series/<slug>.json'));
print(sum(len(s.get('episode_reviews',[]) or []) for s in d.get('seasons',[])))"
If existing reviews >= all dossiers, SKIP the slug entirely.

### from - ABANDONED (already has 37 reviews in data/series/from.json, no gap to fill)
- Do NOT draft from again.

## Quota tracking (correct method after orfree.py fix)
Real API requests today: `python3 -c "import sys; sys.path.insert(0,'scripts/subtitles'); import orfree; print(orfree.requests_today())"`
Guard: 880 actual API requests. Hard orfree limit: 900. Stop before 880.
