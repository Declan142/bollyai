import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: "/search/"
    },
    // Single sitemap-index entry; it references every typed child sitemap.
    sitemap: "https://bollyai.in/sitemap.xml",
    host: "https://bollyai.in"
  };
}
