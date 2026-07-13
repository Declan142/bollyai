import { getDesk, type DeskSlug } from "./desks";
import { formatCrore, getAllFilms, getOttCalendar, type Film, type VerdictRung } from "./data";
import {
  getAllSeries,
  isFreshSeries,
  latestSeason,
  latestSeasonReleaseDate,
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
  return {
    kind: "series",
    slug: series.slug,
    href: `/series/${series.slug}/`,
    desk: series.canonical_industry,
    deskLabel: getDesk(series.canonical_industry)?.label ?? "Streaming",
    title: series.title.value,
    poster: series.poster,
    score: current?.bollymeter?.score ?? null,
    meta: series.platform.value,
    seriesRung: current?.verdict ?? null,
    recency: seriesRecency(series),
    fresh: isFreshSeries(series, now)
  };
}

export const LATEST_SERIES_WINDOW_DAYS = 90;

// The homepage latest rail is deliberately date-led. A title only returns when a new
// season lands, so evergreen catalogue hits cannot crowd out current search intent.
export function latestSeries(limit = 8, now: number = Date.now()): MediaItem[] {
  const windowMs = LATEST_SERIES_WINDOW_DAYS * 86400000;
  return getAllSeries()
    .map((series) => {
      const releaseDate = latestSeasonReleaseDate(series);
      if (!releaseDate) return null;
      return { ...seriesToItem(series, now), recency: releaseDate };
    })
    .filter((item): item is MediaItem => item !== null)
    .filter((item) => {
      const releasedAt = new Date(item.recency).getTime();
      const age = now - releasedAt;
      return Number.isFinite(releasedAt) && age >= 0 && age <= windowMs;
    })
    .sort((a, b) => b.recency.localeCompare(a.recency) || a.title.localeCompare(b.title))
    .slice(0, limit);
}

// Live catalogue tallies for the above-the-fold liveness ribbon. Real counts only.
export function catalogueStats(): { films: number; series: number; total: number } {
  const films = getAllFilms().length;
  const series = getAllSeries().length;
  return { films, series, total: films + series };
}

export function latestCatalogueModified(): string {
  const dates = [
    ...getAllFilms().map((film) => film.date_modified),
    ...getAllSeries().map((series) => series.date_modified)
  ];
  return dates.sort().at(-1) ?? "2026-06-07T00:00:00+05:30";
}

// THE VERDICT STAGE subject (revamp 2026-06-15). Replaces the bento hero with one commanding
// title. Hard rule from the 10-Opus design team: the hero may ONLY feature a title that carries
// REAL key-art (never a monogram in the stage). Among art-bearing titles the best-FURNISHED
// verdict wins - a real BollyMeter score > a verdict word > a box-office figure - recency breaks
// ties. Every signal the stage renders is one the data actually carries (no fabrication).
export type HeroSubject = {
  kind: "film" | "series";
  slug: string;
  title: string;
  href: string;
  desk: DeskSlug;
  deskLabel: string;
  poster: PosterAsset;
  score: number | null; // BollyMeter 0-10 when grounded
  basis: string | null; // one-line grounded basis for the verdict
  verdictWord: string | null; // ladder rung (film) or OTT rung (series)
  boFigure: string | null; // pair-verified box-office figure (films only)
  statusLine: string; // plain-language status fallback
  fresh: boolean;
  recency: string;
};

const hasRealArt = (poster: PosterAsset): boolean =>
  Boolean(poster?.src) && !poster.src.includes("_fallback") && !poster.src.endsWith(".svg");

function filmBoFigure(film: Film): string | null {
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value;
  const net = film.box_office.totals.india_net_inr_cr?.value;
  if (ww) return `${formatCrore(ww)} WW`;
  if (net) return `${formatCrore(net)} India`;
  return null;
}

function rankedSubjects(now: number): HeroSubject[] {
  const maxHeroAgeMs = 120 * 86400000;
  const isCurrent = (iso: string): boolean => {
    const releasedAt = new Date(iso).getTime();
    const age = now - releasedAt;
    return Number.isFinite(releasedAt) && age >= -7 * 86400000 && age <= maxHeroAgeMs;
  };
  const recencyBoost = (iso: string): number => {
    const t = new Date(iso).getTime();
    if (!Number.isFinite(t)) return 0;
    const days = (now - t) / 86400000;
    return Math.max(0, 40 - Math.max(0, days) * 0.25); // ~40 when fresh, decays to 0 by ~160 days
  };

  const scored: Array<{ subj: HeroSubject; weight: number }> = [];

  for (const f of getAllFilms()) {
    if (!hasRealArt(f.poster)) continue;
    const item = filmToItem(f, now);
    if (!isCurrent(item.recency)) continue;
    const bo = filmBoFigure(f);
    const subj: HeroSubject = {
      kind: "film",
      slug: f.slug,
      title: item.title,
      href: item.href,
      desk: item.desk,
      deskLabel: item.deskLabel,
      poster: f.poster,
      score: f.bollymeter?.score ?? null,
      basis: f.bollymeter?.basis ?? null,
      verdictWord: f.verdict.ladder_rung,
      boFigure: bo,
      statusLine: item.meta,
      fresh: item.fresh,
      recency: item.recency
    };
    const weight =
      (subj.score ?? 0) * 15 +
      (subj.verdictWord ? 55 : 0) +
      (bo ? 40 : 0) +
      (subj.poster.variants ? 32 : 0) +
      recencyBoost(item.recency);
    scored.push({ subj, weight });
  }

  for (const s of getAllSeries()) {
    if (!hasRealArt(s.poster)) continue;
    const item = seriesToItem(s, now);
    if (!isCurrent(item.recency)) continue;
    const bm = latestSeason(s)?.bollymeter ?? null;
    const subj: HeroSubject = {
      kind: "series",
      slug: s.slug,
      title: item.title,
      href: item.href,
      desk: item.desk,
      deskLabel: item.deskLabel,
      poster: s.poster,
      score: bm?.score ?? null,
      basis: bm?.basis ?? null,
      verdictWord: item.seriesRung ?? null,
      boFigure: null,
      statusLine: item.meta,
      fresh: item.fresh,
      recency: item.recency
    };
    const weight =
      (subj.score ?? 0) * 15 +
      (subj.verdictWord ? 55 : 0) +
      (subj.poster.variants ? 32 : 0) +
      recencyBoost(item.recency);
    scored.push({ subj, weight });
  }

  scored.sort((a, b) => b.weight - a.weight || b.subj.recency.localeCompare(a.subj.recency));
  return scored.map((x) => x.subj);
}

// The single best title for a standalone stage.
export function heroPick(now: number = Date.now()): HeroSubject | null {
  return rankedSubjects(now)[0] ?? null;
}

function seriesPosterBySlug(slug: string): PosterAsset | null {
  const s = getAllSeries().find((x) => x.slug === slug);
  return s && hasRealArt(s.poster) ? s.poster : null;
}

function seriesLookupKey(title: string): string {
  return title
    .toLowerCase()
    .replace(/\s+season\s+\d+$/i, "")
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

// ONE OTT CALENDAR ROW for the calendar hero. Composed from the real upcoming OTT announcements
// (forward-looking) PLUS the recently-dropped catalogue titles (which carry posters + pages +
// scores) so the calendar is poster-rich and clickable, not 4 thin unlinkable rows.
export type OttCalItem = {
  date: string; // ISO yyyy-mm-dd
  title: string;
  platform: string;
  kind: "film" | "series";
  href: string | null; // null = announced but no page yet
  poster: PosterAsset | null;
  score: number | null; // BollyMeter for already-dropped titles
  upcoming: boolean; // true = future drop, false = now streaming
};

export function ottCalendarDeck(count = 12, now: number = Date.now()): OttCalItem[] {
  const todayIso = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date(now));
  const seen = new Set<string>();
  const coming: OttCalItem[] = [];
  const dropped: OttCalItem[] = [];
  const seriesByTitle = new Map(getAllSeries().map((series) => [seriesLookupKey(series.title.value), series]));

  // 1) genuine upcoming announcements from the OTT calendar (calendar slugs are series slugs)
  for (const e of getOttCalendar().entries) {
    if (e.release_date < todayIso) continue;
    const matchedSeries = e.type === "series" ? seriesByTitle.get(seriesLookupKey(e.title)) : undefined;
    const slug = e.slug ?? matchedSeries?.slug ?? null;
    const key = slug ? `series:${slug}` : `ann:${e.title}-${e.release_date}`;
    if (seen.has(key)) continue;
    seen.add(key);
    coming.push({
      date: e.release_date,
      title: e.title,
      platform: e.platform,
      kind: e.type,
      href: slug ? `/series/${slug}/` : null,
      poster: slug ? seriesPosterBySlug(slug) : null,
      score: null,
      upcoming: true
    });
  }

  // 2) recently dropped on OTT from the catalogue (rich + clickable)
  const recent = [
    ...getAllSeries().map((s) => seriesToItem(s, now)),
    ...getAllFilms()
      .filter((f) => f.status === "ott")
      .map((f) => filmToItem(f, now))
  ]
    .filter((i) => Boolean(i.poster.src) && !i.poster.src.includes("_fallback"))
    .sort((a, b) => b.recency.localeCompare(a.recency));

  for (const i of recent) {
    if (dropped.length >= count) break;
    const key = `${i.kind}:${i.slug}`;
    if (seen.has(key)) continue;
    seen.add(key);
    dropped.push({
      date: i.recency,
      title: i.title,
      platform: i.meta,
      kind: i.kind,
      href: i.href,
      poster: i.poster,
      score: i.score,
      upcoming: false
    });
  }

  coming.sort((a, b) => a.date.localeCompare(b.date)); // soonest drop first
  const droppedSlots = Math.ceil(count / 2);
  const comingSlots = count - droppedSlots;
  const selected = [...dropped.slice(0, droppedSlots), ...coming.slice(0, comingSlots)];
  if (selected.length >= count) return selected;

  return [
    ...selected,
    ...dropped.slice(droppedSlots),
    ...coming.slice(comingSlots)
  ].slice(0, count);
}
