import fs from "node:fs";
import path from "node:path";
import type { DeskSlug } from "./desks";
import { getAllFilms } from "./data";
import { getAllSeries } from "./series";

// "What to Watch" - curated, editorial recommendation lists. This is the one surface
// where BollyAI is allowed to be opinionated and lean-forward, but the fences hold:
// NO first-person viewing claims, every pick names where it streams, every score is
// a craft/word-of-mouth read with a basis - never invented box-office.

export type WatchPick = {
  ref_type: "film" | "series";
  slug: string | null; // links to an on-site entity when one exists; null = external/off-site
  desk?: DeskSlug | null; // for /[desk] film links
  title: string;
  year?: number | null;
  one_line: string; // why it earns the slot - punchy, < 30 words, no viewing claim
  where: string; // platform(s), e.g. "Netflix" / "JioHotstar"
  bollymeter?: number | null; // optional /10
};

export type WatchList = {
  slug: string;
  title: string; // "Best Korean Thrillers Streaming in India"
  kicker: string; // mono eyebrow, e.g. "STREAMING · K-DRAMA"
  desk?: DeskSlug | null;
  updated: string; // ISO
  intro: string; // editorial lede, no first-person viewing
  picks: WatchPick[];
  faq?: Array<{ q: string; a: string }>;
};

const recsDir = path.resolve(process.cwd(), "..", "data", "recommendations");

export function getAllWatchLists(): WatchList[] {
  if (!fs.existsSync(recsDir)) return [];
  return fs
    .readdirSync(recsDir)
    .filter((f) => f.endsWith(".json"))
    .map((f) => JSON.parse(fs.readFileSync(path.join(recsDir, f), "utf8")) as WatchList)
    .sort((a, b) => b.updated.localeCompare(a.updated));
}

export function getWatchList(slug: string): WatchList | undefined {
  return getAllWatchLists().find((l) => l.slug === slug);
}

function titleKey(value: string): string {
  return value
    .normalize("NFKD")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, " ")
    .trim();
}

// Resolve a pick to its on-site URL. Older lists predate catalogue slugs, so an exact
// normalized-title match repairs that internal journey without guessing across near matches.
export function pickHref(pick: WatchPick): string | null {
  if (pick.ref_type === "series") {
    const slug = pick.slug ?? getAllSeries().find((series) => titleKey(series.title.value) === titleKey(pick.title))?.slug;
    return slug ? `/series/${slug}/` : null;
  }

  if (pick.ref_type === "film") {
    const film = getAllFilms().find((candidate) =>
      pick.slug ? candidate.slug === pick.slug : titleKey(candidate.title.value) === titleKey(pick.title)
    );
    const slug = pick.slug ?? film?.slug;
    const desk = pick.desk ?? film?.canonical_industry;
    return slug && desk ? `/${desk}/reviews/${slug}/` : null;
  }

  return null;
}
