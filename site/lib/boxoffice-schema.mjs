const BOARD_SCHEMA = "bollyai-boxoffice-week/v3";
const ALLOWED_INDUSTRIES = new Set(["hollywood", "streaming"]);
const ALLOWED_LANGUAGES = new Set([
  "bg", "ca", "cs", "cy", "da", "de", "el", "en", "es", "et", "eu",
  "fi", "fr", "ga", "gl", "hr", "hu", "is", "it", "lt", "lv", "nb",
  "nl", "no", "pl", "pt", "ro", "sk", "sl", "sr", "sv"
]);
const BOARD_KEYS = ["generated_at", "records", "schema", "status", "territory", "week"];
const RECORD_KEYS = [
  "film", "industry", "language", "release_date", "territory", "week",
  "week_gross_usd"
];
const FILM_KEYS = ["qid", "slug", "title", "type", "url"];
const FIGURE_KEYS = [
  "currency", "label", "measurement", "period", "sources", "territory", "value"
];
const SOURCE_KEYS = [
  "as_of", "currency", "fetched_at", "group", "measurement", "metric",
  "name", "period", "territory", "url", "value"
];
const WEEK_KEYS = ["end", "label", "start"];
const FORBIDDEN_FIELD_PARTS = [
  "budget", "salary", "lifetime", "cumulative", "opening_weekend",
  "week_to_date", "worldwide_gross_usd"
];
const TIMESTAMP_PATTERN =
  /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.\d{1,3})?(?:Z|[+-]\d{2}:\d{2})$/;
const MAX_FUTURE_SKEW_MS = 5 * 60 * 1000;

export class BoxOfficeSchemaError extends Error {
  constructor(code, message) {
    super(message);
    this.name = "BoxOfficeSchemaError";
    this.code = code;
  }
}

function fail(code, message) {
  throw new BoxOfficeSchemaError(code, message);
}

function isObject(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function exactKeys(value, expected, where) {
  if (!isObject(value)) fail("INVALID_OBJECT", `${where} must be an object`);
  const actual = Object.keys(value).sort();
  const wanted = [...expected].sort();
  if (actual.length !== wanted.length || actual.some((key, index) => key !== wanted[index])) {
    fail("INVALID_FIELDS", `${where} fields differ from the v3 contract`);
  }
}

function rejectForbiddenContent(value, where = "board") {
  if (typeof value === "string" && (value.includes("\u2013") || value.includes("\u2014"))) {
    fail("FORBIDDEN_DASH", `${where} contains a forbidden dash`);
  }
  if (Array.isArray(value)) {
    value.forEach((item, index) => rejectForbiddenContent(item, `${where}[${index}]`));
    return;
  }
  if (!isObject(value)) return;
  for (const [key, item] of Object.entries(value)) {
    const normalized = key.trim().toLowerCase().replaceAll("-", "_");
    if (FORBIDDEN_FIELD_PARTS.some((part) => normalized.includes(part))) {
      fail("FORBIDDEN_METRIC", `${where}.${key} is not an exact-week field`);
    }
    rejectForbiddenContent(item, `${where}.${key}`);
  }
}

function isoDate(value, where) {
  if (typeof value !== "string" || !/^(?!0000)\d{4}-\d{2}-\d{2}$/.test(value)) {
    fail("INVALID_DATE", `${where} must be an ISO date`);
  }
  const parsed = new Date(`${value}T00:00:00Z`);
  if (Number.isNaN(parsed.valueOf()) || parsed.toISOString().slice(0, 10) !== value) {
    fail("INVALID_DATE", `${where} must be an ISO date`);
  }
  return parsed;
}

function isoTimestamp(value, where) {
  const match = typeof value === "string"
    ? TIMESTAMP_PATTERN.exec(value)
    : null;
  if (!match) {
    fail("INVALID_TIMESTAMP", `${where} must be an ISO timestamp with timezone`);
  }
  try {
    isoDate(match[1], `${where}.date`);
  } catch (error) {
    if (error instanceof BoxOfficeSchemaError) {
      fail("INVALID_TIMESTAMP", `${where} must be an ISO timestamp with timezone`);
    }
    throw error;
  }
  if (
    Number(match[2]) > 23
    || Number(match[3]) > 59
    || Number(match[4]) > 59
    || Number.isNaN(Date.parse(value))
  ) {
    fail("INVALID_TIMESTAMP", `${where} must be an ISO timestamp with timezone`);
  }
  return new Date(value);
}

function positiveNumber(value, where) {
  if (!Number.isSafeInteger(value) || value <= 0) {
    fail("INVALID_NUMBER", `${where} must be a positive safe integer`);
  }
  return value;
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

function validateWeek(value, where) {
  exactKeys(value, WEEK_KEYS, where);
  const start = isoDate(value.start, `${where}.start`);
  const end = isoDate(value.end, `${where}.end`);
  const durationDays = (end.valueOf() - start.valueOf()) / 86_400_000;
  if (
    durationDays !== 6
    || start.getUTCDay() !== 1
    || end.getUTCDay() !== 0
  ) {
    fail("INVALID_WEEK", `${where} must be one Monday-to-Sunday week`);
  }
  if (value.label !== weekLabel(start, end)) {
    fail("INVALID_WEEK", `${where}.label must match the exact period`);
  }
  return value;
}

function sameWeek(left, right) {
  return (
    left.start === right.start
    && left.end === right.end
    && left.label === right.label
  );
}

function validateFilm(value, where) {
  exactKeys(value, FILM_KEYS, where);
  if (typeof value.title !== "string" || value.title.trim() === "") {
    fail("INVALID_FILM", `${where}.title must be non-empty`);
  }
  if (value.type !== "film" && value.type !== "series") {
    fail("INVALID_FILM", `${where}.type is unsupported`);
  }
  if (value.qid !== null && (typeof value.qid !== "string" || !/^Q[1-9]\d*$/.test(value.qid))) {
    fail("INVALID_FILM", `${where}.qid must be null or a verified-looking QID`);
  }
  if (typeof value.slug !== "string" || !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(value.slug)) {
    fail("INVALID_FILM", `${where}.slug is invalid`);
  }
  if (typeof value.url !== "string" || !value.url.startsWith("/") || !value.url.endsWith("/")) {
    fail("INVALID_FILM", `${where}.url must be a local absolute path`);
  }
}

function canonicalSourceUrl(value, where) {
  if (
    typeof value !== "string"
    || value !== value.trim()
    || /\s/.test(value)
  ) {
    fail("INVALID_SOURCE", `${where} must be public HTTPS`);
  }
  let sourceUrl;
  try {
    sourceUrl = new URL(value);
  } catch {
    fail("INVALID_SOURCE", `${where} must be public HTTPS`);
  }
  const hostname = sourceUrl.hostname
    .toLocaleLowerCase("en-US")
    .replace(/\.$/, "");
  if (
    sourceUrl.protocol !== "https:"
    || !hostname
    || !hostname.includes(".")
    || sourceUrl.username
    || sourceUrl.password
    || sourceUrl.hash
    || hostname === "localhost"
    || hostname.endsWith(".localhost")
    || hostname.endsWith(".local")
    || hostname.endsWith(".internal")
    || hostname.endsWith(".home.arpa")
    || hostname.includes(":")
    || /^\d+(?:\.\d+){0,3}$/.test(hostname)
  ) {
    fail("INVALID_SOURCE", `${where} must use a public HTTPS source hostname`);
  }
  sourceUrl.hostname = hostname;
  sourceUrl.hash = "";
  if (sourceUrl.port === "443") sourceUrl.port = "";
  return { key: sourceUrl.href, hostname };
}

function validateSource(
  value,
  week,
  territory,
  generatedAt,
  trustedSourceGroups,
  where
) {
  exactKeys(value, SOURCE_KEYS, where);
  if (typeof value.name !== "string" || value.name.trim() === "") {
    fail("INVALID_SOURCE", `${where}.name must be non-empty`);
  }
  if (
    typeof value.group !== "string"
    || !/^[a-z0-9]+(?:_[a-z0-9]+)*$/.test(value.group)
  ) {
    fail("INVALID_SOURCE", `${where}.group must be a stable lowercase key`);
  }
  const sourceUrl = canonicalSourceUrl(value.url, `${where}.url`);
  if (trustedSourceGroups.get(sourceUrl.hostname) !== value.group) {
    fail(
      "UNTRUSTED_SOURCE_GROUP",
      `${where}.group is not registered for its source hostname`
    );
  }
  if (value.metric !== "week_gross_usd" || value.measurement !== "exact_week") {
    fail("FORBIDDEN_METRIC", `${where} is not an exact-week gross reading`);
  }
  if (value.currency !== "USD" || value.territory !== territory) {
    fail("SOURCE_SCOPE_MISMATCH", `${where} currency or territory differs`);
  }
  const period = validateWeek(value.period, `${where}.period`);
  if (!sameWeek(period, week)) {
    fail("SOURCE_PERIOD_MISMATCH", `${where}.period differs from board week`);
  }
  const asOf = isoDate(value.as_of, `${where}.as_of`);
  const fetchedAt = isoTimestamp(value.fetched_at, `${where}.fetched_at`);
  const weekEnd = isoDate(week.end, "week.end");
  const weekClosedAt = new Date(weekEnd.valueOf() + 86_400_000);
  const fetchedDay = isoDate(fetchedAt.toISOString().slice(0, 10), `${where}.fetched_at`);
  if (
    asOf < weekEnd
    || asOf > fetchedDay
    || fetchedAt < weekClosedAt
    || fetchedAt > generatedAt
  ) {
    fail("INVALID_SOURCE_TIME", `${where} timestamps do not close the week`);
  }
  positiveNumber(value.value, `${where}.value`);
}

function consensus(sources) {
  if (sources.length < 2) return null;
  const groups = sources.map((source) => source.group);
  if (new Set(groups).size !== groups.length) {
    fail("DUPLICATE_SOURCE_GROUP", "one independent group may contribute once");
  }
  const values = sources.map((source) => source.value).sort((left, right) => left - right);
  const low = values[0];
  const high = values.at(-1);
  const difference = BigInt(high - low);
  const total = BigInt(high) + BigInt(low);
  if (20n * difference <= total) {
    return { value: low, label: "trade estimate" };
  }
  if (8n * difference <= total) {
    return { value: low, label: "lower figure" };
  }
  return null;
}

function validateRecord(value, board, generatedAt, trustedSourceGroups, where) {
  exactKeys(value, RECORD_KEYS, where);
  validateFilm(value.film, `${where}.film`);
  if (!ALLOWED_INDUSTRIES.has(value.industry) || !ALLOWED_LANGUAGES.has(value.language)) {
    fail("OFFBRAND_RECORD", `${where} is outside the Western brand`);
  }
  if (value.territory !== board.territory || !sameWeek(value.week, board.week)) {
    fail("RECORD_SCOPE_MISMATCH", `${where} period or territory differs`);
  }
  const releaseDate = isoDate(value.release_date, `${where}.release_date`);
  if (releaseDate > isoDate(board.week.end, "board.week.end")) {
    fail("INVALID_RELEASE_DATE", `${where}.release_date follows the closed week`);
  }
  const expectedUrl = `/${value.industry}/box-office/${value.film.slug}/`;
  if (value.film.url !== expectedUrl) {
    fail("INVALID_FILM_URL", `${where}.film.url differs from its canonical route`);
  }

  const figure = value.week_gross_usd;
  exactKeys(figure, FIGURE_KEYS, `${where}.week_gross_usd`);
  if (
    figure.currency !== "USD"
    || figure.measurement !== "exact_week"
    || figure.territory !== board.territory
    || !sameWeek(figure.period, board.week)
  ) {
    fail("FIGURE_SCOPE_MISMATCH", `${where}.week_gross_usd scope differs`);
  }
  if (!Array.isArray(figure.sources)) {
    fail("INVALID_SOURCES", `${where}.week_gross_usd.sources must be a list`);
  }
  figure.sources.forEach((source, index) => {
    validateSource(
      source,
      board.week,
      board.territory,
      generatedAt,
      trustedSourceGroups,
      `${where}.week_gross_usd.sources[${index}]`
    );
  });
  const sourceUrls = figure.sources.map(
    (source) => canonicalSourceUrl(source.url, `${where}.source.url`).key
  );
  if (new Set(sourceUrls).size !== sourceUrls.length) {
    fail("DUPLICATE_SOURCE", `${where} repeats a source URL`);
  }

  const decision = consensus(figure.sources);
  if (decision === null) {
    if (figure.value !== null || figure.label !== "tracking") {
      fail("DISHONEST_FIGURE", `${where} must remain tracking`);
    }
    return false;
  }
  positiveNumber(figure.value, `${where}.week_gross_usd.value`);
  if (figure.value !== decision.value || figure.label !== decision.label) {
    fail("DISHONEST_FIGURE", `${where} does not match source consensus`);
  }
  return true;
}

export function parseBoxOfficeBoard(
  value,
  { now = new Date(), trustedSourceGroups = new Map() } = {}
) {
  if (!isObject(value)) fail("INVALID_BOARD", "board must be an object");
  if (!(trustedSourceGroups instanceof Map)) {
    fail("INVALID_SOURCE_REGISTRY", "trustedSourceGroups must be a Map");
  }
  rejectForbiddenContent(value);
  exactKeys(value, BOARD_KEYS, "board");
  if (value.schema !== BOARD_SCHEMA) {
    fail("UNSUPPORTED_SCHEMA", `board.schema must be ${BOARD_SCHEMA}`);
  }
  if (value.status !== "ready" && value.status !== "data_pending") {
    fail("INVALID_STATUS", "board.status is invalid");
  }
  if (value.territory !== "Worldwide") {
    fail("INVALID_TERRITORY", "board.territory must be Worldwide");
  }
  validateWeek(value.week, "board.week");
  const generatedAt = isoTimestamp(value.generated_at, "board.generated_at");
  const validationClock = now instanceof Date ? new Date(now.valueOf()) : new Date(Number.NaN);
  if (Number.isNaN(validationClock.valueOf())) {
    fail("INVALID_CLOCK", "validation clock must be a valid Date");
  }
  const weekEnd = isoDate(value.week.end, "board.week.end");
  const weekClosedAt = new Date(weekEnd.valueOf() + 86_400_000);
  if (generatedAt < weekClosedAt) {
    fail("INVALID_TIMESTAMP", "board.generated_at does not follow the closed week");
  }
  if (generatedAt.valueOf() > validationClock.valueOf() + MAX_FUTURE_SKEW_MS) {
    fail("FUTURE_TIMESTAMP", "board.generated_at is ahead of the validation clock");
  }
  if (!Array.isArray(value.records)) {
    fail("INVALID_RECORDS", "board.records must be a list");
  }
  if (value.status === "data_pending" && value.records.length > 0) {
    fail("INVALID_PENDING_BOARD", "data_pending boards must not carry records");
  }

  const seenSlugs = new Set();
  const seenQids = new Set();
  let publishedCount = 0;
  value.records.forEach((record, index) => {
    if (
      validateRecord(
        record,
        value,
        generatedAt,
        trustedSourceGroups,
        `board.records[${index}]`
      )
    ) {
      publishedCount += 1;
    }
    const film = record.film;
    if (
      seenSlugs.has(film.slug)
      || (film.qid !== null && seenQids.has(film.qid))
    ) {
      fail("DUPLICATE_RECORD", `board.records[${index}] repeats a film`);
    }
    seenSlugs.add(film.slug);
    if (film.qid !== null) seenQids.add(film.qid);
  });
  if (value.status === "ready" && publishedCount === 0) {
    fail("EMPTY_READY_BOARD", "ready board needs a publishable exact-week figure");
  }
  return value;
}

export function loadBoxOfficeBoard({
  filePath,
  readText,
  now,
  trustedSourceGroups
}) {
  if (typeof filePath !== "string" || typeof readText !== "function") {
    fail("INVALID_LOADER", "filePath and injected readText are required");
  }
  const raw = readText(filePath);
  if (typeof raw !== "string") {
    fail("INVALID_LOADER", "readText must return UTF-8 text");
  }
  let parsed;
  try {
    parsed = JSON.parse(raw);
  } catch {
    fail("INVALID_JSON", "box-office board is not valid JSON");
  }
  return parseBoxOfficeBoard(parsed, { now, trustedSourceGroups });
}
