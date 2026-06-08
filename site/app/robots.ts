import type { MetadataRoute } from "next";

export default function robots(): MetadataRoute.Robots {
  return {
    rules: {
      userAgent: "*",
      allow: "/",
      disallow: "/search/"
    },
    sitemap: "https://bollyai.in/sitemap.xml",
    host: "https://bollyai.in"
  };
}
