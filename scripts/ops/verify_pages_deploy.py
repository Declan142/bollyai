#!/usr/bin/env python3
"""Assert that a Cloudflare Pages production deploy actually LANDED.

A wrangler step reporting success is DELIVERED, not LANDED: the historic BollyAI
failure was five green crons whose deploy step was silently skipped for 232
consecutive runs while bollyai.in stayed frozen for 29 days. This script closes
that gap by asking Cloudflare - not the action - what production is currently
serving, and failing loudly when the newest successful production deployment is
older than the run that just claimed to have published one.

Read-only: a single GET against the Pages deployments endpoint. Never mutates.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

API_ROOT = "https://api.cloudflare.com/client/v4"


_TIMESTAMP = re.compile(
    r"^(?P<base>\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2})"
    r"(?:\.(?P<fraction>\d+))?"
    r"(?P<offset>Z|[+-]\d{2}:?\d{2})?$"
)


def parse_cf_timestamp(value: str) -> datetime:
    """Parse RFC3339 as Cloudflare emits it: 1-9 fractional digits, 'Z' suffix.

    ``datetime.fromisoformat`` rejects anything but 3 or 6 fractional digits before
    Python 3.11, and Cloudflare mixes 4, 6 and 7, so the fraction is normalised to
    microseconds here rather than trusted.
    """
    match = _TIMESTAMP.match(value.strip())
    if match is None:
        raise ValueError(f"not an RFC3339 timestamp: {value!r}")
    fraction = (match["fraction"] or "")[:6].ljust(6, "0")
    offset = match["offset"] or "Z"
    if offset == "Z":
        offset = "+00:00"
    elif ":" not in offset:
        offset = f"{offset[:3]}:{offset[3:]}"
    return datetime.fromisoformat(f"{match['base']}.{fraction}{offset}").astimezone(timezone.utc)


def newest_successful_production(payload: dict) -> dict | None:
    """Newest production deployment whose final stage succeeded."""
    candidates = []
    for deployment in payload.get("result") or []:
        if deployment.get("environment") != "production":
            continue
        if ((deployment.get("latest_stage") or {}).get("status")) != "success":
            continue
        candidates.append(deployment)
    if not candidates:
        return None
    return max(candidates, key=lambda d: parse_cf_timestamp(d["created_on"]))


def fetch_deployments(account_id: str, project: str, token: str, timeout: int = 30) -> dict:
    url = f"{API_ROOT}/accounts/{account_id}/pages/projects/{project}/deployments?env=production&per_page=10"
    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    if not payload.get("success"):
        raise RuntimeError(f"Cloudflare API refused the request: {payload.get('errors')}")
    return payload


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", default="bollyai-in")
    parser.add_argument("--max-age-minutes", type=int, default=30)
    parser.add_argument("--now", default=None, help="ISO timestamp override, for tests")
    args = parser.parse_args(argv)

    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    account_id = os.environ.get("CLOUDFLARE_ACCOUNT_ID", "").strip()
    if not token or not account_id:
        print(
            "::error title=Cannot verify deploy::CLOUDFLARE_API_TOKEN / CLOUDFLARE_ACCOUNT_ID "
            "are required to confirm the deploy landed.",
            file=sys.stderr,
        )
        return 1

    try:
        payload = fetch_deployments(account_id, args.project, token)
    except (urllib.error.URLError, RuntimeError, ValueError) as exc:
        print(f"::error title=Cannot verify deploy::{exc}", file=sys.stderr)
        return 1

    deployment = newest_successful_production(payload)
    if deployment is None:
        print(
            f"::error title=No production deployment::Cloudflare Pages project '{args.project}' "
            "has no successful production deployment at all.",
            file=sys.stderr,
        )
        return 1

    now = datetime.now(timezone.utc) if args.now is None else parse_cf_timestamp(args.now)
    created = parse_cf_timestamp(deployment["created_on"])
    age = now - created

    if age > timedelta(minutes=args.max_age_minutes):
        print(
            f"::error title=Deploy did not land::Newest successful production deployment of "
            f"'{args.project}' is {int(age.total_seconds() // 60)} minutes old "
            f"(id={deployment.get('id')}, created_on={deployment['created_on']}), older than the "
            f"{args.max_age_minutes}-minute freshness budget. The workflow claimed to deploy but "
            "production did not move.",
            file=sys.stderr,
        )
        return 1

    print(
        f"production deploy landed: id={deployment.get('id')} created_on={deployment['created_on']} "
        f"age={int(age.total_seconds())}s url={deployment.get('url')}"
    )
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as handle:
            handle.write(
                f"Production deploy landed: `{deployment.get('id')}` at {deployment['created_on']}\n"
            )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
