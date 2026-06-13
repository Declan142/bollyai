#!/usr/bin/env python3
"""Reject FABRICATED critic / reviewer / audience attributions in BollyAI prose.

The cardinal honesty fence: BollyAI has read everyone who has watched, but it must NEVER
manufacture reception. Phrases like "Critics noted that...", "Reviewers praised...",
"Audiences remember...", "widely praised/discussed", "critically acclaimed", "drew acclaim"
assert real-world reception. They are legitimate ONLY when the same series file carries a real
pull_quote / critic_note with a verifiable URL backing that reception. Unbacked, they are
invention - the exact failure that put ~14,700 fake attributions into the catalogue (the
blitz of 2026-06-14) on ~500 series with no subtitles and no documented per-episode reception.

This module only DETECTS the attribution phrases. The backing-quote check (and the
build-breaking verdict) lives in scripts/batch/validate_series.py, which knows the file's
pull_quotes. Standalone, this scanner is the regex half of the gate, mirroring
engine/gates/viewing_claim_regex.py so the engine can reuse it pre-write.
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


# External-reception subjects. BollyAI's OWN take ("the episode lands", "Sunny's choice
# costs him") is fine; attributing a judgement to these third parties is what we gate.
_SUBJ = (r"(?:critics?|reviewers?|audiences?|the\s+audience|viewers?|fans?|commentators?|"
         r"observers?|the\s+(?:trade\s+)?press|the\s+critics|many\s+viewers|some\s+critics)")

# Reception verbs (stemmed loosely with \w*) a subject performs on the work.
_RVERB = (r"(?:noted|note|praised?|panned?|describ\w+|observ\w+|highlight\w+|report\w+|"
          r"point\w+|respond\w+|remember\w*|recall\w*|discuss\w+|hail\w+|call\w+|"
          r"consider\w+|regard\w+|laud\w+|criticis\w+|criticiz\w+|acclaim\w+|love[ds]?|"
          r"mock\w+|cit\w+|singl\w+|felt|found|react\w+|receiv\w+|embrac\w+|debat\w+|"
          r"celebrat\w+|complain\w+|tend\w*|flag\w+|read\b)")

# Reception nouns a work "receives / draws / sparks". Deliberately narrow to UNAMBIGUOUS
# reception words - "attention"/"buzz"/"reactions" are dropped because BollyAI legitimately
# writes "the animation draws attention" (its own craft note, not a reception claim).
_RNOUN = (r"(?:praise|acclaim|criticism|backlash|applause|plaudits|flak|flack|controversy)")

PATTERN_SPECS: tuple[tuple[str, str], ...] = (
    # 1) Subject leads: "Critics noted that", "Audiences most often remember", "Reviewers also praised"
    ("subject_then_reception",
     rf"\b{_SUBJ}\b(?:\W+\w+){{0,4}}?\W+{_RVERB}\b"),
    # 2) Adverb + reception verb (passive consensus): "widely praised", "often described", "critically acclaimed"
    ("adverb_reception",
     r"\b(?:widely|broadly|generally|often|frequently|commonly|universally|critically|"
     r"largely|popularly)\s+(?:praised?|panned?|discuss\w+|describ\w+|regard\w+|consider\w+|"
     r"seen|hail\w+|criticis\w+|criticiz\w+|acclaim\w+|cit\w+|note[ds]?|remember\w*|love[ds]?|"
     r"mock\w+|laud\w+|celebrat\w+|recogni\w+|debat\w+)\b"),
    # 3) Verb then subject: "praised by critics", "hailed by audiences", "discussed among fans"
    ("reception_by_subject",
     rf"\b(?:praised?|panned?|hail\w+|laud\w+|criticis\w+|criticiz\w+|acclaim\w+|celebrat\w+|"
     rf"describ\w+|cit\w+|mock\w+|embrac\w+|discuss\w+|adored?|beloved)\s+(?:by|among|amongst)\s+{_SUBJ}\b"),
    # 4) Work receives/draws/sparks reception: "drew acclaim", "sparked debate", "received criticism"
    ("received_reception",
     rf"\b(?:receiv\w+|drew|draw\w*|won|garner\w+|earn\w+|attract\w+|generat\w+|spark\w+|"
     rf"ignit\w+|met\s+with|prompt\w+|stir\w+|invit\w+)\s+(?:\w+\s+){{0,2}}{_RNOUN}\b"),
    # 5) Reception adjectives / labels: "critically acclaimed", "fan-favorite", "crowd-pleaser", "cult classic"
    ("reception_label",
     r"\b(?:critically[\s-]acclaimed|(?:critical|widespread|universal)\s+acclaim|"
     r"fan[\s-]favou?rites?|crowd[\s-]pleas\w+|cult[\s-](?:classic|favou?rite|hit)|"
     r"breakout[\s-]hit|widely[\s-]regarded|much[\s-]discussed|much[\s-]praised|"
     r"polarising|polarizing|divisive)\b"),
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
    if not text:
        return findings
    for label, pattern in PATTERNS:
        for match in pattern.finditer(text):
            line, column = _line_column(text, match.start())
            findings.append(
                Finding(label=label, line=line, column=column,
                        match=" ".join(match.group(0).split()))
            )
    return sorted(findings, key=lambda item: (item.line, item.column, item.label))


def has_attribution(text: str) -> bool:
    return bool(scan_text(text))


def read_text(path: str | None, inline_text: str | None) -> str:
    if inline_text is not None:
        return inline_text
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def emit_human(findings: Iterable[Finding]) -> None:
    for finding in findings:
        print(f"{finding.line}:{finding.column}: {finding.label}: {finding.match}",
              file=sys.stderr)


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
        print(f"attribution_regex.py: {exc}", file=sys.stderr)
        return 1

    findings = scan_text(text)
    if args.json:
        print(json.dumps([asdict(item) for item in findings], indent=2))
    elif findings:
        emit_human(findings)

    return 2 if findings else 0


if __name__ == "__main__":
    raise SystemExit(main())
