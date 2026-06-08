#!/usr/bin/env python3
"""BollyAI series-JSON fence validator — the gate that makes the buildout loop safe.

Runs every hard fence over a set of series JSON files BEFORE they are committed:
  * valid JSON + required schema fields (matches site/lib/series.ts)
  * SourceValue envelopes on qid/title/original_language/platform + season.release_date
  * canonical_industry == "streaming"; status / renewal.state in allowed sets
  * verdict in the OTT ladder (or null); bollymeter is null OR {score, basis}
  * pull_quotes attributed (text+source+url) and <= 25 words
  * episode_reviews shape (number/title/bollymeter/spoiler_free)
  * NO em-dash / en-dash anywhere (engine/gates/emdash_strip parity)
  * NO first-person viewing claims in any prose field (engine viewing-claim gate)
  * poster attribution present with a takedown line
  * slug matches filename; date_modified present

Usage:
  validate_series.py <slug|path> [<slug|path> ...]   # validate specific files
  validate_series.py --all                            # validate the whole catalogue
  validate_series.py --since <iso>                    # validate files mtime >= iso
Exit 0 = all clean, 1 = at least one failure (reasons on stderr).
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))
from engine.gates.viewing_claim_regex import scan_text  # noqa: E402

SERIES_DIR = REPO_ROOT / "data" / "series"

OTT_RUNGS = {"DISASTER DROP", "SKIP", "ONE-TIME WATCH", "WORTH-IT", "MUST-WATCH"}
STATUS = {"running", "returning", "ended", "limited"}
# Superset of the TS union — real data also carries "returning"/"running".
RENEWAL_STATE = {"renewed", "awaiting", "ended", "final-season", "limited",
                 "returning", "running"}
EMDASH = ("—", "–", "―")  # em / en / horizontal-bar

# Prose fields that must pass the first-person viewing-claim gate.
PROSE_KEYS_SEASON = ("review_body", "season_over_season")
PROSE_KEYS_EPISODE = ("spoiler_free", "the_moment")


def _is_source_value(v) -> bool:
    return (
        isinstance(v, dict)
        and "value" in v
        and "source" in v
        and "fetched_at" in v
        and "confidence" in v
    )


def _walk_strings(node, path="$"):
    """Yield (jsonpath, string) for every string leaf — used for the em-dash sweep.
    Skips _quarantine (internal editor notes, never rendered)."""
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


def _check_viewing(text, where, errs):
    if text and scan_text(text):
        hits = "; ".join(f.match for f in scan_text(text)[:3])
        errs.append(f"viewing-claim in {where}: {hits}")


def validate_file(path: Path) -> list[str]:
    errs: list[str] = []
    try:
        d = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:  # noqa: BLE001
        return [f"invalid JSON: {e}"]

    slug = path.stem
    if d.get("slug") != slug:
        errs.append(f"slug field '{d.get('slug')}' != filename '{slug}'")

    # Required top-level fields
    for f in ("title", "canonical_industry", "origin", "original_language",
              "platform", "status", "logline", "poster", "renewal", "seasons",
              "date_modified"):
        if f not in d:
            errs.append(f"missing top-level field: {f}")

    if d.get("canonical_industry") != "streaming":
        errs.append(f"canonical_industry must be 'streaming', got {d.get('canonical_industry')!r}")
    if d.get("status") not in STATUS:
        errs.append(f"status {d.get('status')!r} not in {sorted(STATUS)}")

    # SourceValue envelopes
    if d.get("qid") is not None and not _is_source_value(d["qid"]):
        errs.append("qid present but not a SourceValue envelope (or null)")
    for f in ("title", "original_language", "platform"):
        if f in d and not _is_source_value(d[f]):
            errs.append(f"{f} is not a SourceValue envelope")

    # Poster
    poster = d.get("poster") or {}
    if not poster.get("src") or not poster.get("alt"):
        errs.append("poster.src / poster.alt missing")
    attr = (poster.get("attribution") or "").lower()
    if "takedown" not in attr:
        errs.append("poster.attribution missing fair-dealing/takedown line")

    # Renewal
    ren = d.get("renewal") or {}
    if ren.get("state") not in RENEWAL_STATE:
        errs.append(f"renewal.state {ren.get('state')!r} not in {sorted(RENEWAL_STATE)}")
    if not ren.get("note") or not ren.get("source"):
        errs.append("renewal.note / renewal.source missing")
    _check_viewing(ren.get("note"), "renewal.note", errs)

    _check_viewing(d.get("logline"), "logline", errs)

    # Seasons
    seasons = d.get("seasons")
    if not isinstance(seasons, list) or not seasons:
        errs.append("seasons must be a non-empty array")
        seasons = []

    for s in seasons:
        n = s.get("number", "?")
        tag = f"S{n}"
        for f in ("number", "year", "episodes", "release_date", "verdict",
                  "bollymeter", "critic", "review_body"):
            if f not in s:
                errs.append(f"{tag}: missing field {f}")
        if not _is_source_value(s.get("release_date")):
            errs.append(f"{tag}: release_date not a SourceValue envelope")
        v = s.get("verdict")
        if v is not None and v not in OTT_RUNGS:
            errs.append(f"{tag}: verdict {v!r} not in OTT ladder")
        bm = s.get("bollymeter")
        if bm is not None:
            if not isinstance(bm, dict) or "score" not in bm or "basis" not in bm:
                errs.append(f"{tag}: bollymeter must be null OR {{score,basis}}")
            else:
                sc = bm.get("score")
                if not isinstance(sc, (int, float)) or not (0 <= sc <= 10):
                    errs.append(f"{tag}: bollymeter.score must be 0-10, got {sc!r}")
                if not (bm.get("basis") or "").strip():
                    errs.append(f"{tag}: bollymeter.basis empty")
        rb = s.get("review_body") or ""
        if len(rb.strip()) < 60:
            errs.append(f"{tag}: review_body too thin ({len(rb.strip())} chars)")
        for key in PROSE_KEYS_SEASON:
            _check_viewing(s.get(key), f"{tag}.{key}", errs)

        crit = s.get("critic") or {}
        for pq in (crit.get("pull_quotes") or []):
            if not (pq.get("text") and pq.get("source") and pq.get("url")):
                errs.append(f"{tag}: pull_quote missing text/source/url")
            elif len(pq["text"].split()) > 25:
                errs.append(f"{tag}: pull_quote > 25 words ({len(pq['text'].split())})")

        for ep in (s.get("episode_reviews") or []):
            etag = f"{tag}E{ep.get('number','?')}"
            if "number" not in ep or "title" not in ep:
                errs.append(f"{etag}: episode missing number/title")
            if "bollymeter" not in ep:
                errs.append(f"{etag}: episode missing bollymeter (number|null)")
            ebm = ep.get("bollymeter")
            if ebm is not None and not (isinstance(ebm, (int, float)) and 0 <= ebm <= 10):
                errs.append(f"{etag}: episode bollymeter must be 0-10 or null")
            if not (ep.get("spoiler_free") or "").strip():
                errs.append(f"{etag}: spoiler_free empty")
            for key in PROSE_KEYS_EPISODE:
                _check_viewing(ep.get(key), f"{etag}.{key}", errs)
            cn = ep.get("critic_note")
            if cn and not (cn.get("text") and cn.get("source") and cn.get("url")):
                errs.append(f"{etag}: critic_note missing text/source/url")

    # Em-dash / en-dash sweep across ALL strings
    for jpath, text in _walk_strings(d):
        if any(dash in text for dash in EMDASH):
            errs.append(f"em/en-dash in {jpath}: ...{text[max(0,_first_dash(text)-15):_first_dash(text)+15]}...")
            break  # one report is enough; fixer strips all

    return errs


def _first_dash(text: str) -> int:
    for i, ch in enumerate(text):
        if ch in EMDASH:
            return i
    return 0


def resolve_targets(args) -> list[Path]:
    if args.all:
        return sorted(SERIES_DIR.glob("*.json"))
    if args.since:
        import datetime
        ts = datetime.datetime.fromisoformat(args.since).timestamp()
        return sorted(p for p in SERIES_DIR.glob("*.json") if p.stat().st_mtime >= ts)
    out = []
    for a in args.targets:
        p = Path(a)
        if p.suffix == ".json" and p.exists():
            out.append(p)
        else:
            out.append(SERIES_DIR / f"{a}.json")
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("targets", nargs="*", help="slugs or json paths")
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--since", help="ISO timestamp; validate files modified at/after")
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
