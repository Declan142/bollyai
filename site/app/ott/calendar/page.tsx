import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import { SectionHero } from "../../../components/SectionHero";
import { OttCalendarBoard } from "../../../components/OttCalendarBoard";
import { formatDate, getOttCalendar } from "../../../lib/data";
import { pageSeo } from "../../../lib/seo";

export const metadata = {
  title: "OTT Release Calendar - New on Netflix, Max, Disney+ & More",
  description:
    "Verified streaming release dates for Western films and series across Netflix, Prime Video, Disney+, Max, Apple TV+, Hulu, Paramount+ and Peacock.",
  ...pageSeo({ path: "/ott/calendar/" })
};

export default function OttCalendarPage() {
  const calendar = getOttCalendar();
  const platforms = Array.from(new Set(calendar.entries.map((entry) => entry.platform))).sort();
  // Freshness contract, evaluated at build time: when the tracked window has already
  // ended, say so instead of presenting an expired board as current. The daily-refresh
  // build keeps this honest within a day even when the calendar roll itself fails -
  // exactly the 2026-06-22..07-06 outage shape, where a June window served as live.
  const windowEnded = new Date().toISOString().slice(0, 10) > calendar.window.end;

  return (
    <main className="page-shell" data-desk="streaming">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          name: "BollyAI OTT calendar",
          numberOfItems: calendar.entries.length,
          itemListElement: calendar.entries.map((entry, index) => ({
            "@type": "ListItem",
            position: index + 1,
            item: {
              "@type": entry.type === "film" ? "Movie" : "TVSeries",
              name: entry.title
            }
          }))
        }}
      />

      <SectionHero
        eyebrow="Streaming desk · OTT Calendar"
        title="What lands on OTT, and when"
        lede={
          <>
            Verified release dates across every platform, each row carrying its source. No platform view counts,
            no guesses, just <b>dates BollyAI can stand behind.</b>
          </>
        }
        stats={[
          { value: String(calendar.entries.length), label: "Verified releases" },
          { value: String(platforms.length), label: "Platforms" },
          { value: `${formatDate(calendar.window.start)} - ${formatDate(calendar.window.end)}`, label: "Tracking window" }
        ]}
      >
        <DateModified value={calendar.generated_at} />
      </SectionHero>

      {windowEnded && (
        <p className="tracking-empty">
          This tracking window ended {formatDate(calendar.window.end)}. Every date below stays verified for its own
          window; the next calendar roll refreshes the board.
        </p>
      )}

      <OttCalendarBoard entries={calendar.entries} />
    </main>
  );
}
