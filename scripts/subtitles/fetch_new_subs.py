#!/usr/bin/env python3
"""fetch_new_subs.py — consumes _engine/fresh-queue.json, tries to pull English
subtitles for new content via subliminal (the proven source: pipx, default
providers; opensubtitlescom errors, rest fine), then pushes successes through
the engine (stats -> extract -> verify) automatically.

Subliminal needs scene-named dummy files: we synthesize them.
  series: <Title>.SxxEyy.1080p.WEB-DL.mkv     (episode probe, ep 1..hint or 1..12)
  film:   <Title>.<year>.1080p.WEB-DL.mkv

Gotchas honored: subliminal writes subs at batch END (be patient); one batch per
run; per-item failures are normal for fresh content (subs often land days after
OTT drop) - failures stay queued, retried next cron tick, give up after MAX_TRIES.

State: _engine/fetch-state.json  {key: {"tries": n, "got": bool, "last": iso}}
Usage: python3 fetch_new_subs.py [--dry-run] [--max-items N]
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path

HERE = Path(__file__).parent
BOLLY = Path.home() / "bollyai"
ENGINE = BOLLY / "data" / "subtitles" / "_engine"
SUBS_SERIES = Path.home() / "bollyai-subs" / "series"
SUBS_FILMS = Path.home() / "bollyai-subs" / "films"
IST = timezone(timedelta(hours=5, minutes=30))
MAX_TRIES = 10  # ~10 daily ticks; OTT subs usually land within days


def state_load() -> dict:
    p = ENGINE / "fetch-state.json"
    return json.loads(p.read_text()) if p.exists() else {}


def state_save(st: dict):
    (ENGINE / "fetch-state.json").write_text(json.dumps(st, ensure_ascii=False, indent=1))


def scene_title(title: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", ".", title or "").strip(".")


def run_subliminal(dummy_dir: Path) -> int:
    """Run subliminal on every dummy in dir; returns count of .srt produced."""
    cmd = ["subliminal", "download", "-l", "en", str(dummy_dir)]
    try:
        subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    except FileNotFoundError:
        # pipx path fallback
        cmd[0] = str(Path.home() / ".local" / "bin" / "subliminal")
        subprocess.run(cmd, capture_output=True, text=True, timeout=1200)
    except subprocess.TimeoutExpired:
        pass
    return len(list(dummy_dir.glob("*.srt")))


def probe_series(item: dict, dry: bool) -> list[Path]:
    """Try to fetch episodes for the latest season. Returns list of new srt paths."""
    title = item.get("title") or item["slug"].replace("-", " ").title()
    sn = int(item.get("season_hint") or 1)
    n_eps = int(item.get("episodes_hint") or 12)
    stitle = scene_title(title)
    dest = SUBS_SERIES / stitle.replace(".", "_") if False else SUBS_SERIES / title.replace(" ", ".")
    got = []
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        for ep in range(1, min(n_eps, 24) + 1):
            (tdir / f"{stitle}.S{sn:02d}E{ep:02d}.1080p.WEB-DL.mkv").touch()
        if dry:
            print(f"  DRY: would probe {min(n_eps,24)} eps of {stitle} S{sn:02d}")
            return []
        n = run_subliminal(tdir)
        if n:
            dest.mkdir(parents=True, exist_ok=True)
            for srt in tdir.glob("*.srt"):
                tgt = dest / srt.name
                if not tgt.exists():
                    shutil.copy2(srt, tgt)
                    got.append(tgt)
    return got


def probe_film(item: dict, dry: bool) -> list[Path]:
    title = item.get("title") or item["slug"].replace("-", " ").title()
    year = (item.get("release_date") or "")[:4] or "2026"
    stitle = scene_title(title)
    got = []
    with tempfile.TemporaryDirectory() as td:
        tdir = Path(td)
        (tdir / f"{stitle}.{year}.1080p.WEB-DL.mkv").touch()
        if dry:
            print(f"  DRY: would probe film {stitle}.{year}")
            return []
        n = run_subliminal(tdir)
        if n:
            SUBS_FILMS.mkdir(parents=True, exist_ok=True)
            for srt in tdir.glob("*.srt"):
                tgt = SUBS_FILMS / srt.name
                if not tgt.exists():
                    shutil.copy2(srt, tgt)
                    got.append(tgt)
    return got


def push_through_engine(slug: str):
    """stage -> stats -> extract -> verify for one series slug (resume-safe)."""
    subprocess.run([sys.executable, str(HERE / "run_batch.py"), slug],
                   capture_output=True, text=True, timeout=7200)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--max-items", type=int, default=8)
    args = ap.parse_args()

    qp = ENGINE / "fresh-queue.json"
    if not qp.exists():
        print("no fresh-queue.json - run freshness_radar.py first")
        return 1
    queue = json.loads(qp.read_text())
    st = state_load()
    processed = 0
    log = []
    for item in queue:
        if processed >= args.max_items:
            break
        key = f"{item['kind']}:{item['slug']}"
        rec = st.get(key, {"tries": 0, "got": False})
        if rec.get("got") or rec["tries"] >= MAX_TRIES:
            continue
        print(f"probe [{rec['tries']+1}/{MAX_TRIES}] {key} ({item.get('why')})")
        try:
            got = (probe_series if item["kind"] == "series" else probe_film)(item, args.dry_run)
        except Exception as e:
            got = []
            print(f"  probe error: {str(e)[:150]}")
        rec["tries"] += 1
        rec["last"] = datetime.now(IST).isoformat()
        if got:
            rec["got"] = True
            rec["files"] = [p.name for p in got]
            print(f"  GOT {len(got)} srt(s)")
            log.append({"key": key, "new_srts": len(got)})
            if item["kind"] == "series" and not args.dry_run:
                # slug used by stage_series = dir name lowercased+dots->hyphens
                dirname = (item.get("title") or item["slug"]).replace(" ", ".")
                from stage_series import to_slug
                push_through_engine(to_slug(dirname))
        st[key] = rec
        processed += 1
    if not args.dry_run:
        state_save(st)
    print(f"\nprocessed {processed} queue items; {len(log)} with new subs")
    return 0


if __name__ == "__main__":
    sys.exit(main())
