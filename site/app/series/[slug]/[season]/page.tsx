import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../../components/AnswerBlock";
import { BollyMeter } from "../../../../components/BollyMeter";
import { CriticConsensus } from "../../../../components/CriticConsensus";
import { DateModified } from "../../../../components/DateModified";
import { DeskTint } from "../../../../components/DeskTint";
import { JsonLd } from "../../../../components/JsonLd";
import { SeasonVerdict } from "../../../../components/SeasonVerdict";
import { formatDate } from "../../../../lib/data";
import { getAllSeries, getSeries } from "../../../../lib/series";
import { breadcrumbJsonLd, seasonReviewJsonLd } from "../../../../lib/jsonld";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllSeries().flatMap((s) =>
    s.seasons.map((season) => ({ slug: s.slug, season: `s${season.number}` }))
  );
}

export default function SeasonPage({ params }: { params: { slug: string; season: string } }) {
  const series = getSeries(params.slug);
  if (!series) notFound();
  const num = Number(params.season.replace(/^s/, ""));
  const season = series.seasons.find((s) => s.number === num);
  if (!season) notFound();

  const review = seasonReviewJsonLd(series, season);

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      {review && <JsonLd data={review} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/series/" },
          { name: series.title.value, url: `/series/${series.slug}/` },
          { name: `Season ${season.number}`, url: `/series/${series.slug}/s${season.number}/` }
        ])}
      />

      <section className="film-hero" data-desk={series.canonical_industry}>
        <div className="poster-frame">
          <img src={series.poster.src} alt={series.poster.alt} width="342" height="513" fetchPriority="high" loading="eager" />
        </div>
        <div className="film-hero__copy">
          <p className="eyebrow">
            {series.title.value} · Season {season.number} · {series.platform.value}
          </p>
          <h1>
            {series.title.value} Season {season.number}
          </h1>
          <AnswerBlock>
            {season.verdict
              ? `${series.title.value} Season ${season.number} is a ${season.verdict}${season.bollymeter ? `, BollyMeter ${season.bollymeter.score.toFixed(1)}/10` : ""}. ${season.episodes} episodes on ${series.platform.value} from ${formatDate(season.release_date.value)}.`
              : `${series.title.value} Season ${season.number} is still dropping on ${series.platform.value}. BollyAI opens a verdict once the season finishes.`}
          </AnswerBlock>
          <SeasonVerdict rung={season.verdict} />
          {season.bollymeter && <BollyMeter score={season.bollymeter.score} basis={season.bollymeter.basis} />}
          <DateModified value={series.date_modified} />
        </div>
      </section>

      <section className="content-sections">
        <div className="ad-slot">Reserved ad slot</div>
        <section className="panel">
          <h2>What BollyAI Thinks</h2>
          <p>{season.review_body}</p>
          <p className="standing-line">
            BollyAI hasn&apos;t watched this. BollyAI has read everyone who has.
          </p>
        </section>

        <section className="panel">
          <h2>The Room</h2>
          <CriticConsensus season={season} />
        </section>

        {season.season_over_season && (
          <section className="panel">
            <h2>Season Over Season</h2>
            <p>{season.season_over_season}</p>
          </section>
        )}

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/`}>All seasons of {series.title.value}</a>
          <a href="/series/">Back to Series</a>
          <a href="/ott/calendar/">OTT calendar</a>
        </nav>
      </section>
    </DeskTint>
  );
}
