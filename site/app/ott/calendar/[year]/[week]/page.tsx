import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../../../components/AnswerBlock";
import { DateModified } from "../../../../../components/DateModified";
import { JsonLd } from "../../../../../components/JsonLd";
import { DESKS } from "../../../../../lib/desks";
import {
  formatDate,
  formatShortDate,
  getOttCalendarArchiveParams,
  getOttCalendarWeek
} from "../../../../../lib/data";
import type { OttCalendarEntry, SourceRef } from "../../../../../lib/data";
import { pageSeo } from "../../../../../lib/seo";

const siteUrl = "https://bollyai.in";

export const dynamicParams = false;

export function generateStaticParams() {
  return getOttCalendarArchiveParams();
}

export function generateMetadata({ params }: { params: { year: string; week: string } }) {
  const page = getOttCalendarWeek(params.year, params.week);
  if (!page) return {};
  return {
    title: `OTT Releases ${page.week.iso_week} - Verified Streaming Calendar`,
    description: `Verified Western streaming releases for ${formatDate(page.week.start)} to ${formatDate(
      page.week.end
    )}, with source links for every date and platform claim.`,
    ...pageSeo({ path: `/ott/calendar/${params.year}/${params.week}/` })
  };
}

export default function OttCalendarArchivePage({ params }: { params: { year: string; week: string } }) {
  const page = getOttCalendarWeek(params.year, params.week);
  if (!page) {
    notFound();
  }

  const answer = `${page.week.iso_week} tracks ${page.entries.length} verified streaming drop${
    page.entries.length === 1 ? "" : "s"
  } across the tracked platforms from ${formatDate(page.week.start)} to ${formatDate(page.week.end)}.`;

  return (
    <main className="page-shell" data-desk="streaming">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          name: `BollyAI OTT calendar ${page.week.iso_week}`,
          numberOfItems: page.entries.length,
          itemListElement: page.entries.map((entry, index) => ({
            "@type": "ListItem",
            position: index + 1,
            item: {
              "@type": entry.type === "film" ? "Movie" : "TVSeries",
              name: entry.title,
              datePublished: entry.release_date,
              ...(entry.url ? { url: `${siteUrl}${entry.url}` } : {})
            }
          }))
        }}
      />
      <section className="section-head">
        <p className="eyebrow">Streaming desk</p>
        <h1>{page.week.iso_week}</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={page.generated_at} />
      </section>

      <section className="calendar-week" aria-labelledby={`week-${page.week.iso_week}`}>
        <div className="calendar-week__head">
          <div>
            <p className="eyebrow">{weekEyebrow(page.week)}</p>
            <h2 id={`week-${page.week.iso_week}`}>
              {formatDate(page.week.start)} to {formatDate(page.week.end)}
            </h2>
          </div>
          <a href="/ott/calendar/">Current calendar</a>
        </div>

        {page.entries.length > 0 ? (
          <div className="calendar-list">
            {page.entries.map((entry) => (
              <CalendarRow entry={entry} key={`${entry.id}-${entry.platform}-${entry.release_date}`} />
            ))}
          </div>
        ) : (
          <p className="tracking-empty">No verified OTT drop found for the tracked platforms in this week window.</p>
        )}
      </section>
    </main>
  );
}

function weekEyebrow(week: { start: string; end: string }): string {
  // Derived at build time. The stored week label froze whatever was true at regen time,
  // so every archive page said "This week" forever. Labels are presentation, not facts -
  // the stored dates stay authoritative, the wording follows the build clock.
  const today = new Date().toISOString().slice(0, 10);
  if (today > week.end) return "Archived week";
  if (today < week.start) return "Upcoming week";
  return "This week";
}

function CalendarRow({ entry }: { entry: OttCalendarEntry }) {
  const desk = DESKS.find((item) => item.slug === entry.industry);
  const title = entry.url ? <a href={entry.url}>{entry.title}</a> : entry.title;
  return (
    <article className="calendar-row calendar-row--weekly" data-desk={entry.industry}>
      <time dateTime={entry.release_date}>{formatShortDate(entry.release_date)}</time>
      <div className="calendar-row__main">
        <strong>{title}</strong>
        <span>
          {entry.type === "film" ? "Film" : "Series"} on {entry.platform}
        </span>
        <p className="calendar-row__verdict">{entry.verdict_line}</p>
      </div>
      <span className="pill">{entry.language.toUpperCase()}</span>
      <span className="pill">{desk?.label ?? entry.industry}</span>
      <span className="source-line">
        Sources: <SourceLinks sources={entry.sources} />
      </span>
    </article>
  );
}

function SourceLinks({ sources }: { sources: SourceRef[] }) {
  return (
    <>
      {sources.map((source, index) => (
        <span key={source.url}>
          {index > 0 ? ", " : ""}
          <a href={source.url} rel="noopener noreferrer" target="_blank">
            {source.name}
          </a>
        </span>
      ))}
    </>
  );
}
