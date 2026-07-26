import type {
  BoxOfficeBoard,
  BoxOfficeRecord
} from "./boxoffice-schema.mjs";

export interface BoxOfficePublicState {
  status: "ready" | "data_pending";
  dataPending: boolean;
  boardRecords: BoxOfficeRecord[];
  rankedRecords: BoxOfficeRecord[];
  jsonLdRecords: BoxOfficeRecord[];
  showStructuredData: boolean;
}

export function projectBoxOfficePublicState(
  board: BoxOfficeBoard
): BoxOfficePublicState;
