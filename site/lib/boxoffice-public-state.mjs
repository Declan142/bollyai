export function projectBoxOfficePublicState(board) {
  const dataPending = board.status === "data_pending";
  const boardRecords = dataPending ? [] : board.records;
  const rankedRecords = boardRecords.filter((record) => (
    Number.isSafeInteger(record.week_gross_usd.value)
    && record.week_gross_usd.value > 0
  ));
  return {
    status: dataPending ? "data_pending" : "ready",
    dataPending,
    boardRecords,
    rankedRecords,
    jsonLdRecords: rankedRecords,
    showStructuredData: rankedRecords.length > 0
  };
}
