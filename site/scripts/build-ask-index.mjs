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

// ---- keyword extraction for oblique-question recall ------------------------------------
// Pulls character/cast/place names (capitalized sequences) + salient content words + mood
// facets from the grounded prose. This is the haystack a "that korean revenge show" style
// query matches against. Honesty fence holds: this is plain text recall over data that is
// ALREADY grounded - it surfaces existing titles, it never asserts a new fact.
const STOP_CAP = new Set([
  "The", "A", "An", "In", "On", "At", "Of", "And", "But", "Or", "As", "It", "He", "She",
  "They", "This", "That", "His", "Her", "Their", "When", "After", "Before", "Season",
  "Episode", "Series", "Show", "Part", "BollyAI", "India", "Netflix", "Prime", "Hotstar",
  "JioHotstar", "SonyLIV", "Disney", "Rotten", "Tomatoes", "Metacritic", "IMDb", "Baeksang",
  "Emmy", "Spoiler", "Review", "Set", "Both", "While", "With", "From", "For", "By", "An",
  "Its", "One", "Two", "Three", "First", "Second", "Third", "New", "Now", "Still"
]);
const STOPWORDS = new Set([
  "about", "after", "again", "their", "there", "these", "those", "which", "while", "would",
  "could", "should", "where", "every", "other", "another", "through", "between", "becomes",
  "become", "story", "stories", "series", "season", "seasons", "episode", "episodes",
  "follows", "follow", "around", "against", "during", "without", "within", "across",
  "drama", "thriller", "comedy", "world", "years", "first", "second", "third", "modern",
  "young", "woman", "women", "child", "children", "people", "family", "friends", "begins"
]);

const properNames = (text) => {
  if (!text) return [];
  const out = [];
  const re = /\b([A-Z][a-z]+(?:[-\s][A-Z][a-z]+){0,2})\b/g;
  let m;
  while ((m = re.exec(text)) !== null) {
    const w = m[1];
    if (STOP_CAP.has(w.split(/[-\s]/)[0])) continue;
    out.push(w.toLowerCase().replace(/\s+/g, " "));
  }
  return out;
};
const contentWords = (text) =>
  (text || "")
    .toLowerCase()
    .replace(/[^a-z0-9\s-]/g, " ")
    .split(/\s+/)
    .filter((w) => w.length > 4 && !STOPWORDS.has(w));

const MOOD_RULES = [
  { g: ["Comedy"], w: ["funny", "feelgood", "lighthearted", "comfort"] },
  { g: ["Family"], w: ["wholesome", "feelgood", "comfort"] },
  { g: ["Romance"], w: ["romantic", "heartfelt"] },
  { g: ["Mystery", "Psychological", "Sci-Fi"], w: ["mindbending", "twisty", "cerebral"] },
  { g: ["Crime", "Thriller"], w: ["gritty", "tense", "dark"] },
  { g: ["Horror"], w: ["scary", "creepy", "dark"] },
  { g: ["Survival", "Action"], w: ["intense", "highstakes"] }
];
const moodTokens = (genres) => {
  const lower = genres.map((g) => g.toLowerCase());
  const out = [];
  for (const rule of MOOD_RULES) {
    if (rule.g.some((g) => lower.includes(g.toLowerCase()))) out.push(...rule.w);
  }
  return out;
};

const buildKw = ({ title, slug, genres, origin, platform, logline, basis, episodeProse }) => {
  const prose = [logline, basis, episodeProse].filter(Boolean).join(" ");
  const tokens = [
    ...norm(slug).split("-"),
    ...norm(title).split(" "),
    ...genres.map((g) => g.toLowerCase()),
    ...moodTokens(genres),
    origin ? origin.toLowerCase() : "",
    platform ? platform.toLowerCase().replace(/[^a-z0-9]+/g, "") : "",
    ...properNames(prose),
    ...contentWords(logline),
    ...contentWords(basis)
  ].filter(Boolean);
  const seen = new Set();
  const uniq = [];
  for (const t of tokens) {
    if (seen.has(t)) continue;
    seen.add(t);
    uniq.push(t);
    if (uniq.join(" ").length > 320) break;
  }
  return uniq.join(" ");
};
const norm = (s) => String(s || "").toLowerCase().replace(/[^a-z0-9\s-]/g, " ").replace(/\s+/g, " ").trim();

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

  const genres = Array.isArray(d.genres) ? d.genres : [];
  // gather a capped slice of grounded episode prose (names + plot beats) for recall
  const episodeProse = (head?.episode_reviews || [])
    .slice(0, 5)
    .map((er) => [er.the_moment, er.spoiler_free].filter(Boolean).join(" "))
    .join(" ")
    .slice(0, 1200);

  records.push({
    t: title,
    u: `/series/${d.slug}/`,
    k: "Series",
    o: d.origin || null,
    l: val(d.original_language) || null,
    g: genres,
    p: val(d.platform) || null,
    v: verdict,
    sc: bm ? bm.score : null,
    b: bm ? clip(bm.basis, 240) : null,
    sn: clip(val(head?.review_body), 260),
    y: head?.year || null,
    e: endingSlugs.has(d.slug),
    pp: hasRealPoster(d.poster?.src),
    wtw: `/series/${d.slug}/where-to-watch/`,
    kw: buildKw({
      title, slug: d.slug, genres, origin: d.origin, platform: val(d.platform),
      logline: val(d.logline), basis: bm ? bm.basis : null, episodeProse
    })
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

  const genres = Array.isArray(d.genres) ? d.genres : [];
  records.push({
    t: title,
    u: `/${desk}/reviews/${d.slug}/`,
    k: "Film",
    o: null,
    l: val(d.original_language) || null,
    g: genres,
    p: null,
    v: typeof verdict === "string" ? verdict : null,
    sc: bm ? bm.score : null,
    b: bm ? clip(bm.basis, 240) : null,
    sn: clip(val(d.logline), 240),
    y: d.release_date ? Number(String(d.release_date).slice(0, 4)) || null : null,
    e: false,
    pp: hasRealPoster(d.poster?.src),
    wtw: null,
    kw: buildKw({
      title, slug: d.slug, genres, origin: null, platform: null,
      logline: val(d.logline), basis: bm ? bm.basis : null, episodeProse: null
    })
  });
}

fs.mkdirSync(publicDir, { recursive: true });
fs.writeFileSync(outFile, JSON.stringify(records));
const grounded = records.filter((r) => r.sc !== null).length;
console.log(`ask-index.json: ${records.length} records (${grounded} with a grounded BollyMeter score)`);
