# BollyAI Design Revamp — Shared Context Brief (read FIRST)

**Date:** 2026-06-15. **Owner:** Aditya (Vyom orchestrating). **You are one of 10 Opus design lenses.**

## The mission (Aditya's exact words)
> "I don't like the way our site BollyAI is looking right now, we are not as nice looking as the
> other bigger sites, the whole structure doesn't look good. Can you have a 10 opus team look at
> design from all our competitors and make sure we are using the latest tech and the latest UI and
> also look at psychology — what would make people stay at our site and be here."

We are producing a **world-class redesign direction** for BollyAI's homepage + global art direction.
Your card feeds the orchestrator's synthesis, which becomes an implemented redesign. Be CONCRETE and
SPECIFIC — name patterns, name mechanisms, give implementable changes. Generic design-essay = failure.

## What BollyAI is
Pan-India cinema / TV / box-office **answer engine**. Disclosed-AI critic — tagline "BollyAI has NOT
watched anything. BollyAI has read everyone who has." / "Har Friday ka faisla" (every Friday's verdict).
Live: **https://bollyai.in**. 7 desks: Bollywood / Kollywood / Tollywood / Mollywood / Sandalwood /
Hollywood / Streaming. **South-first** weighting (Telugu/Tamil > Hindi by OTT volume since 2023).
Audience: Indian film/OTT viewers deciding "is it worth watching / where to watch / what's the verdict."
Signature feature: **BollyMeter** (0–10 verdict score) + a **verdict ladder** + live box-office trackers.

## HARD CONSTRAINTS (a redesign that ignores these is unusable — read carefully)
- **Static export only.** Next.js `output: export` → static HTML → Cloudflare Pages. **No server, no
  DB, no SSR, no edge functions, ₹0 infra.** Anything dynamic must be client-side JS or build-time.
- **No login / no accounts** (no backend). Personalization must be **localStorage / client-only**.
- **Images: self-hosted official press only.** TMDB ToS BANS using their images. **No TMDB, IMDb,
  Letterboxd, or JustWatch images may be served.** Posters are harvested official press stills under
  fair-dealing + attribution + a /takedown page. **Consequence: poster coverage is incomplete — many
  titles currently render a monogram-initials placeholder. This is a live visual-quality problem.**
- **No fake ratings.** Single editorial `reviewRating` only — **never** `AggregateRating` / star-vote
  counts (enforced by a build gate). BollyMeter is editorial, shown with its basis.
- **No fabricated numbers.** Box office publishes only on ≥2-source agreement; OTT view-counts never
  invented. Trust/credibility is the brand — the design must signal earned authority, not faked social proof.
- **Current CSS is hand-written plain CSS** (one 2971-line `globals.css`, OKLCH tokens, no Tailwind,
  no component kit, no animation library). A redesign can ADD tooling but must justify it vs the
  static-export + ₹0 fence and the "no AI-slop" empire rule (banned: Inter/Roboto/system fonts,
  purple-on-white gradients, cookie-cutter Tailwind).

## Current stack
Next.js 14.2 (app router) · React 18 · plain CSS (OKLCH) · static export → CF Pages. Fonts:
**Fraunces** (variable display serif) + **Hanken Grotesk** (body) + **JetBrains Mono** (numbers).
AVIF/WebP poster variants already generated. No Tailwind / no framer-motion / no shadcn.

## Current homepage structure (in render order — this is "the structure that doesn't look good")
1. **FeaturedMosaic** — a *bento wall*: ONE lead verdict tile (backdrop + title + box-office figure +
   verdict meter) competing in a grid with **8 secondary tiles** (mix of films/series), then a live-stats
   ribbon (Series tracked / Films tracked / Desks live / Freshness). **← the hero is a bento, not a stage.**
2. **Trade ticker** — full-bleed scrolling marquee of TITLE + figure + label.
3. **Just Dropped** — horizontal media-rail of 16 newest cards.
4. **Desk-nav** — 6 tiles linking to desk hubs (name + title count).
5. **Big This Week** — horizontal media-rail of 14 cards.
6. **Board-split** — left: "Box Office Now" top-5 bar list; right: "OTT This Week" date list.
7. **Naye Episode Reviews** — rail of episode-review cards.
8. **What to Watch** — rail of curated watchlist cards.
9. **2026 Yearboards** — grid of 7 desk-scoreboard links.
10. **Desk-strip** — 6 desk tiles (label + answer line).

Card anatomy (`MediaCard` / `MosaicTile`): poster (or monogram placeholder) + type badge (Film/Series)
+ "New" flag + score badge (X.X/10) + plate (desk label, title, meta, compact verdict meter).

## Current design tokens (`:root`, OKLCH)
```
--font-display: Fraunces Variable, serif;  --font-body: Hanken Grotesk;  --font-number: JetBrains Mono;
--bg: oklch(11% .03 280);  --bg-deep: oklch(8% .025 280);  (very dark indigo-violet)
--surface: oklch(16% .045 280);  --surface-2: oklch(20% .04 280);
--text: oklch(93% .03 82);  --text-dim: oklch(72% .035 82);  --text-faint: oklch(58% .035 82);
--border: oklch(34% .04 280);  --accent: oklch(78% .16 65) (warm amber, Bollywood);
per-desk accent tinting (Kollywood red, Tollywood gold, Mollywood green, Sandalwood ochre,
Hollywood cool-blue, Streaming orange). Film-grain + scanline texture overlays on body.
h1: clamp(2.55rem, 7vw, 6.6rem) Fraunces. --shadow-poster: big soft drop.
```

## Orchestrator's diagnosis SO FAR (confirm / refute / extend — do NOT just parrot)
- The system has real craft (bespoke OKLCH, good type pairing, texture) but the **homepage composition
  fails**: the hero is a bento with no commanding focal point; everything is similar-weight; the eye
  has nothing to land on.
- **Monogram placeholders** for posterless titles badly cap perceived quality on a *cinema* site.
- Possible muddiness: grain/scanline overlays on top of already-weak/low-res images.
- No motion language, no depth/hover sophistication, no view-transitions — feels static vs "latest UI."
- Nav crams 8 desks + search into a thin strip — busy, not premium.

## Assets you can use
- **Live site:** WebFetch `https://bollyai.in` (real DOM/content/structure).
- **Current homepage screenshot:** Read `/home/aditya/bollyai/design-revamp-2026-06-15/current-home-screenshot.png`
- **WebSearch** for competitor design teardowns / 2026 UI patterns / the specific sites in your lens.
- You may WebFetch competitor URLs for structure (note: returns DOM/text, not pixels — pair with your
  trained knowledge of these well-known products' design language + WebSearch for visual teardowns).

## OUTPUT CONTRACT (write exactly this file, this shape)
Write to: `/home/aditya/bollyai/design-revamp-2026-06-15/lenses/lens-NN-<your-slug>.md`
(your NN + slug are given in your prompt). Use this structure, be DENSE and SPECIFIC:

```
# Lens NN — <Your Lens Name>

## VERDICT (3 sentences max)
The single most important thing this lens demands for BollyAI.

## WHAT THE BEST DO  (named examples + the MECHANISM — why it works, not just "it's nice")
- <Pattern> — <site(s) that nail it> — <why it works / the psychology or craft mechanism>
- ... (5–8 bullets, specific)

## WHERE BOLLYAI FAILS TODAY  (grounded in the screenshot / code / live site — specific, not vague)
- ...

## TOP 5 CONCRETE CHANGES  (ranked; each implementable — name the component/token/section + the change)
1. ...
(specific enough that an engineer could build it: "Replace the bento hero with a full-bleed
billboard: 70vh backdrop, Fraunces title at clamp(4rem,9vw,8rem), single primary CTA, verdict
chip top-left, gradient scrim 0→0.9" — NOT "make the hero better")

## LATEST TECH / UI NOTE  (what 2026 primitive/tool applies within the static-export + ₹0 fence)
- ...

## ANTI-SLOP WARNING  (what NOT to do — the generic redesign trap for this lens)
- ...

## ONE BIG SWING  (the single audacious move only your lens sees — the "kamaal" move, not "theek hai")
- ...
```

Keep it tight and high-density. Specifics win. You have ~15 min. Go.
