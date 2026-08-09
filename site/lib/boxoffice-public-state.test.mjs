import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import {
  latestClosedBoxOfficeWeek,
  projectBoxOfficePublicState
} from "./boxoffice-public-state.mjs";
import { parseBoxOfficeBoard } from "./boxoffice-schema.mjs";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "../..");
const boardPath = path.join(repoRoot, "data", "boxoffice", "current-week.json");
const registryPath = path.join(
  repoRoot,
  "data",
  "boxoffice",
  "source-candidates.json"
);

const loadJson = (filePath) => JSON.parse(fs.readFileSync(filePath, "utf8"));
const readyPath = path.join(repoRoot, "tests", "fixtures", "boxoffice", "ready-v3.json");
const fixtureSourceGroups = new Map([
  ["example.com", "fixture_trade_a"],
  ["example.org", "fixture_trade_b"],
  ["example.net", "fixture_trade_c"]
]);

test("zero cleared sources render pending with zero ranked and JSON-LD items", () => {
  const registry = loadJson(registryPath);
  const activated = registry.candidates.filter((candidate) => (
    candidate.assessment === "cleared"
    && candidate.activation.approved === true
    && candidate.activation.configured === true
  ));
  assert.equal(activated.length, 0);

  const board = parseBoxOfficeBoard(loadJson(boardPath));
  const publicState = projectBoxOfficePublicState(
    board,
    { now: new Date("2026-07-26T12:00:00Z") }
  );

  assert.equal(publicState.status, "data_pending");
  assert.equal(publicState.dataPending, true);
  assert.equal(publicState.stale, false);
  assert.equal(publicState.noCurrentData, true);
  assert.deepEqual(publicState.boardRecords, []);
  assert.deepEqual(publicState.rankedRecords, []);
  assert.deepEqual(publicState.jsonLdRecords, []);
  assert.equal(publicState.showStructuredData, false);
});

test("current ready board renders rows and structured data", () => {
  const board = parseBoxOfficeBoard(
    loadJson(readyPath),
    { trustedSourceGroups: fixtureSourceGroups }
  );
  const publicState = projectBoxOfficePublicState(
    board,
    { now: new Date("2026-07-26T12:00:00Z") }
  );

  assert.equal(publicState.status, "ready");
  assert.equal(publicState.stale, false);
  assert.equal(publicState.noCurrentData, false);
  assert.equal(publicState.boardRecords.length, 1);
  assert.equal(publicState.jsonLdRecords.length, 1);
  assert.equal(publicState.showStructuredData, true);
});

test("stale ready board is withheld from rows rankings and JSON-LD", () => {
  const board = parseBoxOfficeBoard(
    loadJson(readyPath),
    { trustedSourceGroups: fixtureSourceGroups }
  );
  const publicState = projectBoxOfficePublicState(
    board,
    { now: new Date("2026-08-09T12:00:00Z") }
  );

  assert.equal(publicState.status, "no_current_data");
  assert.equal(publicState.stale, true);
  assert.equal(publicState.dataPending, false);
  assert.equal(publicState.noCurrentData, true);
  assert.deepEqual(publicState.boardRecords, []);
  assert.deepEqual(publicState.rankedRecords, []);
  assert.deepEqual(publicState.jsonLdRecords, []);
  assert.equal(publicState.showStructuredData, false);
  assert.equal(publicState.observedWeek.end, "2026-07-19");
  assert.equal(publicState.expectedWeek.end, "2026-08-02");
});

test("old pending board is stale rather than a current pending claim", () => {
  const board = parseBoxOfficeBoard(loadJson(boardPath));
  const publicState = projectBoxOfficePublicState(
    board,
    { now: new Date("2026-08-09T12:00:00Z") }
  );

  assert.equal(publicState.status, "no_current_data");
  assert.equal(publicState.stale, true);
  assert.equal(publicState.dataPending, false);
  assert.equal(publicState.noCurrentData, true);
});

test("latest closed week advances at the Monday UTC boundary", () => {
  assert.deepEqual(
    latestClosedBoxOfficeWeek(new Date("2026-07-26T23:59:59Z")),
    {
      start: "2026-07-13",
      end: "2026-07-19",
      label: "13 to 19 July 2026"
    }
  );
  assert.deepEqual(
    latestClosedBoxOfficeWeek(new Date("2026-07-27T00:00:00Z")),
    {
      start: "2026-07-20",
      end: "2026-07-26",
      label: "20 to 26 July 2026"
    }
  );
});

test("invalid freshness clocks fail closed", () => {
  assert.throws(
    () => latestClosedBoxOfficeWeek(new Date("invalid")),
    /freshness clock must be a valid Date/
  );
});
