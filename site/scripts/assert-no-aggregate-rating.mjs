import fs from "node:fs";
import path from "node:path";

const outDir = path.join(process.cwd(), "out");
const needle = "Aggregate" + "Rating";
const hits = [];

function walk(dir) {
  for (const entry of fs.readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) {
      walk(full);
      continue;
    }
    if (!entry.name.endsWith(".html") && !entry.name.endsWith(".json") && !entry.name.endsWith(".txt")) {
      continue;
    }
    const body = fs.readFileSync(full, "utf8");
    if (body.includes(needle)) {
      hits.push(path.relative(outDir, full));
    }
  }
}

if (!fs.existsSync(outDir)) {
  console.error("site/out does not exist; run next build first.");
  process.exit(1);
}

walk(outDir);

if (hits.length > 0) {
  console.error(`Structured-data lint failed: forbidden rating aggregate found in ${hits.join(", ")}`);
  process.exit(1);
}
