# P07 - REFRESH TICK (model: Sonnet | effort: medium | headless-safe)

You run ONE freshness tick on shipped BollyAI pages in a fresh session - state lives in
files, not memory. You keep pages true; you do not create new surfaces here. Unattended
lane: the worst failure is a quiet fabrication, the second worst is touching something
that is not yours.

## INPUTS
- MAX_SERIES: {{N}}   (default 10)
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST
1. `blueprints/06-REFRESH-OPS.md` - worklist recipe, the returning-season delta, the
   generated-file clobber map (files you must NEVER hand-edit).
2. `blueprints/01-QUALITY-BAR.md` sections 2 and 10.

## HARD FENCES
1. Every changed fact carries a fresh SourceValue envelope (real source, fetched_at now
   +05:30, verified|reported honestly). No source = no change.
2. New seasons appended ONLY when aired or officially dated, with verdict null,
   bollymeter null, empty critic block, audience null, a 60+ char honest holding
   review_body. "Still dropping" is honest; a guessed verdict is not.
3. `date_modified` bumps ONLY on files whose content actually changed (recency rails
   feed on it - churn is pollution).
4. No rich review writing here (P04's lane) - flag candidates instead. No companion
   surface writing (P06's lane) - flag lifecycle changes instead.
5. Never touch the clobber-map files (calendar.json, current-week.json, sitemaps,
   _state logs beyond your one summary line).
6. Never deploy, never IndexNow, never wrangler, never push, never secrets/.env.
7. Do EXACTLY ONE tick, then exit. Ambiguity twice on one item = drop it, log it, move on.

## PROCEDURE
1. **Worklist** (cap MAX_SERIES) via the blueprint 06 snippet, priority:
   (a) `renewal.state == "awaiting"`; (b) `status == "returning"`; (c) latest season year
   >= 2025; tie-break stalest-first via `data/_state/staleness.json` when present.
2. **Verify per series** (WebSearch/WebFetch: Wikipedia first, then official/trade):
   renewal state moved? new season dated? platform moved? status wrong? Capture the
   source URL for every change BEFORE editing.
3. **Apply the returning-season delta** exactly as blueprint 06 writes it: renewal block
   (state/note/source/source_url), status, appended season shell when dated/aired,
   companion lifecycle flags to the report. Python json.dump only.
4. **Gate every touched slug**:
   `python3 scripts/batch/fix_series.py <slugs>` then
   `python3 scripts/batch/validate_series.py <slugs>` -> fix until PASS. Red twice on an
   item = revert THAT file (only if you broke it this session: `git checkout -- <file>`),
   log to `data/_state/buildout-loop.log`, continue.
5. **Commit ONLY files you touched** (list them explicitly in git add):
   `bollyai: refresh - <n> series (<reason classes>)` + trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Never commit red, never `git add -A`
   (the tree may carry other lanes' WIP - not yours).
6. Append one summary line to `data/_state/buildout-loop.log`:
   `<iso> refresh n=<k> renewed=<a> dated=<b> dropped=<c>`.

## RETURN CONTRACT
```json
{
  "refreshed": [{"slug": "", "changed": "<fields>", "source": "<url>"}],
  "new_seasons_appended": ["slug S<n> (<date>)"],
  "review_lane_candidates": ["slug S<n> - <why>"],
  "companion_lifecycle_flags": ["<e.g. 'show-x: finale aired, predictions -> endings'>"],
  "dropped": [{"slug": "", "why": ""}],
  "validator": "<PASS line>",
  "commit": "<hash|none>"
}
```

## DO NOT
Invent a date, a platform, or a renewal. Append an undated rumored season. Bump
date_modified for cosmetic churn. Write review prose. Hand-edit generated files. Start a
second tick. Push, build, deploy, or ping IndexNow.
