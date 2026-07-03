# P09 - FRONTEND FEATURE (model: Opus 4.8 | effort: xhigh on design decisions)

You design and build a frontend change for bollyai.in - a static Next.js export with a
locked visual identity and an anti-slop gate. Distinctive beats safe; slop fails the gate.

## INPUTS (abort if unfilled)
- FEATURE: {{WHAT_TO_BUILD}}
- SURFACES: {{ROUTES_OR_COMPONENTS}}
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST
1. `site/app/globals.css` + `site/app/revamp.css` - the existing design system (tokens,
   type, color). Your change must read as the SAME hand, not a bolt-on.
2. The components you will touch under `site/components/` + their consuming pages under
   `site/app/`.
3. `site/lib/series.ts` / `site/lib/data.ts` if you render data - render ONLY real fields;
   a frontend that implies fake data (fake counts, fake ratings UI) is a fence violation.
4. `blueprints/07-QA-SHIP.md` (gates 4-6 apply to you).

## HARD RULES
1. Commit to a bold aesthetic direction BEFORE writing markup; if the frontend-design skill
   is available in this session, invoke it first. Banned defaults: Inter/Roboto/Arial/system
   font stacks, purple-on-white gradient hero, cookie-cutter Tailwind card grids.
2. Static export constraints: no server components that need a runtime, no dynamic APIs -
   everything must survive `next build` static output.
3. NEVER render an aggregate-rating schema or UI (hard build check). BollyMeter renders as
   BollyAI's own disclosed score, labelled as such.
4. No TMDB-hosted images, ever. Self-hosted `/img/...` paths only, with the existing
   fallback pattern.
5. No em/en dashes in copy. All UI copy obeys QUALITY-BAR (no fake reception language).
6. Respect the file cap: the build hard-fails at 20k output files; a feature that mints
   thousands of new static pages needs the floor's explicit sign-off BEFORE you build it.

## PROCEDURE
1. State the design direction in 3 sentences (aesthetic commitment, typography move,
   layout idea). Then build it.
2. Implement minimally invasive: extend the existing token system; new tokens go in
   globals.css with the same naming style. Match the codebase's component idioms.
3. `cd site && npm run build` - green, with the page count + filecap output noted.
4. Verify rendered output in `site/out/` for 2-3 affected routes (grep for your new
   markup; confirm no broken image paths; check a mobile-width media query exists where
   the design needs one).
5. Dispatch the design-reviewer agent on the change. Under 7.5 = iterate (direction stays,
   execution sharpens) and re-review. Two failed rounds = stop, report with the reviewer's
   notes and your options.
6. Commit `bollyai: frontend - <feature>` + trailer. No push, no deploy (floor ships after
   the full ladder).

## RETURN CONTRACT
```json
{
  "feature": "{{WHAT_TO_BUILD}}",
  "direction": "<the 3-sentence commitment>",
  "files": ["<created/modified>"],
  "build": "<green + page count + filecap line>",
  "design_review": "<score + one-line summary>",
  "rendered_check": "<routes verified in site/out>",
  "commit": "<hash|none>"
}
```

## DO NOT
Ship a first-idea layout. Add a dependency without flagging it. Render fabricated numbers
or aggregate ratings. Push or deploy. Call it done without the design score and the build
tail in your report.
