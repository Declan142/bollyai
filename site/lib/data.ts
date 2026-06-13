import fs from "node:fs";
import path from "node:path";
import type { DeskSlug } from "./desks";

export type Confidence = "verified" | "trade_estimate" | "editorial" | "unverified";

export type SourceValue<T> = {
  value: T;
  source: string;
  fetched_at: string;
  confidence: Confidence;
};

export type MoneyRange = {
  low: number;
  high: number;
};

export type DayRow = {
  date: string;
  day: number;
  net_inr_cr: SourceValue<MoneyRange | null>;
  sources: Array<{
    name: string;
    url: string;
    as_of: string;
  }>;
  label: string;
};

export type Film = {
  qid: SourceValue<string>;
  slug: string;
  canonical_industry: DeskSlug;
  title: SourceValue<string>;
  original_language: SourceValue<string>;
  release_date: SourceValue<string>;
  status: "upcoming" | "live" | "released" | "ott";
  date_modified: string;
  logline: string;
  poster: {
    src: string;
    alt: string;
    attribution: string;
  };
  backdrop?: {
    src: string;
    alt: string;
    attribution: string;
  };
  box_office: {
    day_rows: DayRow[];
    totals: {
      india_net_inr_cr: SourceValue<MoneyRange | null>;
      worldwide_gross_inr_cr: SourceValue<MoneyRange | null>;
      as_of: string;
    };
  };
  verdict: {
    ladder_rung: VerdictRung | null;
    tracking: boolean;
  };
  bollymeter: {
    score: number;
    basis: string;
  } | null;
  ott: {
    platform: SourceValue<string | null>;
    date: SourceValue<string | null>;
    source_url: string | null;
    source_type: OttSourceType | null;
  } | null;
  budget: null | {
    value: number;
    source: string;
    fetched_at: string;
    confidence: Confidence;
    first_party: boolean;
  };
  _quarantine: unknown[];
};

export const VERDICT_RUNGS = [
  "DISASTER",
  "FLOP",
  "BELOW AVERAGE",
  "AVERAGE",
  "SEMI-HIT",
  "HIT",
  "SUPER-HIT",
  "BLOCKBUSTER",
  "ALL-TIME BLOCKBUSTER"
] as const;

export type VerdictRung = (typeof VERDICT_RUNGS)[number];
export type OttSourceType = "press" | "official_social" | "trade";

export type SourceRef = {
  name: string;
  url: string;
  type?: OttSourceType;
};

export type SourceEnvelope<T> = {
  value: T;
  sources: SourceRef[];
  fetched_at?: string;
  confidence: Confidence;
};

export type OttVerdictLineBasis = {
  kind: "catalogue_page" | "calendar_facts" | string;
  source_url?: string | null;
  source_field?: string;
};

const filmsDir = path.resolve(process.cwd(), "..", "data", "films");
const ottCalendarPath = path.resolve(process.cwd(), "..", "data", "ott", "calendar.json");
const ottCalendarArchiveDir = path.resolve(process.cwd(), "..", "data", "ott", "calendar");

export const TARGET_OTT_PLATFORMS = ["Netflix", "Prime Video", "JioHotstar", "ZEE5", "SonyLIV", "aha"] as const;

export const FILM_POSTER_FALLBACK = "/img/films/_fallback.svg";

// Films seeded before the poster harvester runs carry poster: null. ~20 components read
// film.poster.src unguarded, so a null poster crashes static generation. Hand back a FULL
// fallback poster object so every film always has a renderable poster.
function resolveFilmPoster(film: Film): Film {
  if (film.poster?.src) {
    return film;
  }
  const title = typeof film.title === "object" && film.title !== null ? film.title.value : String(film.title ?? "");
  return { ...film, poster: { src: FILM_POSTER_FALLBACK, alt: `${title} poster`, attribution: "" } };
}

export function getAllFilms(): Film[] {
  if (!fs.existsSync(filmsDir)) {
    return [];
  }

  return fs
    .readdirSync(filmsDir)
    .filter((file) => file.endsWith(".json"))
    .sort()
    .map((file) => {
      const full = path.join(filmsDir, file);
      return resolveFilmPoster(JSON.parse(fs.readFileSync(full, "utf8")) as Film);
    })
    .sort((a, b) => filmRank(b) - filmRank(a) || b.date_modified.localeCompare(a.date_modified));
}

// Live runs outrank ended ones; within a tier, the bigger verified worldwide number leads.
// Films without a published pair sink to the back of the rail.
function filmRank(film: Film): number {
  const live = film.status === "live" ? 1_000_000 : 0;
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value?.high ?? 0;
  const net = film.box_office.totals.india_net_inr_cr?.value?.high ?? 0;
  return live + Math.max(ww, net);
}

export function getFilmsByDesk(desk: string): Film[] {
  return getAllFilms().filter((film) => film.canonical_industry === desk);
}

export function getFilm(desk: string, slug: string): Film | undefined {
  return getAllFilms().find((film) => film.canonical_industry === desk && film.slug === slug);
}

export function getLatestModified(): string {
  const dates = getAllFilms().map((film) => film.date_modified);
  dates.push("2026-06-07T00:00:00+05:30");
  return dates.sort().at(-1) ?? "2026-06-07T00:00:00+05:30";
}

export type OttCalendarEntry = {
  id: string;
  title: string;
  title_claim: SourceEnvelope<string>;
  qid?: string | null;
  slug?: string | null;
  url?: string | null;
  industry: DeskSlug;
  industry_claim: SourceEnvelope<DeskSlug>;
  platform: string;
  platform_claim: SourceEnvelope<string>;
  release_date: string;
  release_date_claim: SourceEnvelope<string>;
  type: "film" | "series";
  language: string;
  language_claim: SourceEnvelope<string>;
  status: "verified" | "expected";
  sources: SourceRef[];
  source_url: string;
  source_type: OttSourceType;
  verdict_line: string;
  verdict_line_basis: OttVerdictLineBasis;
  fetched_at: string;
  week?: string;
  section?: "this_week" | "coming" | string;
  verification?: string;
};

export type OttWeek = {
  iso_week: string;
  year: number;
  week: number;
  label: string;
  status: "current" | "coming" | string;
  start: string;
  end: string;
  archive_url: string;
  entry_count: number;
};

export type OttTracking = {
  platforms: string[];
  missing_platforms: string[];
  omitted_unverified?: Array<{ id: string; title: string }>;
};

export type OttCalendar = {
  schema: "ott-calendar/v1";
  generated_at: string;
  window: {
    start: string;
    end: string;
    weeks?: number;
    basis?: string;
  };
  tracking: OttTracking;
  weeks: OttWeek[];
  entries: OttCalendarEntry[];
};

export function getOttCalendar(): OttCalendar {
  if (!fs.existsSync(ottCalendarPath)) {
    return {
      schema: "ott-calendar/v1",
      generated_at: "2026-06-07T00:00:00+05:30",
      window: { start: "2026-06-07", end: "2026-07-05" },
      tracking: { platforms: [...TARGET_OTT_PLATFORMS], missing_platforms: [...TARGET_OTT_PLATFORMS] },
      weeks: [],
      entries: []
    };
  }

  type RawEntry = Omit<
    OttCalendarEntry,
    | "id"
    | "title"
    | "title_claim"
    | "industry"
    | "industry_claim"
    | "platform"
    | "platform_claim"
    | "release_date"
    | "release_date_claim"
    | "language"
    | "language_claim"
    | "status"
    | "sources"
    | "verdict_line"
    | "verdict_line_basis"
  > & {
    id?: string;
    title: string | SourceEnvelope<string>;
    industry: DeskSlug | SourceEnvelope<DeskSlug>;
    platform: string | SourceEnvelope<string>;
    release_date: string | SourceValue<string> | SourceEnvelope<string>;
    language: string | SourceEnvelope<string>;
    sources?: SourceRef[];
    verdict_line?: string;
    verdict_line_basis?: OttVerdictLineBasis;
    status?: "verified" | "expected";
    _status?: "verified" | "unverified";
  };
  type RawCalendar = Partial<Omit<OttCalendar, "entries">> & { entries: RawEntry[] };
  const parsed = JSON.parse(fs.readFileSync(ottCalendarPath, "utf8")) as RawCalendar;
  const entries = parsed.entries.map(normalizeOttEntry);
  return {
    schema: "ott-calendar/v1",
    generated_at: parsed.generated_at ?? "2026-06-07T00:00:00+05:30",
    window: parsed.window ?? { start: "2026-06-07", end: "2026-07-05" },
    tracking: parsed.tracking ?? defaultOttTracking(entries),
    weeks: parsed.weeks ?? weeksFromWindow(parsed.window, entries),
    entries
  };
}

function normalizeOttEntry(entry: {
  id?: string;
  qid?: string | null;
  title: string | SourceEnvelope<string>;
  slug?: string | null;
  url?: string | null;
  industry: DeskSlug | SourceEnvelope<DeskSlug>;
  platform: string | SourceEnvelope<string>;
  release_date: string | SourceValue<string> | SourceEnvelope<string>;
  type: "film" | "series";
  language: string | SourceEnvelope<string>;
  status?: "verified" | "expected";
  _status?: "verified" | "unverified";
  sources?: SourceRef[];
  source_url?: string;
  source_type?: OttSourceType;
  verdict_line?: string;
  verdict_line_basis?: OttVerdictLineBasis;
  fetched_at?: string;
  week?: string;
  section?: "this_week" | "coming" | string;
  verification?: string;
}): OttCalendarEntry {
  const fallbackSources = normalizeSources(
    entry.sources ??
      (entry.source_url
        ? [{ name: sourceTypeLabel(entry.source_type ?? "trade"), url: entry.source_url, type: entry.source_type ?? "trade" }]
        : [])
  );
  const fetchedAt = entry.fetched_at ?? claimFetchedAt(entry.release_date) ?? "2026-06-07T00:00:00+05:30";
  const titleClaim = coerceClaim(entry.title, fallbackSources, fetchedAt);
  const platformClaim = coerceClaim(entry.platform, fallbackSources, fetchedAt);
  const releaseDateClaim = coerceClaim(entry.release_date, fallbackSources, fetchedAt);
  const industryClaim = coerceClaim(entry.industry, fallbackSources, fetchedAt);
  const languageClaim = coerceClaim(entry.language, fallbackSources, fetchedAt);
  const firstSource = fallbackSources[0] ?? { name: sourceTypeLabel(entry.source_type ?? "trade"), url: entry.source_url ?? "#", type: entry.source_type ?? "trade" };
  return {
    ...entry,
    id: entry.id ?? entry.qid ?? `${titleClaim.value}-${releaseDateClaim.value}`,
    title: titleClaim.value,
    title_claim: titleClaim,
    qid: entry.qid ?? null,
    industry: industryClaim.value,
    industry_claim: industryClaim,
    platform: platformClaim.value,
    platform_claim: platformClaim,
    release_date: releaseDateClaim.value,
    release_date_claim: releaseDateClaim,
    language: languageClaim.value,
    language_claim: languageClaim,
    status: entry.status ?? (entry._status === "verified" ? "verified" : "expected"),
    sources: fallbackSources,
    source_url: entry.source_url ?? firstSource.url,
    source_type: entry.source_type ?? firstSource.type ?? "trade",
    verdict_line:
      entry.verdict_line ??
      defaultOttVerdictLine({
        type: entry.type,
        language: languageClaim.value,
        platform: platformClaim.value,
        releaseDate: releaseDateClaim.value
      }),
    verdict_line_basis:
      entry.verdict_line_basis ?? {
        kind: "calendar_facts",
        source_url: null,
        source_field: "calendar.platform_date_language"
      },
    fetched_at: fetchedAt
  };
}

function normalizeSources(sources: SourceRef[]): SourceRef[] {
  const seen = new Set<string>();
  const output: SourceRef[] = [];
  for (const source of sources) {
    if (!source?.url || seen.has(source.url)) continue;
    seen.add(source.url);
    output.push({ name: source.name || sourceTypeLabel(source.type ?? "trade"), url: source.url, type: source.type });
  }
  return output;
}

function coerceClaim<T>(raw: T | SourceValue<T> | SourceEnvelope<T>, fallbackSources: SourceRef[], fetchedAt: string): SourceEnvelope<T> {
  if (raw && typeof raw === "object" && "value" in raw) {
    const maybeEnvelope = raw as SourceEnvelope<T>;
    const legacy = raw as SourceValue<T>;
    return {
      value: maybeEnvelope.value,
      sources: Array.isArray(maybeEnvelope.sources) ? normalizeSources(maybeEnvelope.sources) : fallbackSources,
      fetched_at: maybeEnvelope.fetched_at ?? legacy.fetched_at ?? fetchedAt,
      confidence: maybeEnvelope.confidence ?? legacy.confidence ?? "verified"
    };
  }
  return { value: raw as T, sources: fallbackSources, fetched_at: fetchedAt, confidence: "verified" };
}

function claimFetchedAt<T>(raw: T | SourceValue<T> | SourceEnvelope<T>): string | undefined {
  if (raw && typeof raw === "object" && "fetched_at" in raw) {
    return String(raw.fetched_at);
  }
  return undefined;
}

function sourceTypeLabel(type: OttSourceType): string {
  if (type === "official_social") return "Official social";
  if (type === "press") return "Official press";
  return "Trade source";
}

function defaultOttVerdictLine(entry: { type: "film" | "series"; language: string; platform: string; releaseDate: string }): string {
  const typeLabel = entry.type === "film" ? "film" : "series";
  return `${languageLabel(entry.language)}-language ${typeLabel} listed for ${entry.platform} on ${entry.releaseDate}.`;
}

function languageLabel(code: string): string {
  const labels: Record<string, string> = {
    bn: "Bengali",
    en: "English",
    hi: "Hindi",
    ml: "Malayalam",
    ta: "Tamil",
    te: "Telugu"
  };
  return labels[code.toLowerCase()] ?? code.toUpperCase();
}

function defaultOttTracking(entries: OttCalendarEntry[]): OttTracking {
  const present = new Set(entries.map((entry) => platformSlug(entry.platform)));
  const missing = TARGET_OTT_PLATFORMS.filter((platform) => !present.has(platformSlug(platform)));
  return { platforms: [...TARGET_OTT_PLATFORMS], missing_platforms: missing };
}

function weeksFromWindow(window: OttCalendar["window"] | undefined, entries: OttCalendarEntry[]): OttWeek[] {
  if (!window?.start) return [];
  const start = new Date(window.start);
  const weeks = window.weeks ?? 2;
  return Array.from({ length: weeks }, (_, index) => {
    const weekStart = new Date(start);
    weekStart.setUTCDate(start.getUTCDate() + index * 7);
    const weekEnd = new Date(weekStart);
    weekEnd.setUTCDate(weekStart.getUTCDate() + 6);
    const iso = isoWeek(weekStart);
    const isoKey = `${iso.year}-W${String(iso.week).padStart(2, "0")}`;
    return {
      iso_week: isoKey,
      year: iso.year,
      week: iso.week,
      label: index === 0 ? "This week" : "Coming next week",
      status: index === 0 ? "current" : "coming",
      start: weekStart.toISOString().slice(0, 10),
      end: weekEnd.toISOString().slice(0, 10),
      archive_url: `/ott/calendar/${iso.year}/wk-${String(iso.week).padStart(2, "0")}/`,
      entry_count: entries.filter((entry) => entry.week === isoKey).length
    };
  });
}

function isoWeek(value: Date): { year: number; week: number } {
  const date = new Date(Date.UTC(value.getUTCFullYear(), value.getUTCMonth(), value.getUTCDate()));
  date.setUTCDate(date.getUTCDate() + 4 - (date.getUTCDay() || 7));
  const yearStart = new Date(Date.UTC(date.getUTCFullYear(), 0, 1));
  const week = Math.ceil(((date.getTime() - yearStart.getTime()) / 86400000 + 1) / 7);
  return { year: date.getUTCFullYear(), week };
}

export type OttCalendarWeekPage = {
  schema: "ott-calendar-week/v1";
  generated_at: string;
  week: OttWeek;
  tracking: OttTracking;
  entries: OttCalendarEntry[];
};

export function getOttCalendarWeek(yearParam: string, weekParam: string): OttCalendarWeekPage | undefined {
  const weekNumber = parseWeekParam(weekParam);
  if (!weekNumber) return undefined;
  const isoKey = `${yearParam}-W${String(weekNumber).padStart(2, "0")}`;
  const archivePath = path.join(ottCalendarArchiveDir, `${isoKey}.json`);
  if (fs.existsSync(archivePath)) {
    const parsed = JSON.parse(fs.readFileSync(archivePath, "utf8")) as {
      schema: "ott-calendar-week/v1";
      generated_at: string;
      week: OttWeek;
      entries: Array<Parameters<typeof normalizeOttEntry>[0]>;
    };
    const entries = parsed.entries.map(normalizeOttEntry);
    return {
      schema: "ott-calendar-week/v1",
      generated_at: parsed.generated_at,
      week: parsed.week,
      tracking: defaultOttTracking(entries),
      entries
    };
  }
  const calendar = getOttCalendar();
  const week = calendar.weeks.find((item) => item.iso_week === isoKey);
  if (!week) return undefined;
  return {
    schema: "ott-calendar-week/v1",
    generated_at: calendar.generated_at,
    week,
    tracking: calendar.tracking,
    entries: calendar.entries.filter((entry) => entry.week === isoKey)
  };
}

export function getOttCalendarArchiveParams(): Array<{ year: string; week: string }> {
  const params = new Map<string, { year: string; week: string }>();
  for (const week of getOttCalendar().weeks) {
    params.set(week.iso_week, { year: String(week.year), week: `wk-${String(week.week).padStart(2, "0")}` });
  }
  if (fs.existsSync(ottCalendarArchiveDir)) {
    for (const file of fs.readdirSync(ottCalendarArchiveDir)) {
      const match = file.match(/^(20\d{2})-W(\d{2})\.json$/);
      if (!match) continue;
      params.set(`${match[1]}-W${match[2]}`, { year: match[1], week: `wk-${match[2]}` });
    }
  }
  return Array.from(params.values()).sort((a, b) => `${b.year}-${b.week}`.localeCompare(`${a.year}-${a.week}`));
}

function parseWeekParam(value: string): number | null {
  const match = value.match(/^wk-(\d{1,2})$/);
  if (!match) return null;
  const week = Number(match[1]);
  return week >= 1 && week <= 53 ? week : null;
}

export function platformSlug(platform: string): string {
  return platform
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function getOttPlatforms(): string[] {
  const calendar = getOttCalendar();
  const platformMap = new Map<string, string>();
  for (const platform of calendar.tracking?.platforms ?? TARGET_OTT_PLATFORMS) {
    platformMap.set(platformSlug(platform), platform);
  }
  for (const entry of calendar.entries) {
    platformMap.set(platformSlug(entry.platform), entry.platform);
  }
  return Array.from(platformMap.values());
}

// The /ott/<slug>/ pages are generated from the CALENDAR's platform set, which differs from
// series platform values (a series on "tvN / Netflix" has no /ott/tvn-netflix/ page). Return
// the slug of the first platform token that actually has a static OTT page, else null - so
// callers can link to /ott/netflix/ for a "tvN / Netflix" series, and skip the link otherwise.
export function ottPageSlug(platform: string): string | null {
  const calendarSlugs = new Set(getOttPlatforms().map(platformSlug));
  const candidates = [platform, ...platform.split(/[/,&]/).map((s) => s.trim())];
  for (const c of candidates) {
    const slug = platformSlug(c);
    if (calendarSlugs.has(slug)) return slug;
  }
  return null;
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
    timeZone: "Asia/Kolkata"
  }).format(new Date(value));
}

export function formatShortDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    timeZone: "Asia/Kolkata"
  }).format(new Date(value));
}

export function formatCrore(range: MoneyRange | null): string {
  if (!range) {
    return "early estimates awaited";
  }
  if (range.low === range.high) {
    return `Rs ${range.low.toFixed(1)} cr`;
  }
  return `Rs ${range.low.toFixed(1)}-${range.high.toFixed(1)} cr`;
}

export function budgetDisplay(film: Film): string {
  if (!film.budget || film.budget.first_party !== true) {
    return "undisclosed";
  }
  return `Rs ${film.budget.value.toFixed(0)} cr`;
}
