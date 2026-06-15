# Lane Report: bolly-depth-B (episode review deepening)

**Date:** 2026-06-15
**Worker:** 1 of 1
**Slug set:** black-mirror, hellbound, sweet-home, fauda, emily-in-paris, peaky-blinders, sacred-games, better-call-saul

All 8 subtitle-grounded series deepened with full Mode B craft reviews (BollyAI's own disclosed analysis, no fabricated reception attribution). Pipeline used: `nano_draft.py --force` (gpt-5.4-nano, 250 RPM, azure-cog) for all series; Azure gpt-5-4 was 429-throttled throughout. Sacred-games additionally receiving dossier-grounded upgrade pass (build_review.py via NANO, 2-pass draft + edit) which was running at report time.

---

## Results

| Series | Episodes | New Reviews | Validate | Notes |
|--------|----------|-------------|----------|-------|
| black-mirror | 33/33 | 33 | PASS | 1200-1416 words, em=0 |
| hellbound | 12/12 | 12 | PASS | 1287-1534 words, em=0; 1 rate-limit backoff handled |
| sweet-home | 26/26 | 26 | PASS | 1095-1733 words, em=0 |
| fauda | 55/55 | 55 | PASS | 997-1713 words, em=0; S03E05 failed first pass (timeout), recovered on retry; S02E07 recovered from 179w to 1128w |
| emily-in-paris | 40/40 | 40 | PASS | 1022-1731 words, em=0 |
| peaky-blinders | 36/36 | 36 | PASS | 964-1695 words, em=0 |
| sacred-games | 16/16 | 16 | PASS | 1199-1680 words (nano_draft); 2/16 dossier-grounded upgrade in progress |
| better-call-saul | 63/63 | 63 | PASS | 1156-1591 words, em=0 |
| **Total** | **281/281** | **281** | **8/8 PASS** | |

---

## Validation

All 8 series passed `python3 scripts/batch/validate_series.py`:

```
8/8 clean, 0 failed
PASS black-mirror
PASS hellbound
PASS sweet-home
PASS fauda
PASS emily-in-paris
PASS peaky-blinders
PASS sacred-games
PASS better-call-saul
```

---

## Quality signal

- Em-dash density: 0 across all 281 generated reviews (nano_draft enforces em=0 per house-style v4)
- Attribution violations: 0 (validate_series.py checks attribution_regex.py; all PASS)
- Word count floor: all reviews >= 964 words; 1 short review (fauda S02E07, 179w) recovered to 1128w on retry
- Review mode: Mode B throughout (BollyAI's own craft analysis, no fabricated critic/audience consensus)
- Voice markers: bold first-mention of characters, evocative subheads, jagged rhythm, verdicts that argue

---

## Pipeline notes

- **Azure gpt-5-4 (regen_batch):** 429 on every attempt (series_start → ep_FAIL cycle). Both FULL and KIMI endpoints throttled.
- **Fallback:** `nano_draft.py --force` (gpt-5.4-nano, 250 RPM) - 100% reliable, 5 parallel workers per slug.
- **Dossier extractions:** Running in background (hellbound, sweet-home, peaky-blinders, better-call-saul). Sacred-games has 16/16 dossiers ready; dossier-grounded regen (BOLLYAI_DRAFT_MODEL=NANO BOLLYAI_FINAL_MODEL=NANO via regen_batch.py) upgrading sacred-games at time of report.
- **fauda S05:** Subtitle dossiers existed for S05E01-05 only; nano_draft covered all 55 episodes across all seasons from model knowledge (fauda is a well-documented Israeli series).

---

## One thing least sure about

fauda episode titles: the series JSON uses generic "Episode N" titles for most episodes (no official episode names in data). The reviews are grounded in known plot beats per episode, but if BollyAI's model knowledge of fauda S03/S04/S05 episode-level beats is thin, some Mode B reviews may be less episode-specific than ideal. S03E05 failed on first attempt (TimeoutError), recovered on retry with 1329 words.

---

**Delivered:** 281 deepened episode reviews across 8 series. All validate PASS. Em-dash count: 0.
