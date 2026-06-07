import { notFound } from "next/navigation";
import { DayWiseTable } from "../../../../components/DayWiseTable";
import { DeskTint } from "../../../../components/DeskTint";
import { FilmHero } from "../../../../components/FilmHero";
import { JsonLd } from "../../../../components/JsonLd";
import { TrajectoryChart } from "../../../../components/TrajectoryChart";
import { formatCrore, getAllFilms, getFilm } from "../../../../lib/data";
import { breadcrumbJsonLd, trackerFaqJsonLd } from "../../../../lib/jsonld";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllFilms().map((film) => ({
    desk: film.canonical_industry,
    slug: film.slug
  }));
}

export default function BoxOfficePage({ params }: { params: { desk: string; slug: string } }) {
  const film = getFilm(params.desk, params.slug);
  if (!film) {
    notFound();
  }

  const total = formatCrore(film.box_office.totals.india_net_inr_cr.value);

  return (
    <DeskTint desk={film.canonical_industry} className="film-page">
      <JsonLd data={trackerFaqJsonLd(film)} />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: film.canonical_industry, url: `/${film.canonical_industry}/` },
          { name: `${film.title.value} box office`, url: `/${film.canonical_industry}/box-office/${film.slug}/` }
        ])}
      />
      <FilmHero
        film={film}
        eyebrow="Day-wise box-office tracker"
        answer={`${film.title.value} is tracked at ${total} India nett as of ${film.box_office.totals.as_of}. Rows are sourced trade estimates, not fake-precise official numbers.`}
        showMeter={false}
      />
      <section className="content-sections">
        <div className="ad-slot">Reserved ad slot</div>
        <section className="panel">
          <h2>Day-wise India Nett</h2>
          <DayWiseTable rows={film.box_office.day_rows} />
        </section>
        <section className="panel">
          <h2>Trajectory</h2>
          <TrajectoryChart rows={film.box_office.day_rows} title={film.title.value} />
        </section>
        <section className="panel">
          <h2>Trade Framing</h2>
          <p>
            Trade estimates are cross-checked across independent sources when available. If sources drift beyond the
            publish rule, BollyAI withholds the number and renders “early estimates awaited.”
          </p>
        </section>
        <nav className="mesh-links" aria-label="Film page links">
          <a href={`/${film.canonical_industry}/reviews/${film.slug}/`}>Read our verdict</a>
          <a href={`/${film.canonical_industry}/upcoming/${film.slug}/`}>Pre-release buildup</a>
          <a href={`/${film.canonical_industry}/`}>Back to {film.canonical_industry}</a>
        </nav>
      </section>
    </DeskTint>
  );
}
