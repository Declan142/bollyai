# BollyAI GHA dry-run report

Generated: 2026-06-12T05:46:01Z

Command: `scripts/ops/dryrun.sh all --report scripts/ops/DRYRUN-REPORT.md`

Result: PASS

No push, deploy, or IndexNow network ping was executed.

## daily-refresh

Status: PASS

Evidence:

```text
Fixture data pull completed with --fixture-mode --live-only against temp data.
Static build completed with npm ci, npm run build, and site/out/index.html present.
IndexNow dry-run: 6 URL(s) for host bollyai.in.
Commit skipped in local dry-run.
Deploy skipped in local dry-run.
```

## friday-surge

Status: PASS

Evidence:

```text
Fixture release-day data pull completed against temp data.
Static build completed with npm ci, npm run build, and site/out/index.html present.
IndexNow dry-run: 6 URL(s) for host bollyai.in.
Commit skipped in local dry-run.
Deploy skipped in local dry-run.
```

## ott-calendar-roll

Status: PASS

Evidence:

```text
OTT calendar regen completed with --fixture-mode against temp data.
Static build completed with npm ci, npm run build, and site/out/index.html present.
IndexNow dry-run: 13 URL(s) for host bollyai.in.
Commit skipped in local dry-run.
Deploy skipped in local dry-run.
```

## tentpole-live

Status: PASS

Evidence:

```text
Tentpole live runner completed with --fixture-mode --force against temp data.
Static build completed with npm ci, npm run build, and site/out/index.html present.
IndexNow dry-run: 6 URL(s) for host bollyai.in.
Commit skipped in local dry-run.
Deploy skipped in local dry-run.
```

## health-digest

Status: PASS

Evidence:

```text
BollyAI weekly health digest generated.
Staleness: 19 stale of 19 checked.
Changed URL sidecar: 13 URLs.
IndexNow last submit: 2831 URLs at 2026-06-12T01:10:55Z.
Resend skipped in local dry-run.
Telegram skipped in local dry-run.
```
