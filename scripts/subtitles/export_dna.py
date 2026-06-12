#!/usr/bin/env python3
"""Export public-safe Dialogue DNA aggregates for the site build.

Reads  data/subtitles/<slug>/_stats/*.json   (private corpus)
Writes data/series-dna/<slug>.json           (aggregates ONLY - no dialogue text)

Site components render this as inline SVG (heatmap + season pulse).
"""
import json, os, sys, glob, re

ROOT = os.path.expanduser("~/bollyai")


def downsample(arr, n=24):
    if len(arr) <= n:
        return arr
    out = []
    for i in range(n):
        lo = int(i * len(arr) / n); hi = max(lo + 1, int((i + 1) * len(arr) / n))
        out.append(round(sum(arr[lo:hi]) / (hi - lo)))
    return out


def main(slug):
    stats_dir = os.path.join(ROOT, "data/subtitles", slug, "_stats")
    eps = []
    for f in sorted(glob.glob(os.path.join(stats_dir, "S*.json"))):
        d = json.load(open(f))
        m = re.match(r"S(\d+)E(\d+)", d["episode"])
        eps.append({
            "ep": d["episode"], "season": int(m.group(1)), "n": int(m.group(2)),
            "runtime_min": d["runtime_min"],
            "words": d["words"],
            "wpm": d["words_per_min"],
            "curve": downsample(d["density_per_min"]),
            "longest_silence_sec": (d["top_silences"][0]["secs"] if d["top_silences"] else 0),
            "longest_silence_at": (d["top_silences"][0]["from"] if d["top_silences"] else None),
            "mentions": d.get("name_mentions", {}),
        })
    out = {"slug": slug, "episodes": eps}
    os.makedirs(os.path.join(ROOT, "data/series-dna"), exist_ok=True)
    path = os.path.join(ROOT, "data/series-dna", f"{slug}.json")
    json.dump(out, open(path, "w"), ensure_ascii=False)
    print(f"OK {path}  ({len(eps)} eps)")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "from")
