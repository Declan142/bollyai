import { notFound } from "next/navigation";
import { BollyMeter } from "../../../../components/BollyMeter";
import { DeskTint } from "../../../../components/DeskTint";
import { FilmHero } from "../../../../components/FilmHero";
import { JsonLd } from "../../../../components/JsonLd";
import { getAllFilms, getFilm } from "../../../../lib/data";
import { breadcrumbJsonLd, reviewJsonLd } from "../../../../lib/jsonld";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllFilms().map((film) => ({
    desk: film.canonical_industry,
    slug: film.slug
  }));
}

export default function ReviewPage({ params }: { params: { desk: string; slug: string } }) {
  const film = getFilm(params.desk, params.slug);
  if (!film) {
    notFound();
  }

  const reviewPath = `/${film.canonical_industry}/reviews/${film.slug}/`;

  return (
    <DeskTint desk={film.canonical_industry} className="film-page">
      <JsonLd data={reviewJsonLd(film)} />
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
        answer={`${film.title.value} is a BollyAI ${film.bollymeter.score.toFixed(1)}/10 with a ${film.verdict.ladder_rung} trade verdict. The score is a craft number, not a box-office cheer chant.`}
      />
      <section className="content-sections">
        <div className="ad-slot">Reserved ad slot</div>
        <section className="panel">
          <h2>What BollyAI Thinks</h2>
          <p>
            BollyAI hasn&apos;t watched this. BollyAI has read everyone who has, then weighed public reception,
            critic consensus, and the trade run separately. The verdict says what the money did; the BollyMeter says
            how the film plays as cinema.
          </p>
          <BollyMeter score={film.bollymeter.score} basis={film.bollymeter.basis} />
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
          <a href={`/${film.canonical_industry}/`}>Back to {film.canonical_industry}</a>
        </nav>
      </section>
    </DeskTint>
  );
}
