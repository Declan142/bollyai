import { notFound } from "next/navigation";
import { DeskTint } from "../../../../components/DeskTint";
import { JsonLd } from "../../../../components/JsonLd";
import { DateModified } from "../../../../components/DateModified";
import { getSeries } from "../../../../lib/series";
import { getAllPredictions, getPrediction } from "../../../../lib/predictions";
import { breadcrumbJsonLd, predictionArticleJsonLd, predictionFaqJsonLd } from "../../../../lib/jsonld";
import { pageSeo } from "../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllPredictions()
    .filter((p) => getSeries(p.slug))
    .map((p) => ({ slug: p.slug }));
}

export async function generateMetadata(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const prediction = getPrediction(params.slug);
  const series = getSeries(params.slug);
  if (!prediction || !series) return {};
  const t = series.title.value;
  const title = `${t}: Season ${prediction.season_number} Finale Predictions & Theories`;
  const description = prediction.hook.slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/series/${params.slug}/finale-predictions/`, image: series.poster.src, type: "article" }) };
}

export default async function FinalePredictionsPage(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  const prediction = getPrediction(params.slug);
  if (!series || !prediction) notFound();

  const faqLd = predictionFaqJsonLd(prediction);

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={predictionArticleJsonLd(series, prediction)} />
      {faqLd && <JsonLd data={faqLd} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/series/" },
          { name: series.title.value, url: `/series/${series.slug}/` },
          { name: "Finale Predictions", url: `/series/${series.slug}/finale-predictions/` }
        ])}
      />

      <section className="film-hero" data-desk={series.canonical_industry}>
        <div className="film-hero__copy film-hero__copy--full">
          <p className="eyebrow">
            {series.title.value} · Season {prediction.season_number} · Finale Predictions
          </p>
          <h1>{series.title.value} Season {prediction.season_number}: Finale Predictions & Theories</h1>
          <p className="answer-block">{prediction.hook}</p>
          <DateModified value={prediction.date_modified} />
        </div>
      </section>

      <section className="content-sections">
        <aside className="spoiler-gate" role="note">
          <strong>BollyAI analysis ahead.</strong> These are theories and predictions grounded in
          what Episode {prediction.season_number > 1 ? "9" : "9"} set up, not confirmed plot
          points. BollyAI has not watched this - analysis is read off the published record,
          sourced below.
        </aside>

        {prediction.sections.map((sec) => (
          <section className="panel" key={sec.heading}>
            <h2>{sec.heading}</h2>
            <p>{sec.body}</p>
          </section>
        ))}

        {prediction.theories.length > 0 && (
          <section className="panel">
            <h2>Finale Theories</h2>
            <dl className="watch-faq">
              {prediction.theories.map((t) => (
                <div key={t.title}>
                  <dt>{t.title}</dt>
                  <dd>
                    <strong>Setup:</strong> {t.basis}
                    {" "}
                    <strong>Likelihood:</strong> {t.likelihood}
                  </dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        {prediction.lingering_questions && prediction.lingering_questions.length > 0 && (
          <section className="panel">
            <h2>Quick Answers</h2>
            <dl className="watch-faq">
              {prediction.lingering_questions.map((q) => (
                <div key={q.q}>
                  <dt>{q.q}</dt>
                  <dd>{q.a}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        <section className="panel">
          <h2>Sources</h2>
          <ul className="source-list">
            {prediction.sources.map((s) => (
              <li key={s.url}>
                <a href={s.url} rel="nofollow noopener" target="_blank">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
          <p className="standing-line">
            BollyAI has not watched this. BollyAI has read everyone who has.
            All theories are BollyAI analysis unless otherwise cited.
          </p>
        </section>

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/`}>All seasons of {series.title.value}</a>
          <a href={`/series/${series.slug}/s${prediction.season_number}/`}>
            Season {prediction.season_number} review
          </a>
          <a href="/series/">Back to Series</a>
        </nav>
      </section>
    </DeskTint>
  );
}
