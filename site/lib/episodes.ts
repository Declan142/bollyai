import fs from "node:fs";
import path from "node:path";

/* Long-form per-episode breakdown pages (recap + read + threads).
   Source: data/episodes/<slug>/SxxExx.json - written by the subtitle-grounded
   editorial pipeline. Same hard fences as everything else: no viewing claims,
   no em-dashes, quotes within fair-dealing caps. */

export type EpisodeThread = {
  label: string;
  direction: "plants" | "pays";
  ref_ep: string | null; // e.g. "S01E01"
  text: string;
};

export type EpisodeBreakdown = {
  episode: string; // SxxExx
  season: number;
  number: number;
  title: string;
  air_date: string | null;
  bollymeter: number | null;
  verdict_line: string; // spoiler-light, lives above the fold
  recap: { h: string; body: string[] }[];
  the_read: string[];
  the_moment: string | null;
  threads: EpisodeThread[];
  questions: string[];
};

const episodesDir = path.resolve(process.cwd(), "..", "data", "episodes");

export function getEpisodeBreakdowns(slug: string): EpisodeBreakdown[] {
  const dir = path.join(episodesDir, slug);
  if (!fs.existsSync(dir)) return [];
  return fs
    .readdirSync(dir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf-8")) as EpisodeBreakdown)
    .sort((a, b) => a.season - b.season || a.number - b.number);
}

export function getEpisodeBreakdown(slug: string, season: number, number: number): EpisodeBreakdown | null {
  const p = path.join(episodesDir, slug, `S${String(season).padStart(2, "0")}E${String(number).padStart(2, "0")}.json`);
  if (!fs.existsSync(p)) return null;
  try {
    return JSON.parse(fs.readFileSync(p, "utf-8")) as EpisodeBreakdown;
  } catch {
    return null;
  }
}

export function epPath(slug: string, season: number, number: number): string {
  return `/series/${slug}/s${season}/e${number}/`;
}

/** Parse "SxxExx" into {season, number}. */
export function parseEpId(id: string): { season: number; number: number } | null {
  const m = /^S(\d{2})E(\d{2})$/.exec(id);
  return m ? { season: Number(m[1]), number: Number(m[2]) } : null;
}
