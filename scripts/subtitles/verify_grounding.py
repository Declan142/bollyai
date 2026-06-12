#!/usr/bin/env python3
"""verify_grounding.py — G2 mechanical gate (FREE_MODEL_RULES.md).

Every timestamp must exist in the SRT-derived dialogue; every quote must be a
verbatim substring of the line at its timestamp; quote caps enforced. Claims
that fail are STRIPPED (recorded in _stripped), never argued with.

Speaker-attribution gate: any key_line.speaker not backed by an SDH speaker tag
in the dialogue doc is nulled in-place (quote kept, attribution discarded).
Count logged in _verified.nulled_speakers.

Verifies per-episode dossiers AND _crosspass.json.

Usage:
  python3 verify_grounding.py <slug>            # verify + write report
  python3 verify_grounding.py <slug> --strip    # also strip failing claims in place
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path.home() / "bollyai" / "data" / "subtitles"
TOL = 3.0  # seconds tolerance for timestamp match


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", "", (s or "").lower().replace("'", "")).strip()


def to_secs(ts: str) -> float | None:
    if not ts:
        return None
    m = re.match(r"^(\d+):(\d{2})$", ts.strip())
    if not m:
        return None
    return int(m.group(1)) * 60 + int(m.group(2))


class EpisodeIndex:
    def __init__(self, stats: dict):
        self.lines = stats["dialogue"]
        self.times = [l["t"] for l in self.lines]

    def at(self, ts: str) -> list[dict]:
        s = to_secs(ts)
        if s is None:
            return []
        return [l for l in self.lines if abs(l["t"] - s) <= TOL]

    def has_t(self, ts: str) -> bool:
        return bool(self.at(ts))

    def quote_at(self, ts: str, quote: str) -> bool:
        nq = norm(quote)
        if not nq:
            return False
        return any(nq in norm(l["line"]) for l in self.at(ts))

    def quote_anywhere(self, quote: str) -> bool:
        nq = norm(quote)
        return bool(nq) and any(nq in norm(l["line"]) for l in self.lines)

    def has_sdh_speaker_at(self, ts: str) -> bool:
        """True if any dialogue line within TOL of ts has a non-null speaker (SDH source)."""
        return any(l.get("speaker") for l in self.at(ts))


def load_index(slug: str) -> dict[str, EpisodeIndex]:
    idx = {}
    for p in sorted((ROOT / slug / "_stats").glob("*.json")):
        if p.stem == "series":
            continue
        idx[p.stem] = EpisodeIndex(json.loads(p.read_text()))
    return idx


def verify_dossier(ep: str, d: dict, ix: EpisodeIndex) -> tuple[list[str], dict]:
    """Returns (errors, stripped_copy)."""
    errs = []
    out = json.loads(json.dumps(d))  # deep copy
    stripped = []

    def keep(items, label, check):
        kept = []
        for it in items or []:
            problem = check(it)
            if problem:
                errs.append(f"{label}: {problem}")
                stripped.append({label: it, "why": problem})
            else:
                kept.append(it)
        return kept

    out["beats"] = keep(d.get("beats"), "beat",
                        lambda b: None if ix.has_t(b.get("t", "")) else f"t {b.get('t')} not in dialogue")
    out["character_beats"] = keep(d.get("character_beats"), "character_beat",
                                  lambda b: None if ix.has_t(b.get("evidence_t", "")) else f"evidence_t {b.get('evidence_t')} not in dialogue")
    out["payoffs"] = keep(d.get("payoffs"), "payoff",
                          lambda p: None if (ix.has_t(p.get("plants_from", "")) and ix.has_t(p.get("pays_here", "")))
                          else f"anchor missing ({p.get('plants_from')}->{p.get('pays_here')})")

    def kl_check(kl):
        if not ix.has_t(kl.get("t", "")):
            return f"t {kl.get('t')} not in dialogue"
        if len((kl.get("line") or "").split()) > 15:
            return "quote over 15 words"
        if not ix.quote_at(kl.get("t", ""), kl.get("line", "")):
            return f"quote not verbatim at {kl.get('t')}: {kl.get('line', '')[:50]!r}"
        return None
    out["key_lines"] = keep(d.get("key_lines"), "key_line", kl_check)[:6]

    # Speaker-attribution gate: null any speaker not backed by an SDH tag.
    # Keep the quote; kill only the inferred attribution. Not an error - just a
    # correction for non-SDH corpora where speaker names are LLM-guessed.
    nulled_speakers = 0
    for kl in out["key_lines"]:
        if kl.get("speaker") and not ix.has_sdh_speaker_at(kl.get("t", "")):
            kl["speaker"] = None
            nulled_speakers += 1

    total_q = sum(len((k.get("line") or "").split()) for k in out["key_lines"])
    if total_q > 80:
        errs.append(f"quote budget {total_q} > 80 - trimming")
        while total_q > 80 and out["key_lines"]:
            dropped = out["key_lines"].pop()
            total_q -= len((dropped.get("line") or "").split())
            stripped.append({"key_line": dropped, "why": "quote budget"})

    c = d.get("contradiction") or {}
    if not c or not ix.has_t(c.get("line_t", "")):
        errs.append(f"contradiction line_t {c.get('line_t')} not in dialogue")
        # keep the contradiction text but null the bad anchor rather than lose the spine
        if out.get("contradiction"):
            out["contradiction"]["line_t"] = None

    if d.get("speaker_attribution_confidence") not in ("high", "medium", "low"):
        errs.append("speaker_attribution_confidence enum invalid")
        out["speaker_attribution_confidence"] = "low"

    sc = d.get("self_check") or {}
    if errs and sc.get("every_t_exists") and sc.get("quotes_verbatim"):
        errs.append("DISHONEST self_check (claimed clean, gate found errors)")

    if stripped:
        out["_stripped"] = stripped
    out["_verified"] = {"errors": len(errs), "gate": "G2", "tol_s": TOL,
                        "nulled_speakers": nulled_speakers}
    return errs, out


def verify_crosspass(d: dict, idx: dict[str, EpisodeIndex]) -> tuple[list[str], dict]:
    errs = []
    out = json.loads(json.dumps(d))
    stripped = []

    def anchor_ok(ep, ts):
        return ep in idx and idx[ep].has_t(ts or "")

    kept = []
    for cb in d.get("callbacks", []):
        bad = []
        if not anchor_ok(cb.get("setup_ep"), cb.get("setup_t")):
            bad.append(f"setup {cb.get('setup_ep')} {cb.get('setup_t')}")
        if not anchor_ok(cb.get("payoff_ep"), cb.get("payoff_t")):
            bad.append(f"payoff {cb.get('payoff_ep')} {cb.get('payoff_t')}")
        if bad:
            errs.append(f"callback anchors missing: {', '.join(bad)}")
            stripped.append({"callback": cb, "why": bad})
        else:
            kept.append(cb)
    out["callbacks"] = kept

    for field in ("motifs", "weak_motifs"):
        kept_m = []
        for m in d.get(field, []) or []:
            occ = [o for o in m.get("occurrences", []) if anchor_ok(o.get("ep"), o.get("t"))]
            lost = len(m.get("occurrences", [])) - len(occ)
            if lost:
                errs.append(f"motif '{str(m.get('motif'))[:30]}': {lost} unanchored occurrence(s) dropped")
            m["occurrences"] = occ
            if (field == "motifs" and len(occ) >= 3) or (field == "weak_motifs" and len(occ) >= 2):
                kept_m.append(m)
            elif occ:
                (out.setdefault("weak_motifs", []) if field == "motifs" else stripped).append(
                    m if field == "motifs" else {"motif": m, "why": "under 2 anchored occurrences"})
            else:
                stripped.append({"motif": m, "why": "no anchored occurrences"})
        out[field] = kept_m

    for arc in out.get("character_arcs", []) or []:
        wp = [w for w in arc.get("waypoints", []) if anchor_ok(w.get("ep"), w.get("t"))]
        if len(wp) < len(arc.get("waypoints", [])):
            errs.append(f"arc {arc.get('who')}: {len(arc.get('waypoints', [])) - len(wp)} waypoint(s) dropped")
        arc["waypoints"] = wp

    if stripped:
        out["_stripped"] = stripped
    out["_verified"] = {"errors": len(errs), "gate": "G2", "tol_s": TOL}
    return errs, out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("slug")
    ap.add_argument("--strip", action="store_true", help="write stripped copies in place")
    args = ap.parse_args()

    idx = load_index(args.slug)
    ddir = ROOT / args.slug / "_dossiers"
    report = {"slug": args.slug, "episodes": {}, "crosspass": None}
    any_errs = 0

    for p in sorted(ddir.glob("*.json")):
        ep = p.stem
        if ep.startswith("_") or ep not in idx:
            continue
        d = json.loads(p.read_text())
        errs, cleaned = verify_dossier(ep, d, idx[ep])
        ns = cleaned.get("_verified", {}).get("nulled_speakers", 0)
        report["episodes"][ep] = {"errors": errs, "kept_key_lines": len(cleaned.get("key_lines", [])),
                                  "nulled_speakers": ns}
        any_errs += len(errs)
        if args.strip:
            p.write_text(json.dumps(cleaned, ensure_ascii=False, indent=1))
        flag = "CLEAN" if not errs else f"{len(errs)} ERR"
        ns_note = f" ({ns} speaker(s) nulled)" if ns else ""
        print(f"{flag:>7}  {ep}{ns_note}")

    cp = ddir / "_crosspass.json"
    if cp.exists():
        errs, cleaned = verify_crosspass(json.loads(cp.read_text()), idx)
        report["crosspass"] = {"errors": errs,
                               "kept_callbacks": len(cleaned.get("callbacks", [])),
                               "high_confidence": sum(1 for c in cleaned.get("callbacks", [])
                                                      if c.get("confidence") == "high")}
        any_errs += len(errs)
        if args.strip:
            cp.write_text(json.dumps(cleaned, ensure_ascii=False, indent=1))
        print(f"crosspass: {len(errs)} errors, kept {report['crosspass']['kept_callbacks']} callbacks "
              f"({report['crosspass']['high_confidence']} high)")

    (ddir / "_verify_report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    total_nulled = sum(v.get("nulled_speakers", 0) for v in report["episodes"].values())
    print(f"\nreport written; total errors: {any_errs}; total speakers nulled: {total_nulled}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
