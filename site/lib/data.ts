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

const filmsDir = path.resolve(process.cwd(), "..", "data", "films");
const ottCalendarPath = path.resolve(process.cwd(), "..", "data", "ott", "calendar.json");

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
      return JSON.parse(fs.readFileSync(full, "utf8")) as Film;
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
  title: string;
  qid: string;
  slug?: string;
  industry: DeskSlug;
  platform: string;
  release_date: string;
  type: "film" | "series";
  language: string;
  status: "verified" | "expected";
  source_url: string;
  source_type: OttSourceType;
  fetched_at: string;
};

export type OttCalendar = {
  schema: "ott-calendar/v1";
  generated_at: string;
  window: {
    start: string;
    end: string;
  };
  entries: OttCalendarEntry[];
};

export function getOttCalendar(): OttCalendar {
  if (!fs.existsSync(ottCalendarPath)) {
    return {
      schema: "ott-calendar/v1",
      generated_at: "2026-06-07T00:00:00+05:30",
      window: { start: "2026-06-07", end: "2026-07-05" },
      entries: []
    };
  }

  type RawEntry = Omit<OttCalendarEntry, "release_date" | "status"> & {
    release_date: string | SourceValue<string>;
    status?: "verified" | "expected";
    _status?: "verified" | "unverified";
  };
  type RawCalendar = Omit<OttCalendar, "entries"> & { entries: RawEntry[] };
  const parsed = JSON.parse(fs.readFileSync(ottCalendarPath, "utf8")) as RawCalendar;
  return {
    ...parsed,
    entries: parsed.entries.map((entry) => ({
      ...entry,
      release_date:
        typeof entry.release_date === "object" && entry.release_date !== null
          ? entry.release_date.value
          : entry.release_date,
      status: entry.status ?? (entry._status === "verified" ? "verified" : "expected")
    }))
  };
}

export function platformSlug(platform: string): string {
  return platform
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}

export function getOttPlatforms(): string[] {
  return Array.from(new Set(getOttCalendar().entries.map((entry) => entry.platform))).sort();
}

export function formatDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "long",
    year: "numeric",
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
