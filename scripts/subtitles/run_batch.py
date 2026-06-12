#!/usr/bin/env python3
"""run_batch.py — full backlog orchestrator for the subtitle intelligence engine.

Per series: stage SRTs -> Stage B stats -> dossier extraction (hedged free lane)
-> G2 verify -> ONE repair round for failing episodes -> G2 verify --strip
-> season cross-pass (consensus) -> G2 verify crosspass.

Safety: data/subtitles/_engine/STOP halts between episodes; QUOTA_HALT honored;
ledger at _engine/batch-ledger.jsonl; resume-safe (skips existing dossiers).

Usage: python3 run_batch.py [slug ...]      (default: all staged-able series)
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).parent
sys.path.insert(0, str(HERE))
import orfree
import extract_dossier as ed
import verify_grounding as vg
from stage_series import SERIES_CFG, to_slug, stage_one, SUBS

ROOT = Path.home() / "bollyai" / "data" / "subtitles"
ENGINE = ROOT / "_engine"
ENGINE.mkdir(parents=True, exist_ok=True)
LEDGER = ENGINE / "batch-ledger.jsonl"
STOP = ENGINE / "STOP"
IST = timezone(timedelta(hours=5, minutes=30))


def log(rec: dict):
    rec["ts"] = datetime.now(IST).isoformat()
    with LEDGER.open("a") as f:
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
    print(f"[ledger] {rec}", flush=True)


def halted() -> bool:
    if STOP.exists():
        print("STOP flag present - halting gracefully", flush=True)
        return True
    if (ENGINE / "QUOTA_HALT").exists():
        print("QUOTA_HALT present - halting (rm to resume tomorrow)", flush=True)
        return True
    return False


def process_series(slug: str) -> dict:
    cfg = SERIES_CFG.get(slug, {})
    quote_lang = cfg.get("quote_lang", "en")
    sdir = ROOT / slug
    summary = {"slug": slug, "extracted": 0, "repaired": 0, "failed": [], "crosspass": False}

    eps = sorted(p.stem for p in (sdir / "_stats").glob("*.json") if p.stem != "series")
    # pass 1: extraction
    for ep in eps:
        if halted():
            summary["halted"] = True
            return summary
        try:
            r = ed.extract_one(slug, ep, quote_lang=quote_lang)
            if r is not None:
                summary["extracted"] += 1
                time.sleep(2)  # gentle pacing for the free pools
        except orfree.QuotaExhausted:
            (ENGINE / "QUOTA_HALT").touch()
            summary["halted"] = True
            return summary
        except Exception as e:
            summary["failed"].append(ep)
            log({"event": "extract_fail", "slug": slug, "ep": ep, "err": str(e)[:200]})

    # pass 2: verify, repair round for episodes with errors, then strip
    idx = vg.load_index(slug)
    ddir = sdir / "_dossiers"
    for ep in eps:
        p = ddir / f"{ep}.json"
        if not p.exists() or ep not in idx:
            continue
        errs, _ = vg.verify_dossier(ep, json.loads(p.read_text()), idx[ep])
        if errs and not halted():
            try:
                ed.extract_one(slug, ep, repair_errors=errs, quote_lang=quote_lang)
                summary["repaired"] += 1
                time.sleep(2)
            except Exception as e:
                log({"event": "repair_fail", "slug": slug, "ep": ep, "err": str(e)[:200]})
    # final strip pass
    subprocess.run([sys.executable, str(HERE / "verify_grounding.py"), slug, "--strip"],
                   capture_output=True, text=True)

    # pass 3: cross-pass (skip single-episode corpora; resume-safe: done = don't reburn)
    if len(eps) >= 3 and not halted() and not (sdir / "_dossiers" / "_crosspass.json").exists():
        try:
            r = subprocess.run([sys.executable, str(HERE / "season_crosspass.py"), slug],
                               capture_output=True, text=True, timeout=2400)
            summary["crosspass"] = r.returncode == 0
            if r.returncode != 0:
                log({"event": "crosspass_fail", "slug": slug, "err": (r.stderr or r.stdout)[-300:]})
            else:
                subprocess.run([sys.executable, str(HERE / "verify_grounding.py"), slug, "--strip"],
                               capture_output=True, text=True)
        except Exception as e:
            log({"event": "crosspass_fail", "slug": slug, "err": str(e)[:200]})

    rep = ddir / "_verify_report.json"
    if rep.exists():
        rj = json.loads(rep.read_text())
        summary["verify_errors"] = sum(len(v["errors"]) for v in rj.get("episodes", {}).values())
        if rj.get("crosspass"):
            summary["callbacks_kept"] = rj["crosspass"]["kept_callbacks"]
            summary["callbacks_high"] = rj["crosspass"]["high_confidence"]
    return summary


def main() -> int:
    args = sys.argv[1:]
    if args:
        slugs = args
    else:
        slugs = [to_slug(d.name) for d in sorted(SUBS.iterdir()) if d.is_dir() and to_slug(d.name) != "from"]
    log({"event": "batch_start", "slugs": slugs, "requests_today": orfree.requests_today()})
    for slug in slugs:
        if halted():
            break
        # ensure staged + stats exist
        if not (ROOT / slug / "_stats" / "series.json").exists():
            src_dir = next((d.name for d in SUBS.iterdir() if to_slug(d.name) == slug), None)
            if not src_dir:
                log({"event": "no_subs", "slug": slug})
                continue
            stage_one(src_dir)
        t0 = time.time()
        s = process_series(slug)
        s["mins"] = round((time.time() - t0) / 60, 1)
        log({"event": "series_done", **s})
        if s.get("halted"):
            break
    log({"event": "batch_end", "requests_today": orfree.requests_today()})
    return 0


if __name__ == "__main__":
    sys.exit(main())
