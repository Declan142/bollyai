# P06 - COMPANION SURFACES WORKER (model: Sonnet | effort: medium)

You author one class of BollyAI companion surface (ending-explained, finale-predictions,
or a recommendation list) for the slugs below. The exemplar file is law for shape; the
QUALITY-BAR is law for prose. Full spoilers are licensed ONLY where the surface says so.

## INPUTS (abort if unfilled)
- SURFACE: {{endings|predictions|recommendations}}
- TARGETS: {{SLUGS_OR_LIST_SPECS}}
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST
1. `blueprints/05-COMPANION-SURFACES.md` (your surface's section + shared fences).
2. The exemplar for your surface: `data/endings/from.json` OR `data/predictions/from.json`
   OR `data/recommendations/best-british-mysteries.json`. Mirror the shape EXACTLY.
3. `blueprints/01-QUALITY-BAR.md`.
4. For each target: `data/series/<slug>.json` (facts you may reuse: verdicts, bollymeters,
   seasons, QID - never re-derive, never contradict the hub).

## HARD FENCES
1. Endings: `spoiler: true`, full spoilers licensed; every plot claim grounded in aired
   episodes / dossier / a cited source in `sources[]`. Interpretation is framed as
   BollyAI's own reading.
2. Predictions: theories framed as BollyAI's reasoned read of aired setup. Rumors only as
   "reported by <named outlet>" with the URL in sources[]. Never "sources say". Running
   shows only; a finale that already aired = report it, do not write predictions for it.
3. Recommendations: EVERY pick must exist at `data/series/<slug>.json` (stat each one).
   Western catalogue only. Each pick's WHY grounds in the catalogue's own verdict/bollymeter.
   No filler lists: if the angle does not beat a generic SERP page, report instead of write.
4. Shared: no reception fabrication, no viewing claims, no em/en dashes, real URLs only,
   dates ISO-8601 +05:30, python json.dump only, slug matches filename.

## PROCEDURE
1. Per target: confirm eligibility (endings: ended/limited or finale aired; predictions:
   running pre-finale; recommendations: >= 6 strong in-catalogue picks).
2. Ground: re-read the series file; fetch what the surface needs (finale synopsis, creator
   interviews with URLs for endings; aired-setup threads for predictions).
3. Write the JSON mirroring the exemplar. Hook answers the searcher's literal question in
   the first two sentences. Sections carry one idea each with evocative headers
   (QUALITY-BAR subhead rules apply).
4. Gate: dash-grep your file, then run the surface's test:
   `python3 -m pytest tests/test_ending_explained.py -q` (endings) or
   `python3 -m pytest tests/test_predictions.py -q` (predictions); recommendations:
   validate JSON parses + every pick stats + `python3 -m pytest tests/ -q` stays green.
5. Self-check against QUALITY-BAR section 8.

## RETURN CONTRACT
```json
{
  "surface": "{{SURFACE}}",
  "written": [{"slug": "", "note": "<5 words>"}],
  "skipped": [{"slug": "", "why": ""}],
  "tests": "<paste the pytest summary line>",
  "sources_used": "<what you actually fetched>"
}
```

## DO NOT
Touch data/series/ content (read-only for you). Write predictions for ended shows. Add a
non-catalogue or non-Western pick. Hand-edit generated sitemaps. Commit, push, build, deploy.
