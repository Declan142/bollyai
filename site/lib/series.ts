import fs from "node:fs";
import path from "node:path";
import type { DeskSlug } from "./desks";
import type { Confidence, SourceValue } from "./data";

// OTT verdict ladder (Seat 05 series/OTT variant): 5 rungs, craft + word-of-mouth, not box office.
export const OTT_RUNGS = ["DISASTER DROP", "SKIP", "ONE-TIME WATCH", "WORTH-IT", "MUST-WATCH"] as const;
export type OttRung = (typeof OTT_RUNGS)[number];

export type PullQuote = {
  text: string; // <= 25 words, attributed
  source: string;
  url: string;
};

// Standout-episode reviews. NOT every episode (that's slop) — premieres, finales,
// and the turning-point hours critics and audiences actually argue about.
// Same hard fence as season review_body: NO first-person viewing claims (gate #1).
export type EpisodeReview = {
  number: number; // episode number within the season
  title: string; // episode title (or "Episode N" if untitled)
  air_date?: string | null;
  bollymeter: number | null; // /10 for this single hour, null = unscored
  spoiler_free: string; // BollyAI's read, spoiler-light, no viewing claim
  the_moment?: string | null; // the beat people remember (kept spoiler-careful)
  critic_note?: { text: string; source: string; url: string } | null;
};

export type SeriesSeason = {
  number: number;
  year: number;
  episodes: number;
  release_date: SourceValue<string>;
  verdict: OttRung | null; // null = still dropping / verdict open
  bollymeter: { score: number; basis: string } | null;
  critic: {
    positive_pct: number | null;
    sample: number | null; // n critics
    pull_quotes: PullQuote[];
  };
  audience: {
    rating: number | null;
    scale: number; // e.g. 10 for IMDb
    source: string;
    source_url: string;
  } | null;
  review_body: string; // BollyAI's read — NO first-person viewing claims (gate #1)
  season_over_season: string | null;
  episode_reviews?: EpisodeReview[]; // optional standout-episode breakdowns
};

export type Series = {
  slug: string;
  qid: SourceValue<string> | null; // some series lack a QID at seed time
  title: SourceValue<string>;
  canonical_industry: DeskSlug;
  origin: string; // "India" | "South Korea" | "United States" | ...
  original_language: SourceValue<string>;
  platform: SourceValue<string>;
  status: "running" | "returning" | "ended" | "limited";
  logline: string;
  poster: { src: string; alt: string; attribution: string };
  backdrop?: { src: string; alt: string; attribution: string };
  renewal: {
    state: "renewed" | "awaiting" | "ended" | "final-season" | "limited";
    note: string;
    source: string;
    source_url: string;
  };
  seasons: SeriesSeason[];
  _quarantine: unknown[];
  date_modified: string;
};

const seriesDir = path.resolve(process.cwd(), "..", "data", "series");

const SERIES_POSTER_FALLBACK = "/img/series/_fallback.svg";
const publicDir = path.resolve(process.cwd(), "public");

// At build time, swap any poster whose file isn't on disk to the fallback SVG so a
// not-yet-harvested series never ships a broken <img>. The attribution still reads
// the original (we only degrade the pixels, not the credit line).
function resolvePoster(series: Series): Series {
  const src = series.poster?.src;
  if (!src || !src.startsWith("/")) return series;
  const onDisk = path.join(publicDir, src.replace(/^\//, ""));
  if (fs.existsSync(onDisk)) return series;
  return { ...series, poster: { ...series.poster, src: SERIES_POSTER_FALLBACK } };
}

export function getAllSeries(): Series[] {
  if (!fs.existsSync(seriesDir)) return [];
  return fs
    .readdirSync(seriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(seriesDir, f), "utf8")) as Series)
    .map(resolvePoster)
    .sort((a, b) => b.date_modified.localeCompare(a.date_modified));
}

export function getSeries(slug: string): Series | undefined {
  return getAllSeries().find((s) => s.slug === slug);
}

export function latestSeason(series: Series): SeriesSeason | undefined {
  return [...series.seasons].sort((a, b) => b.number - a.number)[0];
}

// The show's best-scored season — what the franchise is remembered/searched for.
// Used for the HUB title so a declined show isn't headlined by its weakest latest
// season (per-season pages still carry their own per-season verdict). Falls back to
// the latest season when no season has a BollyMeter score yet.
export function peakSeason(series: Series): SeriesSeason | undefined {
  const scored = series.seasons.filter((s) => s.bollymeter);
  if (scored.length === 0) return latestSeason(series);
  return [...scored].sort((a, b) => b.bollymeter!.score - a.bollymeter!.score)[0];
}

export function ottIndex(rung: OttRung): number {
  return Math.max(0, OTT_RUNGS.indexOf(rung));
}

export type { Confidence };
