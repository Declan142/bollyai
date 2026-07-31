import { notFound } from "next/navigation";
import { DeskTint } from "../../../../components/DeskTint";
import { JsonLd } from "../../../../components/JsonLd";
import { DateModified } from "../../../../components/DateModified";
import { getSeries } from "../../../../lib/series";
import { getAllEndings, getEnding } from "../../../../lib/endings";
import { breadcrumbJsonLd, endingArticleJsonLd, endingFaqJsonLd } from "../../../../lib/jsonld";
import { pageSeo } from "../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  // Only build a page where BOTH the ending file and its series exist.
  return getAllEndings()
    .filter((e) => getSeries(e.slug))
    .map((e) => ({ slug: e.slug }));
}

export async function generateMetadata(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const ending = getEnding(params.slug);
  const series = getSeries(params.slug);
  if (!ending || !series) return {};
  const t = series.title.value;
  const title = `${t} Ending Explained - How Does It End?`;
  const description = ending.hook.slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/series/${params.slug}/ending-explained/`, image: series.poster.src, type: "article" }) };
}

export default async function EndingExplainedPage(props: { params: Promise<{ slug: string }> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  const ending = getEnding(params.slug);
  if (!series || !ending) notFound();

  const faqLd = endingFaqJsonLd(ending);

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={endingArticleJsonLd(series, ending)} />
      {faqLd && <JsonLd data={faqLd} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/browse/" },
          { name: series.title.value, url: `/series/${series.slug}/` },
          { name: "Ending Explained", url: `/series/${series.slug}/ending-explained/` }
        ])}
      />

      <section className="film-hero" data-desk={series.canonical_industry}>
        <div className="film-hero__copy film-hero__copy--full">
          <p className="eyebrow">
            {series.title.value} · Season {ending.season_number} · Ending Explained
          </p>
          <h1>{series.title.value}: Ending Explained</h1>
          <p className="answer-block">{ending.hook}</p>
          <DateModified value={ending.date_modified} />
        </div>
      </section>

      <section className="content-sections">
        <aside className="spoiler-gate" role="note">
          <strong>⚠ Full spoilers ahead.</strong> This page explains how {series.title.value}{" "}
          ends, including the Season {ending.season_number} finale. BollyAI hasn&apos;t watched
          this - this walkthrough is read off the published record, sourced below.
        </aside>

        {ending.sections.map((sec) => (
          <section className="panel" key={sec.heading}>
            <h2>{sec.heading}</h2>
            <p>{sec.body}</p>
          </section>
        ))}

        {ending.final_image && (
          <section className="panel">
            <h2>The Final Image</h2>
            <p>{ending.final_image}</p>
          </section>
        )}

        {ending.lingering_questions && ending.lingering_questions.length > 0 && (
          <section className="panel">
            <h2>Lingering Questions</h2>
            <dl className="watch-faq">
              {ending.lingering_questions.map((q) => (
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
            {ending.sources.map((s) => (
              <li key={s.url}>
                <a href={s.url} rel="nofollow noopener" target="_blank">
                  {s.title}
                </a>
              </li>
            ))}
          </ul>
          <p className="standing-line">
            BollyAI hasn&apos;t watched this. BollyAI has read everyone who has.
          </p>
        </section>

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/`}>All seasons of {series.title.value}</a>
          <a href={`/series/${series.slug}/s${ending.season_number}/`}>
            Season {ending.season_number} review
          </a>
          <a href="/browse/">Back to Series</a>
        </nav>
      </section>
    </DeskTint>
  );
}
