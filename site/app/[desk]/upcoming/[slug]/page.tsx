import { notFound } from "next/navigation";
import { DeskTint } from "../../../../components/DeskTint";
import { FilmHero } from "../../../../components/FilmHero";
import { JsonLd } from "../../../../components/JsonLd";
import { getBoxOfficeRecordForFilm, getQualifiedClubsForRecord } from "../../../../lib/boxoffice";
import { formatDate, getAllFilms, getFilm } from "../../../../lib/data";
import { getDesk } from "../../../../lib/desks";
import { breadcrumbJsonLd } from "../../../../lib/jsonld";
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
  const title = `${filmTitle} Release Date, OTT & Pre-release Buzz`;
  const ottPart = film.ott?.platform.value
    ? `OTT: ${film.ott.platform.value}.`
    : "OTT date not confirmed yet.";
  const raw = `${filmTitle} release date, pre-release buildup, and ${ottPart} ${film.logline}`;
  const description = raw.slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description, ...pageSeo({ path: `/${params.desk}/upcoming/${params.slug}/`, image: film.poster.src, type: "article" }) };
}

export default function UpcomingPage({ params }: { params: { desk: string; slug: string } }) {
  const film = getFilm(params.desk, params.slug);
  if (!film) {
    notFound();
  }

  const boardRecord = getBoxOfficeRecordForFilm(film.canonical_industry, film.slug);
  const scoreboardYear = boardRecord?.week?.start.slice(0, 4) ?? film.release_date.value.slice(0, 4);
  const clubLinks = boardRecord ? getQualifiedClubsForRecord(boardRecord) : [];
  const deskLabel = getDesk(film.canonical_industry)?.label ?? film.canonical_industry;

  return (
    <DeskTint desk={film.canonical_industry} className="film-page">
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: film.canonical_industry, url: `/${film.canonical_industry}/` },
          { name: `${film.title.value} buildup`, url: `/${film.canonical_industry}/upcoming/${film.slug}/` }
        ])}
      />
      <FilmHero
        film={film}
        eyebrow="Upcoming and buildup archive"
        answer={`${film.title.value} released on ${formatDate(film.release_date.value)}. This durable buildup page keeps the pre-release trail and links to the review plus day-wise tracker.`}
        showMeter={false}
      />
      <section className="content-sections">
        <section className="panel">
          <h2>What Changed After Release</h2>
          <p>
            The buildup URL persists instead of being redirected. That keeps release-date intent intact while the review
            and tracker answer the post-release questions.
          </p>
        </section>
        <section className="panel">
          <h2>Where To Watch</h2>
          <p>
            {film.ott?.platform.value
              ? `${film.title.value} is listed for ${film.ott.platform.value} from a ${film.ott.source_type ?? "verified"} announcement. Source: ${film.ott.source_url ?? film.ott.platform.source}.`
              : "OTT availability is not confirmed yet."}
          </p>
        </section>
        <nav className="mesh-links" aria-label="Film page links">
          <a href={`/${film.canonical_industry}/reviews/${film.slug}/`}>Now reviewed</a>
          <a href={`/${film.canonical_industry}/box-office/${film.slug}/`}>Track box office</a>
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
