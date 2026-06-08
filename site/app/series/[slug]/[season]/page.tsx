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
import { breadcrumbJsonLd, seasonReviewJsonLd, episodeReviewsJsonLd } from "../../../../lib/jsonld";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllSeries().flatMap((s) =>
    s.seasons.map((season) => ({ slug: s.slug, season: `s${season.number}` }))
  );
}

export function generateMetadata({ params }: { params: { slug: string; season: string } }) {
  const series = getSeries(params.slug);
  if (!series) return {};
  const num = Number(params.season.replace(/^s/, ""));
  const season = series.seasons.find((s) => s.number === num);
  if (!season) return {};
  const t = series.title.value;
  const score = season.bollymeter ? `, BollyMeter ${season.bollymeter.score.toFixed(1)}/10` : "";
  const title = season.verdict
    ? `${t} Season ${num} Review: ${season.verdict}${score}`
    : `${t} Season ${num} Review — Is It Worth Watching?`;
  const lead = season.verdict
    ? `${t} Season ${num} verdict: ${season.verdict}${score}. `
    : `${t} Season ${num} — BollyAI opens a verdict once the season finishes. `;
  const description = (lead + (season.review_body ?? "")).slice(0, 158).replace(/\s+\S*$/, "");
  return { title, description };
}

export default function SeasonPage({ params }: { params: { slug: string; season: string } }) {
  const series = getSeries(params.slug);
  if (!series) notFound();
  const num = Number(params.season.replace(/^s/, ""));
  const season = series.seasons.find((s) => s.number === num);
  if (!season) notFound();

  const review = seasonReviewJsonLd(series, season);
  const episodeLd = episodeReviewsJsonLd(series, season);
  const episodeReviews = season.episode_reviews ?? [];

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      {review && <JsonLd data={review} />}
      {episodeLd && episodeLd.map((ld, i) => <JsonLd key={`ep-${i}`} data={ld} />)}
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

        {episodeReviews.length > 0 && (
          <section className="panel">
            <h2>Standout Episodes</h2>
            <p className="panel-sub">
              The hours worth arguing about — premieres, finales, and the turning points. BollyAI reads the room episode by episode.
            </p>
            <ol className="episode-list">
              {[...episodeReviews]
                .sort((a, b) => a.number - b.number)
                .map((ep) => (
                  <li key={ep.number} className="episode-card">
                    <div className="episode-card__head">
                      <span className="episode-card__n">E{ep.number}</span>
                      <span className="episode-card__title">{ep.title}</span>
                      {ep.bollymeter != null && (
                        <span className="episode-card__score">{ep.bollymeter.toFixed(1)}</span>
                      )}
                    </div>
                    <p className="episode-card__body">{ep.spoiler_free}</p>
                    {ep.the_moment && (
                      <p className="episode-card__moment">
                        <strong>The moment:</strong> {ep.the_moment}
                      </p>
                    )}
                    {ep.critic_note && (
                      <p className="episode-card__critic">
                        &ldquo;{ep.critic_note.text}&rdquo;{" "}
                        <a href={ep.critic_note.url}>— {ep.critic_note.source}</a>
                      </p>
                    )}
                  </li>
                ))}
            </ol>
          </section>
        )}

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
