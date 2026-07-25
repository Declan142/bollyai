import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  BoxOfficeSchemaError,
  loadBoxOfficeBoard,
  parseBoxOfficeBoard as parseRawBoxOfficeBoard
} from "./boxoffice-schema.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../..");
const readyPath = path.join(repoRoot, "tests", "fixtures", "boxoffice", "ready-v3.json");
const pendingPath = path.join(repoRoot, "data", "boxoffice", "current-week.json");

const loadJson = (filePath) => JSON.parse(fs.readFileSync(filePath, "utf8"));
const clone = (value) => JSON.parse(JSON.stringify(value));
const fixtureSourceGroups = new Map([
  ["example.com", "fixture_trade_a"],
  ["example.org", "fixture_trade_b"],
  ["example.net", "fixture_trade_c"]
]);
const parseBoxOfficeBoard = (value, options = {}) => parseRawBoxOfficeBoard(
  value,
  { ...options, trustedSourceGroups: fixtureSourceGroups }
);

function assertCode(code, action) {
  assert.throws(
    action,
    (error) => error instanceof BoxOfficeSchemaError && error.code === code
  );
}

test("shared ready fixture passes the strict v3 parser", () => {
  const board = parseBoxOfficeBoard(loadJson(readyPath));

  assert.equal(board.schema, "bollyai-boxoffice-week/v3");
  assert.equal(board.status, "ready");
  assert.equal(board.records[0].week_gross_usd.value, 100_000_000);
  assert.equal(board.records[0].week_gross_usd.label, "trade estimate");
});

test("canonical pending board passes and carries no rows", () => {
  const board = parseBoxOfficeBoard(loadJson(pendingPath));

  assert.equal(board.status, "data_pending");
  assert.deepEqual(board.records, []);
});

test("loader uses injected text IO and parses exactly once", () => {
  let calls = 0;
  const raw = fs.readFileSync(readyPath, "utf8");
  const board = loadBoxOfficeBoard({
    filePath: "/virtual/current-week.json",
    trustedSourceGroups: fixtureSourceGroups,
    readText(filePath) {
      calls += 1;
      assert.equal(filePath, "/virtual/current-week.json");
      return raw;
    }
  });

  assert.equal(calls, 1);
  assert.equal(board.status, "ready");
});

test("loader rejects invalid JSON without leaking source text", () => {
  assertCode("INVALID_JSON", () => loadBoxOfficeBoard({
    filePath: "/virtual/current-week.json",
    readText: () => "{\"secret\":"
  }));
});

test("v1, v2, legacy lifetime fields, and unexpected fields fail closed", () => {
  for (const schema of ["bollyai-boxoffice-week/v1", "bollyai-boxoffice-week/v2"]) {
    const board = loadJson(readyPath);
    board.schema = schema;
    assertCode("UNSUPPORTED_SCHEMA", () => parseBoxOfficeBoard(board));
  }

  const lifetime = loadJson(readyPath);
  lifetime.records[0].worldwide_gross_usd = lifetime.records[0].week_gross_usd;
  delete lifetime.records[0].week_gross_usd;
  assertCode("FORBIDDEN_METRIC", () => parseBoxOfficeBoard(lifetime));

  const unexpected = loadJson(readyPath);
  unexpected.records[0].notes = "not in v3";
  assertCode("INVALID_FIELDS", () => parseBoxOfficeBoard(unexpected));
});

test("source scope, provenance, and exact period are mandatory", () => {
  const cumulative = loadJson(readyPath);
  cumulative.records[0].week_gross_usd.sources[0].metric = "cumulative_gross_usd";
  assertCode("FORBIDDEN_METRIC", () => parseBoxOfficeBoard(cumulative));

  const stale = loadJson(readyPath);
  stale.records[0].week_gross_usd.sources[0].period = {
    start: "2026-07-06",
    end: "2026-07-12",
    label: "6 to 12 July 2026"
  };
  assertCode("SOURCE_PERIOD_MISMATCH", () => parseBoxOfficeBoard(stale));

  const duplicateGroup = loadJson(readyPath);
  duplicateGroup.records[0].week_gross_usd.sources[1].group = "fixture_trade_a";
  assertCode("UNTRUSTED_SOURCE_GROUP", () => parseBoxOfficeBoard(duplicateGroup));

  const duplicateUrl = loadJson(readyPath);
  duplicateUrl.records[0].week_gross_usd.sources[1].url =
    duplicateUrl.records[0].week_gross_usd.sources[0].url;
  duplicateUrl.records[0].week_gross_usd.sources[1].group = "fixture_trade_a";
  assertCode("DUPLICATE_SOURCE", () => parseBoxOfficeBoard(duplicateUrl));

  const insecureUrl = loadJson(readyPath);
  insecureUrl.records[0].week_gross_usd.sources[0].url = "http://example.com/reading";
  assertCode("INVALID_SOURCE", () => parseBoxOfficeBoard(insecureUrl));

  const credentialUrl = loadJson(readyPath);
  credentialUrl.records[0].week_gross_usd.sources[0].url =
    "https://user@example.com/reading";
  assertCode("INVALID_SOURCE", () => parseBoxOfficeBoard(credentialUrl));

  const whitespaceUrl = loadJson(readyPath);
  whitespaceUrl.records[0].week_gross_usd.sources[0].url =
    "https://example.com/reading\n";
  assertCode("INVALID_SOURCE", () => parseBoxOfficeBoard(whitespaceUrl));

  const futureFetch = loadJson(readyPath);
  futureFetch.records[0].week_gross_usd.sources[0].fetched_at =
    "2026-07-20T08:01:00Z";
  assertCode("INVALID_SOURCE_TIME", () => parseBoxOfficeBoard(futureFetch));

  const unclosedFetch = loadJson(readyPath);
  unclosedFetch.records[0].week_gross_usd.sources[0].as_of = "2026-07-19";
  unclosedFetch.records[0].week_gross_usd.sources[0].fetched_at =
    "2026-07-19T23:59:59Z";
  assertCode("INVALID_SOURCE_TIME", () => parseBoxOfficeBoard(unclosedFetch));
});

test("consensus value and framing are recomputed rather than trusted", () => {
  const dishonestLabel = loadJson(readyPath);
  dishonestLabel.records[0].week_gross_usd.label = "lower figure";
  assertCode("DISHONEST_FIGURE", () => parseBoxOfficeBoard(dishonestLabel));

  const dishonestValue = loadJson(readyPath);
  dishonestValue.records[0].week_gross_usd.value = 108_000_000;
  assertCode("DISHONEST_FIGURE", () => parseBoxOfficeBoard(dishonestValue));

  const lowerFigure = loadJson(readyPath);
  lowerFigure.records[0].week_gross_usd.sources[1].value = 120_000_000;
  lowerFigure.records[0].week_gross_usd.label = "lower figure";
  assert.equal(
    parseBoxOfficeBoard(lowerFigure).records[0].week_gross_usd.value,
    100_000_000
  );

  const exactTenPercent = loadJson(readyPath);
  exactTenPercent.records[0].week_gross_usd.sources[0].value = 19_000_000;
  exactTenPercent.records[0].week_gross_usd.sources[1].value = 21_000_000;
  exactTenPercent.records[0].week_gross_usd.value = 19_000_000;
  assert.equal(
    parseBoxOfficeBoard(exactTenPercent).records[0].week_gross_usd.label,
    "trade estimate"
  );

  const exactTwentyFivePercent = loadJson(readyPath);
  exactTwentyFivePercent.records[0].week_gross_usd.sources[0].value = 7_000_000;
  exactTwentyFivePercent.records[0].week_gross_usd.sources[1].value = 9_000_000;
  exactTwentyFivePercent.records[0].week_gross_usd.value = 7_000_000;
  exactTwentyFivePercent.records[0].week_gross_usd.label = "lower figure";
  assert.equal(
    parseBoxOfficeBoard(exactTwentyFivePercent).records[0].week_gross_usd.label,
    "lower figure"
  );
});

test("source values must be positive cross-runtime safe integers", () => {
  for (const invalidValue of [
    Number.MAX_SAFE_INTEGER + 1,
    9e307,
    100.5
  ]) {
    const board = loadJson(readyPath);
    board.records[0].week_gross_usd.sources[0].value = invalidValue;
    assertCode("INVALID_NUMBER", () => parseBoxOfficeBoard(board));
  }
});

test("a third divergent source cannot be hidden behind an agreeing pair", () => {
  const board = loadJson(readyPath);
  const third = clone(board.records[0].week_gross_usd.sources[1]);
  third.name = "Fixture Trade C";
  third.group = "fixture_trade_c";
  third.url = "https://example.net/fixture-alpha-trade-c";
  third.value = 180_000_000;
  board.records[0].week_gross_usd.sources.push(third);
  board.records[0].week_gross_usd.value = null;
  board.records[0].week_gross_usd.label = "tracking";

  assertCode("EMPTY_READY_BOARD", () => parseBoxOfficeBoard(board));
});

test("source independence is code-owned and URL identity is canonical", () => {
  const unregistered = loadJson(readyPath);
  assertCode(
    "UNTRUSTED_SOURCE_GROUP",
    () => parseRawBoxOfficeBoard(unregistered)
  );

  const spoofed = loadJson(readyPath);
  spoofed.records[0].week_gross_usd.sources[1].group = "fixture_trade_a";
  assertCode("UNTRUSTED_SOURCE_GROUP", () => parseBoxOfficeBoard(spoofed));

  const duplicate = loadJson(readyPath);
  duplicate.records[0].week_gross_usd.sources[1].url =
    "https://EXAMPLE.com:443/fixture-alpha-trade-a";
  duplicate.records[0].week_gross_usd.sources[1].group = "fixture_trade_a";
  assertCode("DUPLICATE_SOURCE", () => parseBoxOfficeBoard(duplicate));

  const fragmented = loadJson(readyPath);
  fragmented.records[0].week_gross_usd.sources[0].url += "#alternate";
  assertCode("INVALID_SOURCE", () => parseBoxOfficeBoard(fragmented));
});

test("literal and non-public source hosts fail closed", () => {
  for (const hostname of [
    "127.0.0.1",
    "169.254.1.1",
    "10.0.0.1",
    "[::1]",
    "127.1",
    "0177.0.0.1",
    "0x7f.0.0.1",
    "127.0.0.01"
  ]) {
    const board = loadJson(readyPath);
    board.records[0].week_gross_usd.sources[0].url =
      `https://${hostname}/reading`;
    const groups = new Map(fixtureSourceGroups);
    groups.set(hostname, "fixture_trade_a");
    assertCode(
      "INVALID_SOURCE",
      () => parseRawBoxOfficeBoard(board, { trustedSourceGroups: groups })
    );
  }
});

test("offbrand rows, duplicate identities, and forbidden dashes fail closed", () => {
  const offbrand = loadJson(readyPath);
  offbrand.records[0].language = "hi";
  assertCode("OFFBRAND_RECORD", () => parseBoxOfficeBoard(offbrand));

  const duplicate = loadJson(readyPath);
  duplicate.records.push(clone(duplicate.records[0]));
  assertCode("DUPLICATE_RECORD", () => parseBoxOfficeBoard(duplicate));

  const duplicateQid = loadJson(readyPath);
  duplicateQid.records[0].film.qid = "Q123456789";
  const sameQid = clone(duplicateQid.records[0]);
  sameQid.film.slug = "fixture-alpha-reissue";
  sameQid.film.url = "/hollywood/box-office/fixture-alpha-reissue/";
  duplicateQid.records.push(sameQid);
  assertCode("DUPLICATE_RECORD", () => parseBoxOfficeBoard(duplicateQid));

  const duplicateSlug = loadJson(readyPath);
  const sameSlug = clone(duplicateSlug.records[0]);
  sameSlug.film.qid = "Q987654321";
  duplicateSlug.records.push(sameSlug);
  assertCode("DUPLICATE_RECORD", () => parseBoxOfficeBoard(duplicateSlug));

  const forbiddenDash = loadJson(readyPath);
  forbiddenDash.records[0].film.title = "Fixture Alpha \u2014 Reissue";
  assertCode("FORBIDDEN_DASH", () => parseBoxOfficeBoard(forbiddenDash));

  const wrongRoute = loadJson(readyPath);
  wrongRoute.records[0].film.url = "/streaming/box-office/fixture-alpha/";
  assertCode("INVALID_FILM_URL", () => parseBoxOfficeBoard(wrongRoute));

  const futureRelease = loadJson(readyPath);
  futureRelease.records[0].release_date = "2026-07-20";
  assertCode("INVALID_RELEASE_DATE", () => parseBoxOfficeBoard(futureRelease));

  const falseLabel = loadJson(readyPath);
  falseLabel.week.label = "Current week";
  assertCode("INVALID_WEEK", () => parseBoxOfficeBoard(falseLabel));
});

test("board timestamps are compared after UTC normalization", () => {
  const board = loadJson(readyPath);
  board.generated_at = "2026-07-19T00:30:00+14:00";

  assertCode("INVALID_TIMESTAMP", () => parseBoxOfficeBoard(board));
});

test("board generation must follow the fully closed Sunday", () => {
  const board = loadJson(readyPath);
  board.generated_at = "2026-07-19T23:59:59Z";

  assertCode("INVALID_TIMESTAMP", () => parseBoxOfficeBoard(board));
});

test("board generation cannot be ahead of the validation clock", () => {
  const board = loadJson(readyPath);
  board.generated_at = "2099-07-20T08:00:00Z";

  assertCode(
    "FUTURE_TIMESTAMP",
    () => parseBoxOfficeBoard(
      board,
      { now: new Date("2026-07-26T00:00:00Z") }
    )
  );
});

test("calendar dates match the canonical Python date contract", () => {
  for (const releaseDate of ["20260710", "2026-W28-5", "0000-07-10"]) {
    const board = loadJson(readyPath);
    board.records[0].release_date = releaseDate;
    assertCode("INVALID_DATE", () => parseBoxOfficeBoard(board));
  }
});

test("noncanonical or impossible timestamps fail closed", () => {
  for (const generatedAt of [
    "2026-02-30T08:00:00Z",
    "2026-07-20 08:00:00Z",
    "July 20 2026 08:00:00Z",
    "2026-07-20T08:00:00.0001Z"
  ]) {
    const board = loadJson(readyPath);
    board.generated_at = generatedAt;
    assertCode("INVALID_TIMESTAMP", () => parseBoxOfficeBoard(board));
  }
});
