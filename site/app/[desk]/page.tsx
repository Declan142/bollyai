import { notFound } from "next/navigation";
import { AnswerBlock } from "../../components/AnswerBlock";
import { DateModified } from "../../components/DateModified";
import { DeskTint } from "../../components/DeskTint";
import { FilmCard } from "../../components/FilmCard";
import { DESK_SLUGS, getDesk } from "../../lib/desks";
import { getFilmsByDesk, getLatestModified } from "../../lib/data";
import { pageSeo } from "../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return DESK_SLUGS.map((desk) => ({ desk }));
}

export async function generateMetadata(props: { params: Promise<{ desk: string }> }) {
  const params = await props.params;
  const desk = getDesk(params.desk);
  if (!desk) return {};
  const title = `${desk.label} Movie Reviews, Box Office & Verdicts`;
  const description = desk.answer.slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/${params.desk}/` }) };
}

export default async function DeskHub(props: { params: Promise<{ desk: string }> }) {
  const params = await props.params;
  const desk = getDesk(params.desk);
  if (!desk) {
    notFound();
  }

  const films = getFilmsByDesk(params.desk);
  const lead = films[0];

  return (
    <DeskTint desk={desk.slug} className="page-shell">
      <section className="section-head">
        <p className="eyebrow">{desk.industryName}</p>
        <h1>{desk.label}</h1>
        <AnswerBlock>{desk.answer}</AnswerBlock>
        <DateModified value={lead?.date_modified ?? getLatestModified()} />
      </section>

      {lead ? (
        <section className="hub-layout">
          <a className="marquee-panel" href={`/${lead.canonical_industry}/reviews/${lead.slug}/`}>
            <img src={lead.poster.src} alt={lead.poster.alt} width="342" height="513" fetchPriority="high" loading="eager" />
            <span className="marquee-panel__copy">
              <span className="eyebrow">Lead verdict</span>
              <h2>{lead.title.value}</h2>
              <span className="answer-block">
                {lead.verdict.ladder_rung ? `${lead.verdict.ladder_rung} trade verdict` : "Tracking, verdict open"}
                {lead.bollymeter ? `, BollyMeter ${lead.bollymeter.score.toFixed(1)}/10.` : ". Review reading the room."}
              </span>
            </span>
          </a>
          <div className="rail">
            {films.map((film) => (
              <FilmCard key={film.slug} film={film} type="box-office" />
            ))}
          </div>
        </section>
      ) : (
        <section className="panel">
          <h2>Desk warming up</h2>
          <p>This desk is live as a pillar; fixture films will appear here once the engine publishes them.</p>
        </section>
      )}
    </DeskTint>
  );
}
