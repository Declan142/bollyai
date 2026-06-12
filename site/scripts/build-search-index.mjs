// Build-time search index for the client-side search page (static export, no server).
// Reads the data layer directly and writes site/public/search-index.json.
// Runs in prebuild AFTER sync-public so it is not clobbered by the public copy.
import fs from "node:fs";
import path from "node:path";

const siteRoot = process.cwd();
const repoRoot = path.resolve(siteRoot, "..");
const dataDir = path.join(repoRoot, "data");
const outFile = path.join(siteRoot, "public", "search-index.json");

const readJson = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const listJson = (dir) =>
  fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(".json")) : [];
const val = (v) => (v && typeof v === "object" && "value" in v ? v.value : v);
const clip = (s, n = 140) => (s ? String(s).slice(0, n).replace(/\s+\S*$/, "") : "");

const entries = [];

// Desks (static, from the canonical list)
const DESKS = [
  ["bollywood", "Bollywood"],
  ["kollywood", "Kollywood"],
  ["tollywood", "Tollywood"],
  ["mollywood", "Mollywood"],
  ["sandalwood", "Sandalwood"],
  ["hollywood", "Hollywood"],
  ["streaming", "Streaming"]
];
for (const [slug, label] of DESKS) {
  entries.push({ t: `${label} desk`, u: `/${slug}/`, k: "Desk", d: `${label} reviews, box office and verdicts` });
}

entries.push(
  {
    t: "Hit-Flop Verdict Calculator",
    u: "/tools/hit-flop-calculator/",
    k: "Tool",
    d: "Estimate an Indian box-office verdict band from budget, gross, GST and distributor-share inputs"
  },
  {
    t: "Box Office Comparator",
    u: "/tools/box-office-comparator/",
    k: "Tool",
    d: "Compare film box-office trajectories day by day using published India nett trade-estimate rows"
  }
);

// Films
for (const f of listJson(path.join(dataDir, "films"))) {
  const d = readJson(path.join(dataDir, "films", f));
  const title = val(d.title);
  const desk = d.canonical_industry;
  if (!title || !desk) continue;
  entries.push({ t: title, u: `/${desk}/reviews/${d.slug}/`, k: "Film", d: clip(val(d.logline)) });
}

// Series + their ending-explained pages
const endingSlugs = new Set(listJson(path.join(dataDir, "endings")).map((f) => f.replace(/\.json$/, "")));
for (const f of listJson(path.join(dataDir, "series"))) {
  const d = readJson(path.join(dataDir, "series", f));
  const title = val(d.title);
  if (!title) continue;
  entries.push({ t: title, u: `/series/${d.slug}/`, k: "Series", d: clip(val(d.logline)) });
  if (endingSlugs.has(d.slug)) {
    entries.push({ t: `${title}: Ending Explained`, u: `/series/${d.slug}/ending-explained/`, k: "Ending", d: clip(val(d.logline)) });
  }
}

// What-to-Watch lists
for (const f of listJson(path.join(dataDir, "recommendations"))) {
  const d = readJson(path.join(dataDir, "recommendations", f));
  if (!d.title || !d.slug) continue;
  entries.push({ t: d.title, u: `/watch/${d.slug}/`, k: "List", d: clip(d.intro) });
}

fs.mkdirSync(path.dirname(outFile), { recursive: true });
fs.writeFileSync(outFile, JSON.stringify(entries));
console.log(`search-index.json: ${entries.length} entries`);
