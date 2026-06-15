# Lens 07 — Motion & Micro-interaction Design

## VERDICT (3 sentences max)
BollyAI's single highest-leverage motion move is a **cross-document View Transition that morphs the clicked poster into the next page's hero** — a zero-JS, ~$0, "expensive-feeling" continuity beat that no Indian cinema-answer site ships, and the browser support (Chrome 126+ / Safari 18.2+) is here *today*. Second: replace the existing JS IntersectionObserver stagger with **pure-CSS `animation-timeline: view()` scroll reveals** and add the **signature numeric drama BollyAI is uniquely entitled to** — the BollyMeter score counting up + its arc filling, box-office bars growing from 0, and a verdict "stamp" thunk on reveal. The brand is *editorial authority over numbers*; motion must make those numbers feel **measured and earned**, never decorative — restrained, transform/opacity-only, fully `prefers-reduced-motion`-gated (which this codebase already does well — extend that discipline, don't bolt on slop).

## WHAT THE BEST DO  (named examples + the MECHANISM)
- **Shared-element page morph** — *Apple TV+ / Letterboxd app / iOS App Store* — tapping a poster makes *that exact poster* fly and scale into the next screen's hero instead of a hard cut. Mechanism: the brain reads it as "I zoomed *into* the thing I touched," preserving object permanence and spatial memory → the navigation feels physical, not like a document swap. This is the web's biggest perceived-quality jump for the least code, and it's the move a static cinema site can *uniquely* own.
- **Scroll-driven reveal with restraint** — *Linear, Vercel, Stripe* — sections fade + rise ~16–24px as they enter the viewport, short (~500ms), already settled by the time your eye arrives. Mechanism: motion *confirms* arrival rather than demanding attention; it signals "this site is alive and made with care" subliminally. The failure mode (which they avoid) is long-distance, scrubbed-to-scroll parallax that fights the reader.
- **Numeric count-up as proof-of-rigor** — *Bloomberg, FT, ESPN/Opta, election-night dashboards* — a number that ticks up reads as *computed/measured*, not asserted. Mechanism: the count *is* the credibility cue. For BollyAI — whose entire moat is "earned authority, no fake ratings" — a BollyMeter that *counts to 8.4 and fills its arc* literally performs the brand promise: "we calculated this."
- **Bar-grow-on-reveal** — *trading dashboards, Pudding.cool data stories* — box-office / chart bars animate width 0→value when scrolled into view. Mechanism: growth implies live measurement and momentum; a pre-filled static bar reads as a screenshot. Perfect for BollyAI's "Box Office Now" board.
- **Hover as a 3-channel depth event** — *Disney+, Max, Netflix tiles* — one hover fires *lift + poster-zoom-within-frame + metadata/scrim reveal + faint accent glow* together, ~200–250ms. Mechanism: parallax between the *frame* (lifts) and the *poster inside it* (zooms past the clip mask) manufactures real depth on a flat card — the card stops being a sticker and becomes a window.
- **The "stamp/verdict" punctuation** — *review shows, sports verdicts, Metacritic's color chip* — the single editorial judgment lands with a tiny over-shoot + settle (a rubber-stamp "thunk"), distinct from the ambient reveals. Mechanism: a *different* motion vocabulary marks *the most important pixel on the page*; motion hierarchy = information hierarchy. BollyAI's verdict ladder (`MUST-WATCH`…`DISASTER DROP`) is begging for this.
- **Living "freshness" tell** — *status pages, live-blog "LIVE" dots, exchange tickers* — one slow pulsing dot signals real-timeness. Mechanism: a single ambient loop says "this is current" without a word. BollyAI already ships `.live-dot` `live-pulse 2.4s` — it just needs to be promoted to a recurring brand signature, not a one-off.

## WHERE BOLLYAI FAILS TODAY  (grounded in code + screenshot + live site)
- **Zero route-transition language.** Poster click → hard white-ish document swap. The *most* cinematic, *cheapest* premium move available to a static site is entirely absent. The pieces are even pre-named for it: `.media-card__poster` (source) and `.poster-frame` / `.film-hero` (target) are a ready-made shared-element pair.
- **Stagger is done in JS, not CSS.** The mosaic uses a load-time `@keyframes mosaic-rise` plus `CountUp.tsx` running an `IntersectionObserver` + `requestAnimationFrame` loop (`components/CountUp.tsx`). That's main-thread work and JS shipped for something `animation-timeline: view()` now does natively at 0 JS — and the JS stagger only fires once on load, so cards entering on scroll get *nothing*.
- **Hovers use generic `ease` and only move the frame.** `globals.css:1160` (`.mosaic-lead`), `:1294` (`.mosaic-tile`), `:572` — all `transition: ... .22–.25s ease`. `ease` is the AI-slop default curve; nothing uses a designed cubic-bezier on hover. Worse: `.media-card` (the *rail* card, the most-repeated element on the page) has **no poster-zoom-within-frame** — only `.mosaic-lead`/`.mosaic-tile` zoom (`:1184`, `:1326`). The 30+ rail cards are flat stickers on hover.
- **The signature numbers are static.** `BollyMeter.tsx` renders `{score.toFixed(1)}` as plain text — no count, no arc fill. `.big-board__bar` (`globals.css:1789`) ships pre-filled at its final width — no grow. `.verdict-meter` is an inert SVG. The three most brand-defining, most-screenshotted elements on the entire site have **zero motion**, which is the inverse of where motion budget should go.
- **The one verdict — the whole point of the site ("Har Friday ka faisla") — lands with no punctuation.** `.browse-verdict[data-rung=...]` (`globals.css:2169`) has gorgeous per-rung colors but appears with no entrance. The most important word on the page arrives as silently as the footer.
- **Ambient texture is set-and-forget, not alive.** `hero-drift` Ken Burns (26s) exists but is the *only* ambient loop besides the lone live-dot. The brand "live answer engine" isn't *felt* anywhere except that 8px dot.
- **No `@view-transition` opt-in, no `view()` usage, no designed easing tokens** anywhere in 2971 lines. The motion system is ~4 ad-hoc keyframes, not a language.

## TOP 5 CONCRETE CHANGES  (ranked; each implementable)

**1. Cross-document poster→hero View Transition (THE move).**
Opt both documents in, then name the shared pair so the browser morphs poster→hero automatically:
```css
@view-transition { navigation: auto; }            /* in globals.css, top level */

/* SOURCE: the poster on a card the user clicks */
.media-card__poster,
.mosaic-lead__backdrop { view-transition-name: var(--vt-poster, none); }
/* TARGET: the hero image on the detail page */
.poster-frame img,
.film-hero__backdrop { view-transition-name: var(--vt-poster, none); }

/* Tune the morph: cinematic ease, slightly slow so the "expensive" reads */
::view-transition-group(*) { animation-duration: 420ms; animation-timing-function: cubic-bezier(.2,.7,.2,1); }
::view-transition-old(root) { animation: vt-fade 180ms both; }
::view-transition-new(root) { animation: vt-fade 280ms 60ms both reverse; }
@keyframes vt-fade { from { opacity: 1 } to { opacity: 0 } }
```
The `view-transition-name` **must be unique per element on each page** — set it inline on the *one* poster being navigated from and the *one* hero on arrival (e.g. `style={{ ['--vt-poster' as any]: `poster-${slug}` }}` on the card's poster and on the detail hero). Group/old/new naming pattern per [Chrome's View Transitions guide](https://developer.chrome.com/docs/web-platform/view-transitions). Wrap the whole block in `@supports (view-transition-name: x)`; non-supporting browsers (Firefox) just hard-cut — graceful, zero penalty. **Static-export note:** this is multi-page-app cross-*document* VT — exactly the static-HTML→static-HTML case, no SSR, no JS framework hook needed.

**2. Convert the mosaic stagger + count-up to pure-CSS scroll-driven reveals (`view()`), delete JS.**
Replace the `mosaic-rise` load-stagger AND retire `CountUp.tsx`'s observer with native scroll-timeline:
```css
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    .reveal {                       /* apply to section blocks + rail cards + board rows */
      animation: rise-in linear both;
      animation-timeline: view();
      animation-range: entry 0% entry 55%;   /* settled before fully in view */
    }
    @keyframes rise-in {
      from { opacity: 0; transform: translateY(22px); }
      to   { opacity: 1; transform: translateY(0); }
    }
  }
}
```
Exact spec: **distance 22px** (hero/section) / **14px** (dense rail cards), **easing baked via `animation-range`** not a bezier (scroll timelines are progress-mapped — `linear` keyframe + a tight `entry 0%→55%` range gives the "already arrived" feel), **stagger via per-column `animation-range` offset** inside a rail (`view()` auto-staggers because each card enters at its own scroll position — *free* stagger, no `nth-child` delays). Keep `CountUp.tsx` ONLY for the liveness ribbon numbers (count-up genuinely needs JS interpolation), but gate it behind the same `view()` check so it doesn't double-fire.

**3. Promote card hover to a real 3-channel depth event with designed curves — and give `.media-card` the poster-zoom it's missing.**
Define motion tokens once, then make the *rail* card behave like the mosaic tiles:
```css
:root {
  --ease-out: cubic-bezier(.22,.61,.36,1);   /* already used by mosaic-rise - promote to token */
  --ease-spring: cubic-bezier(.34,1.4,.64,1); /* gentle overshoot for stamps/meter */
  --dur-hover: 220ms;
}
.media-card { transition: transform var(--dur-hover) var(--ease-out), box-shadow var(--dur-hover) var(--ease-out); }
.media-card:hover, .media-card:focus-within {
  transform: translateY(-6px);
  box-shadow: 0 24px 52px oklch(0% 0 0 / .55), 0 0 36px color-mix(in oklch, var(--accent) 22%, transparent); /* accent glow */
}
.media-card__frame { overflow: hidden; }      /* clip mask for zoom-within-frame */
.media-card__poster { transition: transform 420ms var(--ease-out); transform-origin: center 35%; }
.media-card:hover .media-card__poster,
.media-card:focus-within .media-card__poster { transform: scale(1.06); }  /* poster zooms PAST the frame edge */
.media-card__plate { transition: transform var(--dur-hover) var(--ease-out); }
.media-card:hover .media-card__plate { transform: translateY(-2px); }     /* metadata parallax-rises */
```
Exact values: **lift −6px**, **poster zoom 1.06** (frame stays still → real parallax depth), **glow 36px accent@22%**, **hover 220ms / poster 420ms** (frame snaps, image eases slower = premium), curve `--ease-out`. `:focus-within` mirrors hover so keyboard users get it too. Retro-apply the token to `.mosaic-lead:1160` / `.mosaic-tile:1294`, replacing their bare `ease`.

**4. Make the three signature numbers PERFORM the brand (count + fill + grow), scroll-triggered, pure CSS where possible.**
- **BollyMeter score + arc fill:** drive the SVG arc with a `view()`-timed `stroke-dashoffset` and the numeral with the existing CountUp (scroll-gated). Arc: `animation-range: entry 10% entry 70%`, **700ms-equivalent**, ease via range; the fill should *finish slightly after* the digit lands so it reads "calculated, then confirmed." Color the final arc by rung (reuse `--accent` / the `data-rung` palette).
- **Box-office bars grow 0→width:** `.big-board__bar` (`:1789`) — animate `transform: scaleX()` from 0, `transform-origin:left`, `animation-timeline: view()`, range `entry 0% entry 60%`. **Use `scaleX`, not `width`** (GPU/compositor-friendly, no layout). Stagger is automatic via `view()` per row.
- These cost **0 extra JS** (scroll-driven) except the BollyMeter digit. This is the highest brand-ROI motion on the site: it turns "a number" into "a measurement."

**5. Verdict "stamp" + elevate the freshness pulse to a brand signature.**
- **Verdict stamp:** when `.browse-verdict[data-rung]` / `.calendar-row__verdict` enters view, fire a one-shot stamp:
```css
@supports (animation-timeline: view()) { @media (prefers-reduced-motion: no-preference) {
  .verdict-stamp { animation: stamp both; animation-timeline: view(); animation-range: entry 20% entry 45%; }
  @keyframes stamp {
    0%   { opacity: 0; transform: scale(1.18) rotate(-3deg); filter: blur(1px); }
    70%  { opacity: 1; transform: scale(.97) rotate(-3deg); }
    100% { opacity: 1; transform: scale(1) rotate(-3deg); filter: blur(0); }
  }
}}
```
**Overshoot-and-settle** (1.18→0.97→1), a fixed **−3° tilt** so it reads as a physical rubber stamp, ~**260ms-equivalent**. This is the *only* element allowed an overshoot — that exclusivity is what makes the verdict feel like the headline act.
- **Freshness pulse:** keep `live-pulse 2.4s` but apply the dot consistently at every "live/updated X ago" timestamp across desks, and tint it to the active desk accent. One ambient loop, used as a system tell = the site *feels* live everywhere.

## LATEST TECH / UI NOTE  (2026 primitives inside the static-export + ₹0 fence)
- **Cross-document View Transitions API** — stable in Chrome 126+ and **Safari 18.2+** (Firefox in progress); per [MDN](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API) and the [2026 cross-doc guide](https://trade-assistance.com/blog/cross-document-view-transitions-mpa-2026/). Same-origin only (BollyAI is single-origin static — fine). Opt-in is a single `@view-transition { navigation: auto }` at-rule in both pages' CSS. **Zero JS, zero infra, works on plain static HTML→HTML.** This is *the* 2026 primitive purpose-built for exactly BollyAI's constraint set.
- **CSS Scroll-Driven Animations (`animation-timeline: view()` / `scroll()`)** — Chrome 115+, **Safari 18+**, Firefox behind flag; per [MDN scroll-driven animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations). Named ranges `entry`/`exit`/`contain`/`cover` orchestrate reveals **off the main thread** — replaces the shipped IntersectionObserver+RAF in `CountUp.tsx` for most cases. Gate with `@supports (animation-timeline: view())`; non-supporting browsers see the final state (content fully visible) — *progressive enhancement, never a broken page*.
- **No library needed.** framer-motion / GSAP / Lenis are all **rejected** here: they add JS weight, hydration cost, and an "everyone's stack" feel for motion the platform now does natively. The entire spec above is **pure CSS + the existing tiny CountUp** — fits the ₹0 / static / no-AI-slop fence exactly.
- **`@property` for animatable custom props** (Chrome/Safari shipped) — optional polish to tween OKLCH accent glows smoothly if desired; not required.

## ANTI-SLOP WARNING  (the generic redesign trap for this lens)
- **Do NOT scroll-jack or scrub long parallax.** No pinned sections, no full-page hijacked scroll, no backdrop moving at 0.5× for 100vh. It fights readers who came for a verdict, tanks INP, and screams 2019 template. Reveals must **finish inside `entry 0%→~55%`** and never re-trigger on scroll-up.
- **Don't animate `width`/`height`/`top`/`left`/`filter:blur` on anything frequent** — layout/paint thrash. **transform + opacity only** on hovers, reveals, and bars (`scaleX`, not `width`). The compositor is the budget.
- **One overshoot, one place.** Spring/overshoot curves *only* on the verdict stamp (and a whisper on the meter). If every card bounces, nothing is special and it feels like a toy, not a critic.
- **Don't pile motion on already-muddy images.** Lens-wide problem: grain+scanline over weak posters. Motion must not add a *third* veil — keep poster-zoom subtle (≤1.06) and never blur posters on hover.
- **Respect `prefers-reduced-motion` for real** — not just "skip the fade." Reduced-motion users must still get the *final* state of every count/fill/stamp (show 8.4, full arc, full bar, stamped verdict — just no animation). This codebase already gates `mosaic-rise`/`live-pulse` correctly; **every** new block must wrap in `@media (prefers-reduced-motion: no-preference)` the same way.
- **Don't VT-name more than one element per page per name.** Duplicate `view-transition-name` = the whole transition silently aborts. Name only the single navigated poster + single arrival hero.

## ONE BIG SWING  (the "kamaal" move only this lens sees)
**The "Verdict Reveal" — choreograph the detail page's first 600ms into a single cinematic beat that performs the entire brand thesis on arrival.** When a user clicks a poster, chain it: (1) the **poster morphs into the hero** via View Transition (~420ms), and *as it lands*, (2) the **BollyMeter arc draws and the score counts up to 8.4**, (3) the **verdict stamp thunks down** with its −3° overshoot, (4) the **box-office bar grows** — all sequenced via `view()` ranges + transition-delay so they cascade in ~250ms after the morph settles, not all at once. The result: every navigation *climaxes on the verdict*, turning a static page-load into a tiny title-reveal sequence. No Indian cinema site does *any* of this; doing the *whole chain* — morph → measure → stamp — makes BollyAI *feel* like a verdict engine, literally animating its tagline "Har Friday ka faisla." It's ~120 lines of pure CSS + the existing CountUp, ₹0, static-safe, and it is the difference between "a nice dark site" and "holy shit this feels like a product." The morph alone is the floor; the **choreographed verdict landing is the ceiling, and the ceiling is cheap.**

---
*Sources: [Chrome View Transitions guide](https://developer.chrome.com/docs/web-platform/view-transitions) · [MDN View Transition API](https://developer.mozilla.org/en-US/docs/Web/API/View_Transition_API) · [Cross-doc VT 2026 (Chrome 126/Safari 18.2)](https://trade-assistance.com/blog/cross-document-view-transitions-mpa-2026/) · [MDN Scroll-driven Animations](https://developer.mozilla.org/en-US/docs/Web/CSS/Guides/Scroll-driven_animations) · [animation-timeline MDN](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/Properties/animation-timeline). Grounded in `site/app/globals.css` (2971 lines), `components/{MediaCard,BollyMeter,CountUp,FilmHero}.tsx`, and the current-home screenshot.*
