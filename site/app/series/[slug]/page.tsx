import { notFound } from "next/navigation";
import { DateModified } from "../../../components/DateModified";
import { DeskTint } from "../../../components/DeskTint";
import { JsonLd } from "../../../components/JsonLd";
import { SeasonVerdict } from "../../../components/SeasonVerdict";
import { AnswerBlock } from "../../../components/AnswerBlock";
import { formatDate } from "../../../lib/data";
import { getAllSeries, getSeries, latestSeason, peakSeason } from "../../../lib/series";
import { hasEnding } from "../../../lib/endings";
import { breadcrumbJsonLd, seriesJsonLd, seriesFaq, seriesFaqJsonLd } from "../../../lib/jsonld";
import { pageSeo } from "../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllSeries().map((s) => ({ slug: s.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }) {
  const series = getSeries(params.slug);
  if (!series) return {};
  const peak = peakSeason(series);
  const t = series.title.value;
  const score = peak?.bollymeter ? `, BollyMeter ${peak.bollymeter.score.toFixed(1)}/10` : "";
  const title = peak?.verdict
    ? `${t} Review: ${peak.verdict}${score}`
    : `${t} Review & Verdict — ${series.platform.value}`;
  const lead = peak?.verdict
    ? `Is ${t} worth watching? BollyAI verdict: ${peak.verdict}${score}. `
    : `${t} on ${series.platform.value}. `;
  const description = (lead + series.logline).slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/series/${params.slug}/`, image: series.poster.src, type: "article" }) };
}

export default function SeriesHub({ params }: { params: { slug: string } }) {
  const series = getSeries(params.slug);
  if (!series) notFound();
  const latest = latestSeason(series);
  const faq = seriesFaq(series, peakSeason(series));
  const faqLd = seriesFaqJsonLd(faq);

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

      <section className="film-hero" data-desk={series.canonical_industry}>
        <div className="poster-frame">
          <img src={series.poster.src} alt={series.poster.alt} width="342" height="513" fetchPriority="high" loading="eager" />
        </div>
        <div className="film-hero__copy">
          <p className="eyebrow">{series.origin} · {series.platform.value}</p>
          <h1>{series.title.value}</h1>
          <AnswerBlock>
            {latest
              ? `${series.title.value} ${latest.verdict ? `is a ${latest.verdict}` : "is still dropping"} on ${series.platform.value}${latest.bollymeter ? `, BollyMeter ${latest.bollymeter.score.toFixed(1)}/10` : ""}. ${series.logline}`
              : series.logline}
          </AnswerBlock>
          {latest && <SeasonVerdict rung={latest.verdict} />}
          <p className="renewal-line">
            <strong>Renewal:</strong> {series.renewal.note}{" "}
            <a href={series.renewal.source_url}>({series.renewal.source})</a>
          </p>
          <DateModified value={series.date_modified} />
        </div>
      </section>

      <section className="content-sections">
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

        {hasEnding(series.slug) && (
          <a className="ending-cta" href={`/series/${series.slug}/ending-explained/`}>
            <span className="ending-cta__k">SPOILERS</span>
            <span>How does {series.title.value} end? Read the ending explained →</span>
          </a>
        )}

        <section className="panel">
          <h2>{series.title.value} — Quick Answers</h2>
          <dl className="watch-faq">
            {faq.map((f) => (
              <div key={f.q}>
                <dt>{f.q}</dt>
                <dd>{f.a}</dd>
              </div>
            ))}
          </dl>
        </section>
      </section>
    </DeskTint>
  );
}
