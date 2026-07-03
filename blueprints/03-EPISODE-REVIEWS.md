# BLUEPRINT 03 - Rich episode reviews (the flagship content lane)

Use when: expanding a series to full per-episode coverage, or upgrading thin episode cards
to competitor-grade rich reviews. This lane succeeded the Azure gpt-5.5 drain lanes
(credit expired 2026-07-02); Claude Sonnet/Opus write these natively now.
Prompts: `prompts/P03` (conductor), `prompts/P04` (worker, one series per worker).
Benchmark: Den of Geek's ~2,100-word HotD E1 review. Our target: 1,200-1,700 words of
sectioned analysis with the honesty fences intact.

## What ships where

- **Episode page** `/series/<slug>/s<N>/e<M>`: the full rich review (`review_body` rendered
  as Markdown, verdict box on top, pull_quote as a styled callout when present).
- **Season page**: teaser cards (spoiler_free + the_moment + verdict score + link).
- **Homepage rail**: newest rich reviews, sorted by episode `merged_at` (fallback: series
  `date_modified`).

## The contract stack (read in this order, in full)

1. `scripts/subtitles/REVIEW-HOUSE-STYLE.md` - THE writer's contract (v4): modes,
   structure, subhead craft, opener menu, craft moves, kill-list, scoring, verdict JSON.
   Where instinct conflicts with it, it wins.
2. `blueprints/01-QUALITY-BAR.md` - gates (with the regex pattern tables), traps, rubric.
3. `scripts/subtitles/DOSSIER_SPEC.md` - what a dossier licenses you to say.
4. `site/lib/series.ts` - EpisodeReview schema (rich fields are backward-compatible adds).
5. In-repo taste anchors: `data/series/ozark.json` S1E1 (Mode B register: "treats panic as
   paperwork"), `data/series/mad-men.json` S1E1 (licensed critic_note usage).

## Coverage law (non-negotiable)

- **Every aired episode of every season.** Mode B (no per-episode reception) is the
  WORKHORSE, not a fallback, and must be as good as Mode A.
- **Depth-first**: finish ONE series completely (all seasons validated, committed) before
  the queue advances. No half-covered series left behind.
- **Gap audit before planning** (conductor):
  ```bash
  python3 - <<'PY'
  import json, glob
  rows = []
  for f in sorted(glob.glob('data/series/*.json')):
      d = json.load(open(f))
      for s in d['seasons']:
          ers = s.get('episode_reviews') or []
          rich = sum(1 for e in ers if e.get('review_body'))
          eps = s.get('episodes') or 0
          if rich < eps:
              rows.append((d['slug'], s['number'], rich, eps))
  for slug, n, rich, eps in rows:
      print(f"{slug}\tS{n}\t{rich}/{eps} rich")
  print(f"\n{len(rows)} season-gaps across {len(set(r[0] for r in rows))} series")
  PY
  ```

## Grounding ladder (per episode - decides what you may write)

1. **Dossier exists** (`data/subtitles/<slug>/_dossiers/SxxEyy.json`): full grounding.
   `beats`, `character_beats`, `key_lines`, `open_loops`, `payoffs`, `contradiction` are
   your facts - the contradiction field is the review's spine candidate. Dialogue quotes
   ONLY from `key_lines`: <= 15 words each, attributed to the character name, no
   timestamps in prose, <= 40 quoted words total per review. Respect
   `speaker_attribution_confidence`: low/medium = paraphrase, don't quote a name.
2. **No dossier**: ground in the episode's synopsis from Wikipedia (season article or
   "List of <Show> episodes") + the series page. Full Mode B craft review at the
   specificity the synopsis supports: ZERO dialogue quotes, zero scene-level claims the
   synopsis does not carry. Craft analysis lives at the structure level: what the hour
   sets up, pays off, withholds; where the season bends; how the episode uses its slot.
3. **Nothing groundable**: SKIP the episode with a reason in the report. A coverage gap is
   honest; an invented beat is not.

Banned at every rung: pacing/silence criticism derived from subtitle density ("long
silences", "prolonged pauses", "dead air" - dialogue-only corpora lie about silence; the
draft gates in `tests/test_draft_reviews_gates.py` hard-reject these shapes).

## Episode facts sourcing

Titles, numbers, air dates: Wikipedia "List of <Show> episodes" / per-season articles.
Cross-check `season.episodes` in the series JSON against the real list; if the JSON count
is wrong, fix it and flag it in your report. `air_date` null when genuinely unlisted.
`"Episode N"` as title only when the show truly doesn't title episodes (ozark S1 does
this; most prestige shows have titles - look before defaulting).

## Mode decision (per episode, BEFORE writing)

**Mode A** only when a real, URL-backed quote for THIS episode is in hand. Finding one:
1. WebSearch `"<show>" season <N> episode <M> review <outlet>` - outlets with real
   per-episode coverage: AV Club, Vulture, Den of Geek, IGN, Collider, TVLine, Paste,
   Entertainment Weekly recaps, RogerEbert.com TV, genre sites (Tor/Reactor for SF).
2. WebFetch the candidate URL. Locate the sentence VERBATIM. Trim to <= 25 words without
   altering any word. Record exact outlet name + exact URL.
3. Fetch fails, or the quote is not verbatim-findable, or the review is season-level not
   episode-level = NO quote = Mode B. Never force Mode A; a wrong-scope quote is a gate hit.
Wikipedia "Reception" paragraphs are leads, not sources: chase their citation to the
primary URL and verify there, or drop it.

**Mode B** is everything else: full architecture, BollyAI's own argued read,
`critic_note`/`pull_quote` null, ZERO reception language (run the QUALITY-BAR grep - the
words critics/reviewers/audiences/fans/widely/acclaimed/divisive do not appear).

## Field contract (write exactly this)

| Field | Rule |
|---|---|
| `number`, `title`, `air_date` | Real values per Episode facts sourcing above |
| `spoiler_free` | 80-140 words. Opens on a specific real beat, says what the hour DOES, lands BollyAI's one-line take. Card teaser + meta description, never a synopsis. May use **bold** for a lead name |
| `the_moment` | The beat people will remember, spoiler-careful, 1-2 lines |
| `review_body` | Markdown per the structure budget below. Mode A 1,200-1,700 words; Mode B 900-1,500 |
| `verdict` | `{score, one_liner}`. Score one decimal; one_liner 15-25 words, sharp, no fake-critic phrasing |
| `bollymeter` | SAME number as `verdict.score` (one disclosed craft score, two render points) |
| `critic_note` / `pull_quote` | Mode A: real text + source + URL, <= 25 words. Mode B: null |
| `hero_image` | `/img/series/<slug>/poster.jpg` (or a harvested backdrop/still if it exists on disk) |
| `merged_at` | Write-time ISO-8601 +05:30 (homepage rail sort key) |

## `review_body` structure budget

| Block | Budget | Content |
|---|---|---|
| H1 | 1 line | `<Show> S<N>E<M>: "<Title>" Review` (or the central tension as a question when the hour earns it) |
| Spoiler-care line | 1 line | `*Spoiler-light verdict above. Full episode analysis below.*` |
| Cold-open | 80-120 words, no subhead | The most charged real beat, told FLAT, implying the thesis. One opener move from the HOUSE-STYLE menu; never repeat a move within a series |
| 4-7 `##` subheads | ~180-330 words each | Real beats + analysis proving ONE thesis. Bold first mention of each major character. Mode A weaves its attributed quotes here |
| `## The Verdict` | 120-170 words | The score's reasoning, arguing (concede-assert), + ONE season-arc line |

Worked micro-example of the register (Mode B cold-open, ozark S1E1, in-repo):
"**Del** walks into **Marty**'s life with a number and a threat. The number is $5 million.
The threat needs no decoration. [...] Ozark's first episode works because it treats panic
as paperwork." - flat beats, thesis implied, zero reception. That is the bar.

A subhead set that carries a thesis (invented example, structure only):
`## Money Gets a Moral Job` / `## The Family Is the Alibi` / `## Who Blinks First?` /
`## The Lake House Buys the Ending` - verdicts and images, varied grammar, no locations.

## Write mechanics (corruption-proof, upgrade-safe)

Mutate via python only. Template (adapt, don't retype into the shell by hand):

```bash
python3 - <<'PY'
import json, datetime
SLUG, N = "SLUG", 1
p = f"data/series/{SLUG}.json"
d = json.load(open(p, encoding="utf-8"))
IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))
now = datetime.datetime.now(IST).isoformat(timespec="seconds")
season = next(s for s in d["seasons"] if s["number"] == N)
ers = season.setdefault("episode_reviews", [])
new = {
  "number": 1, "title": "TITLE", "air_date": "YYYY-MM-DD",
  "bollymeter": 8.1,
  "spoiler_free": "...", "the_moment": "...",
  "critic_note": None,                      # Mode A: {"text","source","url"}
  "review_body": "# ...",
  "verdict": {"score": 8.1, "one_liner": "..."},
  "pull_quote": None, "hero_image": f"/img/series/{SLUG}/poster.jpg",
  "merged_at": now,
}
ex = next((e for e in ers if e.get("number") == new["number"]), None)
if ex:
    for k, v in new.items():
        if k in ("critic_note", "pull_quote") and v is None and ex.get(k):
            continue    # NEVER clobber a real sourced quote with null
        ex[k] = v
else:
    ers.append(new); ers.sort(key=lambda e: e["number"])
json.dump(d, open(p, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
PY
```

Upgrade rules on top:
- Existing REAL critic_note/pull_quote survives (the template guard above).
- Existing rich reviews (`review_body` present) are untouched in `expansion` mode;
  rewritten only in `upgrade` mode.
- Score honestly fresh on upgrades; a swing > 1.5 from the old score goes in your report.
- Series `date_modified` bumps ONCE per series, after the last season passes.

## Two-pass quality mechanism (never skip pass 2)

1. **Draft pass**: all episodes of a season per the contract.
2. **Polish pass**: RE-READ the HOUSE-STYLE kill-list + QUALITY-BAR sections 4-6, then
   sweep every draft: kill couplets/hinges/aphorisms/intensifiers/hedges/threes; verify
   ONE thesis per episode (two episodes sharing a thesis = rewrite one); verify the
   verdict argues; run the rubric greps (viewing, attribution, dashes); verify quote caps
   and Mode B purity. Fix in place. The contract re-read IS the quality mechanism.
3. **Mechanical gates** per season:
   `python3 scripts/batch/fix_series.py <slug>` then
   `python3 scripts/batch/validate_series.py <slug>` -> fix until PASS before the next
   season (cheap loop, early catch; the error->fix table is in blueprint 02).

## Cadence + commits

- One series per worker session. 8+ seasons: split by season ranges across sequential
  sessions; the series still finishes before the queue advances.
- Commit per series, only when the whole series validates:
  `bollyai: episode reviews (expansion) - <slug>` or `... (upgrade) - <slug>` + trailer
  `Co-Authored-By: Claude <noreply@anthropic.com>`. No push from lanes.
- Log per series to `data/_state/buildout-loop.log`:
  `<iso> episode-reviews <slug> written=<k> modeA=<a> modeB=<b> skips=<s>`.

## Conductor spot-review (before accepting a worker's series)

At effort xhigh: (1) re-run the validator yourself; (2) read 2 random new `review_body`
fields + 1 `spoiler_free` against QUALITY-BAR - thesis? argued verdict? subhead spine?
Mode B purity? word range honest? at least one real criticism? (3) open 2 Mode A URLs and
confirm the quote text appears on the page; (4) reject with exact failing lines on any
gate hit or 2+ kill-list hits - one rework round with a FRESH worker, then park + log.
Accept only on double-green (validator + read).

## Definition of done (per series)

Every aired episode has a validated review or a reported, reasoned skip; Mode A/B counted;
validator PASS pasted; date_modified bumped; committed; report carries per-season word
ranges, quotes added (with URLs), score swings, and skips.
