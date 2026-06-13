# RICH EPISODE REVIEW — REWIRE SPEC (Vyom floor, 2026-06-13)

Aditya GO: rewire the thin 113-word episode reviews to competitor-grade rich reviews.
Benchmark = Den of Geek HotD E1 (~2100w, sectioned analysis, verdict, sourced image).
Our target: ~1.2-1.7k words, House-style craft, our honesty fences intact.

## ARCHITECTURE (locked by floor)

- **Full rich review lives on the EPISODE page** `site/app/series/[slug]/[season]/[episode]/page.tsx`.
- **Season page** `[season]/page.tsx` = teaser CARDS (the_moment + verdict score + link to full review). Not the full body.
- **Homepage rail** = newest rich reviews (already exists, point it at the richer data).

## SCHEMA (site/lib/series.ts — expand EpisodeReview, backward-compatible)

Keep existing fields. ADD:
```
review_body: string | null;     // rich Markdown, ~1.2-1.7k words, sectioned (## subheads). The meat.
verdict: { score: number; one_liner: string } | null;  // RT-style scannable header
pull_quote: { text: string; source: string; url: string } | null;  // real external critic, <=25w, verify-or-strip
hero_image: string | null;      // /img/series/<slug>/poster.jpg or backdrop/still if harvested
```
- `spoiler_free` (the existing 1-para) STAYS as the card teaser / meta-description / rail hook.
- `review_body` is the new full review.

## FENCE EVOLUTION (flag to Aditya — deliberate, not a violation)

- **Per-episode bollymeter NOW = BollyAI's own DISCLOSED craft score** (the verdict.score), anchored in the
  review's specific grounded points. A disclosed-AI CRITIC giving its /10 is legitimate; what stays banned is
  faking AGGREGATE/reception numbers. This supersedes the "per-ep bollymeter null" rule FOR rich reviews.
  Render must label it clearly as BollyAI's read (not an aggregate). NEVER emit AggregateRating schema (unchanged).
- All other fences UNCHANGED: no first-person viewing claims, grounded-to-dialogue, <=25w attributed quotes,
  no em/en dash, no fabricated reception, pull_quote verify-or-strip, QID never guessed.

## REVIEW HOUSE-STYLE (write scripts/subtitles/REVIEW-HOUSE-STYLE.md)

Fuse the demo recap craft DNA (research/00-HOUSE-STYLE.md) with a REVIEW structure:
- VOICE: front-row film-mad critic, opinionated in service of analysis. English-primary, Indian swagger.
- RESTRAINT rule (earn ONE great line, narrate rest straight). Full KILL-LIST from 00-HOUSE-STYLE
  (no "X is both A and B", no "not X; it's Y", no aphoristic closers, no meta-AI refs, no em-dash,
  no listing-in-threes reflex, no generic intensifiers, no inline timestamps/citations).
- STRUCTURE (~1.2-1.7k words):
  - H1 + spoiler-care line.
  - COLD-OPEN (80-120w): the episode's charged hook, told flat. No meta.
  - 3-5 `##` act-blocks (evocative subheads): what happens + analysis woven (what works, what doesn't,
    themes, character, craft). Grounded to dialogue/dossier. Bold first mention of major characters.
  - `## The Verdict` closer: the score's reasoning + where it leaves the viewer.
- SPOILER POSTURE: spoiler-careful (this is the public review; the ending-explained surface is the spoiler one).
- GROUNDING: every claim traces to the dossier (beats/key_lines/contradictions). Quotes <=25w, attributed to dialogue.

## GENERATION (gpt-5.5 / codex — the proven demo pipeline)

- Adapt demo `engine/build_recap.py` + `edit_recap.py` (gpt-5.5 draft -> edit) to produce `review_body`
  from the LIVE dossier (data/subtitles/<slug>/_dossiers/SXXEYY.json), per the review house-style.
- Route via `gpt code` / codex (gpt-5.5, weekly pool) — NOT the free OpenRouter tier (it degrades at 1.5k length).
- Incremental write + skip-and-continue (the robustness fix) carries over.

## RENDER (frontend-design skill + design-reviewer >= 7.5)

- Episode page: verdict box (score + one_liner + the_moment) at top, hero_image, then rendered Markdown body
  (use the existing markdown renderer - gray-matter/marked per project), pull_quote as a styled callout if present.
- Season page: replace the full-text block with teaser CARDS (poster + S/E + the_moment + score + link).
- Must pass design-reviewer >= 7.5 (anti-slop). No Inter/Roboto; house OKLCH system.

## PILOT FIRST (hard gate before mass-regen)

1. Build schema + house-style + generation + render.
2. Generate + render ONE review: **house-of-the-dragon S1E1** (established, Den of Geek benchmark exists, poster available).
3. Run validate_series + pytest + npm build + design-reviewer.
4. STOP. Floor reviews vs the Den of Geek bar, shows Aditya. NO mass-regen until Aditya approves the pilot.

## AFTER PILOT APPROVED (not now)

- Regenerate the 6 shipped series (farzi/scam/CLOY/EYA/SM + their episodes) in rich format.
- Then resume full-season coverage in rich format (remove STOP, rewire the engine's review step).
- G4 voice-pass + merge_reviews gates adapt to review_body (G4 checks the rich body voice, not just the blurb).

## FENCES FOR THE BUILD LANE
- merge_reviews stays the only write-path into data/series for reviews; floor runs --apply.
- No deploy (floor deploys after pilot approval). No mass-regen (pilot only).
- Mutate JSON via json.dump, never hand-edit strings (curly-quote corruption lesson).
- No em or en dashes anywhere.
