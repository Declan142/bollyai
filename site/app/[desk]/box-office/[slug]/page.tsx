import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../../components/AnswerBlock";
import { BoxOfficeBoardTable } from "../../../../components/BoxOfficeBoardTable";
import { DateModified } from "../../../../components/DateModified";
import { DayWiseTable } from "../../../../components/DayWiseTable";
import { DeskTint } from "../../../../components/DeskTint";
import { FilmHero } from "../../../../components/FilmHero";
import { JsonLd } from "../../../../components/JsonLd";
import { TrajectoryChart } from "../../../../components/TrajectoryChart";
import {
  boxOfficeDatasetJsonLd,
  boxOfficeRecordsItemListJsonLd,
  getBoxOfficeClubs,
  getBoxOfficeRecordForFilm,
  filmBoxOfficeDatasetJsonLd,
  filmDayRowsItemListJsonLd,
  getCurrentBoxOfficeBoard,
  getQualifiedClubsForRecord,
  getYearScoreboardParams,
  getYearScoreboardRecords,
  isYearSlug
} from "../../../../lib/boxoffice";
import { formatCrore, getAllFilms, getFilm } from "../../../../lib/data";
import type { DeskSlug } from "../../../../lib/desks";
import { getDesk } from "../../../../lib/desks";
import { pageSeo } from "../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  const filmParams = getAllFilms().map((film) => ({
    desk: film.canonical_industry,
    slug: film.slug
  }));
  const yearParams = getYearScoreboardParams().map((scoreboard) => ({
    desk: scoreboard.industry,
    slug: scoreboard.year
  }));
  return [...filmParams, ...yearParams];
}

export function generateMetadata({ params }: { params: { desk: string; slug: string } }) {
  if (isYearSlug(params.slug)) {
    const desk = getDesk(params.desk);
    if (!desk) return {};
    return {
      title: `${desk.label} Box Office ${params.slug} - Year Scoreboard`,
      description: `${desk.label} ${params.slug} box-office scoreboard with source-gated trade rows.`,
      ...pageSeo({ path: `/${params.desk}/box-office/${params.slug}/` })
    };
  }

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

export default function BoxOfficePage({ params }: { params: { desk: string; slug: string } }) {
  if (isYearSlug(params.slug)) {
    return <YearScoreboardPage desk={params.desk} year={params.slug} />;
  }

  const film = getFilm(params.desk, params.slug);
  if (!film) {
    notFound();
  }

  const total = formatCrore(film.box_office.totals.india_net_inr_cr.value);
  const boardRecord = getBoxOfficeRecordForFilm(film.canonical_industry, film.slug);
  const scoreboardYear = boardRecord?.week.start.slice(0, 4) ?? film.release_date.value.slice(0, 4);
  const clubLinks = boardRecord ? getQualifiedClubsForRecord(boardRecord) : [];
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

function YearScoreboardPage({ desk, year }: { desk: string; year: string }) {
  const deskMeta = getDesk(desk);
  if (!deskMeta) {
    notFound();
  }

  const board = getCurrentBoxOfficeBoard();
  const records = getYearScoreboardRecords(deskMeta.slug as DeskSlug, year);
  const clubs = getBoxOfficeClubs();
  const answer = `${deskMeta.label} ${year} ranks source-gated rows by verified India nett. Rows remain in tracking until the same renderer-side publish rule clears a figure.`;

  return (
    <DeskTint desk={deskMeta.slug} className="page-shell box-office-hub">
      <JsonLd
        data={boxOfficeDatasetJsonLd({
          name: `${deskMeta.label} box office ${year}`,
          description: `${deskMeta.label} ${year} box-office scoreboard with conservative trade publishing.`,
          url: `/${deskMeta.slug}/box-office/${year}/`,
          dateModified: board.generated_at,
          records
        })}
      />
      <JsonLd
        data={boxOfficeRecordsItemListJsonLd({
          name: `${deskMeta.label} ${year} box-office rows`,
          description: `${deskMeta.label} tracker rows for ${year}.`,
          records
        })}
      />
      <section className="section-head box-office-head">
        <p className="eyebrow">Year scoreboard</p>
        <h1>
          {deskMeta.label} Box Office {year}
        </h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={board.generated_at} />
      </section>

      <section className="panel bo-board-panel">
        <header className="bo-panel-head">
          <div>
            <p className="eyebrow">{deskMeta.industryName}</p>
            <h2>{year} Scoreboard</h2>
          </div>
          <span className="pill">Source-gated</span>
        </header>
        <BoxOfficeBoardTable
          records={records}
          emptyState={`No ${deskMeta.label} row has cleared the ${year} scoreboard yet.`}
          showIndustry={false}
        />
      </section>

      <nav className="mesh-links" aria-label="Scoreboard links">
        <a href="/box-office/">India box office hub</a>
        <a href={`/${deskMeta.slug}/`}>{deskMeta.label} desk</a>
        {clubs.map((club) => (
          <a href={`/box-office/${club.slug}/`} key={club.slug}>
            {club.label}
          </a>
        ))}
      </nav>
    </DeskTint>
  );
}
