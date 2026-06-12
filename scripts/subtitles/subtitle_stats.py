#!/usr/bin/env python3
"""BollyAI Stage B — subtitle parse + per-episode stats engine.

Input:  data/subtitles/<slug>/SxxExx.srt  (private corpus, NEVER published)
Output: data/subtitles/<slug>/_stats/SxxExx.json  (per-episode stats)
        data/subtitles/<slug>/_stats/series.json  (cross-episode aggregates)

Pure stdlib. No LLM. Speaker tags used when SDH provides them
(NAME: line or [NAME] cue), else lines stay unattributed.
"""
import json, os, re, sys, glob, math
from collections import Counter, defaultdict

TAG_RE = re.compile(r"<[^>]+>")
CREDIT_RE = re.compile(r"addic|opensubtitl|podnapisi|subscene|synced|corrected by|subtitles? by|encoded by|resync|www\.|\.com|\.org", re.I)
SDH_BRACKET_RE = re.compile(r"\[[^\]]*\]|\([^)]*\)")  # [door creaks] / (sighs)

# FROM principal cast (public knowledge; used only to COUNT spoken name mentions).
# Other series: drop a roster.json (["Name", ...]) in data/subtitles/<slug>/ - loaded in main().
ROSTER = ["Boyd", "Tabitha", "Jim", "Julie", "Ethan", "Victor", "Sara", "Kenny",
          "Donna", "Kristi", "Jade", "Elgin", "Fatima", "Tian-Chen", "Tillie",
          "Randall", "Marielle", "Dale", "Henry", "Abby", "Martin", "Smiley",
          "Miranda", "Frank", "Tom", "Nathan", "Paula", "Bakta", "Khatri"]
SPEAKER_RE = re.compile(r"^([A-Z][A-Z .'\-]{1,24}):\s*(.*)$")
MUSIC_RE = re.compile(r"^[♪♫\s]+$|^♪.*♪$")
TIME_RE = re.compile(r"(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)")

STOP = set("""the a an and or but to of in on at for with is are was were be been i you he she it we
they this that these those my your his her its our their me him them not no yes do does did have has
had will would can could should what when where why how who if then there here just so as from up out
all about get got like know going go come came back right now well okay ok oh hey um uh don can't""".split())


def parse_srt(path):
    raw = open(path, encoding="utf-8", errors="replace").read()
    raw = raw.replace("﻿", "")
    cues = []
    for block in re.split(r"\n\s*\n", raw):
        m = TIME_RE.search(block)
        if not m:
            continue
        g = [int(x) for x in m.groups()]
        start = g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000.0
        end = g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000.0
        text_lines = block[m.end():].strip().splitlines()
        text = " ".join(l.strip() for l in text_lines if l.strip())
        text = TAG_RE.sub("", text).strip()
        if not text or MUSIC_RE.match(text) or CREDIT_RE.search(text):
            continue
        cues.append({"start": round(start, 2), "end": round(end, 2), "text": text})
    return cues


def split_speakers(cue_text):
    """Split '- line1 - line2' multi-speaker cues; extract NAME: tags if present."""
    parts = [p.strip() for p in re.split(r"(?:^|\s)-\s+", cue_text) if p.strip()]
    if not parts:
        parts = [cue_text]
    out = []
    for p in parts:
        sdh_clean = SDH_BRACKET_RE.sub("", p).strip()
        if not sdh_clean:
            continue
        m = SPEAKER_RE.match(sdh_clean)
        if m and len(m.group(2)) > 0:
            out.append({"speaker": m.group(1).title().strip(), "line": m.group(2).strip()})
        else:
            out.append({"speaker": None, "line": sdh_clean})
    return out


def ngrams(tokens, n):
    return zip(*[tokens[i:] for i in range(n)])


def episode_stats(path, ep_id):
    cues = parse_srt(path)
    if not cues:
        return None
    runtime = cues[-1]["end"]
    lines = []
    for c in cues:
        for sp in split_speakers(c["text"]):
            lines.append({"t": c["start"], "speaker": sp["speaker"], "line": sp["line"]})

    # dialogue density per minute bucket
    nmin = int(math.ceil(runtime / 60.0))
    density = [0] * nmin
    for c in cues:
        b = min(int(c["start"] // 60), nmin - 1)
        density[b] += len(c["text"].split())

    # silence stretches (>= 45s with no cue)
    silences = []
    prev_end = 0.0
    for c in cues:
        gap = c["start"] - prev_end
        if gap >= 45:
            silences.append({"from": round(prev_end, 1), "to": round(c["start"], 1), "secs": round(gap, 1)})
        prev_end = max(prev_end, c["end"])
    silences.sort(key=lambda s: -s["secs"])

    # speaker line counts (only if SDH gave us names)
    speakers = Counter(l["speaker"] for l in lines if l["speaker"])

    # distinctive phrases (3-4 grams, non-stopword anchored)
    tokens = []
    for l in lines:
        tokens += [w for w in re.findall(r"[a-z']+", l["line"].lower())]
    phr = Counter()
    for n in (3, 4):
        for g in ngrams(tokens, n):
            if g[0] in STOP or g[-1] in STOP:
                continue
            if all(w in STOP for w in g):
                continue
            phr[" ".join(g)] += 1
    phrases = [{"phrase": p, "count": c} for p, c in phr.most_common(25) if c >= 2]

    # spoken name mentions (deterministic "who the town talks about")
    joined = " ".join(l["line"] for l in lines)
    mentions = {}
    for name in ROSTER:
        n = len(re.findall(r"\b" + re.escape(name) + r"\b", joined, re.I))
        if n:
            mentions[name] = n

    words = len(tokens)
    return {
        "episode": ep_id,
        "runtime_min": round(runtime / 60.0, 1),
        "cues": len(cues),
        "words": words,
        "words_per_min": round(words / (runtime / 60.0), 1),
        "density_per_min": density,
        "top_silences": silences[:6],
        "speaker_lines": dict(speakers.most_common(30)),
        "name_mentions": mentions,
        "phrases": phrases,
        "dialogue": lines,  # full doc for dossier stage (private)
    }


def main(slug):
    global ROSTER
    root = os.path.expanduser(f"~/bollyai/data/subtitles/{slug}")
    roster_p = os.path.join(root, "roster.json")
    if os.path.exists(roster_p):
        ROSTER = json.load(open(roster_p))
    out = os.path.join(root, "_stats")
    os.makedirs(out, exist_ok=True)
    series = {"episodes": [], "phrase_index": defaultdict(list)}
    for srt in sorted(glob.glob(os.path.join(root, "*.srt"))):
        ep_id = re.search(r"(S\d{2}E\d{2})", os.path.basename(srt))
        ep_id = ep_id.group(1) if ep_id else os.path.basename(srt)[:-4]
        st = episode_stats(srt, ep_id)
        if not st:
            print(f"SKIP {ep_id} (no cues)")
            continue
        json.dump(st, open(os.path.join(out, f"{ep_id}.json"), "w"), ensure_ascii=False)
        series["episodes"].append({k: st[k] for k in
            ("episode", "runtime_min", "cues", "words", "words_per_min", "top_silences", "speaker_lines", "name_mentions")})
        for p in st["phrases"]:
            series["phrase_index"][p["phrase"]].append({"ep": ep_id, "n": p["count"]})
        print(f"OK   {ep_id}  {st['runtime_min']}min  {st['words']}w  {st['words_per_min']}wpm  speakers={len(st['speaker_lines'])}")
    # cross-episode recurring phrases = callback candidates
    series["recurring_phrases"] = sorted(
        [{"phrase": p, "eps": v} for p, v in series["phrase_index"].items() if len(v) >= 2],
        key=lambda x: -len(x["eps"]))[:60]
    del series["phrase_index"]
    json.dump(series, open(os.path.join(out, "series.json"), "w"), ensure_ascii=False, indent=1)
    print(f"\nseries.json: {len(series['episodes'])} eps, {len(series['recurring_phrases'])} recurring phrases")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "from")
