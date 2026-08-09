export type BoxOfficeWeek = {
  start: string;
  end: string;
  label: string;
};

export type WeekGrossSource = {
  name: string;
  url: string;
  group: string;
  as_of: string;
  fetched_at: string;
  metric: "week_gross_usd";
  measurement: "exact_week";
  period: BoxOfficeWeek;
  territory: "Worldwide";
  currency: "USD";
  value: number;
};

export type WeekGrossUsd = {
  value: number | null;
  currency: "USD";
  measurement: "exact_week";
  period: BoxOfficeWeek;
  territory: "Worldwide";
  label: "trade estimate" | "lower figure" | "tracking";
  sources: WeekGrossSource[];
};

export type BoxOfficeRecord = {
  film: {
    title: string;
    type: "film" | "series";
    qid: string | null;
    slug: string;
    url: string;
  };
  language: string;
  industry: "hollywood" | "streaming";
  territory: "Worldwide";
  release_date: string;
  week: BoxOfficeWeek;
  week_gross_usd: WeekGrossUsd;
};

export type BoxOfficeBoard = {
  schema: "bollyai-boxoffice-week/v3";
  status: "ready" | "data_pending";
  generated_at: string;
  territory: "Worldwide";
  week: BoxOfficeWeek;
  records: BoxOfficeRecord[];
};

export class BoxOfficeSchemaError extends Error {
  readonly code: string;
}

export function parseBoxOfficeBoard(
  value: unknown,
  options?: {
    now?: Date;
    trustedSourceGroups?: ReadonlyMap<string, string>;
  },
): BoxOfficeBoard;

export function loadBoxOfficeBoard(options: {
  filePath: string;
  readText: (filePath: string) => string;
  now?: Date;
  trustedSourceGroups?: ReadonlyMap<string, string>;
}): BoxOfficeBoard;
