import { AnswerBlock } from "../components/AnswerBlock";
import { DateModified } from "../components/DateModified";
import { FilmCard } from "../components/FilmCard";
import { JsonLd } from "../components/JsonLd";
import { DESKS } from "../lib/desks";
import { formatCrore, getAllFilms, getLatestModified } from "../lib/data";
import { webSiteJsonLd } from "../lib/jsonld";

export default function HomePage() {
  const films = getAllFilms();
  const lead = films[0];
  const latestModified = getLatestModified();

  return (
    <main className="page-shell" data-desk="bombay">
      <JsonLd data={webSiteJsonLd()} />
      <section className="section-head">
        <p className="eyebrow">Seven desks, one disclosed AI critic</p>
        <h1>BollyAI</h1>
        <AnswerBlock>
          BollyAI answers the live film question: hit, flop, where to watch, and what changed today. Every desk has equal weight, every number carries a source, and every verdict separates money from craft.
        </AnswerBlock>
        <DateModified value={latestModified} />
      </section>

      <section className="desk-strip" aria-label="BollyAI desks">
        {DESKS.map((desk) => (
          <a className="desk-tile" href={`/${desk.slug}/`} data-desk={desk.slug} key={desk.slug}>
            <strong>{desk.label}</strong>
            <span>{desk.answer}</span>
          </a>
        ))}
      </section>

      {lead && (
        <section className="home-lead" data-desk={lead.canonical_industry}>
          <a className="marquee-panel" href={`/${lead.canonical_industry}/box-office/${lead.slug}/`}>
            <img src={lead.poster.src} alt={lead.poster.alt} width="342" height="513" fetchPriority="high" loading="eager" />
            <span className="marquee-panel__copy">
              <span className="eyebrow">Today&apos;s big verdict</span>
              <h2>{lead.title.value}</h2>
              <span className="answer-block">
                {lead.verdict.ladder_rung ?? (lead.verdict.tracking ? "Tracking" : "Verdict open")} with{" "}
                {lead.box_office.totals.india_net_inr_cr?.value
                  ? `${formatCrore(lead.box_office.totals.india_net_inr_cr.value)} India nett tracked.`
                  : lead.box_office.totals.worldwide_gross_inr_cr?.value
                    ? `${formatCrore(lead.box_office.totals.worldwide_gross_inr_cr.value)} worldwide gross tracked.`
                    : "trade figures under verification."}
              </span>
            </span>
          </a>
          <div className="rail">
            {films.map((film) => (
              <FilmCard key={film.slug} film={film} type="box-office" />
            ))}
          </div>
        </section>
      )}

      <section className="content-sections">
        <div className="ad-slot">Reserved ad slot</div>
        <section>
          <h2>Fresh Reviews</h2>
          <div className="film-grid">
            {films.map((film) => (
              <FilmCard key={`review-${film.slug}`} film={film} type="review" />
            ))}
          </div>
        </section>
      </section>
    </main>
  );
}
