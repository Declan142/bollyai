# BOLLYAI REVIEW-BLITZ - WORKER LANE RUNBOOK
Vyom, 2026-06-13. How one writer lane pulls a slice and produces perfection-gated reviews.
Read `BLITZ-PLAN.md` (master plan) and `COMPETITOR-STUDY.md` + `REVIEW-HOUSE-STYLE.md` first.

> A "lane" is one git worktree owning a DISJOINT slice of the work queue. Lanes draft on the
> high-throughput endpoint (NANO), polish on a quality endpoint (FULL / MINI / KIMI / DSV4),
> gate locally, and NEVER push or deploy. The floor reconciles and wave-deploys (P3).

---

## LOCAL CAPACITY - READ THIS FIRST (the box is the bottleneck, NOT the model rate limits)
Host = 16 cores / 31GB RAM. ~9 lanes already drives load ~2x. The model endpoints have spare
RPM; THIS MACHINE does not. So the scaling rules invert what you would normally do:

1. **Scale with REMOTE calls, not more lanes.** The parallelism that actually scales is async
   batches across the 5 endpoints (FULL/NANO/MINI/KIMI/DSV4) fired from WITHIN a few lanes -
   those are network-I/O-bound and cost almost no local CPU. Spawning more worktree lanes burns
   cores for near-zero gain. More remote calls, fewer local lanes.
2. **NEVER run `npm run build` or design-reviewer in a lane.** Headless Chrome + the Next.js
   build storm all 16 cores and stall every other lane. Lanes self-check with
   `validate_series.py` (cheap, fast) ONLY. The FLOOR runs the ONE central build + design-review
   + deploy per wave, serialized. Per-lane pytest is also floor-only (see section 6).
3. **Keep TOTAL fleet <= ~10-11 lanes.** Do NOT spawn a fresh worktree swarm. P2 = REPURPOSE
   freed lanes (MW / BB / PA, etc.) into writer lanes so the net lane count stays flat.

If `uptime` load is already above ~1.5x core count (>24 on this box), do NOT add a lane - add
remote batch width inside an existing lane instead.

---

## 0. The two-pass quality mechanism (why this works)
DRAFT (cheap, parallel, current house-style understanding) -> FINAL POLISH (quality endpoint,
re-sends the FULL upgraded house-style contract, draft->edit) -> validate gate. The re-sent
contract on the polish pass IS the quality. Never call an episode "done" without the polish
pass. `build_review.py` does both passes in one run; you choose the model per pass via env.

## 1. The five endpoints (separate rate limits = real parallelism)
| key | model | endpoint | role |
|---|---|---|---|
| `FULL` | gpt-5-4 | azure-cog eastus2 | quality finals (load-bearing, cap-3, serial+backoff) |
| `NANO` | gpt-5.4-nano | azure-cog eastus2 | bulk DRAFTS + QC (250 RPM, massively parallel) |
| `MINI` | gpt-5-4-mini | azure-cog eastus2 | 2nd quality / draft stream (cap-3) |
| `KIMI` | kimi-k2-6 | azure-foundry eastus2 | 3rd quality stream (thinking; handled internally) |
| `DSV4` | deepseek/deepseek-v4-pro | openrouter | 4th quality stream, OFF-Azure, different corpus |

Because the four quality endpoints (FULL/MINI/KIMI/DSV4) hit DIFFERENT services, they do not
share a 429. The win is firing them concurrently AS ASYNC REMOTE BATCHES from within a small
number of lanes (see section 5) - NOT spawning a lane per endpoint. Remote calls are
I/O-bound and nearly free on local CPU; lanes are not. More remote width, fewer local lanes.

## 2. Set up your lane (worktree isolation - HARD fence)
**Before you create a lane:** do NOT spawn a fresh swarm. P2 REPURPOSES already-running freed
lanes (MW / BB / PA, etc.) - keep the TOTAL fleet <= ~10-11. If `uptime` load is already > ~24
on this 16-core box, do not add a lane; add remote batch width in an existing one (section 5).
Only create a new worktree if you are turning an existing freed lane into a writer.
```bash
N=1                      # your lane number
cd ~/bollyai
git worktree add ../bollyai-wt-blitz-$N -b blitz/$N
cd ../bollyai-wt-blitz-$N
# symlink the heavy/shared dirs so you don't duplicate them per lane:
ln -s ~/bollyai/site/node_modules site/node_modules
ln -s ~/bollyai/data/subtitles    data/subtitles      # dossiers live here (read-only for you)
ln -s ~/bollyai-subs ~/bollyai-subs 2>/dev/null || true
```
Rules: cd into YOUR worktree first. Own ONLY your named slice. No cross-lane file edits. NO
push, NO deploy, NO `wrangler`. You write `data/series/<slug>.json` for YOUR slugs only.

## 3. Get your key into the env once (never echoed, never logged)
```bash
# Azure account key (covers FULL/NANO/MINI/KIMI). Pull silently from vault or az CLI:
export AZURE_FOUNDRY_KEY="$(grep -m1 -i 'API Key' ~/.claude/vault/azure-foundry.md | sed -E 's/.*Key:\*?\*? *//')"
# OpenRouter key (covers DSV4):
export OPENROUTER_API_KEY="$(grep -m1 -iE '^- (\*\*)?API Key' ~/.claude/vault/openrouter.md | sed -E 's/.*Key:\*?\*? *//')"
```
Exporting `AZURE_FOUNDRY_KEY` lets every `build_review.py` call skip an `az` subprocess (200
lanes x 1 az call = pain). If you skip this, the script falls back to the az CLI automatically.
NEVER print these. NEVER paste a key into a commit, a log, or chat.

## 4. Pull your slice from the queue
The queue is `data/_state/blitz-queue.json` (built by `bolly-audit`): per series/season/episode
coverage + quality flags, ranked by traffic. Take the top INCOMPLETE series in your assigned
slice. Work top-traffic first. Stay disjoint from other lanes and from work:5's new-series.

## 5. Draft + polish (one episode = the unit; an ASYNC BATCH = how you scale)

**The unit** (one episode): draft on NANO, polish on a quality endpoint.
```bash
BOLLYAI_DRAFT_MODEL=NANO BOLLYAI_FINAL_MODEL=FULL \
  python3 scripts/subtitles/build_review.py <slug> <season> <episode>
```

**The scaling pattern (USE THIS) - async remote batch WITHIN your lane.** A single lane fans
many episodes out concurrently, round-robining the polish across all four quality endpoints so
no one 429s. These are network-I/O calls, so ~5-6 in flight costs almost no local CPU. This is
the parallelism that scales on this box - NOT more lanes.
🚨 **CONCURRENCY RULE (data-race - learned the hard way):** `build_review.py` does a
read-modify-WRITE of the ENTIRE `data/series/<slug>.json`. Two episodes of the SAME series
running at once = last-write-wins = lost reviews. So: **parallelise ACROSS series, run episodes
SERIALLY within a series.** Never background two episodes of the same slug.
```bash
mkdir -p logs slices
# One file per series: slices/<slug>.eps with "season<TAB>episode" lines (your disjoint slice).
ENDPOINTS=(FULL MINI KIMI DSV4)     # round-robin polish across the 4 quality streams

run_series () {                     # serial within a series -> no JSON race
  local slug="$1" i=0 s e fin
  while IFS=$'\t' read -r s e; do
    [ -z "$s" ] && continue
    fin=${ENDPOINTS[$(( i % ${#ENDPOINTS[@]} ))]}
    BOLLYAI_DRAFT_MODEL=NANO BOLLYAI_FINAL_MODEL=$fin \
      python3 scripts/subtitles/build_review.py "$slug" "$s" "$e" \
      > "logs/${slug}_S${s}E${e}.log" 2>&1
    i=$((i+1))
  done < "slices/${slug}.eps"
}

# Launch up to ~5-6 SERIES concurrently (one in-flight episode each).
for f in slices/*.eps; do
  slug=$(basename "$f" .eps)
  run_series "$slug" &
  while [ "$(jobs -r | wc -l)" -ge 6 ]; do wait -n; done   # cap series-workers, not episodes
done
wait
```
Why this and not more lanes: 5-6 backgrounded `build_review.py` waiting on remote APIs is
near-zero CPU; each extra worktree lane is real load. Add batch width (more SERIES in flight),
not lanes. NANO (250 RPM) absorbs every draft; the four polish endpoints have separate limits
so they run truly parallel. If your slice has fewer ready series than your concurrency cap,
that is fine - you are bounded by ready dossiers, not by the cap.

Backward-compatible defaults: with NO env vars, both passes run on FULL (gpt-5-4), exactly as
the buildout loop does today. The env knobs only ever ADD routing; they never change the
default. `BOLLYAI_REVIEW_MODEL=<key>` sets both passes at once if you want a single endpoint.

Notes:
- KIMI is a thinking model: `build_review.py` forces max_tokens >= 32000 and appends the
  prose-only guard internally, and falls back to reasoning_content if `content` is empty. You
  do nothing special.
- DSV4 (DeepSeek V4 Pro) is paid-but-cheap on OpenRouter and a DIFFERENT training corpus -
  useful as a voice-diversity stream so all finals don't sound like one model.
- The script strips em/en-dashes and leaked subtitle timestamps as belt-and-suspenders, syncs
  bollymeter to the verdict score, and promotes a critic_note to pull_quote when eligible.

## 6. Gate locally BEFORE you call anything done (CHEAP gates only - the box is the bottleneck)
Lanes run ONLY the two cheap gates below. Do NOT run pytest, `npm run build`, or design-reviewer
in a lane - those storm all 16 cores and stall every other lane. The FLOOR runs pytest + the one
central build + design-review + deploy per wave, serialized (P3).
```bash
# a) honesty-fence validator on the slugs you touched (cheap, fast - this is your gate):
python3 scripts/batch/validate_series.py <slug> [<slug> ...]
# b) em/en-dash sweep MUST be empty for the files you touched:
grep -rPl "\x{2014}|\x{2013}" data/series/<slug>.json && echo "EM-DASH FOUND - FIX" || echo "dash-clean"
```
A review only counts as "done" when: validator passes, dash-clean, word count in 1,200-1,700,
it has a real season-arc sentence, the verdict one_liner is a take (not a summary), and (if
groundable) a bollymeter + attributed pull_quote. If a series is too thin to ground, SKIP it
and note why - a missing file is correct, a fabricated one is a fireable offense.

## 7. Quality self-check per review (the house-style rubric, fast pass)
Before moving on, eyeball the polished body against the v2 contract:
- [ ] Has a THESIS (argues one claim), not a recap.
- [ ] Cold-open uses ONE opener-menu move and does not repeat the move used elsewhere in the series.
- [ ] At least one season-arc sentence in the body AND one in The Verdict.
- [ ] Links are intra-series or factually-grounded cross-series only. No invented "watch-next."
- [ ] Restraint held: two-three earned lines, not twenty reaching ones. No kill-list tells.
- [ ] Indian-cinema literacy where natural; English-primary; third person; no viewing claims.
- [ ] Score is honest (a 6 is allowed). bollymeter null if ungroundable (full object or null).

## 8. Commit within your worktree (NOT push)
```bash
git add data/series/<slug>.json
git commit -m "blitz(lane $N): rich reviews <slug> S<n> [thesis+arc+links]"
```
Commit freely inside your worktree. Do NOT push, do NOT deploy. When your slice is gated-green
(validate_series + dash-clean), report to the floor and stop. The floor merges all lanes, runs
the heavy gates ONCE, serialized - pytest + `npm run build` + design-reviewer >= 7.5 - then
wave-deploys (CF Pages Direct Upload) with IndexNow <= 85/wave. Those heavy gates are the
floor's job precisely because they would storm this box if every lane ran them.

## 9. Report (every milestone or block)
```bash
conductor outcome bollyai done|partial|fail "<one line: lane N, slugs, eps gated, endpoint>"
```

## FENCES (repeat, because they are build-breaking)
- LOCAL CAPACITY: NO per-lane `npm run build` / design-reviewer / pytest (they storm 16 cores).
  Lanes gate with validate_series + dash-sweep ONLY. Scale with remote batch width, not lanes.
  Total fleet <= ~10-11; repurpose freed lanes, never spawn a fresh swarm.
- Worktree isolation: own slice only, no cross-lane edits, NO push/deploy from a lane.
- All 10 honesty fences hold. No em-dash. Never serve subtitle text or TMDB images.
- Never echo an Azure or OpenRouter key. Verify-or-strip every specific. Unsure -> null/omit.
- `build_review.py` stays backward-compatible: default behavior unchanged, env only adds routing.
- Surface to the floor (do not decide): real-money, off-topic-from-cinema, destructive ops.
