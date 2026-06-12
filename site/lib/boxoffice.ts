import fs from "node:fs";
import path from "node:path";
import type { DeskSlug } from "./desks";
import type { Film, MoneyRange } from "./data";

export type BoxOfficeSource = {
  name: string;
  url: string;
  as_of?: string;
  group?: string;
  value?: number;
};

export type BoxOfficeFigure = {
  value: MoneyRange | null;
  sources: BoxOfficeSource[];
  label: string;
};

export type BoxOfficeWeek = {
  start: string;
  end: string;
  label: string;
};

export type BoxOfficeRecord = {
  film: {
    title: string;
    type: "film" | "series";
    qid: string | null;
    slug: string | null;
    url: string | null;
  };
  language: string;
  industry: DeskSlug;
  week: BoxOfficeWeek;
  territory: string;
  india_net_inr_cr: BoxOfficeFigure;
  worldwide_gross_inr_cr: BoxOfficeFigure;
  notes?: string;
};

export type BoxOfficeBoard = {
  schema: "bollyai-boxoffice-week/v1";
  DATA_PENDING: boolean;
  generated_at: string;
  week: BoxOfficeWeek;
  territory: string;
  records: BoxOfficeRecord[];
};

export type BoxOfficeClub = {
  slug: string;
  label: string;
  tier: number;
};

export type FigureDecision =
  | {
      published: true;
      range: MoneyRange;
      label: "trade estimate" | "lower figure";
      agreementPct: number;
      basisSources: string[];
      caveat: string | null;
    }
  | {
      published: false;
      range: null;
      label: "tracking";
      reason: string;
      caveat: string;
    };

const boxofficeDir = path.resolve(process.cwd(), "..", "data", "boxoffice");
const currentWeekPath = path.join(boxofficeDir, "current-week.json");

const SOUTH_FIRST: DeskSlug[] = ["tollywood", "kollywood", "mollywood", "sandalwood", "bollywood", "hollywood", "streaming"];
const CLUB_TIERS = [100, 200, 500, 1000] as const;

const SOURCE_GROUPS: Record<string, string> = {
  sacnilk: "sacnilk",
  tracktollywood: "tracktollywood",
  andhraboxoffice: "andhraboxoffice",
  boxofficeindia: "boxofficeindia",
  box_office_india: "boxofficeindia",
  mojo_india: "mojo_india",
  box_office_mojo: "mojo_india",
  bollywood_hungama: "studio_pr",
  bh: "studio_pr",
  taran_adarsh: "studio_pr",
  taran: "studio_pr"
};

const PR_LEANING = new Set(["bollywood_hungama", "bh", "taran_adarsh", "taran"]);

export function getCurrentBoxOfficeBoard(): BoxOfficeBoard {
  if (!fs.existsSync(currentWeekPath)) {
    return {
      schema: "bollyai-boxoffice-week/v1",
      DATA_PENDING: true,
      generated_at: "2026-06-12T00:00:00+05:30",
      week: { start: "2026-06-08", end: "2026-06-14", label: "Week of 8 June 2026" },
      territory: "India",
      records: []
    };
  }

  const parsed = JSON.parse(fs.readFileSync(currentWeekPath, "utf8")) as BoxOfficeBoard;
  return {
    ...parsed,
    records: [...parsed.records].sort(compareRecordsSouthFirst)
  };
}

export function compareRecordsSouthFirst(left: BoxOfficeRecord, right: BoxOfficeRecord): number {
  return industryRank(left.industry) - industryRank(right.industry) || left.film.title.localeCompare(right.film.title);
}

export function decideBoxOfficeFigure(figure: BoxOfficeFigure): FigureDecision {
  const readings = figure.sources.filter((source) => typeof source.value === "number" && Number.isFinite(source.value));
  const pairs: Array<{ pct: number; left: BoxOfficeSource; right: BoxOfficeSource }> = [];

  readings.forEach((left, index) => {
    readings.slice(index + 1).forEach((right) => {
      if (isIndependentPair(left, right)) {
        pairs.push({ pct: agreementPct(left.value as number, right.value as number), left, right });
      }
    });
  });

  pairs.sort((a, b) => a.pct - b.pct);
  const best = pairs[0];

  if (!best) {
    return {
      published: false,
      range: null,
      label: "tracking",
      reason: "single_source_or_no_valid_independent_pair",
      caveat: "Awaiting two independent same-metric sources."
    };
  }

  const low = Math.min(best.left.value as number, best.right.value as number);
  const high = Math.max(best.left.value as number, best.right.value as number);
  const basisSources = [best.left.name, best.right.name];

  if (best.pct <= 10) {
    return {
      published: true,
      range: { low: roundCrore(low), high: roundCrore(low) },
      label: "trade estimate",
      agreementPct: roundPct(best.pct),
      basisSources,
      caveat: null
    };
  }

  if (best.pct <= 25) {
    return {
      published: true,
      range: { low: roundCrore(low), high: roundCrore(low) },
      label: "lower figure",
      agreementPct: roundPct(best.pct),
      basisSources,
      caveat: `Sources vary by ${roundPct(best.pct).toFixed(1)} percent, so the lower figure is shown.`
    };
  }

  return {
    published: false,
    range: null,
    label: "tracking",
    reason: "independent_sources_disagree_over_25_percent",
    caveat: "Sources are too far apart for BollyAI to publish a number."
  };
}

export function uniqueFigureSources(record: BoxOfficeRecord): BoxOfficeSource[] {
  const seen = new Set<string>();
  const output: BoxOfficeSource[] = [];
  for (const source of [...record.india_net_inr_cr.sources, ...record.worldwide_gross_inr_cr.sources]) {
    const key = `${source.name}|${source.url}`;
    if (seen.has(key)) continue;
    seen.add(key);
    output.push(source);
  }
  return output;
}

export function getBoxOfficeClubs(): BoxOfficeClub[] {
  return CLUB_TIERS.map((tier) => ({
    slug: `${tier}-crore-club`,
    label: `${tier} Crore Club`,
    tier
  }));
}

export function getBoxOfficeClub(slug: string): BoxOfficeClub | undefined {
  return getBoxOfficeClubs().find((club) => club.slug === slug);
}

export function getClubRecords(tier: number): BoxOfficeRecord[] {
  return getCurrentBoxOfficeBoard()
    .records.filter((record) => {
      const indiaDecision = decideBoxOfficeFigure(record.india_net_inr_cr);
      const worldwideDecision = decideBoxOfficeFigure(record.worldwide_gross_inr_cr);
      const indiaLow = indiaDecision.published ? indiaDecision.range.low : 0;
      const worldwideLow = worldwideDecision.published ? worldwideDecision.range.low : 0;
      return Math.max(indiaLow, worldwideLow) >= tier;
    })
    .sort(compareRecordsSouthFirst);
}

export function getYearScoreboardRecords(industry: DeskSlug, year: string): BoxOfficeRecord[] {
  return getCurrentBoxOfficeBoard()
    .records.filter((record) => record.industry === industry && record.week.start.startsWith(year))
    .sort(compareRecordsSouthFirst);
}

export function getYearScoreboardParams(): Array<{ industry: DeskSlug; year: string }> {
  const seen = new Set<string>();
  const output: Array<{ industry: DeskSlug; year: string }> = [];
  for (const record of getCurrentBoxOfficeBoard().records) {
    const year = record.week.start.slice(0, 4);
    const key = `${record.industry}-${year}`;
    if (seen.has(key)) continue;
    seen.add(key);
    output.push({ industry: record.industry, year });
  }
  return output.sort((left, right) => industryRank(left.industry) - industryRank(right.industry) || right.year.localeCompare(left.year));
}

export function boxOfficeItemListJsonLd(board: BoxOfficeBoard) {
  return boxOfficeRecordsItemListJsonLd({
    name: `India box office tracker: ${board.week.label}`,
    description: "Current-week Indian theatrical box-office tracking with conservative trade publishing rules.",
    records: board.records
  });
}

export function boxOfficeRecordsItemListJsonLd({
  name,
  description,
  records
}: {
  name: string;
  description: string;
  records: BoxOfficeRecord[];
}) {
  const site = "https://bollyai.in";
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name,
    description,
    itemListOrder: "https://schema.org/ItemListOrderAscending",
    numberOfItems: records.length,
    itemListElement: records.map((record, index) => ({
      "@type": "ListItem",
      position: index + 1,
      item: {
        "@type": record.film.type === "series" ? "TVSeries" : "Movie",
        name: record.film.title,
        ...(record.film.url ? { url: `${site}${record.film.url}` } : {}),
        ...(record.film.qid ? { sameAs: `https://www.wikidata.org/wiki/${record.film.qid}` } : {})
      }
    }))
  };
}

export function boxOfficeDatasetJsonLd({
  name,
  description,
  url,
  dateModified,
  records
}: {
  name: string;
  description: string;
  url: string;
  dateModified: string;
  records: BoxOfficeRecord[];
}) {
  return {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name,
    description,
    url: `https://bollyai.in${url}`,
    dateModified,
    creator: {
      "@type": "Organization",
      name: "BollyAI",
      url: "https://bollyai.in"
    },
    measurementTechnique: "Two-source independent trade verification with conservative lower-bound publishing.",
    variableMeasured: ["India nett box office", "Worldwide gross box office"],
    spatialCoverage: "India",
    keywords: records.map((record) => record.film.title).join(", ")
  };
}

export function filmBoxOfficeDatasetJsonLd(film: Film) {
  return {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${film.title.value} box office tracker`,
    description: `${film.title.value} day-wise India nett box-office tracker with attributed trade sources.`,
    url: `https://bollyai.in/${film.canonical_industry}/box-office/${film.slug}/`,
    dateModified: film.date_modified,
    creator: {
      "@type": "Organization",
      name: "BollyAI",
      url: "https://bollyai.in"
    },
    about: {
      "@type": "Movie",
      name: film.title.value,
      sameAs: `https://www.wikidata.org/wiki/${film.qid.value}`
    },
    measurementTechnique: "Day-wise trade readings rendered through BollyAI box-office publish rules.",
    variableMeasured: "India nett box office"
  };
}

export function filmDayRowsItemListJsonLd(film: Film) {
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `${film.title.value} day-wise box office rows`,
    numberOfItems: film.box_office.day_rows.length,
    itemListElement: film.box_office.day_rows.map((row, index) => ({
      "@type": "ListItem",
      position: index + 1,
      item: {
        "@type": "Dataset",
        name: `${film.title.value} day ${row.day} box office`,
        dateModified: row.net_inr_cr.fetched_at,
        variableMeasured: "India nett box office"
      }
    }))
  };
}

export function isYearSlug(slug: string): boolean {
  return /^20\d{2}$/.test(slug);
}

function industryRank(industry: DeskSlug): number {
  const index = SOUTH_FIRST.indexOf(industry);
  return index === -1 ? SOUTH_FIRST.length : index;
}

function sourceKey(source: BoxOfficeSource): string {
  const raw = source.group || source.name;
  const key = raw.toLowerCase().replace(/[^a-z0-9]+/g, "_").replace(/^_|_$/g, "");
  if (key === "bollywoodhungama") return "bollywood_hungama";
  if (key === "box_office_india") return "boxofficeindia";
  if (key === "box_office_mojo_india") return "mojo_india";
  return key;
}

function sourceGroup(source: BoxOfficeSource): string {
  const key = sourceKey(source);
  return SOURCE_GROUPS[key] ?? key;
}

function isIndependentPair(left: BoxOfficeSource, right: BoxOfficeSource): boolean {
  const leftKey = sourceKey(left);
  const rightKey = sourceKey(right);
  if (leftKey === rightKey) return false;
  if (sourceGroup(left) === sourceGroup(right)) return false;
  if (PR_LEANING.has(leftKey) && PR_LEANING.has(rightKey)) return false;
  return true;
}

function agreementPct(left: number, right: number): number {
  const average = (left + right) / 2;
  if (average === 0) return 0;
  return (Math.abs(left - right) / average) * 100;
}

function roundCrore(value: number): number {
  return Math.round(value * 100) / 100;
}

function roundPct(value: number): number {
  return Math.round(value * 10) / 10;
}
