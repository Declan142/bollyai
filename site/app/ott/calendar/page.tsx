import { AnswerBlock } from "../../../components/AnswerBlock";
import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import { DESKS } from "../../../lib/desks";
import { formatDate, formatShortDate, getOttCalendar } from "../../../lib/data";
import type { OttCalendarEntry, OttWeek, SourceRef } from "../../../lib/data";
import { pageSeo } from "../../../lib/seo";

const siteUrl = "https://bollyai.in";

export const metadata = {
  title: "OTT Release Calendar India - This Week and Next Week",
  description:
    "Verified India OTT release dates for Netflix, Prime Video, JioHotstar, ZEE5, SonyLIV and aha, grouped by week with source links.",
  ...pageSeo({ path: "/ott/calendar/" })
};

export default function OttCalendarPage() {
  const calendar = getOttCalendar();
  const answer = `BollyAI is tracking ${calendar.entries.length} verified OTT drop${
    calendar.entries.length === 1 ? "" : "s"
  } for India from ${formatDate(calendar.window.start)} to ${formatDate(calendar.window.end)}. Single-source trade claims stay off this page.`;

  return (
    <main className="page-shell" data-desk="streaming">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          name: "BollyAI OTT calendar India",
          numberOfItems: calendar.entries.length,
          itemListElement: calendar.entries.map((entry, index) => ({
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
        <h1>OTT Calendar</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={calendar.generated_at} />
      </section>

      <PlatformTracker platforms={calendar.tracking.platforms} entries={calendar.entries} />

      <section className="calendar-weeks" aria-label="Weekly OTT release sections">
        {calendar.weeks.map((week) => (
          <WeekSection key={week.iso_week} week={week} entries={calendar.entries.filter((entry) => entry.week === week.iso_week)} />
        ))}
      </section>
    </main>
  );
}

function PlatformTracker({ platforms, entries }: { platforms: string[]; entries: OttCalendarEntry[] }) {
  return (
    <section className="platform-tracker" aria-label="Tracked OTT platforms">
      {platforms.map((platform) => {
        const count = entries.filter((entry) => entry.platform === platform).length;
        return (
          <a className="platform-chip" href={`/ott/${platformSlug(platform)}/`} key={platform}>
            <span>{platform}</span>
            <strong>{count ? `${count} verified` : "tracking"}</strong>
          </a>
        );
      })}
    </section>
  );
}

function WeekSection({ week, entries }: { week: OttWeek; entries: OttCalendarEntry[] }) {
  return (
    <section className="calendar-week" aria-labelledby={`week-${week.iso_week}`}>
      <div className="calendar-week__head">
        <div>
          <p className="eyebrow">{week.iso_week}</p>
          <h2 id={`week-${week.iso_week}`}>{week.label}</h2>
          <p>
            {formatDate(week.start)} to {formatDate(week.end)}
          </p>
        </div>
        <a href={week.archive_url}>Week archive</a>
      </div>

      {entries.length > 0 ? (
        <div className="calendar-list">
          {entries.map((entry) => (
            <CalendarRow entry={entry} key={`${entry.id}-${entry.platform}-${entry.release_date}`} />
          ))}
        </div>
      ) : (
        <p className="tracking-empty">No verified OTT drop found for the tracked platforms in this week window.</p>
      )}
    </section>
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

function platformSlug(platform: string): string {
  return platform
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-|-$/g, "");
}
