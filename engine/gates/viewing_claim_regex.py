#!/usr/bin/env python3
"""Reject first-person viewing claims in generated BollyAI prose."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    label: str
    line: int
    column: int
    match: str


PATTERN_SPECS: tuple[tuple[str, str], ...] = (
    (
        "english_i_watched",
        r"\bI\s+(?:just\s+|finally\s+|recently\s+|already\s+)?"
        r"(?:watched|saw|viewed|caught|screened|streamed|rewatched)\b",
    ),
    (
        "english_i_have_seen",
        r"\bI(?:'ve| have| had)\s+(?:just\s+|already\s+|finally\s+)?"
        r"(?:watched|seen|viewed|caught|screened|streamed|rewatched)\b",
    ),
    (
        "english_when_i_saw",
        r"\b(?:when|after|before|while)\s+I\s+"
        r"(?:watched|saw|viewed|caught|screened|streamed|rewatched)\b",
    ),
    (
        "english_viewing_clause",
        r"\b(?:after|while|before)\s+watching\s+(?:the\s+)?"
        r"(?:film|movie|episode|show|trailer)\b",
    ),
    (
        "english_my_screening",
        r"\bmy\s+(?:screening|show|showtime|theatre|theater|press\s+show|fdfs)\b",
    ),
    (
        "english_first_person_reaction",
        r"\bI\s+(?:felt|noticed|laughed|cried|walked\s+out|left)\b"
        r".{0,80}\b(?:film|movie|theatre|theater|screening|interval|climax)\b",
    ),
    (
        "hinglish_maine_dekha",
        r"\bma+i+n+e\b(?:\s+[a-z0-9']+){0,8}\s+"
        r"(?:dekha|dekhi|dekhe|dekh\s+li|dekh\s+liye|dekhi\s+thi|dekha\s+tha)\b",
    ),
    (
        "hinglish_humne_dekha",
        r"\b(?:humne|hamne|hum\s+ne|ham\s+ne)\b(?:\s+[a-z0-9']+){0,8}\s+"
        r"(?:dekha|dekhi|dekhe|dekh\s+li|dekh\s+liye|dekhi\s+thi|dekha\s+tha)\b",
    ),
    (
        "hinglish_jab_maine_dekha",
        r"\bjab\s+ma+i+n+e\b(?:\s+[a-z0-9']+){0,8}\s+"
        r"(?:dekha|dekhi|dekhe|dekh\s+li|dekhi\s+thi|dekha\s+tha)\b",
    ),
    (
        "hinglish_theatre_gaya",
        r"\bmain\s+(?:theatre|theater|cinema|hall)\s+"
        r"(?:mein|me|mai|gaya|gayi|gaya\s+tha|gayi\s+thi)\b",
    ),
    (
        "hinglish_theatre_mein_dekha",
        r"\b(?:theatre|theater|cinema|hall)\s+(?:mein|me|mai)\b"
        r".{0,60}\b(?:maine|humne|hamne|dekha|dekhi|dekhe)\b",
    ),
    (
        "hinglish_mujhe_laga",
        r"\bmujhe\s+(?:laga|feel\s+hua)\b.{0,80}"
        r"\b(?:film|movie|picture|interval|climax|dekhte)\b",
    ),
    (
        "hinglish_fdfs_claim",
        r"\b(?:fdfs|first\s+day\s+first\s+show)\b.{0,80}"
        r"\b(?:dekha|dekhi|watched|saw|maine|humne|hamne)\b",
    ),
)

PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = tuple(
    (label, re.compile(pattern, re.IGNORECASE | re.MULTILINE | re.DOTALL))
    for label, pattern in PATTERN_SPECS
)


def _line_column(text: str, offset: int) -> tuple[int, int]:
    line = text.count("\n", 0, offset) + 1
    line_start = text.rfind("\n", 0, offset)
    column = offset + 1 if line_start == -1 else offset - line_start
    return line, column


def scan_text(text: str) -> list[Finding]:
    findings: list[Finding] = []
    for label, pattern in PATTERNS:
        for match in pattern.finditer(text):
            line, column = _line_column(text, match.start())
            findings.append(
                Finding(
                    label=label,
                    line=line,
                    column=column,
                    match=" ".join(match.group(0).split()),
                )
            )
    return sorted(findings, key=lambda item: (item.line, item.column, item.label))


def has_viewing_claim(text: str) -> bool:
    return bool(scan_text(text))


def read_text(path: str | None, inline_text: str | None) -> str:
    if inline_text is not None:
        return inline_text
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def emit_human(findings: Iterable[Finding]) -> None:
    for finding in findings:
        print(
            f"{finding.line}:{finding.column}: {finding.label}: {finding.match}",
            file=sys.stderr,
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Input file. Defaults to stdin.")
    parser.add_argument("--input", dest="input_path", help="Input file.")
    parser.add_argument("--text", help="Inline text to scan.")
    parser.add_argument("--json", action="store_true", help="Emit findings as JSON.")
    args = parser.parse_args(argv)

    input_path = args.input_path or args.path
    try:
        text = read_text(input_path, args.text)
    except OSError as exc:
        print(f"viewing_claim_regex.py: {exc}", file=sys.stderr)
        return 1

    findings = scan_text(text)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    elif findings:
        emit_human(findings)

    return 2 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
