import fs from "node:fs";
import path from "node:path";

// "Finale Predictions" - forward-looking speculation surface for upcoming season finales.
// Honesty fences are distinct from endings.ts:
//   - NO spoiler flag (content is prediction, not revelation).
//   - every prediction cites >= 1 source (setup grounded in published episode coverage).
//   - NO first-person viewing claims (same gate as the rest of the site).
//   - theories must carry likelihood labels so speculation is clearly flagged as BollyAI analysis.
// Content lives in data/predictions/<slug>.json, keyed by the series slug.

export type PredictionTheory = {
  title: string;
  basis: string;
  likelihood: string; // e.g. "HIGH - BollyAI analysis", "MEDIUM - BollyAI speculation"
};

export type PredictionSection = {
  heading: string;
  body: string;
};

export type PredictionQA = {
  q: string;
  a: string;
};

export type PredictionSource = {
  title: string;
  url: string;
};

export type Prediction = {
  slug: string; // matches the series slug
  qid?: string | null;
  title: string;
  season_number: number; // the finale season being predicted
  hook: string; // search-intent lede
  sections: PredictionSection[]; // context + setup sections, >= 2
  theories: PredictionTheory[]; // 6-9 grounded theories
  lingering_questions?: PredictionQA[]; // FAQ driving the FAQPage schema
  sources: PredictionSource[]; // >= 1 grounding source
  date_modified: string; // ISO
};

const predictionsDir = path.resolve(process.cwd(), "..", "data", "predictions");

let _allPredictions: Prediction[] | null = null;

export function getAllPredictions(): Prediction[] {
  if (_allPredictions) return _allPredictions;
  if (!fs.existsSync(predictionsDir)) return [];
  _allPredictions = fs
    .readdirSync(predictionsDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(predictionsDir, f), "utf8")) as Prediction)
    .sort((a, b) => b.date_modified.localeCompare(a.date_modified));
  return _allPredictions;
}

export function getPrediction(slug: string): Prediction | undefined {
  return getAllPredictions().find((p) => p.slug === slug);
}

export function hasPrediction(slug: string): boolean {
  return fs.existsSync(path.join(predictionsDir, `${slug}.json`));
}
