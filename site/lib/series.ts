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

export function getAllSeries(): Series[] {
  if (!fs.existsSync(seriesDir)) return [];
  return fs
    .readdirSync(seriesDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(seriesDir, f), "utf8")) as Series)
    .sort((a, b) => b.date_modified.localeCompare(a.date_modified));
}

export function getSeries(slug: string): Series | undefined {
  return getAllSeries().find((s) => s.slug === slug);
}

export function latestSeason(series: Series): SeriesSeason | undefined {
  return [...series.seasons].sort((a, b) => b.number - a.number)[0];
}

export function ottIndex(rung: OttRung): number {
  return Math.max(0, OTT_RUNGS.indexOf(rung));
}

export type { Confidence };
