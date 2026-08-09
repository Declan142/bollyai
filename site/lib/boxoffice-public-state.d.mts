import type {
  BoxOfficeBoard,
  BoxOfficeRecord,
  BoxOfficeWeek
} from "./boxoffice-schema.mjs";

export interface BoxOfficePublicState {
  status: "ready" | "data_pending" | "no_current_data";
  dataPending: boolean;
  stale: boolean;
  noCurrentData: boolean;
  expectedWeek: BoxOfficeWeek;
  observedWeek: BoxOfficeWeek;
  boardRecords: BoxOfficeRecord[];
  rankedRecords: BoxOfficeRecord[];
  jsonLdRecords: BoxOfficeRecord[];
  showStructuredData: boolean;
}

export function projectBoxOfficePublicState(
  board: BoxOfficeBoard,
  options?: { now?: Date }
): BoxOfficePublicState;

export function latestClosedBoxOfficeWeek(now?: Date): BoxOfficeWeek;
