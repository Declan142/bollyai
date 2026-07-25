import fs from "node:fs";
import path from "node:path";
import {
  loadBoxOfficeBoard
} from "./boxoffice-schema.mjs";
import type {
  BoxOfficeBoard,
  BoxOfficeRecord,
  BoxOfficeWeek,
  WeekGrossSource
} from "./boxoffice-schema.mjs";
import type { Film } from "./data";
import { DESK_SLUGS, type DeskSlug } from "./desks";

export type {
  BoxOfficeBoard,
  BoxOfficeRecord,
  BoxOfficeWeek,
  WeekGrossSource,
  WeekGrossUsd
} from "./boxoffice-schema.mjs";

const boxofficeDir = path.resolve(process.cwd(), "..", "data", "boxoffice");
const currentWeekPath = path.join(boxofficeDir, "current-week.json");
const WESTERN_DESK_ORDER: DeskSlug[] = ["hollywood", "streaming"];

export function getCurrentBoxOfficeBoard(): BoxOfficeBoard {
  const board = loadBoxOfficeBoard({
    filePath: currentWeekPath,
    readText: (filePath) => fs.readFileSync(filePath, "utf8")
  });
  return {
    ...board,
    records: board.records
      .filter((record) => (
        (DESK_SLUGS as readonly string[]).includes(record.industry)
      ))
      .sort(compareRecordsWesternFirst)
  };
}

export function compareRecordsWesternFirst(
  left: BoxOfficeRecord,
  right: BoxOfficeRecord
): number {
  const leftGross = getPublishedWeekGrossUsd(left) ?? -1;
  const rightGross = getPublishedWeekGrossUsd(right) ?? -1;
  return (
    rightGross - leftGross
    || industryRank(left.industry) - industryRank(right.industry)
    || left.film.title.localeCompare(right.film.title)
  );
}

export function getPublishedWeekGrossUsd(
  record: BoxOfficeRecord
): number | null {
  return record.week_gross_usd.value;
}

export function uniqueWeekGrossSources(
  record: BoxOfficeRecord
): WeekGrossSource[] {
  return record.week_gross_usd.sources;
}

export function boxOfficeItemListJsonLd(board: BoxOfficeBoard) {
  return boxOfficeRecordsItemListJsonLd({
    name: `Worldwide weekly box office: ${board.week.label}`,
    description:
      "Latest verified closed-week worldwide theatrical gross, published only after exact-period source consensus.",
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
    itemListOrder: "https://schema.org/ItemListOrderDescending",
    numberOfItems: records.length,
    itemListElement: records.map((record, index) => ({
      "@type": "ListItem",
      position: index + 1,
      item: {
        "@type": record.film.type === "series" ? "TVSeries" : "Movie",
        name: record.film.title,
        url: `${site}${record.film.url}`,
        ...(record.film.qid
          ? { sameAs: `https://www.wikidata.org/wiki/${record.film.qid}` }
          : {})
      }
    }))
  };
}

export function boxOfficeDatasetJsonLd({
  name,
  description,
  url,
  dateModified,
  period,
  records
}: {
  name: string;
  description: string;
  url: string;
  dateModified: string;
  period: BoxOfficeWeek;
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
    license: "https://bollyai.in/about",
    measurementTechnique:
      "Exact closed-week gross consensus across at least two independent source groups. The lower reading is published only when the full source spread is within 25 percent.",
    variableMeasured: ["Exact-week worldwide theatrical gross (USD)"],
    temporalCoverage: `${period.start}/${period.end}`,
    spatialCoverage: "Worldwide",
    keywords: records.map((record) => record.film.title).join(", ")
  };
}

export function filmBoxOfficeDatasetJsonLd(film: Film) {
  return {
    "@context": "https://schema.org",
    "@type": "Dataset",
    name: `${film.title.value} box office tracker`,
    description:
      `${film.title.value} day-wise India nett box-office tracker with attributed trade sources.`,
    url: `https://bollyai.in/${film.canonical_industry}/box-office/${film.slug}/`,
    dateModified: film.date_modified,
    creator: {
      "@type": "Organization",
      name: "BollyAI",
      url: "https://bollyai.in"
    },
    license: "https://bollyai.in/about",
    about: {
      "@type": "Movie",
      name: film.title.value,
      sameAs: `https://www.wikidata.org/wiki/${film.qid.value}`
    },
    measurementTechnique:
      "Day-wise trade readings rendered through BollyAI box-office publish rules.",
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
        license: "https://bollyai.in/about",
        variableMeasured: "India nett box office"
      }
    }))
  };
}

function industryRank(industry: DeskSlug): number {
  const index = WESTERN_DESK_ORDER.indexOf(industry);
  return index === -1 ? WESTERN_DESK_ORDER.length : index;
}
