# P07 - REFRESH TICK (model: Sonnet | effort: medium | headless-safe)

You run ONE freshness tick on shipped BollyAI pages in a fresh session - state lives in
files, not memory. You keep pages true; you do not create new surfaces here.

## INPUTS
- MAX_SERIES: {{N}}   (default 10)
- REPO: the directory containing CLAUDE.md; cd there first; all paths repo-relative.

## READ FIRST
1. `blueprints/06-REFRESH-OPS.md` (the playbook - especially the returning-season section).
2. `blueprints/01-QUALITY-BAR.md` sections 2 and 8.

## HARD FENCES (unattended lane - the worst failure is a quiet fabrication)
1. Every changed fact carries a fresh SourceValue envelope (real source, fetched_at now
   +05:30, honest confidence). No source = no change.
2. New seasons get verdict/bollymeter NULL until reception is real. "Still dropping" is
   honest; a guessed verdict is not.
3. `date_modified` bumps ONLY on files whose content actually changed.
4. No rich review writing here (that is the P04 lane) - flag candidates instead.
5. Never deploy, never IndexNow, never wrangler, never push, never touch secrets or .env.
6. Do EXACTLY ONE tick, then exit. Ambiguity twice on one item = drop it, log it, move on.

## PROCEDURE
1. Build the worklist (cap MAX_SERIES), priority order:
   a. `renewal.state == "awaiting"` series (renewal news likely);
   b. `status == "returning"` series (new-season dates move);
   c. series whose latest season year is 2025/2026 (facts still settling).
   Use `data/_state/staleness.json` if present to break ties (oldest first).
2. Per series: WebSearch/WebFetch current status (renewal, dates, platform moves) from
   Wikipedia/official/trade press. Apply the returning-season playbook from the blueprint:
   renewal block, status, append confirmed new seasons (envelope on release_date), retire
   stale renewal notes. Record what changed and the source URL.
3. Gate every touched slug:
   `python3 scripts/batch/fix_series.py <slugs>` then
   `python3 scripts/batch/validate_series.py <slugs>` -> fix until PASS. Red twice on an
   item = revert that item (git checkout -- that file ONLY if you broke it this session),
   log to `data/_state/buildout-loop.log`, continue.
4. If anything beyond data/series changed: `python3 -m pytest tests/ -q` must be green.
5. Commit ONLY the files you touched:
   `bollyai: refresh - <n> series (<reason classes>)` + trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Never commit red.
6. Append one summary line to `data/_state/buildout-loop.log`.

## RETURN CONTRACT
```json
{
  "refreshed": [{"slug": "", "changed": "<fields>", "source": "<url>"}],
  "new_seasons_appended": ["slug S<n>"],
  "review_lane_candidates": ["slug S<n> - <why>"],
  "dropped": [{"slug": "", "why": ""}],
  "validator": "<PASS line>", "commit": "<hash|none>"
}
```

## DO NOT
Invent a date, a platform, or a renewal. Bump date_modified for cosmetic churn. Write
review prose. Start a second tick. Push, build, deploy, or ping IndexNow.
