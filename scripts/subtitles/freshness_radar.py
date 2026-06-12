#!/usr/bin/env python3
"""freshness_radar.py — discovers what's NEW (what people are searching) and queues
subtitle acquisition for it. Discovery is DATA-driven, never model-memory:

  R1. data/ott/calendar.json — verified weekly OTT calendar (series + films, daily refresh)
  R2. catalogue series with status running/returning whose latest season release_date is
      within the lookback window (new episodes likely landing weekly)
  R3. manual adds — _engine/fresh-manual.json (["slug-or-title", ...])

Output: data/subtitles/_engine/fresh-queue.json
  [{"kind": "series|film", "title": ..., "slug": ..., "release_date": ...,
    "season_hint": N, "why": "calendar|running-catalogue|manual"}]

No network. Pure read of repo data. fetch_new_subs.py consumes the queue.
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date, timedelta
from pathlib import Path

BOLLY = Path.home() / "bollyai"
ENGINE = BOLLY / "data" / "subtitles" / "_engine"
ENGINE.mkdir(parents=True, exist_ok=True)
LOOKBACK_D = 45   # a show that dropped a season within 45d is "what people search now"
LOOKAHEAD_D = 14


def sv(x):
    """Unwrap SourceValue envelope or pass through plain values."""
    if isinstance(x, dict) and "value" in x:
        return x["value"]
    return x


def slugify(title: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "-", (title or "").lower()).strip("-")
    return s


def parse_date(s):
    try:
        return date.fromisoformat(str(s)[:10])
    except Exception:
        return None


def r1_calendar(queue: list, seen: set):
    p = BOLLY / "data" / "ott" / "calendar.json"
    if not p.exists():
        return
    cal = json.loads(p.read_text())
    today = date.today()
    for e in cal.get("entries", []):
        title = sv(e.get("title"))
        rd = parse_date(sv(e.get("release_date")))
        kind = e.get("type") or "series"
        if not title:
            continue
        if rd and not (today - timedelta(days=LOOKBACK_D) <= rd <= today + timedelta(days=LOOKAHEAD_D)):
            continue
        slug = e.get("slug") or slugify(title)
        if slug in seen:
            continue
        seen.add(slug)
        queue.append({"kind": kind, "title": title, "slug": slug,
                      "release_date": str(rd) if rd else None,
                      "platform": sv(e.get("platform")), "language": sv(e.get("language")),
                      "why": "calendar"})


def r2_running_catalogue(queue: list, seen: set):
    sdir = BOLLY / "data" / "series"
    today = date.today()
    for p in sdir.glob("*.json"):
        try:
            d = json.loads(p.read_text())
        except Exception:
            continue
        if d.get("status") not in ("running", "returning"):
            continue
        seasons = d.get("seasons") or []
        if not seasons:
            continue
        last = seasons[-1]
        rd = parse_date(sv(last.get("release_date")))
        if not rd:
            continue
        if today - timedelta(days=LOOKBACK_D) <= rd <= today + timedelta(days=LOOKAHEAD_D):
            slug = d.get("slug") or p.stem
            if slug in seen:
                continue
            seen.add(slug)
            queue.append({"kind": "series", "title": sv(d.get("title")), "slug": slug,
                          "release_date": str(rd), "season_hint": last.get("number"),
                          "episodes_hint": last.get("episodes"),
                          "why": "running-catalogue"})


def r3_manual(queue: list, seen: set):
    p = ENGINE / "fresh-manual.json"
    if not p.exists():
        return
    for item in json.loads(p.read_text()):
        if isinstance(item, str):
            item = {"title": item}
        slug = item.get("slug") or slugify(item.get("title", ""))
        if not slug or slug in seen:
            continue
        seen.add(slug)
        queue.append({"kind": item.get("kind", "series"), "title": item.get("title"),
                      "slug": slug, "season_hint": item.get("season_hint"),
                      "release_date": item.get("release_date"), "why": "manual"})


def main() -> int:
    queue: list = []
    seen: set = set()
    r3_manual(queue, seen)       # manual first (highest intent)
    r1_calendar(queue, seen)
    r2_running_catalogue(queue, seen)
    out = ENGINE / "fresh-queue.json"
    out.write_text(json.dumps(queue, ensure_ascii=False, indent=1))
    print(f"fresh-queue: {len(queue)} items "
          f"({sum(1 for q in queue if q['kind']=='series')} series, "
          f"{sum(1 for q in queue if q['kind']=='film')} films)")
    for q in queue:
        print(f"  [{q['why']:>17}] {q['kind']:<6} {q['slug']:<40} {q.get('release_date')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
