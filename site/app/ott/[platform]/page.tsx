import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../components/AnswerBlock";
import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import { formatDate, getOttCalendar, getOttPlatforms, platformSlug } from "../../../lib/data";
import { pageSeo } from "../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getOttPlatforms().map((platform) => ({ platform: platformSlug(platform) }));
}

export async function generateMetadata(props: { params: Promise<{ platform: string }> }) {
  const params = await props.params;
  const platform = getOttPlatforms().find((item) => platformSlug(item) === params.platform);
  if (!platform) return {};
  const title = `What to Watch on ${platform} - New Releases & Verdicts`;
  const description = `Upcoming and new ${platform} releases - verified Western streaming dates, film and series announcements, and BollyAI verdicts.`
    .slice(0, 158)
    .replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/ott/${params.platform}/` }) };
}

export default async function OttPlatformPage(props: { params: Promise<{ platform: string }> }) {
  const params = await props.params;
  const calendar = getOttCalendar();
  const platform = getOttPlatforms().find((item) => platformSlug(item) === params.platform);
  if (!platform) {
    notFound();
  }

  const entries = calendar.entries.filter((entry) => entry.platform === platform);
  const latest = entries.map((entry) => entry.fetched_at).sort().at(-1) ?? calendar.generated_at;
  const answer = `BollyAI is tracking ${entries.length} attributed ${platform} OTT announcement${
    entries.length === 1 ? "" : "s"
  } in the ${formatDate(calendar.window.start)} to ${formatDate(calendar.window.end)} tracking window.`;

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
            identifier: entry.qid,
            datePublished: entry.release_date
          }))
        }}
      />
      <section className="section-head">
        <p className="eyebrow">Streaming desk</p>
        <h1>{platform}</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={latest} />
      </section>

      <section className="calendar-list">
        {entries.map((entry) => (
          <article className="calendar-row" data-desk={entry.industry} key={`${entry.qid}-${entry.release_date}`}>
            <time dateTime={entry.release_date}>{formatDate(entry.release_date)}</time>
            <strong>{entry.title}</strong>
            <span className="pill">{entry.language.toUpperCase()}</span>
            <span className="pill">{entry.source_type}</span>
            <span className="source-line">
              Source: <a href={entry.source_url}>{entry.source_url}</a>
            </span>
          </article>
        ))}
      </section>
    </main>
  );
}
