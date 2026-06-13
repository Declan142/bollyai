# BollyAI "build all new" campaign (Aditya 2026-06-13 "sab build kar saari new series + new movies")

## Gap (codex-discovered + deduped vs catalog)
- 13 NEW series + 40 NEW films + ~20 new-SEASONS of existing series.
- Grounded only (no TMDB live; codex web-research is the discovery substitute). No fabrication.

## In-flight jobs
- **Batch-1 series reviews**: bg `bls2siyl9` (regen_batch landman the-madison lioness
  mayor-of-kingstown the-pitt; Azure serial). Auto-notifies. gpt-5.5-retry the content-filter
  fails (violent: landman/lioness/mayor-of-kingstown).
- **40-film authoring**: codex `20260613T110514Z_code_main_drm5ln4u` (workdir ~/bollyai,
  fenced to data/films/). NO auto-announce - poll `gpt status <id>`. Then validate_films +
  claim-verify-gate (box_office/bollymeter) before commit.

## Done
- Original 6 series (50 eps rich) + 2 fixes LIVE on bollyai.in earlier (436e3e1).
- Batch-1 series (5) authored + validated + committed+pushed **f7d82ae** (structure +
  metadata, review_body building now). + teach-you-a-lesson +2 reviews.

## Subs state (13 new series)
- GOT: landman(10) the-madison(8) lioness(9) mayor-of-kingstown(10) the-pitt(12)
  the-studio(1) mr-and-mrs-smith(12) nobody-wants-this(10).
- NOT yet (re-fetch needed): the-perfect-couple, indian-police-force, call-me-bae,
  kerala-crime-files, save-the-tigers.

## Pending (next batches)
1. Deploy batch-1 (series reviews + films) when both jobs land + gated.
2. Author remaining 8 new series (the-studio, mr-and-mrs-smith, nobody-wants-this +
   the 5 no-subs ones) via FRESH lanes (4/lane max - ctx blows past that).
3. New-SEASONS expansion for existing-series demand titles (Squid Game S2/S3, Stranger
   Things 5, Wednesday S2, Severance S2, Mirzapur S3, Panchayat S3/S4, Paatal Lok S2,
   Suzhal S2, House of the Dragon S2, The Boys S4, The Bear S3/S4, etc.) - episode-expansion.
4. Multi-season subs: landman S2 / lioness S2 / mayor S2-4 only have S1 subs so far.

## Fences (unbroken)
grounded+verify-or-strip · no em/en dash · bollymeter null-or-full · box_office pair-verify ·
fence#10 skip-if-thin · gpt-5.5 for violent (Azure content-filter) · deploy=standing-grant
(gates=approval) · IndexNow 55/wave cap · force-push DENIED · build_review = only write-path.
