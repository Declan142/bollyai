const DAY_MS = 86_400_000;

function isoDate(value) {
  return value.toISOString().slice(0, 10);
}

function weekLabel(start, end) {
  const month = (value) => new Intl.DateTimeFormat(
    "en-US",
    { month: "long", timeZone: "UTC" }
  ).format(value);
  if (start.getUTCMonth() === end.getUTCMonth()) {
    return `${start.getUTCDate()} to ${end.getUTCDate()} ${month(end)} ${end.getUTCFullYear()}`;
  }
  return (
    `${start.getUTCDate()} ${month(start)} to `
    + `${end.getUTCDate()} ${month(end)} ${end.getUTCFullYear()}`
  );
}

export function latestClosedBoxOfficeWeek(now = new Date()) {
  if (!(now instanceof Date) || Number.isNaN(now.valueOf())) {
    throw new TypeError("box-office freshness clock must be a valid Date");
  }
  const reference = new Date(Date.UTC(
    now.getUTCFullYear(),
    now.getUTCMonth(),
    now.getUTCDate()
  ));
  const daysSinceMonday = (reference.getUTCDay() + 6) % 7;
  const currentMonday = new Date(reference.valueOf() - daysSinceMonday * DAY_MS);
  const start = new Date(currentMonday.valueOf() - 7 * DAY_MS);
  const end = new Date(start.valueOf() + 6 * DAY_MS);
  return {
    start: isoDate(start),
    end: isoDate(end),
    label: weekLabel(start, end)
  };
}

function sameWeek(left, right) {
  return (
    left.start === right.start
    && left.end === right.end
    && left.label === right.label
  );
}

export function projectBoxOfficePublicState(board, { now = new Date() } = {}) {
  const expectedWeek = latestClosedBoxOfficeWeek(now);
  const stale = !sameWeek(board.week, expectedWeek);
  const dataPending = !stale && board.status === "data_pending";
  const noCurrentData = stale || dataPending;
  const boardRecords = noCurrentData ? [] : board.records;
  const rankedRecords = boardRecords.filter((record) => (
    Number.isSafeInteger(record.week_gross_usd.value)
    && record.week_gross_usd.value > 0
  ));
  return {
    status: stale ? "no_current_data" : board.status,
    dataPending,
    stale,
    noCurrentData,
    expectedWeek,
    observedWeek: board.week,
    boardRecords,
    rankedRecords,
    jsonLdRecords: rankedRecords,
    showStructuredData: rankedRecords.length > 0
  };
}
