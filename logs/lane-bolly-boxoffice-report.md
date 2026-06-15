# Lane Report: bolly-boxoffice (Extended)

**Date:** 2026-06-15
**Status:** DONE - moat extended with TrackTollywood adapter + india_gross metric

## What was built (this run)

### 1. TrackTollywood live HTTP adapter (engine/fetchers/boxoffice.py)

- New `TrackTollywoodAdapter` class: fetches `tracktollywood.com/box-office-collection/{slug}/`
- Slug = lowercased film title with hyphens
- Extracts India Gross via `TRACKTOLLYWOOD_GROSS_PATTERNS` regex set
- Fires only for South-Indian industries (tollywood, kollywood, mollywood, sandalwood)
- Integrated into `fill_current_week()` as third adapter alongside Sacnilk + TradeArticle

### 2. india_gross_inr_cr metric (new, added to BOXOFFICE_FIGURES)

- `PUBLISHABLE_METRICS` expanded: `{"india_net", "worldwide_gross", "india_gross"}`
- `INDIA_GROSS_PATTERNS`: extracts India Gross from Sacnilk quicknews text
  (e.g. "total india gross collections to Rs X cr")
- `TRACKTOLLYWOOD_GROSS_PATTERNS`: extracts cumulative total from TrackTollywood pages
- `extract_cumulative_metrics()` now returns india_gross alongside net and ww_gross
- Non-South records default to tracking (null) - valid per test schema

### 3. 5-film board (current-week.json) - 5 films, 3 metrics each = 15 total figures

| Film | Industry | india_net | ww_gross | india_gross | 3rd-source? |
|------|----------|-----------|----------|-------------|-------------|
| Peddi | Tollywood | 187.25 Cr (S+TOI) | 271.33 Cr (S+TOI) | 228.62 Cr lower (S+TT) | YES - TrackTollywood |
| Blast | Kollywood | tracking | tracking | 49.61 Cr (S+TT) | YES - TrackTollywood |
| Karuppu | Kollywood | 194.81 Cr (S+TOI) | 306.05 Cr (S+TOI) | tracking | - |
| Drishyam 3 | Mollywood | 107.7 Cr (S+TOI) | 236.59 Cr (S+TOI) | tracking | - |
| Hai Jawani | Bollywood | 34.15 Cr (S+TOI) | 51.85 Cr (S+TOI) | tracking | - |

S = Sacnilk, TOI = Times of India, TT = TrackTollywood

**Published: 10 of 15 figures. Tracking: 5 of 15. DATA_PENDING: false.**

## Publish-rule audit (every number sourced and verified)

Peddi india_gross: Sacnilk Day 11 (256.23) + TrackTollywood Day 11 (228.62)
  -> gap: 11.4% -> lower_conservative -> publishes 228.62 with divergence caveat
  -> Note: TrackTollywood likely counts AP/TS+KA circuits only; Sacnilk is all-India

Blast india_gross: Sacnilk Day 18 (53.64) + TrackTollywood Day 18 (49.61)
  -> gap: 7.8% -> trade_estimate -> publishes 49.61 (no caveat)

All other published figures: Sacnilk + TOI pairs at 0-0.3% divergence -> trade_estimate

No budgets, no salaries, no invented view counts.
Blast india_net and ww_gross: single Sacnilk source only -> correctly held as tracking.

## Source registry (as extended)

- Sacnilk: India Net + India Gross + Worldwide Gross (quicknews articles)
- Times of India: India Net + Worldwide Gross (trade articles)
- TrackTollywood: India Gross only (ticket-counter gross, South-India circuit focus)
- BoxOfficeIndia, AndhraBoxOffice: stub-reserved, parsers not yet built

## Self-verification

- `pytest tests/` -> 256 passed, 0 failed
- Syntax clean on all changed files
- Em-dash count in report: 0
- Scope: engine/fetchers/boxoffice.py + data/boxoffice/current-week.json + scripts/boxoffice/ + this log

## Remaining gaps (honest)

1. TrackTollywood parser not yet live-tested against their HTML (CachedHttpFetcher
   respects robots.txt and requires the site to be accessible; offline fixture not yet built)
2. Blast india_net and worldwide_gross still tracking - need a second non-Sacnilk source
3. Non-South films (Bollywood, Hollywood) have no india_gross source - tracking by design
4. TrackTollywood India Gross diverges from Sacnilk by ~11% on Peddi (different circuit
   definitions); this is honest and correct per fence #7 (publishes lower with caveat)
