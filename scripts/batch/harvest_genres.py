#!/usr/bin/env python3
"""Backfill series genres from Wikidata P136 (keyless SPARQL, QID-keyed) - the
Wikidata-spine way (see project-bollyai-no-tmdb-wikidata-spine). Writes a
normalized genres:[...] facet list into each series JSON, inserted right after
`status`. Light-maps messy Wikidata labels into clean filter buckets.

Usage: harvest_genres.py            # all series with a qid
       harvest_genres.py <slug...>  # only these
"""
from __future__ import annotations
import glob, json, os, re, sys, time
import requests

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SDIR = os.path.join(ROOT, "data", "series")
UA = "BollyAI-genre-harvester/1.0 (https://bollyai.in; takedown@bollyai.in)"
SPARQL = "https://query.wikidata.org/sparql"

# messy Wikidata label -> clean facet bucket(s)
MAP = {
    "television drama": ["Drama"], "drama": ["Drama"], "melodrama": ["Drama"], "teleserye": ["Drama"],
    "thriller": ["Thriller"], "psychological thriller": ["Thriller", "Psychological"],
    "techno-thriller": ["Thriller"], "political thriller": ["Thriller", "Political"], "conspiracy thriller": ["Thriller"],
    "romance": ["Romance"], "romantic comedy": ["Romance", "Comedy"], "romance film": ["Romance"], "romantic drama": ["Romance", "Drama"],
    "comedy": ["Comedy"], "comedy-drama": ["Comedy", "Drama"], "comedy drama": ["Comedy", "Drama"],
    "sitcom": ["Comedy"], "situation comedy": ["Comedy"], "black comedy": ["Comedy"], "satire": ["Comedy"], "dark comedy": ["Comedy"],
    "crime": ["Crime"], "crime film": ["Crime"], "crime drama": ["Crime"], "crime fiction": ["Crime"],
    "police procedural": ["Crime"], "heist": ["Crime"], "gangster": ["Crime"], "neo-noir": ["Crime"], "noir": ["Crime"],
    "science fiction": ["Sci-Fi"], "science fiction film": ["Sci-Fi"], "dystopia": ["Sci-Fi"],
    "post-apocalyptic": ["Sci-Fi"], "cyberpunk": ["Sci-Fi"], "space opera": ["Sci-Fi"],
    "fantasy": ["Fantasy"], "dark fantasy": ["Fantasy"], "urban fantasy": ["Fantasy"], "high fantasy": ["Fantasy"], "fantasy film": ["Fantasy"],
    "horror": ["Horror"], "horror film": ["Horror"], "zombie": ["Horror"], "survival horror": ["Horror"],
    "action": ["Action"], "action fiction": ["Action"], "action film": ["Action"], "martial arts": ["Action"], "action thriller": ["Action", "Thriller"],
    "mystery": ["Mystery"], "mystery fiction": ["Mystery"], "whodunit": ["Mystery"], "detective fiction": ["Mystery"],
    "historical drama": ["Historical"], "historical": ["Historical"], "period drama": ["Historical"],
    "history": ["Historical"], "historical fiction": ["Historical"], "period piece": ["Historical"],
    "teen drama": ["Teen"], "teen": ["Teen"],
    "medical drama": ["Medical"], "medical fiction": ["Medical"],
    "legal drama": ["Legal"], "courtroom drama": ["Legal"],
    "slice of life": ["Slice of Life"],
    "coming-of-age story": ["Coming of Age"], "coming-of-age": ["Coming of Age"], "bildungsroman": ["Coming of Age"],
    "supernatural fiction": ["Supernatural"], "supernatural": ["Supernatural"], "occult": ["Supernatural"],
    "war film": ["War"], "war": ["War"],
    "biographical film": ["Biographical"], "biography": ["Biographical"], "biographical": ["Biographical"],
    "adventure": ["Adventure"], "adventure fiction": ["Adventure"], "adventure film": ["Adventure"],
    "documentary": ["Documentary"], "docuseries": ["Documentary"], "documentary film": ["Documentary"],
    "anime": ["Anime"], "isekai": ["Anime", "Fantasy"], "shonen": ["Anime"], "seinen": ["Anime"],
    "spy fiction": ["Spy"], "spy film": ["Spy"], "espionage": ["Spy"],
    "musical": ["Musical"], "sports": ["Sports"], "sports film": ["Sports"],
    "superhero": ["Superhero"], "superhero fiction": ["Superhero"],
    "family": ["Family"], "family film": ["Family"],
    "raunchy comedy": ["Comedy"], "screwball comedy": ["Comedy"], "workplace comedy": ["Comedy"],
    "buddy": ["Action"], "wuxia": ["Action"], "thriller drama": ["Thriller", "Drama"],
}


REMAP = {
    "korean drama": ["Drama"], "japanese drama": ["Drama"], "chinese drama": ["Drama"],
    "lgbt-related": ["LGBTQ"], "lgbt": ["LGBTQ"], "youth": ["Teen"],
    "psychological drama": ["Drama", "Psychological"], "alternate history": ["Alternate History"],
}
DROP = {"science", "korean", "japanese", "chinese", "american", "british",
        "live action", "live-action", "anime and manga", "manga", "live", ""}

# Curated fallback for well-known titles Wikidata P136 does not carry. Applied
# ONLY when the Wikidata query yields no genre for that slug.
SEED = {
    "money-heist": ["Crime", "Thriller"], "sherlock": ["Mystery", "Crime", "Drama"],
    "the-crown": ["Historical", "Drama", "Biographical"], "elite": ["Teen", "Thriller", "Drama"],
    "fauda": ["Thriller", "Action", "Drama"], "lupin": ["Crime", "Mystery", "Thriller"],
    "slow-horses": ["Spy", "Thriller", "Drama"], "true-detective": ["Crime", "Mystery", "Drama"],
    "heeramandi": ["Historical", "Drama"], "aarya": ["Crime", "Thriller", "Drama"],
    "adolescence": ["Crime", "Drama"], "baby-reindeer": ["Drama", "Thriller"],
    "bambai-meri-jaan": ["Crime", "Drama"], "berlin": ["Crime", "Thriller"],
    "black-warrant": ["Crime", "Drama"], "bodyguard": ["Thriller", "Drama"],
    "business-proposal": ["Romance", "Comedy"], "class": ["Teen", "Drama", "Crime"],
    "criminal-justice": ["Legal", "Crime", "Drama"], "gullak": ["Comedy", "Drama", "Family"],
    "guns-and-gulaabs": ["Crime", "Comedy"], "half-ca": ["Drama", "Coming of Age"],
    "hometown-cha-cha-cha": ["Romance", "Comedy", "Drama"], "itaewon-class": ["Drama"],
    "jubilee": ["Drama", "Historical"], "kaala-paani": ["Thriller", "Survival", "Drama"],
    "killer-soup": ["Crime", "Comedy", "Thriller"], "kohrra": ["Crime", "Mystery", "Drama"],
    "maharani": ["Drama", "Political"], "move-to-heaven": ["Drama"],
    "mumbai-diaries": ["Medical", "Drama", "Thriller"], "poacher": ["Crime", "Thriller", "Drama"],
    "scoop": ["Crime", "Drama"], "suzhal-the-vortex": ["Crime", "Mystery", "Thriller"],
    "the-railway-men": ["Drama", "Historical", "Thriller"], "top-boy": ["Crime", "Drama"],
    "trial-by-fire": ["Drama"], "vadhandhi-the-fable-of-velonie": ["Crime", "Mystery", "Thriller"],
    # second wave of Wikidata-P136 gaps (canonical, hand-verified)
    "dark": ["Sci-Fi", "Thriller", "Mystery"], "loki": ["Sci-Fi", "Fantasy", "Action"],
    "the-witcher": ["Fantasy", "Action", "Adventure"], "the-mandalorian": ["Sci-Fi", "Action", "Adventure"],
    "foundation": ["Sci-Fi", "Drama"], "silo": ["Sci-Fi", "Mystery", "Thriller"],
    "the-expanse": ["Sci-Fi", "Thriller", "Drama"], "arcane": ["Action", "Fantasy", "Adventure", "Drama"],
    "invincible": ["Action", "Superhero", "Drama"], "black-mirror": ["Sci-Fi", "Thriller", "Drama"],
    "fleabag": ["Comedy", "Drama"], "the-umbrella-academy": ["Sci-Fi", "Action", "Comedy"],
    "dandadan": ["Anime", "Comedy", "Supernatural", "Action"], "mob-psycho-100": ["Anime", "Action", "Comedy", "Supernatural"],
    "steins-gate": ["Anime", "Sci-Fi", "Thriller"], "bleach-thousand-year-blood-war": ["Anime", "Action", "Fantasy"],
    "solo-leveling": ["Anime", "Action", "Fantasy"], "code-geass": ["Anime", "Sci-Fi", "Action"],
    "cowboy-bebop-1998": ["Anime", "Sci-Fi", "Action"], "hunter-x-hunter-2011": ["Anime", "Adventure", "Action", "Fantasy"],
    "one-punch-man": ["Anime", "Action", "Comedy", "Superhero"], "frieren-beyond-journeys-end": ["Anime", "Fantasy", "Adventure"],
    "monster-2004": ["Anime", "Thriller", "Mystery", "Crime"], "dahaad": ["Crime", "Thriller", "Drama"],
    "delhi-crime": ["Crime", "Drama", "Thriller"], "farzi": ["Crime", "Thriller", "Drama"],
    "mirzapur": ["Crime", "Action", "Drama"], "sacred-games": ["Crime", "Thriller", "Drama"],
    "paatal-lok": ["Crime", "Thriller", "Drama"], "kaalkoot": ["Crime", "Drama"],
    "the-family-man": ["Action", "Thriller", "Drama"], "made-in-india-a-titan-story": ["Drama", "Biographical"],
    "brown": ["Crime", "Mystery", "Thriller"], "raakh": ["Crime", "Thriller", "Drama"],
    "maa-behen": ["Drama"], "thukra-ke-mera-pyaar": ["Drama", "Romance"],
    "signal": ["Crime", "Thriller", "Mystery"], "hospital-playlist": ["Medical", "Drama", "Comedy"],
    "a-killer-paradox": ["Crime", "Thriller", "Drama"], "extraordinary-attorney-woo": ["Legal", "Drama"],
    "sky-castle": ["Drama", "Thriller"], "big-mouth": ["Crime", "Thriller", "Drama"],
    "when-the-phone-rings": ["Thriller", "Romance", "Drama"], "taxi-driver": ["Action", "Crime", "Drama"],
    "sanctuary-sumo": ["Sports", "Drama"], "suburra": ["Crime", "Drama", "Thriller"],
}


def clean(label: str) -> list[str]:
    l = label.lower().strip()
    if l in MAP:
        return MAP[l]
    # "X anime and manga" / "X anime" -> Anime + clean(X)
    m = re.match(r"(.*?)\s+anime(?:\s+and\s+manga)?$", l)
    if m:
        base = m.group(1).strip()
        return list(dict.fromkeys(["Anime"] + (clean(base) if base else [])))
    l = re.sub(r"\s*\(.*?\)", "", l)
    l = re.sub(r"\b(film|fiction|series|television|tv|genre|programme|program)\b", "", l).strip()
    l = re.sub(r"\s+", " ", l).strip()
    if l in MAP:
        return MAP[l]
    if l in REMAP:
        return REMAP[l]
    if l in DROP or not l or len(l) > 22:
        return []
    return [l.title()]


def fetch(qids: list[str]) -> dict[str, dict[str, list[str]]]:
    vals = " ".join(f"wd:{q}" for q in qids)
    q = (f"SELECT ?item ?g ?inst WHERE {{ VALUES ?item {{ {vals} }} "
         f'OPTIONAL {{ ?item wdt:P136 ?gg. ?gg rdfs:label ?g FILTER(lang(?g)="en") }} '
         f'OPTIONAL {{ ?item wdt:P31 ?ii. ?ii rdfs:label ?inst FILTER(lang(?inst)="en") }} }}')
    r = requests.get(SPARQL, params={"query": q, "format": "json"},
                     headers={"User-Agent": UA, "Accept": "application/sparql-results+json"}, timeout=60)
    r.raise_for_status()
    out: dict[str, dict[str, list[str]]] = {}
    for b in r.json()["results"]["bindings"]:
        qid = b["item"]["value"].rsplit("/", 1)[-1]
        d = out.setdefault(qid, {"genres": [], "inst": []})
        if "g" in b:
            d["genres"].append(b["g"]["value"])
        if "inst" in b:
            d["inst"].append(b["inst"]["value"])
    return out


def with_genres(d: dict, genres: list[str]) -> dict:
    out = {}
    for k, v in d.items():
        if k == "genres":
            continue
        out[k] = v
        if k == "status":
            out["genres"] = genres
    if "genres" not in out:
        out["genres"] = genres
    return out


def main() -> int:
    only = set(sys.argv[1:])
    files, qid2slug = {}, {}
    for f in glob.glob(os.path.join(SDIR, "*.json")):
        d = json.load(open(f, encoding="utf-8"))
        slug = d["slug"]
        if only and slug not in only:
            continue
        files[slug] = (f, d)
        qid = d.get("qid")
        qv = qid.get("value") if isinstance(qid, dict) else None
        if qv:
            qid2slug.setdefault(qv, []).append(slug)
    qids = list(qid2slug)
    print(f"querying Wikidata P136 for {len(qids)} QIDs ({len(files)} series)...", flush=True)
    raw: dict[str, dict[str, list[str]]] = {}
    for i in range(0, len(qids), 30):
        batch = qids[i:i + 30]
        for attempt in range(3):
            try:
                raw.update(fetch(batch))
                break
            except Exception as e:  # noqa: BLE001
                print(f"  batch {i} attempt {attempt + 1} failed: {e}", flush=True)
                time.sleep(3)
        time.sleep(1.0)
    changed = got = 0
    for q, data in raw.items():
        genres: list[str] = []
        is_anime = any("anime" in s.lower() for s in data.get("inst", []))
        if is_anime:
            genres.append("Anime")
        for lab in data.get("genres", []):
            for g in clean(lab):
                if g not in genres:
                    genres.append(g)
        genres = genres[:5]
        if not genres:
            continue
        got += 1
        for slug in qid2slug[q]:
            f, d = files[slug]
            if d.get("genres") != genres:
                nd = with_genres(d, genres)
                open(f, "w", encoding="utf-8").write(json.dumps(nd, ensure_ascii=False, indent=2) + "\n")
                files[slug] = (f, nd)
                changed += 1
    # Curated fallback for the well-known titles Wikidata P136 misses.
    for slug, (f, d) in list(files.items()):
        if not d.get("genres") and slug in SEED:
            nd = with_genres(d, SEED[slug])
            open(f, "w", encoding="utf-8").write(json.dumps(nd, ensure_ascii=False, indent=2) + "\n")
            files[slug] = (f, nd)
            changed += 1
    no_genre = [slug for slug, (f, d) in files.items() if not d.get("genres")]
    print(f"DONE qids={len(qids)} with_genre={got} files_updated={changed} "
          f"no_genre={len(no_genre)}", flush=True)
    if no_genre:
        print("no-genre slugs:", " ".join(sorted(no_genre)[:40]), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
