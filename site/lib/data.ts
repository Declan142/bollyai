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
  tmdb_id: SourceValue<number>;
  wikidata_qid: SourceValue<string>;
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
    ladder_rung: VerdictRung;
    tracking: boolean;
  };
  bollymeter: {
    score: number;
    basis: string;
  };
  ott: {
    platform: SourceValue<string | null>;
    date: SourceValue<string | null>;
    link_via: "tmdb-watch-providers";
    country_link: string;
  };
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
    .sort((a, b) => b.date_modified.localeCompare(a.date_modified));
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
  tmdb_id: number;
  industry: DeskSlug;
  platform: string;
  release_date: string;
  type: "film" | "series";
  language: string;
  status: "verified" | "expected";
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
