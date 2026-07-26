import { notFound } from "next/navigation";
import { DateModified } from "../../../components/DateModified";
import { DeskTint } from "../../../components/DeskTint";
import { JsonLd } from "../../../components/JsonLd";
import { RelatedSeries } from "../../../components/RelatedSeries";
import { TitleHero } from "../../../components/TitleHero";
import { BoxOfficeTable } from "../../../components/BoxOfficeTable";
import { VerdictReceipt } from "../../../components/VerdictReceipt";
import { EpisodeList } from "../../../components/EpisodeList";
import { formatDate } from "../../../lib/data";
import { getAllSeries, getSeries, latestSeason, peakSeason, qualifiesForWhereToWatch } from "../../../lib/series";
import { hasEnding } from "../../../lib/endings";
import { hasPrediction } from "../../../lib/predictions";
import { getExplainersForSlug } from "../../../lib/explainers";
import { breadcrumbJsonLd, seriesJsonLd, seriesFaq, seriesFaqJsonLd } from "../../../lib/jsonld";
import { ogImage, pageSeo } from "../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllSeries().map((s) => ({ slug: s.slug }));
}

export async function generateMetadata(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  if (!series) return {};
  const peak = peakSeason(series);
  const t = series.title.value;
  const score = peak?.bollymeter ? `, BollyMeter ${peak.bollymeter.score.toFixed(1)}/10` : "";
  const title = peak?.verdict
    ? `${t} Review: ${peak.verdict}${score}`
    : `${t} Review & Verdict - ${series.platform.value}`;
  const lead = peak?.verdict
    ? `Is ${t} worth watching? BollyAI verdict: ${peak.verdict}${score}. `
    : `${t} on ${series.platform.value}. `;
  const description = (lead + series.logline).slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/series/${params.slug}/`, image: ogImage(series.slug) ?? series.poster.src, type: "article" }) };
}

export default async function SeriesHub(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  if (!series) notFound();
  const latest = latestSeason(series);
  const peak = peakSeason(series);
  const faq = seriesFaq(series, peak);
  const faqLd = seriesFaqJsonLd(faq);

  // Standout-episode breakdowns surface for whichever season carries the richest set.
  const episodeSeason = [...series.seasons]
    .sort((a, b) => (b.episode_reviews?.length ?? 0) - (a.episode_reviews?.length ?? 0))[0];
  const standoutEpisodes = episodeSeason?.episode_reviews ?? [];
  const explainers = getExplainersForSlug(series.slug);

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={seriesJsonLd(series)} />
      {faqLd && <JsonLd data={faqLd} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/series/" },
          { name: series.title.value, url: `/series/${series.slug}/` }
        ])}
      />

      <TitleHero series={series} peak={peak} latest={latest} />

      <section className="content-sections">
        <BoxOfficeTable series={series} />

        <VerdictReceipt series={series} season={peak} />

        {standoutEpisodes.length > 0 && (
          <EpisodeList slug={series.slug} seasonNumber={episodeSeason.number} episodes={standoutEpisodes} />
        )}

        <section className="panel">
          <h2>Seasons</h2>
          <ol className="season-list">
            {[...series.seasons]
              .sort((a, b) => b.number - a.number)
              .map((s) => (
                <li key={s.number} className="season-row">
                  <a href={`/series/${series.slug}/s${s.number}/`}>
                    <span className="season-row__n">Season {s.number}</span>
                    <span className="season-row__meta">
                      {s.year} · {s.episodes} ep{s.episodes === 1 ? "" : "s"} · {formatDate(s.release_date.value)}
                    </span>
                    <span className="season-row__verdict">{s.verdict ?? "still dropping"}</span>
                  </a>
                </li>
              ))}
          </ol>
        </section>

        {qualifiesForWhereToWatch(series) && (
          <a className="ending-cta" href={`/series/${series.slug}/where-to-watch/`}>
            <span className="ending-cta__k">STREAM</span>
            <span>Where to watch {series.title.value} in India →</span>
          </a>
        )}

        {hasEnding(series.slug) && (
          <a className="ending-cta" href={`/series/${series.slug}/ending-explained/`}>
            <span className="ending-cta__k">SPOILERS</span>
            <span>How does {series.title.value} end? Read the ending explained →</span>
          </a>
        )}

        {hasPrediction(series.slug) && (
          <a className="ending-cta" href={`/series/${series.slug}/finale-predictions/`}>
            <span className="ending-cta__k">FINALE</span>
            <span>{series.title.value} finale: what could happen? BollyAI predictions →</span>
          </a>
        )}

        {explainers.length > 0 && (
          <section className="panel">
            <h2>{series.title.value}: All Articles</h2>
            <ul className="source-list">
              {explainers.map((e) => (
                <li key={e.topic}>
                  <a href={`/series/${series.slug}/explainer/${e.topic}/`}>{e.title}</a>
                </li>
              ))}
            </ul>
          </section>
        )}

        <section className="panel">
          <h2>{series.title.value} - Quick Answers</h2>
          <dl className="watch-faq">
            {faq.map((f) => (
              <div key={f.q}>
                <dt>{f.q}</dt>
                <dd>{f.a}</dd>
              </div>
            ))}
          </dl>
        </section>

        <DateModified value={series.date_modified} />

        <RelatedSeries slug={series.slug} />
      </section>
    </DeskTint>
  );
}
