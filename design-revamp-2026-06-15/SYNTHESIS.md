# BollyAI Redesign — LOCKED DIRECTION (synthesis of the 10-Opus team)

**Date:** 2026-06-15 · Orchestrated by Vyom · 10 Opus lenses, near-unanimous convergence.

## The one-line reframe (all 10 lenses agree)
Stop imitating a streaming **rail-wall** (a game BollyAI can't win — incomplete posters, no fake
social proof allowed). Become **"THE FRIDAY VERDICT" — an honest decision instrument you operate**,
led by the verdict, with the honesty discipline turned into the visible aesthetic. The homepage should
*say its own tagline* ("Har Friday ka faisla") in one glance — today it whispers it as wallpaper.

## Convergence map (how many of the 10 independently demanded each move)
| Move | Lenses | Status |
|---|---|---|
| Kill the 9-tile bento → ONE full-bleed **Verdict Stage** hero | **10/10** | LOCK |
| **BollyMeter** promoted from badge → hero **medallion/dial** (the signature) | 01,02,04,05,08,10 | LOCK |
| **Honesty as visible aesthetic** (badge strip + "Verdict Receipt") | 02,04,08,10 | LOCK |
| Collapse **10 sections → 6** descending-priority funnel; cut nav 11→5 | 09,10,05 | LOCK |
| Native-CSS **View Transitions** (poster→hero morph) + scroll reveals | 03,05,06,07 | LOCK |
| **Neutralize muddy indigo bg → near-black**; scarce hot accent | 05,01,03 | LOCK |
| **Typographic "BollyAI Edition" one-sheet** replaces monogram | 05,06 | LOCK |
| **localStorage diary / "your verdict vs BollyMeter"** retention loop | 01,04,08 | LOCK (phased) |
| Client-side **ask bar** = answer-engine identity in 5s | 09,10 | LOCK (phased) |
| Stay **Next 14.2**; latest-UI = the CSS platform, not a framework bump | 06 | LOCK |

## Hard asset reality (verified this session — shapes the whole design)
- Films: 62 titles, **only 21 have real posters** (41 are monograms). Series: 559, **464 posters** (83%).
- **Backdrops: 1 on the entire site.** → The billboard hero CANNOT use backdrops.
  **SOLUTION:** hero = the real **portrait poster as a hero object** + a heavily-blurred, scaled copy
  of the same poster filling the full bleed (ambient "backdrop-from-poster") + scrim. Zero new assets.
- Harvester can't cheaply fix the gap (last sweep 0/55 — remaining titles have no Wikipedia poster).
  → The **typographic one-sheet IS the answer**: make poster-absence an ownable house style.

## PHASE 1 — "Make it look world-class" (THIS session; the literal complaint)
1. **`VerdictStage` hero** — full-bleed 78vh/68vh, poster-as-keyart + ambient blur + scrim, lower-left
   editorial composition: dated masthead → desk eyebrow → Fraunces H1 `clamp(3.2rem,8vw,7rem)` opsz-max
   → verdict-as-answer line → BO chip w/ "2 sources ✓" → ONE CTA. **BollyMeter dial** bottom-right.
   Honesty badge strip. Lead curated to a poster-bearing title. Desk-accent bound to lead industry.
2. **Art-direction token pass** — bg indigo→near-black graphite (chroma .025–.045 → .005–.012); accent
   .16→.19 + `--accent-hot` .225 used on ≤3 elements/viewport; strip accent off borders/placeholders;
   remove the 8px banding bg; reduce/scope grain off weak images; spacing scale `--space-section`.
3. **`BollyMeterDial`** reusable component (hero + card sizes) — conic-gradient ring, JetBrains number,
   ladder word, basis line; count-up + arc-fill on reveal.
4. **"BollyAI Edition" one-sheet placeholder** — Fraunces title + desk color bar + embossed score +
   year/industry in mono + faint reel watermark. Kills the monogram cheapness site-wide.
5. **Motion layer (pure CSS, ₹0)** — `@view-transition{navigation:auto}` poster→hero morph; scroll
   reveals `animation-timeline:view()`; 3-channel card hover (lift −6px, poster zoom 1.06, accent glow);
   bar-grow `scaleX`; verdict stamp −3° overshoot. Tokens `--ease-out`/`--ease-spring`. All `@supports`
   + `prefers-reduced-motion` gated. Refactor globals.css into `@layer`.
6. **Structure pass** — collapse toward the 6-section funnel; de-duplicate the 3–4 desk-nav repeats.
7. **PosterImage perf** — `fetchpriority`/`decoding`/`loading` + hero preload (LCP).
8. **Lightweight retention seeds** — honesty trust-chip cluster; BollyMeter-as-event reveal; localStorage
   Watchlist toggle on cards; "new verdicts since you were here" Friday ribbon.

## PHASE 2 — "Make them stay" (scoped follow-on, needs Aditya's go)
- Full **localStorage Diary** `/meri-diary` + **"Your Friday Court"** (cast your 0-10 vs BollyMeter,
  persistent self-portrait, copy-to-clipboard "my BollyAI year") — the un-leaveable retention loop.
- **Ask bar** answer-engine: client-side fuzzy over build-time index → verdict + where-to-watch inline.
- **"Verdict Receipt"** interaction: tap any figure → 2 sources + divergence% + timestamp + QID.
- **Title-page score-stack masthead** + **day-wise box-office table** w/ source chips (beat Sacnilk/Koimoi).
- **"BollyAI Wrapped"** Jan virality share-card. **`/friday`** dated drop + `.ics` appointment.
- Next 15 / React 19 bump as an isolated tests-green PR.
- Tentpole **poster/backdrop harvest** (Pushpa 2, Kalki, Dune 2, Deadpool…) — official press, attributed.

## Hard fences honored throughout
Static export · ₹0 · no login (localStorage only) · no TMDB/IMDb/Letterboxd images · no AggregateRating ·
no fabricated numbers · no em-dash · no AI-slop (keep bespoke OKLCH+Fraunces, no Tailwind/framer/shadcn) ·
design-reviewer ≥7.5 + tests + build green before ship.
