// Build-time index for the client-side "Ask BollyAI" answer engine (static export, no server).
// Reads the grounded review/verdict data layer and writes site/public/ask-index.json.
// HONESTY FENCE: only data that is already grounded ships here. A verdict rung or a
// bollymeter object is present in the source ONLY when it was groundable (the authoring
// fence sets bollymeter to null otherwise), so this script never manufactures a score or a
// verdict - it copies grounded fields verbatim and clips prose. No fabrication is possible
// downstream because the client can only answer from what this file contains.
import fs from "node:fs";
import path from "node:path";

const siteRoot = process.cwd();
const repoRoot = path.resolve(siteRoot, "..");
const dataDir = path.join(repoRoot, "data");
const publicDir = path.join(siteRoot, "public");
const outFile = path.join(publicDir, "ask-index.json");

const readJson = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const listJson = (dir) =>
  fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(".json")) : [];
const val = (v) => (v && typeof v === "object" && "value" in v ? v.value : v);
const clip = (s, n) => {
  if (!s) return null;
  const str = String(s).trim();
  if (str.length <= n) return str;
  return str.slice(0, n).replace(/\s+\S*$/, "").trim() + "…";
};
const hasRealPoster = (src) => Boolean(src) && !src.includes("_fallback") && !src.endsWith(".svg");

const endingSlugs = new Set(
  listJson(path.join(dataDir, "endings")).map((f) => f.replace(/\.json$/, ""))
);

const records = [];

// ---- Series: headline verdict = the latest season carrying grounded fields -------------
for (const f of listJson(path.join(dataDir, "series"))) {
  const d = readJson(path.join(dataDir, "series", f));
  const title = val(d.title);
  if (!title || !d.slug) continue;

  const seasons = Array.isArray(d.seasons) ? d.seasons : [];
  // walk seasons newest-first; take the first that has a grounded verdict or bollymeter
  let head = null;
  for (const s of [...seasons].sort((a, b) => (b.number ?? 0) - (a.number ?? 0))) {
    if (s.verdict || (s.bollymeter && typeof s.bollymeter.score === "number")) {
      head = s;
      break;
    }
  }
  const bm = head?.bollymeter && typeof head.bollymeter.score === "number" ? head.bollymeter : null;
  const verdict = head?.verdict || null;
  if (!verdict && !bm) continue; // nothing grounded to answer with - skip (never fabricate)

  records.push({
    t: title,
    u: `/series/${d.slug}/`,
    k: "Series",
    o: d.origin || null,
    l: val(d.original_language) || null,
    g: Array.isArray(d.genres) ? d.genres : [],
    p: val(d.platform) || null,
    v: verdict,
    sc: bm ? bm.score : null,
    b: bm ? clip(bm.basis, 240) : null,
    sn: clip(val(head?.review_body), 260),
    y: head?.year || null,
    e: endingSlugs.has(d.slug),
    pp: hasRealPoster(d.poster?.src),
    wtw: `/series/${d.slug}/where-to-watch/`
  });
}

// ---- Films: grounded verdict + bollymeter (logline as the grounded snippet) -------------
for (const f of listJson(path.join(dataDir, "films"))) {
  const d = readJson(path.join(dataDir, "films", f));
  const title = val(d.title);
  const desk = d.canonical_industry;
  if (!title || !desk || !d.slug) continue;
  const bm = d.bollymeter && typeof d.bollymeter.score === "number" ? d.bollymeter : null;
  const verdict = d.verdict || null;
  if (!verdict && !bm) continue;

  records.push({
    t: title,
    u: `/${desk}/reviews/${d.slug}/`,
    k: "Film",
    o: null,
    l: val(d.original_language) || null,
    g: Array.isArray(d.genres) ? d.genres : [],
    p: null,
    v: typeof verdict === "string" ? verdict : null,
    sc: bm ? bm.score : null,
    b: bm ? clip(bm.basis, 240) : null,
    sn: clip(val(d.logline), 240),
    y: d.release_date ? Number(String(d.release_date).slice(0, 4)) || null : null,
    e: false,
    pp: hasRealPoster(d.poster?.src),
    wtw: null
  });
}

fs.mkdirSync(publicDir, { recursive: true });
fs.writeFileSync(outFile, JSON.stringify(records));
const grounded = records.filter((r) => r.sc !== null).length;
console.log(`ask-index.json: ${records.length} records (${grounded} with a grounded BollyMeter score)`);
