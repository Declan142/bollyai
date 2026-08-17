#!/usr/bin/env python3
"""Detect dated renewal notes that lack a matching series-season shell.

The audit is read-only. A checked-in baseline admits existing debt while any new
finding fails the command. Removing a known finding is allowed without weakening
the baseline gate, so ordinary content repairs can only improve the result.
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


MONTHS = {
    name.lower(): number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}
MONTH_PATTERN = "|".join(name.title() for name in MONTHS)
DATED_SEASON_PATTERN = re.compile(
    rf"\bSeason\s+(?P<season>\d+)\b"
    rf"(?:(?!\bSeason\b)[^.;]){{0,120}}?"
    rf"\b(?:premiere(?:d|s)?|premiering|released|debuted|dropped|began airing|arrives)\s+"
    rf"(?P<month>{MONTH_PATTERN})\s+(?P<day>\d{{1,2}}),\s+(?P<year>20\d{{2}})",
    re.IGNORECASE,
)
BASELINE_SCHEMA = "series-lifecycle-baseline/v1"


@dataclass(frozen=True)
class Finding:
    code: str
    slug: str
    season: int
    release_date: str
    path: str

    @property
    def finding_id(self) -> str:
        return f"{self.code}:{self.slug}:s{self.season}:{self.release_date}"


def _iso_date(match: re.Match[str]) -> str:
    value = date(
        int(match.group("year")),
        MONTHS[match.group("month").lower()],
        int(match.group("day")),
    )
    return value.isoformat()


def audit_series(series_dir: Path, *, repo_root: Path | None = None) -> list[Finding]:
    findings: list[Finding] = []
    for path in sorted(series_dir.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        renewal = payload.get("renewal") or {}
        note = renewal.get("note")
        if not isinstance(note, str):
            continue

        existing_seasons = {
            season.get("number")
            for season in payload.get("seasons", [])
            if isinstance(season, dict)
        }
        for match in DATED_SEASON_PATTERN.finditer(note):
            season_number = int(match.group("season"))
            if season_number in existing_seasons:
                continue
            relative_path = path.relative_to(repo_root) if repo_root else path
            findings.append(
                Finding(
                    code="dated-season-missing-shell",
                    slug=str(payload.get("slug") or path.stem),
                    season=season_number,
                    release_date=_iso_date(match),
                    path=relative_path.as_posix(),
                )
            )
    return sorted(findings, key=lambda item: item.finding_id)


def load_baseline(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if payload.get("schema") != BASELINE_SCHEMA:
        raise ValueError(f"unsupported lifecycle baseline schema: {payload.get('schema')!r}")
    known = payload.get("known_findings")
    if not isinstance(known, list) or not all(isinstance(item, str) for item in known):
        raise ValueError("lifecycle baseline known_findings must be a string list")
    if len(known) != len(set(known)):
        raise ValueError("lifecycle baseline contains duplicate finding IDs")
    return set(known)


def evaluate(findings: list[Finding], known: set[str]) -> dict[str, object]:
    current = {finding.finding_id for finding in findings}
    return {
        "schema": "series-lifecycle-audit/v1",
        "checked_findings": len(findings),
        "known_debt": sorted(current & known),
        "resolved_debt": sorted(known - current),
        "unexpected": sorted(current - known),
        "findings": [asdict(finding) | {"id": finding.finding_id} for finding in findings],
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument(
        "--baseline",
        type=Path,
        default=Path(__file__).with_name("series-lifecycle-baseline.json"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = args.root.resolve()
    baseline = args.baseline if args.baseline.is_absolute() else root / args.baseline
    findings = audit_series(root / "data" / "series", repo_root=root)
    report = evaluate(findings, load_baseline(baseline))
    print(json.dumps(report, indent=2, sort_keys=True))
    return 1 if report["unexpected"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
