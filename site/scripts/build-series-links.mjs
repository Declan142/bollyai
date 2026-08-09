// Build the inter-series LINK MESH as centralized, computed data.
//
// Why a generator (not links baked into 554 series files): editing a "related" block into
// every JSON means N-squared collisions, stale reciprocity, and merge wars across writer
// lanes. Instead we compute ONE artifact, data/_state/series-links.json, from the catalogue
// plus a small editorial overlay. lib/links.ts is a thin render-time CONSUMER of this artifact
// (mirrors how build-search-index.mjs feeds SearchClient). Scoring logic lives ONLY here.
//
// Signals (all derived from real fields - no fabricated metric):
//   curated watch_next  - hand-picked editorial picks, outrank everything
//   universe            - shared-canon / franchise family (curated overlay)
//   genre               - shared facet tags, RARITY-WEIGHTED so "Drama" (367 titles) barely
//                         counts and "Survival" (4 titles) counts a lot
//   region/language     - same original language (Korean cohort, anime cohort, Hindi cohort...)
//   origin              - same country, different language (mild)
//   platform            - same streaming home (tokenised: "JTBC / Netflix" -> netflix cohort)
//   era                 - peak seasons within a few years of each other
//
// Honesty fences honoured: no viewing claims, no invented numbers, no em-dash in any emitted
// reason string. Curated slugs that don't resolve are DROPPED with a warning (never shipped).

import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const here = path.dirname(fileURLToPath(import.meta.url));
const repoRoot = path.resolve(here, "..", "..");
const seriesDir = path.join(repoRoot, "data", "series");
const curatedPath = path.join(repoRoot, "data", "_state", "series-links-curated.json");
const outPath = path.join(repoRoot, "data", "_state", "series-links.json");

const PER_SERIES = 10; // related links computed per title (component shows ~8)

// Human language names for the region reason ("More Korean thrillers").
const LANG_NAME = {
  en: "English", hi: "Hindi", ko: "Korean", ja: "Japanese", ta: "Tamil", te: "Telugu",
  ml: "Malayalam", kn: "Kannada", es: "Spanish", fr: "French", de: "German", it: "Italian",
  he: "Israeli", sv: "Swedish", no: "Norwegian", da: "Danish", tr: "Turkish", pl: "Polish",
  is: "Icelandic", pt: "Portuguese", yi: "Yiddish"
};

// A short, audience-facing genre word for the reason line. Picks the RAREST shared genre
// (the most distinctive thing two shows have in common) and frames it.
function langLabel(code) {
  return LANG_NAME[code?.toLowerCase?.()] || (code ? code.toUpperCase() : "");
}

function normGenre(g) {
  return String(g || "").trim().toLowerCase();
}

function normTitle(t) {
  return String(t || "").toLowerCase().replace(/[^a-z0-9]+/g, " ").trim();
}

function platformTokens(p) {
  return String(p || "")
    .split(/[/,&]|\band\b/i)
    .map((x) => x.trim().toLowerCase())
    .filter(Boolean);
}

function peakYear(s) {
  let best = null;
  for (const season of s.seasons || []) {
    const y = season.year;
    if (typeof y === "number" && (best === null || y > best)) best = y;
  }
  return best;
}

function hasScore(s) {
  return (s.seasons || []).some((season) => season.bollymeter && typeof season.bollymeter.score === "number");
}

// ---- load catalogue ----
if (!fs.existsSync(seriesDir)) {
  console.error(`[links] no series dir at ${seriesDir}`);
  process.exit(0);
}
const files = fs.readdirSync(seriesDir).filter((f) => f.endsWith(".json"));
const all = [];
for (const f of files) {
  try {
    all.push(JSON.parse(fs.readFileSync(path.join(seriesDir, f), "utf8")));
  } catch (e) {
    console.warn(`[links] skip unparseable ${f}: ${e.message}`);
  }
}
const bySlug = new Map(all.map((s) => [s.slug, s]));

// Genre rarity: idf-style weight. A genre on 1 title is gold; a genre on 367 is noise.
const genreFreq = new Map();
for (const s of all) {
  for (const g of s.genres || []) {
    const k = normGenre(g);
    if (k) genreFreq.set(k, (genreFreq.get(k) || 0) + 1);
  }
}
const N = all.length || 1;
function genreWeight(k) {
  const freq = genreFreq.get(k) || N;
  // log-idf, clamped: ubiquitous genres ~0.1, singletons ~ up to ~3.
  return Math.max(0.1, Math.log(N / freq));
}

// Pretty-print a genre key back to a display word using the first real-cased occurrence.
const genreDisplay = new Map();
for (const s of all) {
  for (const g of s.genres || []) {
    const k = normGenre(g);
    if (k && !genreDisplay.has(k)) genreDisplay.set(k, String(g).trim());
  }
}

// ---- curated overlay ----
let curated = { universes: [], watch_next: {} };
if (fs.existsSync(curatedPath)) {
  try {
    curated = JSON.parse(fs.readFileSync(curatedPath, "utf8"));
  } catch (e) {
    console.warn(`[links] curated overlay unreadable, ignoring: ${e.message}`);
  }
}
const warnings = [];

// universe family lookup: slug -> { family, blurb, members:Set }
const universeOf = new Map();
for (const u of curated.universes || []) {
  const members = (u.slugs || []).filter((sl) => {
    if (bySlug.has(sl)) return true;
    warnings.push(`universe "${u.family}" references missing slug "${sl}"`);
    return false;
  });
  for (const sl of members) {
    universeOf.set(sl, { family: u.family, blurb: u.blurb || `Same universe as ${u.family}`, members: new Set(members) });
  }
}

// ---- scoring ----
// Returns { score, kind, reason } for candidate b relative to source a, or null if no signal.
function edge(a, b) {
  // Defensive: never recommend a near-duplicate (same normalised title) - the catalogue has
  // genuine dup entries (e.g. scam-1992 vs scam-1992-the-harshad-mehta-story).
  if (normTitle(a.title?.value) === normTitle(b.title?.value)) return null;

  const buckets = [];

  // universe (shared canon) - strongest computed-tier signal
  const ua = universeOf.get(a.slug);
  if (ua && ua.members.has(b.slug)) {
    buckets.push({ kind: "universe", score: 50, reason: ua.blurb });
  }

  // genre overlap, rarity-weighted
  const ag = new Set((a.genres || []).map(normGenre).filter(Boolean));
  const shared = (b.genres || []).map(normGenre).filter((k) => k && ag.has(k));
  if (shared.length) {
    const uniq = [...new Set(shared)];
    let gScore = 0;
    for (const k of uniq) gScore += genreWeight(k);
    gScore = Math.min(gScore * 2.2, 22); // cap so genre alone can't bury universe
    // reason: the two rarest shared genres, display-cased
    const ranked = uniq.sort((x, y) => genreWeight(y) - genreWeight(x));
    const top = ranked.slice(0, 2).map((k) => genreDisplay.get(k) || k);
    const reason = top.length === 2 ? `More ${top[0]} ${top[1].toLowerCase()}` : `More ${top[0]}`;
    buckets.push({ kind: "genre", score: gScore, sharedCount: uniq.length, reason });
  }

  // region: same original language (the cohort that feels most "if you liked this")
  const la = a.original_language?.value?.toLowerCase?.();
  const lb = b.original_language?.value?.toLowerCase?.();
  if (la && lb && la === lb) {
    const label = langLabel(la);
    // anime gets its own framing; otherwise "More <Lang> series"
    const isAnime = (a.genres || []).map(normGenre).includes("anime") && (b.genres || []).map(normGenre).includes("anime");
    const reason = isAnime ? "More anime like this" : `More ${label} series`;
    buckets.push({ kind: "region", score: 6, reason });
  } else {
    // same country, different language (e.g. multi-language Indian originals)
    if (a.origin && b.origin && a.origin === b.origin && a.origin.toLowerCase() !== "united states") {
      buckets.push({ kind: "origin", score: 3, reason: `More from ${a.origin}` });
    }
  }

  // platform cohort
  const pa = new Set(platformTokens(a.platform?.value));
  const pShared = platformTokens(b.platform?.value).some((t) => pa.has(t));
  if (pShared) {
    const plat = (a.platform?.value || "").split(/[/,&]/)[0].trim();
    buckets.push({ kind: "platform", score: 4, reason: `Also on ${plat}` });
  }

  // era proximity
  const ya = peakYear(a);
  const yb = peakYear(b);
  if (ya !== null && yb !== null) {
    const d = Math.abs(ya - yb);
    if (d <= 2) buckets.push({ kind: "era", score: 2, reason: "From the same era" });
    else if (d <= 5) buckets.push({ kind: "era", score: 1, reason: "From around the same time" });
  }

  if (!buckets.length) return null;

  const score = buckets.reduce((sum, x) => sum + x.score, 0);

  // Choose the headline reason: universe > strong genre(>=2 shared) > region > platform >
  // single genre > origin > era. This is what reads best as the visible hook.
  const pick = (kind) => buckets.find((x) => x.kind === kind);
  const strongGenre = buckets.find((x) => x.kind === "genre" && (x.sharedCount || 0) >= 2);
  const headline =
    pick("universe") ||
    strongGenre ||
    pick("region") ||
    pick("platform") ||
    pick("genre") ||
    pick("origin") ||
    pick("era");

  return { score, kind: headline.kind, reason: headline.reason };
}

// ---- build per-series related lists ----
const links = {};
for (const a of all) {
  const scored = [];
  for (const b of all) {
    if (b.slug === a.slug) continue;
    const e = edge(a, b);
    if (!e) continue;
    scored.push({
      slug: b.slug,
      reason: e.reason,
      kind: e.kind,
      score: Math.round(e.score * 100) / 100,
      _scored: hasScore(b) ? 1 : 0,
      _recency: peakYear(b) || 0
    });
  }
  // deterministic ordering: score desc, then reviewed-first, then newer-first, then slug
  scored.sort(
    (x, y) =>
      y.score - x.score ||
      y._scored - x._scored ||
      y._recency - x._recency ||
      x.slug.localeCompare(y.slug)
  );

  // overlay curated watch_next at the TOP (deduped), preserving curated order
  const curatedPicks = [];
  const seen = new Set();
  for (const pick of curated.watch_next?.[a.slug] || []) {
    if (!bySlug.has(pick.slug)) {
      warnings.push(`watch_next["${a.slug}"] references missing slug "${pick.slug}"`);
      continue;
    }
    if (pick.slug === a.slug || seen.has(pick.slug)) continue;
    if (normTitle(bySlug.get(pick.slug).title?.value) === normTitle(a.title?.value)) continue;
    seen.add(pick.slug);
    curatedPicks.push({ slug: pick.slug, reason: pick.note, kind: "curated", score: 1000 });
  }

  const merged = [...curatedPicks];
  for (const s of scored) {
    if (seen.has(s.slug)) continue;
    seen.add(s.slug);
    merged.push({ slug: s.slug, reason: s.reason, kind: s.kind, score: s.score });
    if (merged.length >= PER_SERIES) break;
  }

  if (merged.length) links[a.slug] = merged;
}

// ---- emit ----
// em-dash fence: assert no em/en dash leaked into any reason string.
const dashHit = [];
for (const [slug, arr] of Object.entries(links)) {
  for (const l of arr) {
    if (/[\u2013\u2014]/.test(l.reason)) dashHit.push(`${slug} -> ${l.slug}: ${l.reason}`);
  }
}
if (dashHit.length) {
  console.error(`[links] EM-DASH in reason strings (fence):\n  ${dashHit.join("\n  ")}`);
  process.exit(1);
}

const out = {
  _doc: "GENERATED by site/scripts/build-series-links.mjs - do not hand-edit. Centralized inter-series link mesh consumed by lib/links.ts. Re-run after the catalogue changes.",
  generated: new Date().toISOString(),
  version: 1,
  per_series: PER_SERIES,
  total_series: all.length,
  total_with_links: Object.keys(links).length,
  links
};
fs.writeFileSync(outPath, JSON.stringify(out, null, 2) + "\n");

const edges = Object.values(links).reduce((n, a) => n + a.length, 0);
console.log(`[links] ${Object.keys(links).length}/${all.length} series linked, ${edges} edges, avg ${(edges / Math.max(1, Object.keys(links).length)).toFixed(1)}/series -> ${path.relative(repoRoot, outPath)}`);
if (warnings.length) {
  console.warn(`[links] ${warnings.length} curation warning(s):`);
  for (const w of warnings) console.warn(`  - ${w}`);
}
