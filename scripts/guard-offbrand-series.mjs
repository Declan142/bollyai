/**
 * guard-offbrand-series.mjs  --  Prebuild guard for off-brand Indian series.
 *
 * Fails the build (exit 1) if any Indian-language series whose slug is NOT in
 * the protect-list JSON is still present in data/series/.
 *
 * Usage (add to package.json prebuild):
 *   "prebuild": "node scripts/guard-offbrand-series.mjs --protect-list .cull-protect-list.json"
 *
 * Or run standalone:
 *   node scripts/guard-offbrand-series.mjs --protect-list .cull-protect-list.json
 *
 * Protect-list format:  { "protect": ["slug-a", "slug-b", ...] }
 * If the file does not exist the guard exits 0 (not yet wired) with a warning.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const SERIES_DIR = path.join(REPO_ROOT, "data", "series");

const INDIAN_LANGS = new Set(["hi", "ur", "ta", "te", "ml", "kn", "bn", "mr", "pa", "gu"]);
const INDIAN_DESKS = new Set(["bollywood", "tollywood", "kollywood", "mollywood", "sandalwood"]);

function parseArgs() {
  const args = process.argv.slice(2);
  const idx = args.indexOf("--protect-list");
  if (idx === -1 || !args[idx + 1]) {
    console.error("Usage: node scripts/guard-offbrand-series.mjs --protect-list <path>");
    process.exit(1);
  }
  return { protectListPath: args[idx + 1] };
}

function loadProtectList(filePath) {
  const abs = path.resolve(REPO_ROOT, filePath);
  if (!fs.existsSync(abs)) {
    console.warn(`[guard-offbrand] WARN: protect-list not found at ${abs} -- guard is inactive (exit 0).`);
    process.exit(0);
  }
  const raw = JSON.parse(fs.readFileSync(abs, "utf8"));
  if (Array.isArray(raw)) return new Set(raw);
  if (raw && Array.isArray(raw.protect)) return new Set(raw.protect);
  throw new Error(`Unrecognized protect-list format in ${abs}. Expected {"protect": [...]} or a plain array.`);
}

function isIndianSeries(data) {
  const lang =
    typeof data.original_language === "object" && data.original_language !== null
      ? data.original_language.value
      : data.original_language;
  if (INDIAN_LANGS.has(lang)) return true;
  if (INDIAN_DESKS.has(data.canonical_industry)) return true;
  return false;
}

function main() {
  const { protectListPath } = parseArgs();
  const protectSet = loadProtectList(protectListPath);

  const files = fs.readdirSync(SERIES_DIR).filter((f) => f.endsWith(".json"));
  const violations = [];

  for (const file of files) {
    const slug = file.replace(/\.json$/, "");
    if (protectSet.has(slug)) continue;
    const data = JSON.parse(fs.readFileSync(path.join(SERIES_DIR, file), "utf8"));
    if (isIndianSeries(data)) {
      violations.push(slug);
    }
  }

  if (violations.length === 0) {
    console.log(`[guard-offbrand] OK: no unprotected Indian-language series in data/series/.`);
    process.exit(0);
  }

  console.error(`[guard-offbrand] BUILD FAIL: ${violations.length} unprotected Indian-language series remain in data/series/:`);
  for (const slug of violations.sort()) {
    console.error(`  - ${slug}`);
  }
  console.error(`Add them to the protect-list or run: node scripts/batch/archive_offbrand_series.py --cull-list ... --apply`);
  process.exit(1);
}

main();
