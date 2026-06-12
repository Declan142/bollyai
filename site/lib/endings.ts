import fs from "node:fs";
import path from "node:path";

// "Ending Explained" - spoiler-FULL walkthroughs of how a show ends. This is the
// ONE surface that is deliberately spoiler-heavy (everything else on BollyAI is
// spoiler-free). The honesty fences still hold and are STRICTER here:
//   - spoiler === true is mandatory (the page renders a spoiler gate from it).
//   - every ending cites >= 1 source (the Wikipedia plot/finale it is grounded in);
//     a walkthrough with no source is a fabrication risk and the gate hard-fails it.
//   - NO first-person viewing claims (same viewing_claim gate as the rest of the site).
// Content lives in data/endings/<slug>.json, keyed by the series slug.

export type EndingSection = {
  heading: string;
  body: string;
};

export type EndingQA = {
  q: string;
  a: string;
};

export type EndingSource = {
  title: string;
  url: string;
};

export type Ending = {
  slug: string; // matches the series slug
  qid?: string | null;
  title: string;
  season_number: number; // the finale season this explains
  spoiler: true; // always true - this is the gate flag
  hook: string; // the search-intent lede, e.g. "How does Dark end? ..."
  sections: EndingSection[]; // the walkthrough, >= 3 sections
  final_image?: string | null; // the literal last shot / closing beat, optional
  lingering_questions?: EndingQA[]; // optional FAQ - drives the FAQPage schema
  sources: EndingSource[]; // >= 1, what the walkthrough is grounded in
  date_modified: string; // ISO
};

const endingsDir = path.resolve(process.cwd(), "..", "data", "endings");

export function getAllEndings(): Ending[] {
  if (!fs.existsSync(endingsDir)) return [];
  return fs
    .readdirSync(endingsDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(endingsDir, f), "utf8")) as Ending)
    .sort((a, b) => b.date_modified.localeCompare(a.date_modified));
}

export function getEnding(slug: string): Ending | undefined {
  return getAllEndings().find((e) => e.slug === slug);
}

export function hasEnding(slug: string): boolean {
  return fs.existsSync(path.join(endingsDir, `${slug}.json`));
}
