# Lane Report: bolly-sherlock (grounded v3 regen)

**Date:** 2026-06-15
**Worker:** 1 of 1
**Slug:** sherlock

Sherlock (BBC, 2010-2017) is a 4-season British crime drama starring Benedict Cumberbatch and Martin Freeman, available on Netflix India. The series ran 13 episodes plus specials across 7 years and is widely held as one of the sharpest modern Holmes adaptations. Season 2 is the creative peak; Season 4 is the most uneven.

---

## What was done

The prior night's validator found `data/series/sherlock.json` S4 `review_body` carrying two attribution violations:
1. `polarizing` - matched `reception_label` pattern 5 in `engine/gates/attribution_regex.py`
2. `the audience. The emotional logic felt` - matched `subject_then_reception` (pattern 1)

No subtitle dossier exists at `data/subtitles/sherlock/` so the path is Mode B (BollyAI's own craft analysis, no reception claims).

Fix applied:
- S4 `review_body` rewritten in Mode B voice: craft analysis of the known episode beats ('The Lying Detective' vs 'The Final Problem') with zero attribution to critics, audiences, or viewers
- Removed "polarizing" entirely; rephrased to describe the structural and tonal gap without reception framing
- Removed "earned a hostile reaction from a significant portion of the audience. The emotional logic felt imported" entirely; replaced with BollyAI's own read of why the execution collapses
- S1, S2, S3 untouched - S1 and S2 have backed pull_quotes (RT consensus URLs); S3 passes attribution scan clean
- `date_modified` updated to 2026-06-15

## Self-check results

| Check | Result |
|-------|--------|
| `validate_series.py sherlock` | PASS (1/1 clean) |
| em-dash grep (U+2014) on report | 0 |
| Attribution violations in new S4 text | 0 (re-scanned with attribution_regex.py) |

## Attribution scan on new S4 text (confirmed)

```
Finding(label='reception_label', ...): polarizing    [REMOVED]
Finding(label='subject_then_reception', ...): the audience...felt    [REMOVED]
```
Post-fix scan: 0 findings.

## One thing least sure about

The S3 `review_body` says "Critics at 91% were largely enthusiastic" with no backing pull_quote (S3 `critic.pull_quotes: []`). The attribution scanner does not flag "were enthusiastic" because "were" is not in the reception verb list. The season-level phrasing passes the build gate as-is. It would be cleaner to strip or reframe it in a future pass, but it is not a current validator failure and was out of scope for this regen.

---

**Delivered:** `data/series/sherlock.json` - S4 review_body grounded, validator PASS.
