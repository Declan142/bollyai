import type { Metadata } from "next";

const SITE = "https://bollyai.in";
const DEFAULT_OG = "/og-default.png"; // 1200x630 branded card (public/og-default.png)
const DEFAULT_OG_ALT = "BollyAI - Har Friday ka faisla. OTT & movie verdicts for India.";

function abs(p: string): string {
  if (p.startsWith("http")) return p;
  return `${SITE}${p.startsWith("/") ? "" : "/"}${p}`;
}

export type SeoInput = {
  /** Canonical path WITH trailing slash, e.g. "/series/aarya/" or "/". */
  path: string;
  /** Site-relative or absolute share image (e.g. a poster). Falls back to the branded default card. */
  image?: string | null;
  /** OpenGraph type - "website" (default) for hubs, "article" for a single verdict / explainer. */
  type?: "website" | "article";
};

/**
 * Canonical URL + OpenGraph image + large Twitter card for one route.
 * Static-export safe: og:image points at a real static asset, no runtime generation.
 *
 * Spread it into a route's metadata (page title & description flow into og:/twitter: via
 * Next's metadata merge, so they need not be repeated here):
 *
 *   export const metadata = { title, description, ...pageSeo({ path: "/series/" }) };
 *   // or, per-title with its poster as the share image:
 *   return { title, description, ...pageSeo({ path: `/series/${slug}/`, image: series.poster.src, type: "article" }) };
 */
export function pageSeo({ path, image, type = "website" }: SeoInput): Metadata {
  const canonical = abs(path);
  // Only raster images make valid share cards - X/Facebook/WhatsApp don't render an SVG
  // og:image, so an SVG poster fallback must degrade to the branded default card.
  const raster = image && image.length > 0 && !image.toLowerCase().endsWith(".svg") ? image : null;
  const usingDefault = !raster;
  const ogUrl = abs(raster ?? DEFAULT_OG);
  return {
    alternates: { canonical },
    openGraph: {
      type,
      siteName: "BollyAI",
      url: canonical,
      images: [
        usingDefault ? { url: ogUrl, width: 1200, height: 630, alt: DEFAULT_OG_ALT } : { url: ogUrl }
      ]
    },
    twitter: {
      card: "summary_large_image",
      images: [ogUrl]
    }
  };
}

/** Generated share card for a series (scripts/og/og_series.py), if one exists. */
export function ogImage(slug: string, season?: number): string | null {
  const fs = require("node:fs") as typeof import("node:fs");
  const path = require("node:path") as typeof import("node:path");
  const rel = season != null ? `/img/series/${slug}/og-s${season}.jpg` : `/img/series/${slug}/og.jpg`;
  return fs.existsSync(path.resolve(process.cwd(), "public", rel.slice(1))) ? rel : null;
}
