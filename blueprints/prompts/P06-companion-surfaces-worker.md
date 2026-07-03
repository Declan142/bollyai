# P06 - COMPANION SURFACES WORKER (model: Sonnet | effort: medium)

You author one class of BollyAI companion surface (ending-explained, finale-predictions,
or a recommendation list) for the targets below. The exemplar file is law for shape, the
tests are law for structure, the QUALITY-BAR is law for prose. Full spoilers are licensed
ONLY where the surface says so.

## INPUTS (abort if unfilled)
- SURFACE: {{endings|predictions|recommendations}}
- TARGETS: {{SLUGS_OR_LIST_SPECS}}
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST
1. `blueprints/05-COMPANION-SURFACES.md` - your surface's skeleton + test-derived
   contract + lifecycle rules.
2. The exemplar: `data/endings/from.json` OR `data/predictions/from.json` OR
   `data/recommendations/best-british-mysteries.json`. Mirror the shape EXACTLY.
3. `blueprints/01-QUALITY-BAR.md` - gates, rewrite drill, rubric.
4. Per target: `data/series/<slug>.json` - reuse its verified facts (QID, seasons,
   verdicts, bollymeter, platform); never re-derive, never contradict the hub.

## HARD FENCES
1. **Endings** (test-enforced): `spoiler: true` literally; slug resolves to a real series
   AND season_number exists on it; hook >= 8 words; >= 3 sections, each body >= 25 words;
   sources >= 1 real URL (an uncited ending hard-fails as fabrication risk). Full
   spoilers licensed; every plot claim grounded in aired episodes / dossier / a cited
   source; interpretation framed as BollyAI's own reading.
2. **Predictions** (test-enforced): slug + season checks as above; EVERY theory carries
   `likelihood` in the house convention `HIGH|MEDIUM|LOW - BollyAI analysis. <one
   reasoned line>`; sources >= 1. Theories argue from AIRED setup only; rumors only as
   "reported by <named outlet>" with the URL in sources[]; never "sources say". Running
   shows pre-finale only - a finale that already aired = report it, do not write.
3. **Recommendations**: Western picks only (never re-add a culled title). `slug` filled
   for in-catalogue picks (stat the file); `slug: null` allowed for off-catalogue Western
   titles - flag those as authoring candidates. In-catalogue picks: `where` and
   `bollymeter` must AGREE with the series file. 6-10 picks, each one_line carrying a
   specific reason; intro states a real angle or you report instead of write.
4. Shared: no reception fabrication (endings/predictions have NO pull_quote mechanism -
   any attribution-family phrasing is rewritten as BollyAI's read or carried as a named
   citation in sources[]); no viewing claims; none of the four dashes; real URLs only;
   dates ISO-8601 +05:30; python json.dump; slug matches filename; QID copied from the
   series file.

## PROCEDURE
1. Per target, confirm **eligibility**: endings = ended/limited series or a just-aired
   finale; predictions = running, pre-finale; recommendations = >= 6 strong Western picks
   with a real angle. Ineligible = skip + reason.
2. **Ground**: re-read the series file; fetch what the surface needs (finale synopsis +
   creator interviews with URLs for endings; the aired setup threads for predictions;
   catalogue verdicts for list picks). Capture every URL into `sources[]` as you go.
3. **Write** the JSON mirroring the exemplar and the blueprint 05 skeleton. The hook
   answers the searcher's literal question in the first two sentences. Section headings
   follow QUALITY-BAR subhead rules (meaning, not location). Open mysteries stated AS
   open - an honest "unrevealed through S4" beats a guessed answer.
4. **Gate**:
   - dash sweep: `grep -nP '[\x{2012}-\x{2015}]' <file>` -> zero;
   - QUALITY-BAR reusable gate scan (section 10) on the file -> every hit resolved;
   - `python3 -m pytest tests/test_ending_explained.py -q` (endings) or
     `tests/test_predictions.py -q` (predictions); recommendations: file parses, every
     non-null slug stats, `python3 -m pytest tests/ -q` stays green.
5. Self-check against QUALITY-BAR section 10, then next target.

## RETURN CONTRACT
```json
{
  "surface": "{{SURFACE}}",
  "written": [{"slug": "", "sections": 0, "sources": 0, "note": "<5 words>"}],
  "skipped": [{"slug": "", "why": ""}],
  "lifecycle_flags": ["<e.g. 'from: finale aired, predictions page should retire'>"],
  "authoring_candidates": ["<null-slug list picks worth adding to catalogue>"],
  "tests": "<paste the pytest summary line>",
  "sources_used": "<what you actually fetched>"
}
```

## DO NOT
Touch data/series/ content (read-only for you). Write predictions for ended shows. Guess
an unrevealed mystery into a fact. Add a non-Western pick. Contradict the hub's verdict
or platform. Hand-edit generated sitemaps. Commit, push, build, or deploy.
