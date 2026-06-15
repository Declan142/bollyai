import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import { SectionHero } from "../../../components/SectionHero";
import { OttCalendarBoard } from "../../../components/OttCalendarBoard";
import { formatDate, getOttCalendar } from "../../../lib/data";
import { pageSeo } from "../../../lib/seo";

export const metadata = {
  title: "OTT Release Calendar India - Upcoming Movies & Series",
  description:
    "Verified OTT release dates for Indian movies and series across Netflix, JioHotstar, SonyLIV, ZEE5, Prime Video and more.",
  ...pageSeo({ path: "/ott/calendar/" })
};

export default function OttCalendarPage() {
  const calendar = getOttCalendar();
  const platforms = Array.from(new Set(calendar.entries.map((entry) => entry.platform))).sort();

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

      <OttCalendarBoard entries={calendar.entries} />
    </main>
  );
}
