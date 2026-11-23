import rawCalendar from "../../../../data/ott/calendar.json";
import { CurrentOttCalendar } from "../../../components/CurrentOttCalendar";
import { getAllFilms, getOttCalendar } from "../../../lib/data";
import { parseOttFeed } from "../../../lib/ott-feed.mjs";
import { pageSeo } from "../../../lib/seo";
import { getAllSeries } from "../../../lib/series";

export const metadata = {
  title: "OTT Release Calendar - New on Netflix, Max, Disney+ & More",
  description: "Find announced streaming dates for Western films and series, with the platform and a source for each premiere.",
  ...pageSeo({ path: "/ott/calendar/" })
};

export default function OttCalendarPage() {
  const published = parseOttFeed(rawCalendar);
  if (!published) throw new Error("The bundled OTT calendar failed source or window validation.");
  const paths = new Set([
    ...getAllSeries().map((item) => `/series/${item.slug}/`),
    ...getAllFilms().map((item) => `/${item.canonical_industry}/reviews/${item.slug}/`)
  ]);
  const catalogueLinks: Record<string, string> = {};
  for (const row of getOttCalendar().entries) {
    if (typeof row.url === "string" && paths.has(row.url)) catalogueLinks[`${row.type}:${row.title}`] = row.url;
  }
  return (
    <main className="page-shell" data-desk="streaming">
      <CurrentOttCalendar published={published} catalogueLinks={catalogueLinks} />
    </main>
  );
}
