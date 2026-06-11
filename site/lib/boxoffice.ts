import fs from "node:fs";
import path from "node:path";
import type { DeskSlug } from "./desks";
import type { MoneyRange } from "./data";

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
      range: { low: roundCrore(low), high: roundCrore(high) },
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

export function boxOfficeItemListJsonLd(board: BoxOfficeBoard) {
  const site = "https://bollyai.in";
  return {
    "@context": "https://schema.org",
    "@type": "ItemList",
    name: `India box office tracker: ${board.week.label}`,
    description: "Current-week Indian theatrical box-office tracking with conservative trade publishing rules.",
    itemListOrder: "https://schema.org/ItemListOrderAscending",
    numberOfItems: board.records.length,
    itemListElement: board.records.map((record, index) => ({
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
