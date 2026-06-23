import fs from "node:fs";
import path from "node:path";

// "Explainers" - standalone FROM article hub: explainer / theory / guide / character pieces.
// Each article is keyed by (slug, topic); many articles per series.
// Data lives in data/explainers/<slug>/<topic>.json.
// Honesty fences (from FROM-HUB-CONTRACT.md):
//   - Every plot "fact" must be attributable to a specific aired episode.
//   - Theory content is ALWAYS labeled (kind=theory or inline label).
//   - NO first-person viewing claims.
//   - NO em-dash anywhere.
//   - NO fabricated quotes or view counts.

export type ExplainerSection = {
  heading: string;
  body: string;
};

export type ExplainerFAQ = {
  q: string;
  a: string;
};

export type ExplainerSource = {
  text: string;
  url: string;
};

export type Explainer = {
  slug: string;     // matches the series slug
  topic: string;    // URL-safe identifier e.g. "boy-in-white"
  title: string;
  kind: "explainer" | "theory" | "guide" | "character";
  hook: string;     // 1-3 sentence search-intent lede, no em-dash
  spoiler: boolean;
  sections: ExplainerSection[];
  faq: ExplainerFAQ[];
  sources: ExplainerSource[];
  related: string[]; // topic slugs of related explainers
  date_modified: string; // ISO-8601
};

const explainersRoot = path.resolve(process.cwd(), "..", "data", "explainers");

let _cache: Map<string, Explainer[]> | null = null;

function loadAll(): Map<string, Explainer[]> {
  if (_cache) return _cache;
  const map = new Map<string, Explainer[]>();
  if (!fs.existsSync(explainersRoot)) return map;
  for (const seriesSlug of fs.readdirSync(explainersRoot)) {
    const dir = path.join(explainersRoot, seriesSlug);
    if (!fs.statSync(dir).isDirectory()) continue;
    const articles = fs
      .readdirSync(dir)
      .filter((f) => f.endsWith(".json"))
      .map((f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8")) as Explainer)
      .sort((a, b) => b.date_modified.localeCompare(a.date_modified));
    if (articles.length > 0) map.set(seriesSlug, articles);
  }
  _cache = map;
  return map;
}

export function getAllExplainers(): Explainer[] {
  const map = loadAll();
  return Array.from(map.values()).flat();
}

export function getExplainersForSlug(slug: string): Explainer[] {
  return loadAll().get(slug) ?? [];
}

export function getExplainer(slug: string, topic: string): Explainer | undefined {
  return getExplainersForSlug(slug).find((e) => e.topic === topic);
}

export function hasExplainers(slug: string): boolean {
  return getExplainersForSlug(slug).length > 0;
}

// Returns all (slug, topic) pairs for generateStaticParams.
export function getAllExplainerParams(): Array<{ slug: string; topic: string }> {
  const map = loadAll();
  const out: Array<{ slug: string; topic: string }> = [];
  for (const [slug, articles] of map.entries()) {
    for (const a of articles) {
      out.push({ slug, topic: a.topic });
    }
  }
  return out;
}
