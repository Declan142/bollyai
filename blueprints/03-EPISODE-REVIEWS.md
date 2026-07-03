# BLUEPRINT 03 - Rich episode reviews (the flagship content lane)

Use when: expanding a series to full per-episode coverage, or upgrading thin episode cards
to competitor-grade rich reviews. This lane succeeded the Azure gpt-5.5 drain lanes
(credit expired 2026-07-02); Claude Sonnet/Opus now write these natively.
Prompts: `prompts/P03` (conductor), `prompts/P04` (worker, one series per worker).

## What ships where

- **Episode page** `/series/<slug>/s<N>/e<M>`: the full rich review (`review_body`).
- **Season page**: teaser cards (spoiler_free + the_moment + verdict score + link).
- **Homepage rail**: newest rich reviews (sorted by episode `merged_at`, falling back to
  series `date_modified`).

## The contract stack (read in this order, in full)

1. `scripts/subtitles/REVIEW-HOUSE-STYLE.md` - THE writer's contract (v4): modes, structure,
   subhead craft, opener menu, kill-list, scoring, verdict JSON. Where instinct conflicts
   with it, it wins.
2. `blueprints/01-QUALITY-BAR.md` - constitution (gates + traps + rubric).
3. `scripts/subtitles/DOSSIER_SPEC.md` - what a dossier licenses you to say.
4. `site/lib/series.ts` - EpisodeReview schema (rich fields are backward-compatible adds).

## Coverage law (non-negotiable)

- **Every episode of every season.** When BollyAI covers a series, ALL episodes get reviewed.
  Mode B (no per-episode reception) is the WORKHORSE, not a fallback, and must be as good
  as Mode A.
- **Depth-first**: finish ONE series completely (all seasons, all episodes, validated,
  committed) before touching the next. No half-covered series left behind.
- **Gap audit before planning** (conductor):
  ```bash
  python3 - <<'PY'
  import json, glob
  for f in sorted(glob.glob('data/series/*.json')):
      d = json.load(open(f))
      for s in d['seasons']:
          ers = s.get('episode_reviews') or []
          rich = sum(1 for e in ers if e.get('review_body'))
          eps = s.get('episodes') or 0
          if rich < eps:
              print(f"{d['slug']}\tS{s['number']}\t{rich}/{eps} rich")
  PY
  ```

## Grounding ladder (per episode - decides what you may write)

1. **Dossier exists** (`data/subtitles/<slug>/_dossiers/SxxEyy.json`): full grounding.
   Beats, character beats, key_lines, payoffs, contradiction are your facts. Dialogue
   quotes ONLY from `key_lines`, <= 15 words each, attributed to the character name, no
   timestamps in prose, <= 40 quoted words total in the review.
2. **No dossier**: ground in the episode's Wikipedia/official synopsis + the series page.
   Write the full Mode B craft review at the specificity the synopsis supports. ZERO
   dialogue quotes, zero scene-level claims the synopsis does not carry. Craft analysis
   works at the structure level: what the hour sets up, pays off, where the season bends.
3. **Nothing groundable** (no synopsis, contradictory sources): SKIP the episode, report it.
   A gap in coverage is honest; an invented beat is not.

Also banned regardless of rung: pacing/silence criticism derived from subtitle density
(dialogue-only corpora lie about silence - see QUALITY-BAR trap table).

## Mode decision (per episode, BEFORE writing)

- **Mode A** (rich + reception): ONLY when a real, URL-backed quote for THIS episode exists
  (critic_note or pull_quote). Weave attributed quotes in; attribution language is licensed.
- **Mode B** (rich, zero reception): everything else. Full architecture, BollyAI's own
  argued read, `pull_quote`/`critic_note` null, ZERO reception language ("critics",
  "audiences", "widely", "acclaimed" do not appear).

## Field contract (write exactly this)

| Field | Rule |
|---|---|
| `number`, `title`, `air_date` | Real episode number/title/date from the episode list. "Episode N" only if genuinely untitled |
| `spoiler_free` | 80-140 words. Opens on a specific real beat, says what the hour DOES, lands BollyAI's one-line take. Card teaser + meta description, never a synopsis |
| `the_moment` | The beat people remember, spoiler-careful, one or two lines |
| `review_body` | Markdown. Mode A ~1,200-1,700 words; Mode B ~900-1,500. H1 `<Show> S<N>E<M>: "<Title>" Review`, italic spoiler-care line, 80-120 word cold-open (no subhead), 4-7 evocative `##` subheads proving ONE thesis, `## The Verdict` closer (120-170 words) with one season-arc line. Bold first mention of major characters |
| `verdict` | `{score, one_liner}`. Score = BollyAI's disclosed craft /10, one decimal; one_liner 15-25 words, sharp, no fake-critic phrasing |
| `bollymeter` | SAME value as `verdict.score` (one disclosed score, two render points) |
| `critic_note` / `pull_quote` | Mode A: real text + source + URL, <= 25 words. Mode B: null |
| `hero_image` | `/img/series/<slug>/poster.jpg` (or a harvested backdrop if one exists) |
| `merged_at` | ISO-8601 +05:30 timestamp of this write (powers the homepage rail sort) |

Series-level after the pass: bump `date_modified` (ISO-8601 +05:30) once per series.

## Write mechanics (corruption-proof)

- Mutate via python: `json.load` -> edit the dict -> `json.dump(indent=2, ensure_ascii=False)`.
  NEVER string-edit JSON with sed/Edit-on-substrings (curly-quote corruption lesson).
- Upgrades keep what is real: an existing REAL critic_note/pull_quote survives the upgrade;
  thin prose gets rewritten around it. Never delete a real sourced quote.
- Existing rich reviews (with `review_body`) are not redone unless the run is explicitly an
  upgrade pass for that series.

## Two-pass quality mechanism (why the output is good)

1. **Draft pass**: write all episodes of a season per the contract.
2. **Polish pass**: RE-READ `REVIEW-HOUSE-STYLE.md` kill-list + QUALITY-BAR section 8, then
   sweep every draft: kill couplets/hinges/aphorisms/intensifiers/hedges, verify thesis +
   argued verdict + subhead quality, verify zero reception language in Mode B, verify quote
   caps. Fix in place. The contract re-read IS the quality mechanism - never skip it.
3. **Mechanical gates**: `python3 scripts/batch/fix_series.py <slug>` then
   `python3 scripts/batch/validate_series.py <slug>` -> fix until PASS.
   Validate after each SEASON, not each episode (cheap loop, early catch).

## Cadence + commits

- One series per worker session. 8+ seasons = split by season ranges across sequential
  sessions, same rules, series still finished before the queue advances.
- Commit per series, only when the whole series validates:
  `bollyai: episode reviews (expansion) - <slug>` or `... (upgrade) - <slug>`, trailer
  `Co-Authored-By: Claude <noreply@anthropic.com>`. No push from lanes; floor pushes after
  pytest. Log one line per series to `data/_state/buildout-loop.log`.

## Conductor spot-review (before accepting a worker's series)

Read 2 random rich bodies + 1 spoiler_free from the returned series against QUALITY-BAR
section 8 (effort xhigh). Any gate hit = reject back to the worker with the specific lines;
any 2+ kill-list hits = same. Then `validate_series.py <slug>` independently. Accept only
on double-green.

## Definition of done (per series)

Every aired episode has a validated review (or a reported, reasoned skip); modes counted;
validator PASS; date_modified bumped; committed; report lists per-season word-count ranges,
Mode A/B split, quotes added (with URLs), and skips.
