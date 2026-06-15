import { getDesk, type DeskSlug } from "./desks";
import { formatCrore, getAllFilms, getOttCalendar, type Film, type VerdictRung } from "./data";
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

// FEATURED MOSAIC - the above-the-fold "many doors in". The lead tile (today's big verdict)
// is a Film and handled separately by the page; this builds the deduped, films+series-MIXED
// secondary set that fills the rest of the bento wall. High-signal (Big This Week) and the
// freshest landings (Just Dropped) are interleaved so the wall reads both "best" and "newest",
// then any gap is back-filled from the remaining pool. Real ordering only, never a fake metric.
export function mosaicSecondary(excludeFilmSlug: string, count = 8, now: number = Date.now()): MediaItem[] {
  const big = bigThisWeek(count + 24, now);
  const fresh = justDropped(count + 24, now);

  // Build one deduped, films+series-interleaved priority list (best AND newest, no lead).
  const ordered: MediaItem[] = [];
  const seen = new Set<string>([`film:${excludeFilmSlug}`]);
  const push = (item?: MediaItem) => {
    if (!item) return;
    const key = `${item.kind}:${item.slug}`;
    if (seen.has(key)) return;
    seen.add(key);
    ordered.push(item);
  };
  const longest = Math.max(big.length, fresh.length);
  for (let i = 0; i < longest; i++) {
    push(big[i]);
    push(fresh[i]);
  }

  // Artwork-first for the hero wall: a tile carrying a real poster pops far harder than a
  // placeholder, so surface poster-having titles first (priority order preserved), then
  // back-fill with placeholder titles. Still 100% real titles - only the order is biased.
  const hasPoster = (i: MediaItem) => Boolean(i.poster.src) && !i.poster.src.includes("_fallback");
  const withArt = ordered.filter(hasPoster);
  const withoutArt = ordered.filter((i) => !hasPoster(i));
  return [...withArt, ...withoutArt].slice(0, count);
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

// On-brand tilt: BollyAI is pan-INDIA cinema first. When an Indian title is as well-furnished as a
// global one, the Indian title should lead the stage. A boost (not a hard gate) - a clearly richer
// global verdict can still win, but a desi faisla is preferred for the flagship first impression.
const INDIAN_LANGS = new Set(["hi", "ta", "te", "ml", "kn", "bn", "mr", "pa"]);

function filmBoFigure(film: Film): string | null {
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value;
  const net = film.box_office.totals.india_net_inr_cr?.value;
  if (ww) return `${formatCrore(ww)} WW`;
  if (net) return `${formatCrore(net)} India`;
  return null;
}

function rankedSubjects(now: number): HeroSubject[] {
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
    const indian = f.canonical_industry !== "hollywood";
    const weight =
      (subj.score != null ? 100 : 0) + (subj.verdictWord ? 55 : 0) + (bo ? 40 : 0) + (indian ? 45 : 0) + recencyBoost(item.recency);
    scored.push({ subj, weight });
  }

  for (const s of getAllSeries()) {
    if (!hasRealArt(s.poster)) continue;
    const item = seriesToItem(s, now);
    const bm = peakSeason(s)?.bollymeter ?? latestSeason(s)?.bollymeter ?? null;
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
    const indian = INDIAN_LANGS.has((s.original_language?.value ?? "").toLowerCase());
    const weight = (subj.score != null ? 100 : 0) + (subj.verdictWord ? 55 : 0) + (indian ? 45 : 0) + recencyBoost(item.recency);
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

  // 1) genuine upcoming announcements from the OTT calendar (calendar slugs are series slugs)
  for (const e of getOttCalendar().entries) {
    if (e.release_date < todayIso) continue;
    const key = e.slug ? `series:${e.slug}` : `ann:${e.title}-${e.release_date}`;
    if (seen.has(key)) continue;
    seen.add(key);
    coming.push({
      date: e.release_date,
      title: e.title,
      platform: e.platform,
      kind: e.type,
      href: e.slug ? `/series/${e.slug}/` : null,
      poster: e.slug ? seriesPosterBySlug(e.slug) : null,
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
    if (coming.length + dropped.length >= count) break;
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
  // Artwork-first (mirrors mosaicSecondary): a poster-bearing card pops far harder than a
  // placeholder one-sheet and feeds the ambient hero backdrop, so surface poster-having
  // titles first. Date order is preserved within each group, and per-card upcoming/dropped
  // state is intact (it lives on the card, not the position).
  const all = [...coming, ...dropped];
  const hasPoster = (c: (typeof all)[number]) => {
    const src = c.poster?.src;
    return !!src && !src.includes("_fallback");
  };
  return [...all.filter(hasPoster), ...all.filter((c) => !hasPoster(c))].slice(0, count);
}

// The featured DECK for the rotating hero marquee - the top N furnished, art-bearing titles
// (deduped by slug). Multiple posters, each its own clickable verdict; click goes to the title.
export function heroDeck(count = 6, now: number = Date.now()): HeroSubject[] {
  const seen = new Set<string>();
  const deck: HeroSubject[] = [];
  for (const subj of rankedSubjects(now)) {
    const key = `${subj.kind}:${subj.slug}`;
    if (seen.has(key)) continue;
    seen.add(key);
    deck.push(subj);
    if (deck.length >= count) break;
  }
  return deck;
}
