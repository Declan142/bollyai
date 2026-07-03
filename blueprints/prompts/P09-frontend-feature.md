# P09 - FRONTEND FEATURE (model: Opus 4.8 | effort: xhigh on design decisions)

You design and build a frontend change for bollyai.in - a static Next.js export with a
locked visual identity and an anti-slop gate. Distinctive beats safe; slop fails the
gate. You commit to an aesthetic direction BEFORE markup, and you prove the change in
the built output, not in your head.

## INPUTS (abort if unfilled)
- FEATURE: {{WHAT_TO_BUILD}}
- SURFACES: {{ROUTES_OR_COMPONENTS}}
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST
1. `site/app/globals.css` + `site/app/revamp.css` - the design system: tokens, type
   scale, color. Your change must read as the SAME hand, not a bolt-on.
2. The components you will touch under `site/components/` + their consuming pages under
   `site/app/` (the series routes span hub/season/episode/where-to-watch/
   ending-explained/finale-predictions - know which render paths your change hits).
3. `site/lib/series.ts` / `site/lib/data.ts` if you render data - render ONLY real
   fields. A UI that implies fake data (invented counts, star-rating aggregates, fake
   "users say" chrome) is a fence violation, not a design choice.
4. `blueprints/07-QA-SHIP.md` - gates 4-6 apply to you; the filecap is yours to respect.

## HARD RULES
1. Commit to a bold direction BEFORE markup; if the frontend-design skill is available
   in this session, invoke it first. Banned defaults: Inter/Roboto/Arial/system font
   stacks, purple-on-white gradient hero, cookie-cutter Tailwind card grids, generic
   shadcn look.
2. Static export constraints: no runtime server components, no dynamic APIs - everything
   must survive `next build` static output. Client interactivity = small, self-contained,
   no new heavyweight dependency without flagging it FIRST in your report plan.
3. NEVER render AggregateRating schema or aggregate-star UI (hard build check).
   BollyMeter renders as BollyAI's own disclosed score, labelled as such. The disclosure
   line stays where surfaces carry it.
4. No TMDB-hosted images, no hotlinks. Self-hosted `/img/...` with the existing fallback
   pattern (`_fallback.svg` swap when the file is missing - series.ts shows the idiom).
5. None of the four dashes in UI copy; all copy obeys QUALITY-BAR (no fake reception
   language in labels, empty-states, or marketing lines).
6. Respect the file cap: the build hard-fails at >= 20k output files. A feature that
   mints thousands of new static pages (new per-entity route) needs the floor's explicit
   sign-off BEFORE you build it - say so and stop if FEATURE implies one.
7. Mobile is not optional: every new layout carries its narrow-viewport behavior.

## PROCEDURE
1. **Direction** (3 sentences, written before any code): the aesthetic commitment, the
   typography move, the layout idea. If a design skill produced a direction, restate it
   in your own three sentences.
2. **Implement** minimally invasive: extend the existing token system (new tokens in
   globals.css, same naming style); match the codebase's component idioms (server
   components + data via lib functions; small client islands only where interaction
   demands).
3. **Build**: `cd site && npm run build` - green, note page count + filecap line. Any
   data-shape change = run `python3 -m pytest tests/ -q` too.
4. **Prove it rendered**: for 2-3 affected routes, inspect `site/out/<route>/index.html` -
   grep for your new markup, confirm image paths resolve to files that exist in
   `site/out/img/...`, confirm the narrow-viewport CSS is present. Paste the greps.
5. **Design gate**: dispatch the design-reviewer agent on the rendered change. Under 7.5
   = iterate execution (direction stays, execution sharpens), re-review. Two failed
   rounds = stop, report the reviewer's notes + your options.
6. **Commit**: `bollyai: frontend - <feature>` + trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`. No push, no deploy (floor ships
   after the full ladder).

## RETURN CONTRACT
```json
{
  "feature": "{{WHAT_TO_BUILD}}",
  "direction": "<the 3-sentence commitment>",
  "files": ["<created/modified>"],
  "new_dependencies": ["<none unless flagged + justified>"],
  "build": "<green + page count + filecap line>",
  "tests": "<pytest line if data shapes touched, else n/a>",
  "rendered_check": "<routes verified in site/out + grep evidence>",
  "design_review": "<score + one-line summary per round>",
  "commit": "<hash|none>"
}
```

## DO NOT
Ship a first-idea layout. Add a dependency silently. Render fabricated numbers,
aggregate ratings, or fake social proof. Mint a new thousand-page route without floor
sign-off. Break the static export. Push or deploy. Call it done without the design score,
the build tail, and the site/out evidence in your report.
