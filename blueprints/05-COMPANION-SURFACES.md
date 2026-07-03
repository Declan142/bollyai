# BLUEPRINT 05 - Companion surfaces (endings, predictions, lists, explainers)

Use when: authoring the high-intent SEO surfaces that orbit a series hub. Prompt:
`prompts/P06`. Every surface inherits the full QUALITY-BAR; what changes per surface is
the SPOILER POSTURE and the shape. Exemplars are law - mirror them exactly.

## Surface map

| Surface | Data | Route | Gate |
|---|---|---|---|
| Ending explained | `data/endings/<slug>.json` | `/series/<slug>/ending-explained` | `tests/test_ending_explained.py` |
| Finale predictions | `data/predictions/<slug>.json` | `/series/<slug>/finale-predictions` | `tests/test_predictions.py` |
| Recommendation lists | `data/recommendations/<list-slug>.json` | browse/list surfaces | build + shared fences |
| Topic explainers | `data/explainers/<slug>/...` | `/series/<slug>/explainer/<topic>` | mirror `from/` exemplars |
| Episode deep data | `data/episodes/<slug>/SxxEyy.json` | episode page enrichment | mirror `from/` exemplars |
| Where to watch | COMPUTED from series JSON | `/series/<slug>/where-to-watch` | >= 2 seasons only; NO authoring |

## Ending explained (`data/endings/<slug>.json`)

The one licensed FULL-SPOILER surface. Test-enforced contract (transcribed from
`tests/test_ending_explained.py`):
- `slug` == filename AND resolves to a real `data/series/<slug>.json`;
- `season_number` (int) must EXIST as a season on that series;
- `spoiler` must be literally `true`;
- `hook` >= 8 words; `sections` >= 3, each `heading` non-empty and `body` >= 25 words;
- `sources` >= 1 real entry (an uncited ending hard-fails as fabrication risk);
- no viewing claims, none of the four dashes, `date_modified` present.

Shape (from the `from.json` exemplar):
```json
{
  "slug": "SLUG", "qid": "Q000000", "title": "TITLE", "season_number": 4,
  "spoiler": true,
  "hook": "ANSWER THE SEARCH QUESTION IN THE FIRST TWO SENTENCES: what is X, who are Y, how did it end. Then promise the breakdown.",
  "sections": [
    { "heading": "The premise and the rules", "body": ">= 25 words. Plot claims grounded in aired episodes / dossier / a cited source. Interpretation framed as BollyAI's own reading." }
  ],
  "final_image": "One or two lines: the literal final shot, described flat.",
  "lingering_questions": [ { "q": "The question searchers ask verbatim?", "a": "The grounded answer; open mysteries stated AS open." } ],
  "sources": [ { "title": "PAGE TITLE - Wikipedia", "url": "https://..." } ],
  "date_modified": "NOW+05:30"
}
```
Craft: section headings follow QUALITY-BAR subhead rules (meaning, not location). The
`from.json` exemplar runs 6 sections: premise/rules -> season-by-season -> the finale
beat-by-beat -> what it means -> final_image -> open questions. When to author: ended or
limited series, or a just-aired season finale on a tracked flagship.

## Finale predictions (`data/predictions/<slug>.json`)

Forward-looking, speculation EXPLICITLY labelled. Test-enforced contract:
- slug/season checks as endings; `hook` present; sections + theories + sources present;
- **every theory carries a `likelihood` field** - this is the label that marks speculation
  as BollyAI analysis; `sources` >= 1; no viewing claims; no fancy dashes.

Shape (from the `from.json` exemplar):
```json
{
  "slug": "SLUG", "qid": "Q000000", "title": "TITLE", "season_number": 4,
  "hook": "Finale date + platform (sourced), then the cliffhanger state in two sentences.",
  "sections": [ { "heading": "What Episode N Left Hanging", "body": "The aired setup, stated flat, every claim from aired episodes." } ],
  "theories": [
    {
      "title": "The prediction, as a claim",
      "basis": "The aired evidence: which scenes/lines/structures point here. No leaks, no invented beats.",
      "likelihood": "HIGH - BollyAI analysis. One line on why the show's own patterns support it."
    }
  ],
  "lingering_questions": [ { "q": "When is the finale?", "a": "Date + platform + '(Source: ...)' - sourced, never guessed." } ],
  "sources": [ { "title": "...", "url": "https://..." } ],
  "date_modified": "NOW+05:30"
}
```
Conventions: `likelihood` values `HIGH/MEDIUM/LOW - BollyAI analysis.` + one reasoned
line. Rumors ONLY as "reported by <named outlet>" with the URL in sources[]. Never
"sources say". LIFECYCLE: running shows pre-finale only; once the finale airs, the
ending-explained surface takes over - refresh or retire the predictions page in the same
pass and say so in the report. `site/public/sitemap-predictions.xml` regenerates at
build; never hand-edit it.

## Recommendation lists (`data/recommendations/<list-slug>.json`)

Shape (from `best-british-mysteries.json`):
```json
{
  "slug": "LIST-SLUG", "title": "Best X & Y", "kicker": "STREAMING · BRITISH",
  "desk": "streaming", "updated": "NOW+05:30",
  "intro": "The angle that beats the SERP, in BollyAI's voice. Why this tradition/genre, framed with a real point of view.",
  "picks": [
    {
      "ref_type": "series", "slug": "in-catalogue-slug-or-null", "title": "TITLE", "year": 2013,
      "one_line": "One sharp line: what it is + why it earns the slot. QUALITY-BAR register.",
      "where": "Netflix", "bollymeter": 8.6
    }
  ],
  "faq": [ { "q": "The comparison question searchers actually ask?", "a": "A direct, opinionated, grounded answer naming specific picks." } ]
}
```
Rules:
- Picks must be WESTERN (the 2026-06-26 cull stripped non-Western picks; never re-add one).
- `slug` filled when the title exists in `data/series/` (internal link + hub consistency);
  `slug: null` is allowed for a Western title not yet in catalogue (the exemplar does
  this) - flag null-slug picks in your report as authoring candidates.
- For in-catalogue picks: `where` and `bollymeter` must AGREE with the series file
  (platform.value; the peak-season bollymeter). Never contradict the hub.
- 6-10 picks; `updated` bumps only when picks/copy actually change; kicker uses the
  middle-dot style (`STREAMING · BRITISH`), which is legal - only dashes are banned.
- A list earns its page only if the intro states a real angle and every one_line carries
  a specific reason. No filler lists.

## Explainers + episode deep data

`data/explainers/<slug>/` and `data/episodes/<slug>/SxxEyy.json` exist for the deep-dive
`from` cohort. Before authoring either, read the `from` exemplars in full and mirror;
these surfaces are commissioned per-show by the floor, not batch-produced.

## Shared fences + gates

- JSON via python json.dump; slug matches filename; dates ISO-8601 +05:30.
- Dash sweep: `grep -nP '[\x{2012}-\x{2015}]' <file>` -> zero.
- Run the QUALITY-BAR reusable gate scan (section 10) on every file you write - endings
  and predictions carry NO pull_quote mechanism, so ANY attribution-family phrasing must
  be rewritten as BollyAI's own read or carried as a named-outlet citation in sources[].
- QID: copy from the series file (verified there); never re-derive.
- Gates: the surface's pytest file + `python3 -m pytest tests/ -q` before any commit that
  also touches series data.
- Commit: `bollyai: <surface> - <slugs>` + trailer. No push from lanes.
