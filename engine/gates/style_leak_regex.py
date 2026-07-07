#!/usr/bin/env python3
"""Reject tooling leaks and dropped-value fragments in generated BollyAI prose.

Gate 6 (corpus-repair R4, 2026-07). The 2026-07-02 upgrade campaign shipped
validator-CLEAN prose that cited the internal subtitle dossier as a source
("the dossier notes dense dialogue...") and collapsed timestamp templating
into broken English ("silences from to and again from to"). Both violate
01-QUALITY-BAR (prose never mentions the tooling; no timestamps in prose).
The bar was right; the validator could not see the patterns. Now it can.

G-PLACEHOLDER-H1 (the third R4 pattern) lands only after R3 Tier-1 clears
its corpus - shipping it early reddens the suite on known, queued work.
"""

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
        "tooling_leak_tool_cited_as_source",
        r"\bthe\s+(?:dossier|subtitles?)(?:'s)?\s+"
        r"(?:notes?|marks?|records?|gives?|shows?|has|have|logs?|lists?"
        r"|confirms?|clocks?|counts?|flags?|tracks?)\b",
    ),
    (
        "tooling_leak_per_the_dossier",
        r"\bper\s+the\s+dossier\b",
    ),
    (
        "dropped_value_from_to",
        r"\bfrom\s+to\b(?=[\s,.;:)]|$)",
    ),
    (
        "dropped_value_between_and",
        r"\bbetween\s+and\b",
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


def has_style_leak(text: str) -> bool:
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
        print(f"style_leak_regex.py: {exc}", file=sys.stderr)
        return 1

    findings = scan_text(text)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    elif findings:
        emit_human(findings)

    return 2 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
