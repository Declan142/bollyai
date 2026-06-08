// Dedicated image sitemap (Next 14 sitemap.ts can't emit the image: namespace).
// Opens Google Images discovery for the poster-rich catalogue. Only includes a
// poster that actually exists on disk and is not the fallback SVG. Runs in prebuild
// AFTER sync-public so the poster files are present under site/public.
import fs from "node:fs";
import path from "node:path";

const siteRoot = process.cwd();
const repoRoot = path.resolve(siteRoot, "..");
const dataDir = path.join(repoRoot, "data");
const publicDir = path.join(siteRoot, "public");
const SITE = "https://bollyai.in";

const readJson = (p) => JSON.parse(fs.readFileSync(p, "utf8"));
const listJson = (dir) =>
  fs.existsSync(dir) ? fs.readdirSync(dir).filter((f) => f.endsWith(".json")) : [];
const val = (v) => (v && typeof v === "object" && "value" in v ? v.value : v);
const esc = (s) =>
  String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const usablePoster = (src) => {
  if (!src || src.includes("_fallback")) return false;
  return fs.existsSync(path.join(publicDir, src.replace(/^\//, "")));
};

const rows = [];

for (const f of listJson(path.join(dataDir, "films"))) {
  const d = readJson(path.join(dataDir, "films", f));
  const src = d.poster?.src;
  if (!usablePoster(src) || !d.canonical_industry) continue;
  rows.push({ page: `${SITE}/${d.canonical_industry}/reviews/${d.slug}/`, img: `${SITE}${src}`, title: val(d.title) });
}

for (const f of listJson(path.join(dataDir, "series"))) {
  const d = readJson(path.join(dataDir, "series", f));
  const src = d.poster?.src;
  if (!usablePoster(src)) continue;
  rows.push({ page: `${SITE}/series/${d.slug}/`, img: `${SITE}${src}`, title: `${val(d.title)} poster` });
}

const body = rows
  .map(
    (r) =>
      `<url><loc>${esc(r.page)}</loc><image:image><image:loc>${esc(r.img)}</image:loc>` +
      `<image:title>${esc(r.title)}</image:title></image:image></url>`
  )
  .join("\n");

const xml =
  `<?xml version="1.0" encoding="UTF-8"?>\n` +
  `<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" ` +
  `xmlns:image="http://www.google.com/schemas/sitemap-image/1.1">\n${body}\n</urlset>\n`;

fs.writeFileSync(path.join(publicDir, "sitemap-images.xml"), xml);
console.log(`sitemap-images.xml: ${rows.length} poster entries`);
