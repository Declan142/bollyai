#!/usr/bin/env python3
"""Strip em-dashes and emoji-like symbols from generated prose."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path


DASH_TRANSLATION = str.maketrans(
    {
        "\u2014": " - ",
        "\u2013": " - ",
        "\u2015": " - ",
        "\u2212": "-",
    }
)


def is_emoji_like(char: str) -> bool:
    codepoint = ord(char)
    if codepoint in (0x200D, 0xFE0E, 0xFE0F):
        return True
    return (
        0x1F000 <= codepoint <= 0x1FAFF
        or 0x2600 <= codepoint <= 0x27BF
        or 0x2300 <= codepoint <= 0x23FF
    )


def strip_prose(text: str) -> str:
    text = text.translate(DASH_TRANSLATION)
    text = "".join(char for char in text if not is_emoji_like(char))
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r" *\n *", "\n", text)
    return text


def read_input(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def write_output(path: str | None, text: str) -> None:
    if path:
        output = Path(path)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
    else:
        sys.stdout.write(text)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("path", nargs="?", help="Input file. Defaults to stdin.")
    parser.add_argument("--input", dest="input_path", help="Input file.")
    parser.add_argument("--output", help="Output file. Defaults to stdout.")
    parser.add_argument("--check", action="store_true", help="Fail if changes are needed.")
    args = parser.parse_args(argv)

    input_path = args.input_path or args.path
    try:
        original = read_input(input_path)
    except OSError as exc:
        print(f"emdash_strip.py: {exc}", file=sys.stderr)
        return 1

    cleaned = strip_prose(original)
    if args.check:
        if cleaned != original:
            print("emdash_strip.py: prose contains em-dashes or emoji-like symbols", file=sys.stderr)
            return 2
        return 0

    write_output(args.output, cleaned)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
