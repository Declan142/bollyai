#!/usr/bin/env python3
"""stage_series.py — copy SRTs from ~/bollyai-subs/series/<Dir>/ into the private
corpus layout data/subtitles/<slug>/SxxExx.srt, drop the public-knowledge cast
roster (name-mention counting only), then run Stage B stats.

Usage: python3 stage_series.py <slug|all> [--list]
"""
from __future__ import annotations

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

SUBS = Path.home() / "bollyai-subs" / "series"
ROOT = Path.home() / "bollyai" / "data" / "subtitles"
EP_RE = re.compile(r"(S\d{2}E\d{2})", re.I)

# dir-name -> slug (site convention: lowercase, dots to hyphens)
def to_slug(dirname: str) -> str:
    import re as _re
    return _re.sub(r"[^a-z0-9-]+", "", dirname.lower().replace(".", "-").replace("'", ""))

# principal-cast rosters: PUBLIC KNOWLEDGE names, used ONLY to count spoken mentions.
# quote_lang: en = English-original dialogue; en-sub = translated subtitle rendering.
SERIES_CFG: dict[str, dict] = {
    "scam-1992": {"roster": ["Harshad", "Bhushan", "Sucheta", "Debashis", "Ashwin", "Pranav",
                             "Madhavan", "Manu", "Tyagi", "Jyoti", "Hemali", "Sharad", "Mehta"],
                  "quote_lang": "en-sub"},
    "panchayat": {"roster": ["Abhishek", "Manju", "Brij", "Vikas", "Prahlad", "Rinki",
                             "Bhushan", "Kranti", "Binod", "Madhav", "Sachiv", "Pradhan"],
                  "quote_lang": "en-sub"},
    "mirzapur": {"roster": ["Kaleen", "Guddu", "Bablu", "Munna", "Golu", "Dimpy", "Beena",
                            "Maqbool", "Sweety", "Ramakant", "Sharad", "Lala", "Madhuri",
                            "Robin", "Dadda", "Tripathi", "Satyanand", "Maurya"],
                 "quote_lang": "en-sub"},
    "sacred-games": {"roster": ["Sartaj", "Ganesh", "Gaitonde", "Katekar", "Anjali", "Mathur",
                                "Parulkar", "Bunty", "Kukoo", "Jojo", "Guruji", "Majid",
                                "Subhadra", "Trivedi", "Malcolm", "Shahid", "Batya", "Dilbagh"],
                     "quote_lang": "en-sub"},
    "paatal-lok": {"roster": ["Hathiram", "Ansari", "Sanjeev", "Mehra", "Dolly", "Hathoda",
                              "Tyagi", "Gul", "Renu", "Siddharth", "Chanda", "Kabir", "Tope",
                              "Chaku", "Masterji"],
                   "quote_lang": "en-sub"},
    "the-family-man": {"roster": ["Srikant", "Suchitra", "Suchi", "JK", "Talpade", "Zoya",
                                  "Milind", "Dhriti", "Atharv", "Moosa", "Raji", "Chellam",
                                  "Kulkarni", "Sambit", "Arvind", "Sajid", "Bhaskaran", "Deepan"],
                       "quote_lang": "en-sub"},
    "farzi": {"roster": ["Sunny", "Firoz", "Michael", "Megha", "Nanu", "Mansoor", "Anees",
                         "Sharma", "Rekha", "Yasir", "Bilal"],
              "quote_lang": "en-sub"},
    "squid-game": {"roster": ["Gi-hun", "Sang-woo", "Sae-byeok", "Il-nam", "Ali", "Deok-su",
                              "Mi-nyeo", "Jun-ho", "In-ho", "Hyun-ju", "Myung-gi", "Jun-hee",
                              "Dae-ho", "Gyeong-seok", "No-eul"],
                   "quote_lang": "en-sub"},
    "the-glory": {"roster": ["Dong-eun", "Yeon-jin", "Yeo-jeong", "Hyeon-nam", "Do-yeong",
                             "Jae-jun", "Sa-ra", "Hye-jeong", "Myeong-o", "Gyeong-ran", "Ye-sol"],
                  "quote_lang": "en-sub"},
    "kingdom": {"roster": ["Chang", "Seo-bi", "Yeong-shin", "Hak-ju", "Beom-pal", "Moo-young",
                           "Cho", "Beom-il", "Deok-sung"],
                "quote_lang": "en-sub"},
    "crash-landing-on-you": {"roster": ["Jeong-hyeok", "Se-ri", "Seung-jun", "Dan", "Man-bok",
                                        "Chi-su", "Ju-meok", "Eun-dong", "Gwang-beom", "Yoon",
                                        "Cheol-gang", "Se-hyeong"],
                             "quote_lang": "en-sub"},
    "house-of-the-dragon": {"roster": ["Rhaenyra", "Daemon", "Alicent", "Viserys", "Otto",
                                       "Aegon", "Aemond", "Criston", "Corlys", "Rhaenys",
                                       "Laenor", "Laena", "Helaena", "Lucerys", "Jacaerys",
                                       "Mysaria", "Larys", "Harwin", "Daeron"],
                            "quote_lang": "en"},
    "yellowstone": {"roster": ["John", "Beth", "Kayce", "Jamie", "Rip", "Monica", "Tate",
                               "Lloyd", "Jimmy", "Rainwater", "Walker", "Colby", "Teeter",
                               "Travis", "Mo", "Carter", "Summer", "Garrett", "Caroline", "Sarah"],
                    "quote_lang": "en"},
    "from": {"roster": [], "quote_lang": "en"},  # roster hardcoded in subtitle_stats.py; already done
}


def stage_one(dirname: str) -> str | None:
    slug = to_slug(dirname)
    src = SUBS / dirname
    dst = ROOT / slug
    dst.mkdir(parents=True, exist_ok=True)
    n = 0
    for srt in sorted(src.glob("*.srt")):
        m = EP_RE.search(srt.name)
        if not m:
            print(f"  skip (no SxxExx): {srt.name}")
            continue
        ep = m.group(1).upper()
        target = dst / f"{ep}.srt"
        if not target.exists():
            shutil.copy2(srt, target)
            n += 1
    cfg = SERIES_CFG.get(slug, {})
    if cfg.get("roster"):
        (dst / "roster.json").write_text(json.dumps(cfg["roster"]))
    print(f"{slug}: staged {n} new SRTs")
    # Stage B
    r = subprocess.run([sys.executable, str(Path(__file__).parent / "subtitle_stats.py"), slug],
                       capture_output=True, text=True)
    tail = [l for l in r.stdout.splitlines() if l.strip()][-1:] or ["(no output)"]
    print(f"  stats: {tail[0]}")
    if r.returncode != 0:
        print(f"  STATS FAIL: {r.stderr[:300]}")
        return None
    return slug


def main() -> int:
    arg = sys.argv[1] if len(sys.argv) > 1 else "all"
    dirs = sorted(d.name for d in SUBS.iterdir() if d.is_dir())
    if arg == "--list" or arg == "list":
        for d in dirs:
            print(f"{d}  ->  {to_slug(d)}")
        return 0
    if arg != "all":
        dirs = [d for d in dirs if to_slug(d) == arg]
        if not dirs:
            print(f"no subs dir for slug {arg}")
            return 1
    for d in dirs:
        if to_slug(d) == "from":
            continue  # FROM already staged + processed (showcase)
        stage_one(d)
    return 0


if __name__ == "__main__":
    sys.exit(main())
