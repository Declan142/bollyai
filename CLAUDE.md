# BollyAI — project guide for any Claude/Vyom session opened in this repo

> Global empire rules (verify-or-strip, no em-dash, infra hard-rules, safety, delegation)
> are inherited from `~/.claude/CLAUDE.md`. This file is the PROJECT LAYER only.

## What this is

Western cinema/TV/box-office answer engine. Disclosed-AI critic: "BollyAI has NOT watched
anything. BollyAI has read everyone who has." Live: https://bollyai.in. Stack: Next.js static
export, CF Pages Direct Upload, JSON-in-repo (no PocketBase), GH Actions crons. Desks:
Hollywood (films) + Streaming (Western / global series).

🚨 BRAND LOCK (Aditya, 2026-06-24): bollyai = Western series + movies, NOT pan-India cinema
(despite the legacy name). Indian-cinema content is OFF-BRAND. 117 Indian-origin series +
their 24 ending-explainers + 1 wholly-Indian recommendation list were archived (reversible)
to `data/_archive/indian*/`. A prebuild guard (`scripts/guard-offbrand-series.mjs`, wired in
`site/package.json`) FAILS the build if any unprotected Indian-language series (hi/ur/ta/te/
ml/kn/bn/mr/pa/gu) reappears in `data/series/`. Do NOT author Indian-cinema pages. OPEN
QUESTION (not yet ruled): Korean dramas + anime + India-targeted lists currently remain.

## BollyAI honesty fences (HARD - a violation fails the validator and the build)

These are build gates enforced by `tests/` and `scripts/batch/validate_series.py`. Violate
one and the build breaks. They are non-negotiable.

1. **No first-person viewing claims.** Never: "I watched / I saw / maine dekhi / humne dekha /
   when I saw / my screening." BollyAI writes in third person about what critics and audiences
   reported. Gate #1 in `tests/test_viewing_claim.py` (29 assertions, 0 tolerance).

2. **No em-dashes or en-dashes anywhere** (`--`, `-`). Use a spaced hyphen ` - ` or rephrase.
   Gate enforced across all prose fields.

3. **No fabricated Indian OTT numbers.** JioHotstar, Netflix India, SonyLIV, Prime Video India,
   ZEE5 do NOT publish per-title viewership. NEVER invent "X million views / streams." Netflix
   global hours-viewed / Top-10 ARE real and citable - use only with attribution. RT % only
   with real critic sample size. Unsure = omit or set null.

4. **bollymeter null if ungroundable.** `{"score": <0-10 float>, "basis": "<1-2 grounded
   sentences>"}` only when you can cite real reception. If not: set the entire `bollymeter`
   field to `null` (never a partial object). Never inflate scores.

5. **pull_quotes = real + attributed.** Each `{text, source, url}`: real quote, real URL,
   <=25 words. Use `[]` if none verified. Never invent a quote.

6. **No TMDB images served.** TMDB ToS bans ad-revenue + image-hosting use. TMDB = metadata
   only. Served images = self-hosted official press via harvester under Sec 52(1)(a) +
   attribution + /takedown page. No JustWatch scrape, no IMDb datasets, no Letterboxd.

7. **BO publish rule.** >= 2 sources within 10% = "trade estimate." 10-25% divergence = publish
   LOWER with caveat. Else no number. Budgets/salaries: never auto-publish.

8. **Never serve subtitle text.** Subtitles are fuel for analysis (ending-explained, recaps,
   episode guides), not cargo to redistribute. Dialogue quotes <= 25w with citation only.

9. **Wikidata QID: never guess.** If you cannot confidently identify it from Wikipedia sidebar
   or wikidata.org search, set `qid` to `null`.

10. **If too thin to ground, skip.** A missing file is correct; a fabricated one is a fireable
    offense. Series premiered days ago with no reviews = SKIP, note why in report.

## Quality gates - pass all before calling anything "done"

- **Honesty fence validator:** `python3 scripts/batch/validate_series.py <slug...>` - must
  pass on all written files before commit.
- **Full test suite:** `python3 -m pytest tests/` (150 content tests + gate assertions).
- **Build green:** `cd site && npm run build` - `assert-no-aggregate-rating` is a hard check.
- **design-reviewer >= 7.5** before any frontend change ships (anti-slop gate).
- **No em-dash 3-layer:** prompt + QA + auto-strip. Check with `grep -r -- '--' data/`.

## Deploy / infra

CF Pages Direct Upload (manual/floor) + a daily-refresh GHA cron that also build+deploys:
`npx wrangler pages deploy site/out --project-name=bollyai-in --branch=main`
Creds (manual deploy): `~/.claude/vault/cloudflare-master.md` (empire-god token, All-accounts).
ACCOUNT_ID=18c1d9f76c2153a2dde6efa561116b17. 🚨 `vault/cloudflare.md` Pages token does NOT
scope bollyai-in (auth 10000) - do NOT use it here; god token is the standing creds (Aditya
2026-06-21 "use god token for now"). The GHA daily-refresh uses its own working
`CLOUDFLARE_API_TOKEN` GH secret (runs green) - leave it; do not put the god token in GH secrets.
Build self-guards the CF 20k-file cap via `postbuild:filecap` (strips avif + hard-fails if >=20k).

IndexNow: content-hash-gated re-pings only. Script: `scripts/indexnow_ping.sh` (throttled,
85 URLs/wave max). Google Search Console: manual verify required (Aditya's Google login).

Hourly buildout loop: `data/_state/buildout-loop.log` + single-flight flock + BUILDOUT_STOP
flag. To stop: `touch data/_state/BUILDOUT_STOP`. Loop commits but does NOT deploy - new
series go live only on manual deploy (velocity-throttled by design).

**Deploy/push authority: GRANTED to Vyom (Aditya, 2026-06-13)** - hard conditions:
push only with full test suite green; deploy only with tests + `npm run build` green
(+ design-reviewer >= 7.5 for any frontend change); IndexNow stays hash-gated +
throttled. Force-push / history rewrite / branch deletion remain DENIED, always.

## Repo conventions

- Schema: `site/lib/series.ts` (Series / SeriesSeason / EpisodeReview types). Match exactly.
- Gold exemplar: `data/series/squid-game.json` - mirror shape, depth, tone.
- State / ledger: `data/_state/library-buildout.md` - read before authoring batches.
- Authoring brief (full): `scripts/batch/AUTHORING_BRIEF.md` - read in full before writing.
- Batch toolchain: `validate_series.py`, `fix_series.py`, `ingest_batch.sh`, `harvest_genres.py`.
- Poster path convention: `/img/series/<slug>/poster.jpg` (harvested separately, write JSON
  block only; SVG fallback if no real poster found).
- `canonical_industry` is ALWAYS the string `"streaming"`.
- SourceValue envelope required for: `qid`, `title`, `original_language`, `platform`, each
  `season.release_date`. `confidence`: `"verified"` (Wikipedia/Wikidata/official) or
  `"reported"` (trade press).
- `date_modified`: ISO-8601 +05:30. `_quarantine`: `[]`.
- Genres: controlled set from AUTHORING_BRIEF.md Step 4 (no nationality tags like
  "Korean Drama"). 2-5 facet tags max.
- Spark (`gpt swarm`) silently no-ops repo edits - diff-verify always; use Claude agents for
  content generation, not Spark.

## Don't

- Never serve TMDB images (ToS ban on ad-revenue + image-hosting use).
- Never invent Indian OTT view counts (platforms do not publish them).
- Never guess a Wikidata QID.
- Never write first-person viewing claims in any language.
- Never set a partial bollymeter object - full object or null.
- Never overwrite an existing `data/series/<slug>.json` without reading it first.
- Deploy/push: standing grant (2026-06-13) under the conditions above - tests/build/design
  gates are the approval now; skip a gate = no ship.
- Never use `gpt swarm` (Spark) for repo edits - exits 0 silently even when it no-ops tasks.
- Never add off-topic subdomains to bollyai.in (apex topical map locked to pan-India cinema).
- Never touch TMDB watch-providers "JustWatch scrape" path - attribution only via TMDB API.

---
*Project layer only. Empire rules at `~/.claude/CLAUDE.md`. State at `./RESUME.md`.*
