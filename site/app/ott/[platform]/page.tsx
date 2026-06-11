import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../components/AnswerBlock";
import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import { DESKS } from "../../../lib/desks";
import { formatDate, formatShortDate, getOttCalendar, getOttPlatforms, platformSlug } from "../../../lib/data";
import type { OttCalendarEntry, SourceRef } from "../../../lib/data";
import { pageSeo } from "../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getOttPlatforms().map((platform) => ({ platform: platformSlug(platform) }));
}

export function generateMetadata({ params }: { params: { platform: string } }) {
  const platform = getOttPlatforms().find((item) => platformSlug(item) === params.platform);
  if (!platform) return {};
  const title = `What to Watch on ${platform} India - New OTT Releases`;
  const description = `Verified ${platform} India OTT release dates from BollyAI, with source links for every date and platform claim.`
    .slice(0, 158)
    .replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/ott/${params.platform}/` }) };
}

export default function OttPlatformPage({ params }: { params: { platform: string } }) {
  const calendar = getOttCalendar();
  const platform = getOttPlatforms().find((item) => platformSlug(item) === params.platform);
  if (!platform) {
    notFound();
  }

  const entries = calendar.entries.filter((entry) => entry.platform === platform);
  const latest = entries.map((entry) => entry.fetched_at).sort().at(-1) ?? calendar.generated_at;
  const answer = entries.length
    ? `BollyAI is tracking ${entries.length} verified ${platform} OTT drop${
        entries.length === 1 ? "" : "s"
      } from ${formatDate(calendar.window.start)} to ${formatDate(calendar.window.end)}.`
    : `BollyAI is tracking ${platform} India, but no verified drop passed the official-source or two-trade-source gate for ${formatDate(
        calendar.window.start
      )} to ${formatDate(calendar.window.end)}.`;

  return (
    <main className="page-shell" data-desk="streaming">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: `${platform} OTT releases on BollyAI`,
          mainEntity: entries.map((entry) => ({
            "@type": entry.type === "film" ? "Movie" : "TVSeries",
            name: entry.title,
            ...(entry.qid ? { identifier: entry.qid } : {}),
            ...(entry.url ? { url: `https://bollyai.in${entry.url}` } : {})
          }))
        }}
      />
      <section className="section-head">
        <p className="eyebrow">Streaming desk</p>
        <h1>{platform}</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={latest} />
      </section>

      {entries.length > 0 ? (
        <section className="calendar-list">
          {entries.map((entry) => (
            <CalendarRow entry={entry} key={`${entry.id}-${entry.release_date}`} />
          ))}
        </section>
      ) : (
        <p className="tracking-empty">Tracking is active. Unverified single-source listings are withheld until a stronger source pair appears.</p>
      )}
    </main>
  );
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
