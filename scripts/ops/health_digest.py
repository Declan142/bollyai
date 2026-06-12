#!/usr/bin/env python3
"""Build and optionally send the weekly BollyAI ops digest."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
RESEND_ENDPOINT = "https://api.resend.com/emails"


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def read_json(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def git_log_lines() -> list[str]:
    command = [
        "git",
        "log",
        "--since=7 days ago",
        "--pretty=format:%h %s",
        "--",
        ".github",
        "data",
        "engine",
        "scripts",
        "site",
        "tests",
    ]
    try:
        completed = subprocess.run(
            command,
            cwd=REPO_ROOT,
            check=True,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []
    return [line for line in completed.stdout.splitlines() if line.strip()]


def sitemap_url_count() -> int | None:
    sitemap = REPO_ROOT / "site/public/sitemap.xml"
    if not sitemap.exists():
        return None
    text = sitemap.read_text(encoding="utf-8")
    return text.count("<loc>")


def build_digest(data_dir: Path) -> str:
    staleness = read_json(data_dir / "_state/staleness.json", {})
    changed = read_json(data_dir / "_state/changed-urls.json", {})
    indexnow = read_json(data_dir / "_state/indexnow_ping_state.json", {})
    commits = git_log_lines()
    page_count = sitemap_url_count()

    stale_count = staleness.get("stale_count", 0)
    checked_count = staleness.get("checked_count", 0)
    changed_count = len(changed.get("urls", [])) if isinstance(changed, dict) else 0
    last_indexnow_count = indexnow.get("last_count", "not recorded")
    last_indexnow_at = indexnow.get("updated_at", "not recorded")

    lines = [
        "BollyAI weekly health digest",
        f"Generated: {utc_now()}",
        "",
        "Snapshot",
        f"- Staleness: {stale_count} stale of {checked_count} checked",
        f"- Changed URL sidecar: {changed_count} URLs",
        f"- IndexNow last submit: {last_indexnow_count} URLs at {last_indexnow_at}",
    ]
    if page_count is not None:
        lines.append(f"- Sitemap index entries: {page_count}")

    lines.extend(["", "Recent commits"])
    if commits:
        lines.extend(f"- {line}" for line in commits[:12])
    else:
        lines.append("- No commits found in the last 7 days")

    lines.extend(["", "Action notes"])
    if stale_count:
        lines.append("- Review stale live trackers and decide whether source outage is expected")
    else:
        lines.append("- No stale live trackers in the latest local report")
    if changed_count == 0:
        lines.append("- Changed URL sidecar is empty or missing")
    else:
        lines.append("- Changed URL sidecar is populated for the next armed delta ping")

    return "\n".join(lines) + "\n"


def send_resend(subject: str, body: str) -> None:
    api_key = os.environ.get("RESEND_API_KEY", "")
    to_email = os.environ.get("DIGEST_TO", "") or os.environ.get("RESEND_TO", "")
    from_email = os.environ.get("DIGEST_FROM", "") or "BollyAI Ops <ops@bollyai.in>"

    if not api_key or not to_email:
        print("health_digest.py: Resend env missing; skipping send.", file=sys.stderr)
        return

    payload = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "text": body,
    }
    request = urllib.request.Request(
        RESEND_ENDPOINT,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            if response.status >= 300:
                raise RuntimeError(f"Resend returned HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Resend HTTP {exc.code}: {detail}") from exc


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--output", help="Write digest text to this path.")
    parser.add_argument("--dry-run", action="store_true", help="Build only; do not send Resend email.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = REPO_ROOT / data_dir

    body = build_digest(data_dir)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(body, encoding="utf-8")

    print(body, end="")
    if not args.dry_run:
        send_resend("BollyAI weekly health digest", body)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
