import fs from "node:fs";
import path from "node:path";
import { getAllSeries, peakSeason, type Series } from "./series";

// Render-time CONSUMER of the centralized link mesh (data/_state/series-links.json, built by
// site/scripts/build-series-links.mjs). This module does NO scoring - it reads the precomputed
// artifact and resolves slugs to live Series objects, silently dropping any related slug that
// no longer exists in the catalogue. That makes the mesh self-healing: if a writer lane removes
// a series, every dangling edge to it just disappears at render with no broken link. Mirrors how
// lib/recommendations.ts consumes data/recommendations/*.json.

export type RelatedKind = "curated" | "universe" | "genre" | "region" | "origin" | "platform" | "era";

type RawLink = { slug: string; reason: string; kind: RelatedKind; score: number };
type LinkArtifact = { links: Record<string, RawLink[]> };

// A resolved related-series link, ready to render.
export type RelatedSeries = {
  series: Series;
  reason: string; // visible hook, e.g. "More Korean thrillers" / curated note
  kind: RelatedKind;
};

const artifactPath = path.resolve(process.cwd(), "..", "data", "_state", "series-links.json");

let _artifact: LinkArtifact | null = null;
function loadArtifact(): LinkArtifact {
  if (_artifact) return _artifact;
  if (!fs.existsSync(artifactPath)) {
    _artifact = { links: {} };
    return _artifact;
  }
  try {
    _artifact = JSON.parse(fs.readFileSync(artifactPath, "utf8")) as LinkArtifact;
  } catch {
    _artifact = { links: {} };
  }
  return _artifact;
}

// Live slug -> Series index, built once per render process. Used to resolve mesh edges and to
// drop any edge whose target is no longer in the catalogue.
let _index: Map<string, Series> | null = null;
function seriesIndex(): Map<string, Series> {
  if (_index) return _index;
  _index = new Map(getAllSeries().map((s) => [s.slug, s]));
  return _index;
}

// The related-series mesh for one title: curated picks first (already ordered in the artifact),
// then computed edges, with dead slugs filtered out. Returns up to `limit` resolved links.
export function getRelatedSeries(slug: string, limit = 8): RelatedSeries[] {
  const raw = loadArtifact().links[slug];
  if (!raw || raw.length === 0) return [];
  const index = seriesIndex();
  const out: RelatedSeries[] = [];
  for (const link of raw) {
    if (link.slug === slug) continue;
    const series = index.get(link.slug);
    if (!series) continue; // self-healing: edge to a removed title is silently dropped
    out.push({ series, reason: link.reason, kind: link.kind });
    if (out.length >= limit) break;
  }
  return out;
}

// Convenience for the card plate: the franchise's best-known score (or null).
export function relatedScore(series: Series): number | null {
  return peakSeason(series)?.bollymeter?.score ?? null;
}
