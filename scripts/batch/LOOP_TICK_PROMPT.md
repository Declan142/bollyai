You are running ONE tick of the BollyAI library buildout loop, in a FRESH session
(this is the hourly "clean context" mechanism - state lives in files, not memory).

READ FIRST, in order:
1. /home/aditya/bollyai/data/_state/library-buildout.md   (ledger: current count, target, rules)
2. /home/aditya/bollyai/scripts/batch/AUTHORING_BRIEF.md   (authoring spec + every honesty fence)
3. /home/aditya/bollyai/RESUME.md                          (project state)

TARGET CHECK: run `ls /home/aditya/bollyai/data/series/*.json | wc -l`. If it is >= 1000,
print "target reached" and EXIT immediately (do nothing else). The launcher also guards this.

EXCLUSION: the slugs i-will-find-you, beef, physical-100, you are RESERVED by the deep
subtitle-grounded lane - never author them here (treat as already-existing; skip).

Then DO EXACTLY ONE BATCH:

1. Pick ~30 NEW WESTERN series across 5 DISJOINT themed pools (US / UK / Hollywood prestige +
   Western-European). BRAND LOCK (Aditya 2026-06-26 "full on western"): English-language leads,
   Western-European non-English (Spanish/German/French/Italian/Nordic) OK. NEVER author Korean,
   Japanese / anime, Indian, or any other non-Western series - the prebuild Western-allowlist
   guard (scripts/guard-offbrand-series.mjs) will FAIL the build. List data/series/ first and
   EXCLUDE every slug that already exists. Curate well-known, well-reviewed shows that have a
   real Wikipedia page and real critical reception - skip anything too obscure or too fresh to ground.

2. Spawn 5 parallel general-purpose subagents (model: sonnet), one per pool. Give each:
   the path /home/aditya/bollyai/scripts/batch/AUTHORING_BRIEF.md, its ~6 slug->title list,
   and the instruction to author grounded JSON per the brief and self-validate with
   `python3 /home/aditya/bollyai/scripts/batch/validate_series.py <its slugs>` before reporting.
   (Subagent fan-out works in this headless mode - it has been verified.)

3. LIGHT reconcile after they finish: for any season dated 2025 or 2026, or any verdict that
   looks generous for a show you know was divisive, quickly WebSearch/WebFetch to verify the
   key stat (RT %, release date, "X exists") and fix or null anything you cannot confirm.
   Confirm each new file has a `genres` array (2-5 tags from the brief's controlled set); add
   it if a subagent missed it.

4. Run: `bash /home/aditya/bollyai/scripts/batch/ingest_batch.sh <all new slugs>`
   (fix -> validate -> posters -> build). RUN IT IN THE FOREGROUND and WAIT for it to finish in
   THIS SAME TURN (use a long Bash timeout, e.g. 1800000 ms). DO NOT background ingest and end the
   turn - if you background it then exit, step 5's commit never runs and the whole batch is LOST
   (this regression hit ticks 1-2 on 2026-06-16). If it fails, fix the reported issues and re-run
   ONCE. If it still fails, append the problem to data/_state/buildout-loop.log and EXIT WITHOUT
   committing. Never commit red.

5. If green: `cd /home/aditya/bollyai && git add data/series/ site/public/img/series/ data/_state/library-buildout.md`
   then commit with a descriptive message ending with the trailer
   `Co-Authored-By: Claude <noreply@anthropic.com>`. Do NOT push and do NOT deploy - the
   Vyom floor (orchestrator) runs the full pytest suite, then pushes + deploys in throttled
   waves. Your job ends at a green local commit.

6. Update the ledger (data/_state/library-buildout.md): bump the "Progress" count and add a
   one-line batch entry with the commit hash and the slugs added.

HARD FENCES (unattended - violating these is the worst failure):
- NEVER deploy, NEVER run IndexNow, NEVER call wrangler, NEVER git push --force, NEVER touch
  .env or ~/.claude/vault.
- Honor EVERY honesty fence in the brief: no first-person viewing claims, no fabricated
  numbers (esp. Indian-platform view counts), no em-dashes, bollymeter null when ungroundable,
  pull-quotes real + attributed + <=25 words.
- Do EXACTLY ONE batch, then exit. Do not start a second batch, do not loop.
- On ANY ambiguity or a gate failing twice: log to data/_state/buildout-loop.log and exit
  cleanly. A skipped tick costs nothing; bad or fabricated data is unacceptable.
