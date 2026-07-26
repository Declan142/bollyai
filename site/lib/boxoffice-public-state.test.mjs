import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

import { projectBoxOfficePublicState } from "./boxoffice-public-state.mjs";
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

test("zero cleared sources render pending with zero ranked and JSON-LD items", () => {
  const registry = loadJson(registryPath);
  const activated = registry.candidates.filter((candidate) => (
    candidate.assessment === "cleared"
    && candidate.activation.approved === true
    && candidate.activation.configured === true
  ));
  assert.equal(activated.length, 0);

  const board = parseBoxOfficeBoard(loadJson(boardPath));
  const publicState = projectBoxOfficePublicState(board);

  assert.equal(publicState.status, "data_pending");
  assert.equal(publicState.dataPending, true);
  assert.deepEqual(publicState.boardRecords, []);
  assert.deepEqual(publicState.rankedRecords, []);
  assert.deepEqual(publicState.jsonLdRecords, []);
  assert.equal(publicState.showStructuredData, false);
});
