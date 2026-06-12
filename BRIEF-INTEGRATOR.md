# INTEGRATOR: bolly-quality + bolly-ottfill merge (main repo, 2026-06-12 evening)
1. `git merge --no-edit agents/bolly-quality-0612c` then `git merge --no-edit agents/bolly-ottfill-0612c`.
   Generated conflicts (site/public/sitemap*.xml, search-index.json, last.txt): --ours. Source/data conflicts: resolve keeping both lanes' intent; irreconcilable = STOP + report.
2. `python3 -m pytest tests/` + `cd site && npm run build` green.
3. NO push/deploy/IndexNow (floor, credentialed). `conductor outcome bollyai done|partial|fail "<line>"`
