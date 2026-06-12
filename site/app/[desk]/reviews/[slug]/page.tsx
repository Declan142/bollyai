import { notFound } from "next/navigation";
import { BollyMeter } from "../../../../components/BollyMeter";
import { DeskTint } from "../../../../components/DeskTint";
import { FilmHero } from "../../../../components/FilmHero";
import { JsonLd } from "../../../../components/JsonLd";
import { getBoxOfficeRecordForFilm, getQualifiedClubsForRecord } from "../../../../lib/boxoffice";
import { getAllFilms, getFilm } from "../../../../lib/data";
import { getDesk } from "../../../../lib/desks";
import { breadcrumbJsonLd, reviewJsonLd } from "../../../../lib/jsonld";
import { pageSeo } from "../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllFilms().map((film) => ({
    desk: film.canonical_industry,
    slug: film.slug
  }));
}

export function generateMetadata({ params }: { params: { desk: string; slug: string } }) {
  const film = getFilm(params.desk, params.slug);
  if (!film) return {};
  const filmTitle = film.title.value;
  const rung = film.verdict.ladder_rung;
  const score = film.bollymeter ? film.bollymeter.score.toFixed(1) : null;
  const title = rung && score
    ? `${filmTitle} Review: ${rung}, BollyMeter ${score}/10`
    : rung
    ? `${filmTitle} Review: ${rung} Trade Verdict`
    : score
    ? `${filmTitle} Review: BollyMeter ${score}/10`
    : `${filmTitle} Review - Verdict Tracking`;
  const verdictPart = rung
    ? `Verdict: ${rung}${score ? `, BollyMeter ${score}/10` : ""}.`
    : score
    ? `BollyMeter ${score}/10, verdict still open.`
    : "Verdict tracking, run not closed yet.";
  const raw = `Is ${filmTitle} worth watching? ${verdictPart} ${film.logline}`;
  const description = raw.slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/${params.desk}/reviews/${params.slug}/`, image: film.poster.src, type: "article" }) };
}

export default function ReviewPage({ params }: { params: { desk: string; slug: string } }) {
  const film = getFilm(params.desk, params.slug);
  if (!film) {
    notFound();
  }

  const reviewPath = `/${film.canonical_industry}/reviews/${film.slug}/`;
  const boardRecord = getBoxOfficeRecordForFilm(film.canonical_industry, film.slug);
  const scoreboardYear = boardRecord?.week.start.slice(0, 4) ?? film.release_date.value.slice(0, 4);
  const clubLinks = boardRecord ? getQualifiedClubsForRecord(boardRecord) : [];
  const deskLabel = getDesk(film.canonical_industry)?.label ?? film.canonical_industry;

  return (
    <DeskTint desk={film.canonical_industry} className="film-page">
      {(() => {
        const review = reviewJsonLd(film);
        return review ? <JsonLd data={review} /> : null;
      })()}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: film.canonical_industry, url: `/${film.canonical_industry}/` },
          { name: `${film.title.value} review`, url: reviewPath }
        ])}
      />
      <FilmHero
        film={film}
        eyebrow="Review"
        answer={
          film.bollymeter
            ? `${film.title.value} is a BollyAI ${film.bollymeter.score.toFixed(1)}/10 with a ${film.verdict.ladder_rung ?? "still-tracking"} trade verdict. The score is a craft number, not a box-office cheer chant.`
            : `${film.title.value} is still in its run. BollyAI is reading the room before scoring it, and the trade verdict stays open until the run ends.`
        }
      />
      <section className="content-sections">
        <section className="panel">
          <h2>What BollyAI Thinks</h2>
          <p>
            BollyAI hasn&apos;t watched this. BollyAI has read everyone who has, then weighed public reception,
            critic consensus, and the trade run separately. The verdict says what the money did; the BollyMeter says
            how the film plays as cinema.
          </p>
          {film.bollymeter ? (
            <BollyMeter score={film.bollymeter.score} basis={film.bollymeter.basis} />
          ) : (
            <p className="answer-block">BollyMeter pending. The room is still talking; the score lands when the reading is honest.</p>
          )}
        </section>
        <section className="panel">
          <h2>Source-Led Verdict</h2>
          <p>{film.logline}</p>
          <p>
            Budget: <strong>undisclosed</strong>. BollyAI only renders budgets with a cited first-party source, so
            speculative budget chatter stays off the page.
          </p>
        </section>
        <nav className="mesh-links" aria-label="Film page links">
          <a href={`/${film.canonical_industry}/box-office/${film.slug}/`}>Live box-office tracker</a>
          <a href={`/${film.canonical_industry}/upcoming/${film.slug}/`}>Pre-release buildup</a>
          <a href={`/${film.canonical_industry}/box-office/${scoreboardYear}/`}>{deskLabel} {scoreboardYear} scoreboard</a>
          {clubLinks.map((club) => (
            <a href={`/box-office/${club.slug}/`} key={club.slug}>
              {club.label}
            </a>
          ))}
          <a href={`/${film.canonical_industry}/`}>Back to {deskLabel}</a>
        </nav>
      </section>
    </DeskTint>
  );
}
