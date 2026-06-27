/**
 * guard-offbrand-films.mjs  --  Prebuild guard: enforce WESTERN-ONLY films.
 *
 * BRAND LOCK (Aditya, 2026-06-26): bollyai = Western series + movies ONLY.
 * Fails the build (exit 1) if any film whose canonical_industry is NOT
 * "hollywood" is present in data/films/.
 *
 * Usage (wired in site/package.json prebuild):
 *   node scripts/guard-offbrand-films.mjs
 */

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = path.resolve(__dirname, "..");
const FILMS_DIR = path.join(REPO_ROOT, "data", "films");

const ALLOWED_INDUSTRIES = new Set(["hollywood"]);

function main() {
  if (!fs.existsSync(FILMS_DIR)) {
    console.log("[guard-films] OK: data/films/ does not exist, nothing to check.");
    process.exit(0);
  }

  const files = fs.readdirSync(FILMS_DIR).filter((f) => f.endsWith(".json"));
  const violations = [];

  for (const file of files) {
    const data = JSON.parse(fs.readFileSync(path.join(FILMS_DIR, file), "utf8"));
    const industry = data.canonical_industry;
    if (!ALLOWED_INDUSTRIES.has(industry)) {
      const title = typeof data.title === "object" ? data.title?.value : data.title;
      violations.push(`${file} (${industry}) - ${title}`);
    }
  }

  if (violations.length === 0) {
    console.log(`[guard-films] OK: all ${files.length} films in data/films/ are Western (hollywood).`);
    process.exit(0);
  }

  console.error(`[guard-films] BUILD FAIL: ${violations.length} non-Western films remain in data/films/:`);
  for (const v of violations.sort()) {
    console.error(`  - ${v}`);
  }
  console.error(`Archive them: git mv data/films/<qid>.json data/_archive/non-western-films/`);
  process.exit(1);
}

main();
