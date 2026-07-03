# BLUEPRINT 05 - Companion surfaces (endings, predictions, lists, explainers)

Use when: authoring the high-intent SEO surfaces that orbit a series hub. Prompt:
`prompts/P06`. Every surface inherits the full QUALITY-BAR; the spoiler POSTURE is the
only thing that changes per surface.

## Surface map

| Surface | Data | Route | Test gate |
|---|---|---|---|
| Ending explained | `data/endings/<slug>.json` | `/series/<slug>/ending-explained` | `tests/test_ending_explained.py` |
| Finale predictions | `data/predictions/<slug>.json` | `/series/<slug>/finale-predictions` | `tests/test_predictions.py` |
| Recommendation lists | `data/recommendations/<list-slug>.json` | browse/lists surfaces | (validated at build) |
| Topic explainers | `data/explainers/<slug>/...` | `/series/<slug>/explainer/<topic>` | mirror `from/` exemplars |
| Episode deep data | `data/episodes/<slug>/SxxEyy.json` | episode page enrichment | mirror `from/` exemplars |
| Where to watch | COMPUTED from series JSON | `/series/<slug>/where-to-watch` | multi-season only (>= 2 seasons); no authoring |

Exemplars are law: before writing a surface, read its `from.json` (or `from/` dir) exemplar
and mirror the shape exactly. Run the surface's pytest file after writing.

## Ending explained (`data/endings/<slug>.json`)

- Shape (mirror `data/endings/from.json`): slug, qid, title, season_number,
  `spoiler: true`, hook, sections[], final_image, lingering_questions[], sources[],
  date_modified.
- FULL spoilers are the point here - this is the licensed spoiler surface.
- Still banned: invented reception, invented beats, dashes, viewing claims. Every plot
  claim grounds in the dossier, aired-episode synopses, or a cited source in `sources[]`.
- `sources[]` must be real URLs actually consulted. Empty sources on interpretive claims =
  reframe as BollyAI's own reading ("BollyAI's read of the final shot...").
- When to author: ended/limited series, or a season finale that just aired for a tracked
  flagship. The hook answers the searcher's literal question in the first two sentences.

## Finale predictions (`data/predictions/<slug>.json`)

- Shape (mirror `data/predictions/from.json`): slug, qid, title, season_number, hook,
  sections[], theories[], lingering_questions[], sources[], date_modified.
- Predictions are FRAMED as predictions - BollyAI's reasoned theories from aired setup,
  never leaks presented as fact, never "sources say". A rumor may appear only as
  "reported by <named outlet>" with the URL in sources[].
- Lifecycle rule: predictions pages are for RUNNING shows pre-finale. After the finale
  airs, the ending-explained surface takes over; refresh or retire the prediction page in
  the same pass (note it in the report).
- `site/public/sitemap-predictions.xml` regenerates at build - do not hand-edit it.

## Recommendation lists (`data/recommendations/<list-slug>.json`)

- Shape (mirror `best-british-mysteries.json`): slug, title, kicker, desk, updated,
  intro, picks[], faq[].
- HARD RULE: every pick references an EXISTING `data/series/<slug>.json` (Western
  catalogue only - the 2026-06-26 cull stripped non-Western picks; never re-add one).
  Check each pick with a stat on the file before writing.
- A list earns its page only if it beats the SERP: a real angle in the kicker/intro, picks
  with one-line WHY each grounded in the catalogue's own verdicts/bollymeters, FAQ answering
  actual searcher questions. No filler lists.
- `updated` bumps only when picks/copy actually change.

## Shared fences

- JSON via python json.dump only; slug matches filename; date fields ISO-8601 +05:30.
- No em/en dashes anywhere; run a dash grep before validating.
- QID: from the series file (already verified there); never re-guess.
- After writing: run the surface's pytest file + `python3 -m pytest tests/ -q` before any
  commit that also touches series data.
- Commit: `bollyai: <surface> - <slugs>` + standard trailer. No push from lanes.
