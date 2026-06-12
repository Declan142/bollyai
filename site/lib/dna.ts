import fs from "node:fs";
import path from "node:path";

export type DnaEpisode = {
  ep: string;
  season: number;
  n: number;
  runtime_min: number;
  words: number;
  wpm: number;
  curve: number[];
  longest_silence_sec: number;
  longest_silence_at: number | null;
  mentions: Record<string, number>;
};

export type SeriesDna = { slug: string; episodes: DnaEpisode[] };

const dnaDir = path.resolve(process.cwd(), "..", "data", "series-dna");

export function getDna(slug: string): SeriesDna | null {
  const p = path.join(dnaDir, `${slug}.json`);
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, "utf-8")) as SeriesDna;
  } catch {
    return null;
  }
}

export function seasonDna(dna: SeriesDna | null, season: number): DnaEpisode[] {
  if (!dna) return [];
  return dna.episodes.filter((e) => e.season === season).sort((a, b) => a.n - b.n);
}

/** Top characters for a season's heatmap, ranked by total spoken mentions. */
export function topMentioned(eps: DnaEpisode[], limit = 10): string[] {
  const totals = new Map<string, number>();
  for (const e of eps) {
    for (const [name, n] of Object.entries(e.mentions)) {
      totals.set(name, (totals.get(name) ?? 0) + n);
    }
  }
  return [...totals.entries()]
    .sort((a, b) => b[1] - a[1])
    .slice(0, limit)
    .map(([name]) => name);
}
