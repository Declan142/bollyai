// Full segmented sitemap system (replaces the flat Next sitemap.ts).
// 2026 best practice: a sitemap INDEX -> typed child sitemaps, so Google Search
// Console reports indexation PER content type, plus accurate per-URL and per-child
// <lastmod> (the one sitemap signal Google actually uses). Image sitemap folded in.
// Runs in prebuild AFTER sync-public so poster files are present for the on-disk check.
import fs from "node:fs";
import path from "node:path";

const siteRoot = process.cwd();
const repoRoot = path.resolve(siteRoot, "..");
const dataDir = path.join(repoRoot, "data");
const publicDir = path.join(siteRoot, "public");
const SITE = "https://bollyai.in";
const LAUNCH = "2026-06-08"; // real first-publish date for static/utility pages

const readJson = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const listJson = (dir) =>
  fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(".json")).map((f) => readJson(path.join(dir, f))) : [];
const val = (v) => (v && typeof v === "object" && "value" in v ? v.value : v);
const day = (iso) => (iso ? String(iso).slice(0, 10) : LAUNCH);
const maxDay = (arr) => arr.map(day).sort().at(-1) || LAUNCH;
const esc = (s) =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const platformSlug = (p) => p.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "");

// ---- load data ----
const films = listJson(path.join(dataDir, "films"));
const series = listJson(path.join(dataDir, "series"));
const endings = listJson(path.join(dataDir, "endings"));
const watch = listJson(path.join(dataDir, "recommendations"));
const calendar = fs.existsSync(path.join(dataDir, "ott", "calendar.json"))
  ? readJson(path.join(dataDir, "ott", "calendar.json"))
  : { generated_at: LAUNCH, entries: [] };

const DESKS = ["bollywood", "kollywood", "tollywood", "mollywood", "sandalwood", "hollywood", "streaming"];

// ---- build URL rows per child {loc, lastmod} ----
const urlXml = (rows) =>
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
  rows.map((r) => `<url><loc>${esc(r.loc)}</loc><lastmod>${r.lastmod}</lastmod></url>`).join("\n") +
  `\n</urlset>\n`;

// pages: statics + desk hubs + ott
const staticPaths = [
  "/",
  "/about/",
  "/privacy/",
  "/disclaimer/",
  "/contact/",
  "/takedown/",
  "/how-bollyai-works/",
  "/series/",
  "/watch/",
  "/tools/hit-flop-calculator/",
  "/tools/box-office-comparator/"
];
const pages = [];
for (const p of staticPaths) pages.push({ loc: `${SITE}${p}`, lastmod: LAUNCH });
for (const desk of DESKS) {
  const deskMod = maxDay(films.filter((f) => f.canonical_industry === desk).map((f) => f.date_modified));
  pages.push({ loc: `${SITE}/${desk}/`, lastmod: deskMod });
}
pages.push({ loc: `${SITE}/ott/calendar/`, lastmod: day(calendar.generated_at) });
const platforms = [...new Set((calendar.entries || []).map((e) => e.platform).filter(Boolean))];
for (const plat of platforms) {
  const lm = maxDay((calendar.entries || []).filter((e) => e.platform === plat).map((e) => e.fetched_at));
  pages.push({ loc: `${SITE}/ott/${platformSlug(plat)}/`, lastmod: lm });
}

// films: review + box-office + upcoming
const filmRows = [];
for (const f of films) {
  const lm = day(f.date_modified);
  filmRows.push(
    { loc: `${SITE}/${f.canonical_industry}/reviews/${f.slug}/`, lastmod: lm },
    { loc: `${SITE}/${f.canonical_industry}/box-office/${f.slug}/`, lastmod: lm },
    { loc: `${SITE}/${f.canonical_industry}/upcoming/${f.slug}/`, lastmod: lm }
  );
}

// series hubs + seasons + where-to-watch (separate children)
const seriesRows = [];
const seasonRows = [];
const w2wRows = [];
for (const s of series) {
  const lm = day(s.date_modified);
  seriesRows.push({ loc: `${SITE}/series/${s.slug}/`, lastmod: lm });
  // mirror qualifiesForWhereToWatch(): multi-season titles only (single-season w2w pages
  // are near-duplicates of the hub per the IG gate)
  if ((s.seasons || []).length >= 2) {
    w2wRows.push({ loc: `${SITE}/series/${s.slug}/where-to-watch/`, lastmod: lm });
  }
  for (const season of s.seasons || []) {
    seasonRows.push({ loc: `${SITE}/series/${s.slug}/s${season.number}/`, lastmod: lm });
  }
}

// endings
const endingRows = endings.map((e) => ({ loc: `${SITE}/series/${e.slug}/ending-explained/`, lastmod: day(e.date_modified) }));

// watch lists
const watchRows = watch.map((l) => ({ loc: `${SITE}/watch/${l.slug}/`, lastmod: day(l.updated) }));

// ---- image sitemap (image: namespace) ----
const usablePoster = (src) => src && !src.includes("_fallback") && fs.existsSync(path.join(publicDir, src.replace(/^\//, "")));
const imgRows = [];
for (const f of films) {
  if (!usablePoster(f.poster?.src) || !f.canonical_industry) continue;
  imgRows.push({ page: `${SITE}/${f.canonical_industry}/reviews/${f.slug}/`, img: `${SITE}${f.poster.src}`, title: val(f.title) });
}
for (const s of series) {
  if (!usablePoster(s.poster?.src)) continue;
  imgRows.push({ page: `${SITE}/series/${s.slug}/`, img: `${SITE}${s.poster.src}`, title: `${val(s.title)} poster` });
}
const imageXml =
  `<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n` +
  imgRows.map((r) => `<url><loc>${esc(r.page)}</loc><image:image><image:loc>${esc(r.img)}</image:loc><image:title>${esc(r.title)}</image:title></image:image></url>`).join("\n") +
  `\n</urlset>\n`;

// ---- write children + collect for index ----
const children = [
  ["sitemap-pages.xml", urlXml(pages), maxDay(pages.map((r) => r.lastmod))],
  ["sitemap-films.xml", urlXml(filmRows), maxDay(filmRows.map((r) => r.lastmod))],
  ["sitemap-series.xml", urlXml(seriesRows), maxDay(seriesRows.map((r) => r.lastmod))],
  ["sitemap-where-to-watch.xml", urlXml(w2wRows), maxDay(w2wRows.map((r) => r.lastmod))],
  ["sitemap-seasons.xml", urlXml(seasonRows), maxDay(seasonRows.map((r) => r.lastmod))],
  ["sitemap-endings.xml", urlXml(endingRows), maxDay(endingRows.map((r) => r.lastmod))],
  ["sitemap-watch.xml", urlXml(watchRows), maxDay(watchRows.map((r) => r.lastmod))],
  ["sitemap-images.xml", imageXml, LAUNCH]
];

for (const [name, xml] of children) fs.writeFileSync(path.join(publicDir, name), xml);

// ---- sitemap index (with per-child lastmod) ----
const indexXml =
  `<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n` +
  children.map(([name, , lm]) => `<sitemap><loc>${SITE}/${name}</loc><lastmod>${lm}</lastmod></sitemap>`).join("\n") +
  `\n</sitemapindex>\n`;
fs.writeFileSync(path.join(publicDir, "sitemap.xml"), indexXml);

const total = pages.length + filmRows.length + seriesRows.length + w2wRows.length + seasonRows.length + endingRows.length + watchRows.length;
console.log(
  `sitemaps: index + ${children.length} children | ${total} URLs ` +
  `(pages ${pages.length}, films ${filmRows.length}, series ${seriesRows.length}, where-to-watch ${w2wRows.length}, seasons ${seasonRows.length}, endings ${endingRows.length}, watch ${watchRows.length}) + ${imgRows.length} images`
);
