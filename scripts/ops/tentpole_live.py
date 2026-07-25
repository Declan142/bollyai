#!/usr/bin/env python3
"""Opt-in runner for high-frequency tentpole tracking."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
FETCHERS_DIR = REPO_ROOT / "engine/fetchers"
sys.path.insert(0, str(FETCHERS_DIR))

import run_all as run_all_fetchers  # noqa: E402


def read_json(path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}
    return payload if isinstance(payload, dict) else {}


def enabled_from_config(data_dir: Path) -> tuple[bool, str]:
    config = read_json(data_dir / "_state/tentpole-live.json")
    if not config:
        return False, "missing_config"
    if config.get("enabled") is True:
        return True, "enabled_config"
    return False, "disabled_config"


def write_github_output(path_text: str | None, payload: dict[str, Any]) -> None:
    if not path_text:
        return
    path = Path(path_text)
    with path.open("a", encoding="utf-8") as handle:
        for key, value in payload.items():
            handle.write(f"{key}={str(value).lower() if isinstance(value, bool) else value}\n")


def run_fetchers(args: argparse.Namespace, data_dir: Path) -> dict[str, Any]:
    fetcher_args = argparse.Namespace(
        fixture_mode=bool(args.fixture_mode),
        live_only=True,
        write=None if args.dry_run else str(data_dir),
        today=args.today,
        boxoffice_fixture=None,
    )
    return run_all_fetchers.run(fetcher_args)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default="data")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--fixture-mode", action="store_true")
    parser.add_argument("--force", action="store_true", help="Run without the opt-in state file.")
    parser.add_argument("--today", help="Override today as YYYY-MM-DD for fixture runs.")
    parser.add_argument("--github-output", help="Append ran/reason outputs for GitHub Actions.")
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    data_dir = Path(args.data_dir)
    if not data_dir.is_absolute():
        data_dir = REPO_ROOT / data_dir
    if (
        args.fixture_mode
        and not args.dry_run
        and data_dir.resolve() == (REPO_ROOT / "data").resolve()
    ):
        parser.error("fixture mode cannot write the public data directory")

    enabled, reason = (True, "force") if args.force else enabled_from_config(data_dir)
    if not enabled:
        result = {
            "schema": "tentpole-live-result/v1",
            "ran": False,
            "reason": reason,
            "dry_run": bool(args.dry_run),
        }
        print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
        write_github_output(args.github_output, {"ran": False, "reason": reason})
        return 0

    fetcher_result = run_fetchers(args, data_dir)
    result = {
        "schema": "tentpole-live-result/v1",
        "ran": True,
        "reason": reason,
        "dry_run": bool(args.dry_run),
        "fetcher": fetcher_result,
    }
    print(json.dumps(result, ensure_ascii=True, indent=2, sort_keys=True))
    write_github_output(args.github_output, {"ran": True, "reason": reason})
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
