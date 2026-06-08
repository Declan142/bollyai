import { notFound } from "next/navigation";
import { DateModified } from "../../../components/DateModified";
import { DeskTint } from "../../../components/DeskTint";
import { JsonLd } from "../../../components/JsonLd";
import { breadcrumbJsonLd, watchListJsonLd, watchListFaqJsonLd } from "../../../lib/jsonld";
import { getAllWatchLists, getWatchList, pickHref } from "../../../lib/recommendations";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllWatchLists().map((l) => ({ slug: l.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }) {
  const list = getWatchList(params.slug);
  if (!list) return {};
  return { title: list.title, description: list.intro };
}

export default function WatchListPage({ params }: { params: { slug: string } }) {
  const list = getWatchList(params.slug);
  if (!list) notFound();
  const faqLd = watchListFaqJsonLd(list);

  return (
    <DeskTint desk={list.desk ?? "streaming"} className="film-page">
      <JsonLd data={watchListJsonLd(list)} />
      {faqLd && <JsonLd data={faqLd} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "What to Watch", url: "/watch/" },
          { name: list.title, url: `/watch/${list.slug}/` }
        ])}
      />

      <section className="section-head">
        <p className="eyebrow">{list.kicker}</p>
        <h1>{list.title}</h1>
        <p className="answer-block">{list.intro}</p>
        <DateModified value={list.updated} />
      </section>

      <section className="content-sections">
        <div className="ad-slot">Reserved ad slot</div>

        <ol className="pick-list">
          {list.picks.map((pick, i) => {
            const href = pickHref(pick);
            const inner = (
              <>
                <div className="pick-card__head">
                  <span className="pick-card__rank">{String(i + 1).padStart(2, "0")}</span>
                  <span className="pick-card__title">
                    {pick.title}
                    {pick.year ? <span className="pick-card__year"> ({pick.year})</span> : null}
                  </span>
                  {pick.bollymeter != null && (
                    <span className="pick-card__score">{pick.bollymeter.toFixed(1)}</span>
                  )}
                </div>
                <p className="pick-card__line">{pick.one_line}</p>
                <p className="pick-card__where">
                  <span className="pick-card__type">{pick.ref_type === "series" ? "Series" : "Film"}</span>
                  <span>Streaming on {pick.where}</span>
                  {href && <span className="pick-card__go">Read the verdict →</span>}
                </p>
              </>
            );
            return (
              <li className="pick-card" key={`${pick.slug ?? pick.title}-${i}`}>
                {href ? <a href={href} className="pick-card__link">{inner}</a> : inner}
              </li>
            );
          })}
        </ol>

        {list.faq && list.faq.length > 0 && (
          <section className="panel">
            <h2>Quick Answers</h2>
            <dl className="watch-faq">
              {list.faq.map((f, i) => (
                <div key={i}>
                  <dt>{f.q}</dt>
                  <dd>{f.a}</dd>
                </div>
              ))}
            </dl>
          </section>
        )}

        <p className="standing-line">BollyAI hasn&apos;t watched these. BollyAI has read everyone who has.</p>

        <nav className="mesh-links" aria-label="Watch links">
          <a href="/watch/">All watch lists</a>
          <a href="/series/">Series desk</a>
          <a href="/ott/calendar/">OTT calendar</a>
        </nav>
      </section>
    </DeskTint>
  );
}
