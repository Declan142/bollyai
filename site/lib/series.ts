import fs from "node:fs";
import path from "node:path";
import type { DeskSlug } from "./desks";
import type { Confidence, SourceValue } from "./data";
import { isFreeInIndia, platformInfo } from "./platforms";

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

export type PosterVariants = {
  avifSrcSet: string;
  webpSrcSet: string;
  widths: number[];
};

export type PosterAsset = {
  src: string;
  alt: string;
  attribution: string;
  variants?: PosterVariants;
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
  genres?: string[]; // facet tags (Wikidata P136, normalized) — optional
  logline: string;
  poster: PosterAsset;
  backdrop?: PosterAsset;
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
const POSTER_VARIANT_WIDTHS = [185, 342, 500];

function posterVariantPath(src: string, width: number, extension: "avif" | "webp"): string {
  return src.replace(/poster\.jpg$/, `w${width}.${extension}`);
}

function posterVariants(src: string): PosterVariants | undefined {
  if (!src.startsWith("/img/series/") || src.includes("_fallback") || !src.endsWith("/poster.jpg")) return undefined;
  const manifest = path.join(publicDir, src.replace(/poster\.jpg$/, "manifest.json").replace(/^\//, ""));
  if (!fs.existsSync(manifest)) return undefined;
  const hasEveryVariant = POSTER_VARIANT_WIDTHS.every((width) =>
    (["avif", "webp"] as const).every((extension) => {
      const variant = posterVariantPath(src, width, extension);
      return fs.existsSync(path.join(publicDir, variant.replace(/^\//, "")));
    })
  );
  if (!hasEveryVariant) return undefined;
  return {
    widths: POSTER_VARIANT_WIDTHS,
    avifSrcSet: POSTER_VARIANT_WIDTHS.map((width) => `${posterVariantPath(src, width, "avif")} ${width}w`).join(", "),
    webpSrcSet: POSTER_VARIANT_WIDTHS.map((width) => `${posterVariantPath(src, width, "webp")} ${width}w`).join(", ")
  };
}

function attachPosterVariants(series: Series): Series {
  const variants = posterVariants(series.poster.src);
  return variants ? { ...series, poster: { ...series.poster, variants } } : series;
}

// At build time, swap any poster whose file isn't on disk to the fallback SVG so a
// not-yet-harvested series never ships a broken <img>. The attribution still reads
// the original (we only degrade the pixels, not the credit line).
function resolvePoster(series: Series): Series {
  const src = series.poster?.src;
  if (!src || !src.startsWith("/")) return series;
  const onDisk = path.join(publicDir, src.replace(/^\//, ""));
  if (fs.existsSync(onDisk)) return attachPosterVariants(series);
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

// Most recent season air date (ISO yyyy-mm-dd) — the recency signal that powers
// "recent always surfaces first" across the browse + home rails.
export function seriesRecency(series: Series): string {
  let best = "";
  for (const s of series.seasons) {
    const d = s.release_date?.value;
    if (d && d > best) best = d;
  }
  return best || series.date_modified.slice(0, 10);
}

// "Fresh" = a season aired within the last `days` of the build (gets the NEW badge).
export function isFreshSeries(series: Series, now: number = Date.now(), days = 150): boolean {
  const t = new Date(seriesRecency(series)).getTime();
  return Number.isFinite(t) && now - t <= days * 86400000 && now - t >= 0;
}

// All series, newest-content first. Default order for the viral browse + home.
export function getSeriesByRecency(): Series[] {
  return [...getAllSeries()].sort((a, b) => seriesRecency(b).localeCompare(seriesRecency(a)));
}

// ---- Where-to-Watch surface (per-title streaming guide) ----

// Total aired episodes across all seasons — the "how long is the binge" number.
export function totalEpisodes(series: Series): number {
  return series.seasons.reduce((sum, s) => sum + (s.episodes || 0), 0);
}

// Tokenise a platform string ("JTBC / Netflix" -> ["jtbc","netflix"]) so a show on a
// combined platform still shares the "Netflix" cohort.
function platformTokens(p: string): string[] {
  return p
    .split(/[/,&]|\band\b/i)
    .map((x) => x.trim().toLowerCase())
    .filter(Boolean);
}

// Other series sharing a streaming platform — powers the "more to watch on X" mesh and
// the internal-link cluster. Ranks by shared-genre overlap, then recency. Excludes self.
export function moreOnPlatform(series: Series, limit = 6): Series[] {
  const mine = new Set(platformTokens(series.platform.value));
  const myGenres = new Set(series.genres ?? []);
  return getAllSeries()
    .filter((s) => s.slug !== series.slug && platformTokens(s.platform.value).some((tok) => mine.has(tok)))
    .map((s) => ({ s, shared: (s.genres ?? []).filter((g) => myGenres.has(g)).length }))
    .sort((a, b) => b.shared - a.shared || seriesRecency(b.s).localeCompare(seriesRecency(a.s)))
    .slice(0, limit)
    .map((x) => x.s);
}

// Platform-specific FAQ for the where-to-watch page — deliberately does NOT repeat the
// hub's "Quick Answers" (where can I watch / how many seasons / is it worth it). These
// target the India access questions the hub never answers: free-or-paid, how-to-watch,
// dub/subtitle. Built ONLY from real fields + the platform table. No fabricated availability.
export function whereToWatchFaq(series: Series): Array<{ q: string; a: string }> {
  const t = series.title.value;
  const plat = series.platform.value;
  const info = platformInfo(plat);
  const free = isFreeInIndia(plat);
  const lang = series.original_language.value;
  const foreign = !["en", "hi"].includes(lang.toLowerCase());
  const faq: Array<{ q: string; a: string }> = [];

  faq.push({
    q: `Is ${t} free to watch in India?`,
    a: free
      ? `Yes — ${t} streams free with ads on ${plat} in India, no subscription needed.`
      : `No — ${t} needs a ${plat} subscription in India. ${info.note}`
  });
  faq.push({
    q: `How do I watch ${t} on ${plat} in India?`,
    a: `${info.note} ${t} then plays in full on ${plat}; BollyAI tracks it on ${plat} only.`
  });
  faq.push({
    q: foreign ? `Can I watch ${t} dubbed or subtitled in India?` : `What language is ${t} in?`,
    a: foreign
      ? `${t} is a ${lang.toUpperCase()} original; ${plat} carries subtitles and often a dub for popular titles.`
      : `${t} is in ${lang.toUpperCase()} and streams as-is on ${plat}.`
  });
  return faq;
}

// Build a standalone streaming guide ONLY for multi-season titles. The IG gate showed a
// single-season where-to-watch page is a near-duplicate of its own hub (cosine ~0.93 — the
// hub already answers "where to watch X"); a multi-season page carries genuinely distinct
// info: per-season binge order + divergent season verdicts the hub frames differently and
// the SERP lacks. Single-season titles stay on the hub.
export function qualifiesForWhereToWatch(series: Series): boolean {
  return series.seasons.length >= 2;
}

export type { Confidence };
