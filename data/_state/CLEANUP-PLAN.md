# BollyAI Pre-Existing Fabrication CLEANUP (2026-06-14 - Aditya chose Strip+Regen)

268 of 559 live series FAIL the new attribution gate (full list: data/_state/preexisting-fabrication-audit.md).
Two tracks, BOTH gate-protected. The FLOOR reconciles + ships waves; lanes never build/commit/deploy.

## TRACK A - REGEN (failing series that HAVE subtitle grounding, ~/bollyai-subs/series/)
Regenerate clean rich v3 via scripts/subtitles/build_review.py (5 endpoints FULL/NANO/MINI/KIMI/DSV4,
v3 house-style) -> python3 scripts/batch/validate_series.py <slug> must exit 0.

## TRACK B - STRIP (failing series WITHOUT subs)
scripts/cleanup/strip_attribution.py (work:7 builds it): for each prose field that fails the gate,
NANO-rewrite (gpt-5.4-nano) to REMOVE every critic/audience/reviewer attribution while keeping
BollyAI's OWN disclosed analysis of the real beats - grammatical, no dangling fragments, NO invented
reception -> re-gate -> iterate once -> NULL the field only as last resort.

## RULES (hard)
- NEVER keep a file that fails validate_series (the attribution gate is build-breaking).
- NO per-lane npm build / git commit / deploy. The FLOOR reconciles: gate EVERY changed file (exit 0)
  -> pytest -> ONE central npm build -> wrangler deploy -> IndexNow <=85 -> push, in WAVES.
- verify-or-strip, no em-dash, all 10 honesty fences. Report per batch:
  conductor outcome bollyai done "track-X: <series + result>".
