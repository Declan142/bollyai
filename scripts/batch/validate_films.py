#!/usr/bin/env python3
"""BollyAI film-JSON fence validator.

Mirrors validate_series.py structure. Checks:
  * JSON parseable
  * Required top-level fields: qid, slug, canonical_industry
  * slug matches filename stem
  * film.review shape if present:
      spoiler_free non-empty
      the_moment  <= 25 words OR null
      bollymeter  0-10 float OR null
      critic_note {text, source, url} with text <= 25 words, OR null
  * No em-dash / en-dash anywhere (same rule as series)
  * No first-person viewing claims in prose fields

Usage:
  validate_films.py <slug|path> [<slug|path> ...]
  validate_films.py --all
Exit 0 = all clean, 1 = at least one failure (reasons on stderr).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from engine.gates.viewing_claim_regex import scan_text  # noqa: E402

FILMS_DIR = REPO_ROOT / "data" / "films"
EMDASH = ("—", "–", "―")

PROSE_FIELDS_REVIEW = ("spoiler_free", "the_moment")


def _walk_strings(node, path="$"):
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            if k == "_quarantine":
                continue
            yield from _walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from _walk_strings(v, f"{path}[{i}]")


def _first_dash(text: str) -> int:
    for i, ch in enumerate(text):
        if ch in EMDASH:
            return i
    return 0


def _check_viewing(text, where, errs):
    if text and scan_text(text):
        hits = "; ".join(f.match for f in scan_text(text)[:3])
        errs.append(f"viewing-claim in {where}: {hits}")


def validate_file(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        return [f"invalid JSON: {e}"]

    # Required top-level fields
    for f in ("qid", "slug", "canonical_industry"):
        if f not in d:
            errs.append(f"missing required field: {f}")

    if d.get("slug") != path.stem:
        # Film files are named by QID; slug mismatch is only an error when
        # the file stem looks like a slug itself (not a Q-number).
        stem = path.stem
        if not stem.startswith("Q") or not stem[1:].isdigit():
            errs.append(f"slug field '{d.get('slug')}' != filename stem '{stem}'")

    _check_viewing(d.get("logline"), "logline", errs)

    # film.review shape (optional field)
    rev = d.get("review")
    if rev is not None:
        if not isinstance(rev, dict):
            errs.append("review must be an object")
        else:
            sf = (rev.get("spoiler_free") or "").strip()
            if not sf:
                errs.append("review.spoiler_free empty")

            tm = rev.get("the_moment")
            if tm is not None:
                if not isinstance(tm, str):
                    errs.append("review.the_moment must be string or null")
                elif len(tm.split()) > 25:
                    errs.append(f"review.the_moment > 25 words ({len(tm.split())})")

            bm = rev.get("bollymeter")
            if bm is not None:
                if not isinstance(bm, (int, float)) or not (0 <= bm <= 10):
                    errs.append(f"review.bollymeter must be 0-10 float or null, got {bm!r}")

            cn = rev.get("critic_note")
            if cn is not None:
                if not isinstance(cn, dict):
                    errs.append("review.critic_note must be object or null")
                else:
                    if not (cn.get("text") and cn.get("source") and cn.get("url")):
                        errs.append("review.critic_note missing text/source/url")
                    elif len(cn["text"].split()) > 25:
                        errs.append(f"review.critic_note.text > 25 words ({len(cn['text'].split())})")

            for field in PROSE_FIELDS_REVIEW:
                _check_viewing(rev.get(field), f"review.{field}", errs)

    # Em-dash sweep across all strings
    for jpath, text in _walk_strings(d):
        if any(dash in text for dash in EMDASH):
            errs.append(f"em/en-dash in {jpath}: ...{text[max(0, _first_dash(text)-15):_first_dash(text)+15]}...")
            break

    return errs


def resolve_targets(args) -> list[Path]:
    if args.all:
        return sorted(FILMS_DIR.glob("*.json"))
    out = []
    for a in args.targets:
        p = Path(a)
        if p.suffix == ".json" and p.exists():
            out.append(p)
        else:
            # Accept slug or Q-number
            direct = FILMS_DIR / f"{a}.json"
            if direct.exists():
                out.append(direct)
            else:
                # Scan for slug match
                match = next(
                    (f for f in FILMS_DIR.glob("*.json")
                     if json.loads(f.read_text()).get("slug") == a),
                    None
                )
                if match:
                    out.append(match)
                else:
                    out.append(direct)  # will fail with "file not found" in main
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="*", help="slugs, Q-numbers, or json paths")
    ap.add_argument("--all", action="store_true")
    args = ap.parse_args()

    targets = resolve_targets(args)
    if not targets:
        print("no target files", file=sys.stderr)
        return 1

    failed = 0
    for p in targets:
        if not p.exists():
            print(f"FAIL {p.stem}: file not found", file=sys.stderr)
            failed += 1
            continue
        errs = validate_file(p)
        if errs:
            failed += 1
            print(f"FAIL {p.stem}", file=sys.stderr)
            for e in errs:
                print(f"   - {e}", file=sys.stderr)
        else:
            print(f"PASS {p.stem}")
    print(f"\n{len(targets)-failed}/{len(targets)} clean, {failed} failed", file=sys.stderr)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
