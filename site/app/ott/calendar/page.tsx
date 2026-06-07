import { AnswerBlock } from "../../../components/AnswerBlock";
import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import { DESKS } from "../../../lib/desks";
import { formatDate, getOttCalendar } from "../../../lib/data";

export default function OttCalendarPage() {
  const calendar = getOttCalendar();
  const platforms = Array.from(new Set(calendar.entries.map((entry) => entry.platform))).sort();
  const answer = `BollyAI is tracking ${calendar.entries.length} verified OTT releases from ${formatDate(
    calendar.window.start
  )} to ${formatDate(calendar.window.end)} across ${platforms.length} platforms.`;

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
      <section className="section-head">
        <p className="eyebrow">Streaming desk</p>
        <h1>OTT Calendar</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={calendar.generated_at} />
      </section>

      <section className="calendar-list">
        {calendar.entries.map((entry) => {
          const desk = DESKS.find((item) => item.slug === entry.industry);
          return (
            <article className="calendar-row" data-desk={entry.industry} key={`${entry.title}-${entry.platform}-${entry.release_date}`}>
              <time dateTime={entry.release_date}>{formatDate(entry.release_date)}</time>
              <strong>{entry.title}</strong>
              <span className="pill">{entry.platform}</span>
              <span className="pill">{desk?.label ?? entry.industry}</span>
              <span className="source-line">
                Source: <a href={entry.source_url}>{entry.source_url}</a> ({entry.source_type})
              </span>
            </article>
          );
        })}
      </section>
      <div className="ad-slot">Reserved ad slot</div>
    </main>
  );
}
