# BollyAI Interactive Tools Data Notes

Scope for this lane: Seat 08 top two static tools, Hit-Flop Verdict Calculator and X-vs-Y Box Office Comparator.

## Current data used

- Calculator options come from `data/films/*.json`.
- Prefilled gross uses `box_office.totals.worldwide_gross_inr_cr` when present.
- Budget prefill is used only when `budget` is present in the film JSON.
- Comparator options use only `box_office.day_rows[]` entries where `day > 0` and `net_inr_cr.value` is published.
- Comparator cumulative values are derived by summing the published low/high India nett ranges. No missing day is interpolated.

## Tracking states

- Current film records expose pair-verified box-office ranges more often than first-party budgets, so the calculator asks for budget input when a film budget is undisclosed.
- The default 0.45 distributor-share ratio is an assumption. Any output using it renders as a verdict band.
- Worldwide day-wise gross and footfalls are disabled in the comparator until Seat 03 emits those fields.
- Calendar-aligned comparison can be sparse unless both films share overlapping published dates.

## Seat 03 data-fill steps

1. Add `budget { value, source, fetched_at, confidence, first_party }` only when a first-party or defensible trade source exists.
2. Add optional `box_office.share_ratio { value, source, fetched_at, confidence }` when a film-specific distributor share is sourced.
3. Continue emitting `box_office.day_rows[] { day, date, net_inr_cr, sources, label }` with the existing two-source publish rule.
4. Add `box_office.day_rows[].ww_gross_cr` only when day-wise worldwide gross clears the same publish rule.
5. Add `box_office.day_rows[].footfalls` only when the ATP source and admissions calculation are explicit.
6. Keep unverified figures out of the published value fields. Use null plus a clear tracking label instead.
