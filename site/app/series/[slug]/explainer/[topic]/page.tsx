import { notFound } from "next/navigation";
import { DeskTint } from "../../../../../components/DeskTint";
import { JsonLd } from "../../../../../components/JsonLd";
import { DateModified } from "../../../../../components/DateModified";
import { getSeries } from "../../../../../lib/series";
import { getAllExplainerParams, getExplainer, getExplainersForSlug } from "../../../../../lib/explainers";
import { breadcrumbJsonLd, explainerArticleJsonLd, explainerFaqJsonLd } from "../../../../../lib/jsonld";
import { pageSeo } from "../../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllExplainerParams().filter((p) => getSeries(p.slug));
}

export async function generateMetadata(props: { params: Promise<{ slug: string; topic: string }> }) {
  const params = await props.params;
  const explainer = getExplainer(params.slug, params.topic);
  const series = getSeries(params.slug);
  if (!explainer || !series) return {};
  const description = explainer.hook.slice(0, 158).replace(/\s+\S*$/, "");
  return {
    title: explainer.title,
    description,
    ...pageSeo({
      path: `/series/${params.slug}/explainer/${params.topic}/`,
      image: series.poster.src,
      type: "article"
    })
  };
}

export default async function ExplainerPage(props: { params: Promise<{ slug: string; topic: string }> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  const explainer = getExplainer(params.slug, params.topic);
  if (!series || !explainer) notFound();

  const faqLd = explainerFaqJsonLd(explainer);
  const peers = getExplainersForSlug(params.slug).filter((e) => e.topic !== params.topic);
  const related = explainer.related
    .map((t) => peers.find((p) => p.topic === t))
    .filter(Boolean) as typeof peers;

  const kindLabel: Record<string, string> = {
    explainer: "Explainer",
    theory: "Theory",
    guide: "Guide",
    character: "Character"
  };

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={explainerArticleJsonLd(series, explainer)} />
      {faqLd && <JsonLd data={faqLd} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/series/" },
          { name: series.title.value, url: `/series/${series.slug}/` },
          { name: explainer.title, url: `/series/${series.slug}/explainer/${explainer.topic}/` }
        ])}
      />

      <section className="film-hero" data-desk={series.canonical_industry}>
        <div className="film-hero__copy film-hero__copy--full">
          <p className="eyebrow">
            {series.title.value} · {kindLabel[explainer.kind] ?? explainer.kind}
          </p>
          <h1>{explainer.title}</h1>
          <p className="answer-block">{explainer.hook}</p>
          <DateModified value={explainer.date_modified} />
        </div>
      </section>

      <section className="content-sections">
        {explainer.spoiler && (
          <aside className="spoiler-gate" role="note">
            <strong>Spoilers ahead for aired episodes.</strong> BollyAI has not watched this.
            BollyAI has read everyone who has. All analysis is sourced from the published record.
          </aside>
        )}

        {explainer.sections.map((sec) => (
          <section className="panel" key={sec.heading}>
            <h2>{sec.heading}</h2>
            <p>{sec.body}</p>
          </section>
        ))}

        {explainer.faq.length > 0 && (
          <section className="panel">
            <h2>Quick Answers</h2>
            <dl className="watch-faq">
              {explainer.faq.map((f) => (
                <div key={f.q}>
                  <dt>{f.q}</dt>
                  <dd>{f.a}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        {explainer.sources.length > 0 && (
          <section className="panel">
            <h2>Sources</h2>
            <ul className="source-list">
              {explainer.sources.map((s, i) => (
                <li key={`${i}-${s.url}`}>
                  <a href={s.url} rel="nofollow noopener" target="_blank">
                    {s.text}
                  </a>
                </li>
              ))}
            </ul>
            <p className="standing-line">
              BollyAI has not watched this. BollyAI has read everyone who has.
              All theories and analysis are BollyAI editorial unless otherwise cited.
            </p>
          </section>
        )}

        {related.length > 0 && (
          <section className="panel">
            <h2>More {series.title.value} Articles</h2>
            <ul className="source-list">
              {related.map((r) => (
                <li key={r.topic}>
                  <a href={`/series/${series.slug}/explainer/${r.topic}/`}>{r.title}</a>
                </li>
              ))}
            </ul>
          </section>
        )}

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/`}>All about {series.title.value}</a>
          <a href="/series/">Back to Series</a>
        </nav>
      </section>
    </DeskTint>
  );
}
