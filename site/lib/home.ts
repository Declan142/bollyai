import { getDesk, type DeskSlug } from "./desks";
import { formatCrore, getAllFilms, type Film, type VerdictRung } from "./data";
import {
  getAllSeries,
  isFreshSeries,
  latestSeason,
  peakSeason,
  seriesRecency,
  type OttRung,
  type PosterAsset,
  type Series
} from "./series";

// One unified shape for the homepage rails so a single card component renders BOTH a
// film and a series. The card never special-cases inside markup - it reads MediaItem.
export type MediaItem = {
  kind: "film" | "series";
  slug: string;
  href: string;
  desk: DeskSlug;
  deskLabel: string;
  title: string;
  poster: PosterAsset;
  score: number | null; // BollyMeter 0-10 (the cross-type signal; film rungs are box-office, not /10)
  meta: string; // platform line (series) or box-office figure / status (film)
  filmRung?: VerdictRung | null; // 9-rung theatrical ladder (films)
  filmTracking?: boolean;
  seriesRung?: OttRung | null; // 5-rung OTT ladder (series)
  recency: string; // ISO yyyy-mm-dd, drives the recency-first ordering
  fresh: boolean; // landed inside the freshness window -> NEW badge
};

// Theatrical figure for the card meta line: prefer the bigger verified number, fall back
// to a plain-language status so an unverified film still reads cleanly (never a fabricated cr).
function filmFigure(film: Film): string {
  const net = film.box_office.totals.india_net_inr_cr?.value;
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value;
  if (ww) return `${formatCrore(ww)} WW`;
  if (net) return `${formatCrore(net)} India`;
  if (film.status === "live") return "In cinemas now";
  if (film.status === "upcoming") return "Releasing soon";
  if (film.status === "ott") return film.ott?.platform?.value ?? "Now streaming";
  return "Figures under verification";
}

// Films are routed by lifecycle: upcoming -> /upcoming, theatrical -> /box-office,
// already-on-OTT -> /reviews (the verdict surface). Every route is statically generated
// for every film, so the card link is always live.
function filmHref(film: Film): string {
  const surface = film.status === "upcoming" ? "upcoming" : film.status === "ott" ? "reviews" : "box-office";
  return `/${film.canonical_industry}/${surface}/${film.slug}/`;
}

const FILM_FRESH_DAYS = 75;

function isFreshFilm(film: Film, now: number): boolean {
  const t = new Date(film.release_date?.value ?? "").getTime();
  return Number.isFinite(t) && now - t <= FILM_FRESH_DAYS * 86400000 && now - t >= -7 * 86400000;
}

export function filmToItem(film: Film, now: number = Date.now()): MediaItem {
  return {
    kind: "film",
    slug: film.slug,
    href: filmHref(film),
    desk: film.canonical_industry,
    deskLabel: getDesk(film.canonical_industry)?.label ?? film.canonical_industry,
    title: film.title.value,
    poster: film.poster,
    score: film.bollymeter?.score ?? null,
    meta: filmFigure(film),
    filmRung: film.verdict.ladder_rung,
    filmTracking: film.verdict.tracking,
    recency: film.release_date?.value ?? film.date_modified.slice(0, 10),
    fresh: isFreshFilm(film, now)
  };
}

export function seriesToItem(series: Series, now: number = Date.now()): MediaItem {
  const current = latestSeason(series); // current state for the verdict rung
  const peak = peakSeason(series); // best-known score for the franchise signal
  return {
    kind: "series",
    slug: series.slug,
    href: `/series/${series.slug}/`,
    desk: series.canonical_industry,
    deskLabel: getDesk(series.canonical_industry)?.label ?? "Streaming",
    title: series.title.value,
    poster: series.poster,
    score: peak?.bollymeter?.score ?? current?.bollymeter?.score ?? null,
    meta: series.platform.value,
    seriesRung: current?.verdict ?? null,
    recency: seriesRecency(series),
    fresh: isFreshSeries(series, now)
  };
}

// JUST DROPPED - the unified beat: newest films AND series interleaved, freshest first.
export function justDropped(limit = 16, now: number = Date.now()): MediaItem[] {
  const items = [...getAllFilms().map((f) => filmToItem(f, now)), ...getAllSeries().map((s) => seriesToItem(s, now))];
  return items.sort((a, b) => b.recency.localeCompare(a.recency)).slice(0, limit);
}

// BIG THIS WEEK - the high-signal mixed rail. Live theatrical runs pin first (they ARE the
// week's argument), then everything from the last 120 days ranked by BollyMeter. Grounded:
// the ordering is real box-office status + real scores, never a fabricated "trending" metric.
export function bigThisWeek(limit = 14, now: number = Date.now()): MediaItem[] {
  const liveFilms = getAllFilms()
    .filter((f) => f.status === "live")
    .map((f) => filmToItem(f, now));
  const liveSlugs = new Set(liveFilms.map((i) => `film:${i.slug}`));

  const windowMs = 120 * 86400000;
  const recent = [...getAllFilms().map((f) => filmToItem(f, now)), ...getAllSeries().map((s) => seriesToItem(s, now))]
    .filter((i) => !liveSlugs.has(`${i.kind}:${i.slug}`))
    .filter((i) => {
      const t = new Date(i.recency).getTime();
      return Number.isFinite(t) && now - t <= windowMs;
    })
    .sort((a, b) => (b.score ?? 0) - (a.score ?? 0) || b.recency.localeCompare(a.recency));

  return [...liveFilms, ...recent].slice(0, limit);
}

// Per-desk counts for the quick-nav strip (films + series that map to that desk).
export function deskCounts(): Record<DeskSlug, number> {
  const counts = {
    bollywood: 0,
    kollywood: 0,
    tollywood: 0,
    mollywood: 0,
    sandalwood: 0,
    hollywood: 0,
    streaming: 0
  } as Record<DeskSlug, number>;
  for (const f of getAllFilms()) counts[f.canonical_industry] = (counts[f.canonical_industry] ?? 0) + 1;
  for (const s of getAllSeries()) counts[s.canonical_industry] = (counts[s.canonical_industry] ?? 0) + 1;
  return counts;
}

// Live catalogue tallies for the above-the-fold liveness ribbon. Real counts only.
export function catalogueStats(): { films: number; series: number; total: number } {
  const films = getAllFilms().length;
  const series = getAllSeries().length;
  return { films, series, total: films + series };
}
