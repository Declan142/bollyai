/**
 * guard-offbrand-series.mjs  --  Prebuild guard: enforce WESTERN-ONLY series.
 *
 * BRAND LOCK (Aditya, 2026-06-26 "we are going full on western"): bollyai = Western
 * series + movies. Fails the build (exit 1) if any series whose original_language is
 * NOT in the Western allowlist (and whose slug is NOT in the protect-list) is present
 * in data/series/.
 *
 * Allowlist > denylist by design: the old denylist (Indian ISO codes) let Korean (ko),
 * Japanese (ja), and string-valued "Hindi" languages slip through. An allowlist catches
 * every non-Western language, present and future.
 *
 * Usage (wired in site/package.json prebuild):
 *   node scripts/guard-offbrand-series.mjs --protect-list .cull-protect-list.json
 *
 * Protect-list format:  { "protect": ["slug-a", ...] }  -- explicit non-Western overrides.
 * If the file does not exist the guard exits 0 (not yet wired) with a warning.
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const SERIES_DIR = path.join(REPO_ROOT, "data", "series");

// Western languages we KEEP. MUST stay in sync with scripts/batch/plan_western_cull.py.
const WESTERN_KEEP = new Set([
  "en", "English",                              // anglophone core
  "es", "de", "fr", "it",                       // major Western European
  "sv", "da", "no", "nb", "nn", "fi", "is",     // Nordic
  "pl", "cs", "sk", "hu", "ro", "el",           // Central/Eastern European + Greek
  "nl", "ca", "pt", "gl", "lb", "yi", "ga",     // Dutch / Iberian / misc European
]);

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
    console.warn(`[guard-western] WARN: protect-list not found at ${abs} -- guard is inactive (exit 0).`);
    process.exit(0);
  }
  const raw = JSON.parse(fs.readFileSync(abs, "utf8"));
  if (Array.isArray(raw)) return new Set(raw);
  if (raw && Array.isArray(raw.protect)) return new Set(raw.protect);
  throw new Error(`Unrecognized protect-list format in ${abs}. Expected {"protect": [...]} or a plain array.`);
}

function langOf(data) {
  const ol = data.original_language;
  return typeof ol === "object" && ol !== null ? ol.value : ol;
}

function isNonWestern(data) {
  const lang = langOf(data);
  return !WESTERN_KEEP.has(lang);
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
    if (isNonWestern(data)) {
      violations.push(`${slug} (${langOf(data)})`);
    }
  }

  if (violations.length === 0) {
    console.log(`[guard-western] OK: all series in data/series/ are Western (or protected).`);
    process.exit(0);
  }

  console.error(`[guard-western] BUILD FAIL: ${violations.length} non-Western series remain in data/series/:`);
  for (const v of violations.sort()) {
    console.error(`  - ${v}`);
  }
  console.error(`Archive them: python3 scripts/batch/western_cull_apply.py --cull-list <list> --apply`);
  console.error(`Or add the slug to the protect-list for an explicit override.`);
  process.exit(1);
}

main();
