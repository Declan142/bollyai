// Full segmented sitemap system (replaces the flat Next sitemap.ts).
// 2026 best practice: a sitemap INDEX -> typed child sitemaps, so Google Search
// Console reports indexation PER content type, plus accurate per-URL and per-child
// <lastmod> (the one sitemap signal Google actually uses). Image sitemap folded in.
// Runs in prebuild AFTER sync-public so poster files are present for the on-disk check.
import fs from "node:fs";
import path from "node:path";
import { loadBoxOfficeBoard } from "../lib/boxoffice-schema.mjs";

const siteRoot = process.cwd();
const repoRoot = path.resolve(siteRoot, "..");
const dataDir = path.join(repoRoot, "data");
const publicDir = path.join(siteRoot, "public");
const SITE = "https://bollyai.in";
const LAUNCH = "2026-06-08"; // real first-publish date for static/utility pages
const HOME_TEMPLATE_REVISION = "2026-08-01";

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
const predictions = listJson(path.join(dataDir, "predictions"));
const watch = listJson(path.join(dataDir, "recommendations"));
const calendar = fs.existsSync(path.join(dataDir, "ott", "calendar.json"))
  ? readJson(path.join(dataDir, "ott", "calendar.json"))
  : { generated_at: LAUNCH, entries: [] };
const boxofficePath = path.join(dataDir, "boxoffice", "current-week.json");
const boxoffice = loadBoxOfficeBoard({
  filePath: boxofficePath,
  readText: (filePath) => fs.readFileSync(filePath, "utf8")
});

// /streaming/ is a Cloudflare redirect to the canonical /browse/ catalogue.
const DESKS = ["hollywood"];
const homeModified = maxDay([
  HOME_TEMPLATE_REVISION,
  ...films.map((film) => film.date_modified),
  ...series.map((show) => show.date_modified),
  ...watch.map((list) => list.updated),
  calendar.generated_at
]);

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
  "/box-office/",
  "/ask/",
  "/browse/",
  "/series/diary/",
  "/watch/",
  "/tools/",
  "/tools/hit-flop-calculator/",
  "/tools/box-office-comparator/"
];
// /box-office/ is noindex whenever the weekly board has no published rows (see
// site/app/box-office/page.tsx) - a noindex URL must not be advertised in the sitemap.
const boxOfficeIsPublished = boxoffice.status === "ready" && (boxoffice.records || []).length > 0;
const pages = [];
for (const p of staticPaths) {
  if (p === "/box-office/" && !boxOfficeIsPublished) continue;
  pages.push({
    loc: `${SITE}${p}`,
    lastmod: p === "/" ? homeModified : p === "/box-office/" ? day(boxoffice.generated_at) : LAUNCH
  });
}
for (const desk of DESKS) {
  const deskMod = maxDay(films.filter((f) => f.canonical_industry === desk).map((f) => f.date_modified));
  pages.push({ loc: `${SITE}/${desk}/`, lastmod: deskMod });
}
pages.push({ loc: `${SITE}/ott/calendar/`, lastmod: day(calendar.generated_at) });
for (const week of calendar.weeks || []) {
  if (!week.archive_url) continue;
  pages.push({ loc: `${SITE}${week.archive_url}`, lastmod: day(calendar.generated_at) });
}
const archiveDir = path.join(dataDir, "ott", "calendar");
if (fs.existsSync(archiveDir)) {
  for (const file of fs.readdirSync(archiveDir)) {
    const match = file.match(/^(20\d{2})-W(\d{2})\.json$/);
    if (!match) continue;
    const archive = readJson(path.join(archiveDir, file));
    const url = `${SITE}/ott/calendar/${match[1]}/wk-${match[2]}/`;
    if (!pages.some((row) => row.loc === url)) {
      pages.push({ loc: url, lastmod: day(archive.generated_at || calendar.generated_at) });
    }
  }
}
const trackedPlatforms = calendar.tracking?.platforms || [];
const platforms = [...new Set([...trackedPlatforms, ...(calendar.entries || []).map((e) => val(e.platform)).filter(Boolean)])];
for (const plat of platforms) {
  const lm = maxDay((calendar.entries || []).filter((e) => val(e.platform) === plat).map((e) => e.fetched_at));
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
const episodeRowsByLocation = new Map();
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
    for (const episode of season.episode_reviews || []) {
      if (!episode.review_body?.trim()) continue;
      const loc = `${SITE}/series/${s.slug}/s${season.number}/e${episode.number}/`;
      episodeRowsByLocation.set(loc, { loc, lastmod: lm });
    }
  }
}

// Subtitle-grounded breakdowns and rich embedded episode reviews share one route. Keep a
// deduplicated sitemap row for both sources so every indexable exported episode is discoverable.
const episodeDataDir = path.join(dataDir, "episodes");
if (fs.existsSync(episodeDataDir)) {
  const seriesBySlug = new Map(series.map((show) => [show.slug, show]));
  for (const slug of fs.readdirSync(episodeDataDir)) {
    const dir = path.join(episodeDataDir, slug);
    if (!fs.statSync(dir).isDirectory()) continue;
    for (const episode of listJson(dir)) {
      if (!Number.isInteger(episode.season) || !Number.isInteger(episode.number)) continue;
      const loc = `${SITE}/series/${slug}/s${episode.season}/e${episode.number}/`;
      episodeRowsByLocation.set(loc, { loc, lastmod: day(seriesBySlug.get(slug)?.date_modified) });
    }
  }
}
const episodeRows = [...episodeRowsByLocation.values()].sort((a, b) => a.loc.localeCompare(b.loc));

// Standalone explainers are indexable editorial pages, not utility search results.
const explainerRows = [];
const explainersDir = path.join(dataDir, "explainers");
if (fs.existsSync(explainersDir)) {
  for (const slug of fs.readdirSync(explainersDir)) {
    const dir = path.join(explainersDir, slug);
    if (!fs.statSync(dir).isDirectory()) continue;
    for (const explainer of listJson(dir)) {
      if (!explainer.topic) continue;
      explainerRows.push({
        loc: `${SITE}/series/${slug}/explainer/${explainer.topic}/`,
        lastmod: day(explainer.date_modified)
      });
    }
  }
}

// endings
const endingRows = endings.map((e) => ({ loc: `${SITE}/series/${e.slug}/ending-explained/`, lastmod: day(e.date_modified) }));

// finale predictions
const predictionRows = predictions.map((p) => ({ loc: `${SITE}/series/${p.slug}/finale-predictions/`, lastmod: day(p.date_modified) }));

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
  ["sitemap-episodes.xml", urlXml(episodeRows), maxDay(episodeRows.map((r) => r.lastmod))],
  ["sitemap-explainers.xml", urlXml(explainerRows), maxDay(explainerRows.map((r) => r.lastmod))],
  ["sitemap-endings.xml", urlXml(endingRows), maxDay(endingRows.map((r) => r.lastmod))],
  ["sitemap-predictions.xml", urlXml(predictionRows), maxDay(predictionRows.map((r) => r.lastmod))],
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

const total = pages.length + filmRows.length + seriesRows.length + w2wRows.length + seasonRows.length + episodeRows.length + explainerRows.length + endingRows.length + predictionRows.length + watchRows.length;
console.log(
  `sitemaps: index + ${children.length} children | ${total} URLs ` +
  `(pages ${pages.length}, films ${filmRows.length}, series ${seriesRows.length}, where-to-watch ${w2wRows.length}, seasons ${seasonRows.length}, episodes ${episodeRows.length}, explainers ${explainerRows.length}, endings ${endingRows.length}, predictions ${predictionRows.length}, watch ${watchRows.length}) + ${imgRows.length} images`
);
