import { notFound } from "next/navigation";
import { DayWiseTable } from "../../../../components/DayWiseTable";
import { DeskTint } from "../../../../components/DeskTint";
import { FilmHero } from "../../../../components/FilmHero";
import { JsonLd } from "../../../../components/JsonLd";
import { TrajectoryChart } from "../../../../components/TrajectoryChart";
import {
  filmBoxOfficeDatasetJsonLd,
  filmDayRowsItemListJsonLd
} from "../../../../lib/boxoffice";
import { formatCrore, getAllFilms, getFilm } from "../../../../lib/data";
import { getDesk } from "../../../../lib/desks";
import { pageSeo } from "../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllFilms().map((film) => ({
    desk: film.canonical_industry,
    slug: film.slug
  }));
}

export async function generateMetadata(props: { params: Promise<{ desk: string; slug: string }> }) {
  const params = await props.params;
  const film = getFilm(params.desk, params.slug);
  if (!film) return {};
  const filmTitle = film.title.value;
  const hasTotal = film.box_office.totals.india_net_inr_cr.value !== null;
  const title = hasTotal
    ? `${filmTitle} Box Office Collection - Day-wise India Nett`
    : `${filmTitle} Box Office - Tracking`;
  const totalStr = hasTotal
    ? `India nett: ${formatCrore(film.box_office.totals.india_net_inr_cr.value)} as of ${film.box_office.totals.as_of}.`
    : "India nett collection tracking - estimates awaited.";
  const raw = `${filmTitle} day-wise box office. ${totalStr} ${film.logline}`;
  const description = raw.slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/${params.desk}/box-office/${params.slug}/`, image: film.poster.src, type: "article" }) };
}

export default async function BoxOfficePage(props: { params: Promise<{ desk: string; slug: string }> }) {
  const params = await props.params;
  const film = getFilm(params.desk, params.slug);
  if (!film) {
    notFound();
  }

  const total = formatCrore(film.box_office.totals.india_net_inr_cr.value);
  const deskLabel = getDesk(film.canonical_industry)?.label ?? film.canonical_industry;

  return (
    <DeskTint desk={film.canonical_industry} className="film-page">
      <JsonLd data={filmBoxOfficeDatasetJsonLd(film)} />
      <JsonLd data={filmDayRowsItemListJsonLd(film)} />
      <FilmHero
        film={film}
        eyebrow="Day-wise box-office tracker"
        answer={`${film.title.value} is tracked at ${total} India nett as of ${film.box_office.totals.as_of}. Rows are sourced trade estimates, not fake-precise official numbers.`}
        showMeter={false}
      />
      <section className="content-sections">
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
            publish rule, BollyAI withholds the number and renders "early estimates awaited."
          </p>
        </section>
        <nav className="mesh-links" aria-label="Film page links">
          <a href={`/${film.canonical_industry}/reviews/${film.slug}/`}>Read our verdict</a>
          <a href={`/${film.canonical_industry}/upcoming/${film.slug}/`}>Pre-release buildup</a>
          <a href="/box-office/">Latest verified weekly board</a>
          <a href={`/${film.canonical_industry}/`}>Back to {deskLabel}</a>
        </nav>
      </section>
    </DeskTint>
  );
}
