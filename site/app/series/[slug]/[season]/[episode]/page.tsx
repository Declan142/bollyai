import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../../../components/AnswerBlock";
import { DateModified } from "../../../../../components/DateModified";
import { DeskTint } from "../../../../../components/DeskTint";
import { JsonLd } from "../../../../../components/JsonLd";
import { formatDate } from "../../../../../lib/data";
import { getAllSeries, getSeries } from "../../../../../lib/series";
import { getEpisodeBreakdowns, getEpisodeBreakdown, epPath, parseEpId } from "../../../../../lib/episodes";
import { breadcrumbJsonLd } from "../../../../../lib/jsonld";
import { ogImage, pageSeo } from "../../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getAllSeries().flatMap((s) =>
    getEpisodeBreakdowns(s.slug).map((ep) => ({
      slug: s.slug,
      season: `s${ep.season}`,
      episode: `e${ep.number}`
    }))
  );
}

type Params = { slug: string; season: string; episode: string };

function nums(params: Params) {
  return { season: Number(params.season.replace(/^s/, "")), number: Number(params.episode.replace(/^e/, "")) };
}

export function generateMetadata({ params }: { params: Params }) {
  const series = getSeries(params.slug);
  if (!series) return {};
  const { season, number } = nums(params);
  const ep = getEpisodeBreakdown(params.slug, season, number);
  if (!ep) return {};
  const t = series.title.value;
  const score = ep.bollymeter != null ? `, BollyMeter ${ep.bollymeter.toFixed(1)}/10` : "";
  const title = `${t} Season ${season} Episode ${number} Recap: ${ep.title}${score}`;
  const description = (`${t} S${season}E${number} "${ep.title}" recap and breakdown. ` + ep.verdict_line)
    .slice(0, 158)
    .replace(/\s+\S*$/, "");
  return {
    title,
    description,
    ...pageSeo({ path: epPath(params.slug, season, number), image: ogImage(params.slug, season) ?? ogImage(params.slug) ?? series.poster.src, type: "article" })
  };
}

export default function EpisodePage({ params }: { params: Params }) {
  const series = getSeries(params.slug);
  if (!series) notFound();
  const { season, number } = nums(params);
  const ep = getEpisodeBreakdown(params.slug, season, number);
  if (!ep) notFound();

  const all = getEpisodeBreakdowns(params.slug);
  const idx = all.findIndex((e) => e.episode === ep.episode);
  const prev = idx > 0 ? all[idx - 1] : null;
  const next = idx < all.length - 1 ? all[idx + 1] : null;
  const t = series.title.value;

  const reviewLd = {
    "@context": "https://schema.org",
    "@type": "Review",
    itemReviewed: {
      "@type": "TVEpisode",
      name: ep.title,
      episodeNumber: ep.number,
      partOfSeason: { "@type": "TVSeason", seasonNumber: ep.season },
      partOfSeries: { "@type": "TVSeries", name: t }
    },
    ...(ep.bollymeter != null
      ? { reviewRating: { "@type": "Rating", ratingValue: ep.bollymeter, bestRating: 10, worstRating: 0 } }
      : {}),
    author: { "@type": "Organization", name: "BollyAI", url: "https://bollyai.in" },
    reviewBody: ep.verdict_line
  };

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={reviewLd} />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/series/" },
          { name: t, url: `/series/${series.slug}/` },
          { name: `Season ${ep.season}`, url: `/series/${series.slug}/s${ep.season}/` },
          { name: `Episode ${ep.number}`, url: epPath(series.slug, ep.season, ep.number) }
        ])}
      />

      <section className="ep-hero">
        <p className="eyebrow">
          <a href={`/series/${series.slug}/`}>{t}</a> · <a href={`/series/${series.slug}/s${ep.season}/`}>Season {ep.season}</a> · Episode {ep.number}
          {ep.air_date && <> · {formatDate(ep.air_date)}</>}
        </p>
        <h1>
          <span className="ep-hero__n">S{ep.season}E{ep.number}</span> {ep.title}
        </h1>
        {ep.bollymeter != null && (
          <p className="ep-hero__score">
            <span>{ep.bollymeter.toFixed(1)}</span>/10 BOLLYMETER
          </p>
        )}
        <AnswerBlock>{ep.verdict_line}</AnswerBlock>
        <p className="spoiler-warning">Full spoilers for this episode below. Spoiler-light verdict above is all you get for free.</p>
        <DateModified value={series.date_modified} />
      </section>

      <section className="content-sections">
        <section className="panel ep-recap">
          <h2>What Happens in {t} S{ep.season}E{ep.number}</h2>
          {ep.recap.map((sec) => (
            <div key={sec.h}>
              <h3>{sec.h}</h3>
              {sec.body.map((p, i) => (
                <p key={i}>{p}</p>
              ))}
            </div>
          ))}
        </section>

        <section className="panel">
          <h2>The Read</h2>
          {ep.the_read.map((p, i) => (
            <p key={i}>{p}</p>
          ))}
          {ep.the_moment && (
            <p className="episode-card__moment">
              <strong>The moment:</strong> {ep.the_moment}
            </p>
          )}
        </section>

        {ep.threads.length > 0 && (
          <section className="panel">
            <h2>Threads</h2>
            <p className="panel-sub">
              What this hour plants, and what it pays off. BollyAI tracks every thread across the whole run.
            </p>
            <ul className="thread-list">
              {ep.threads.map((th) => {
                const ref = th.ref_ep ? parseEpId(th.ref_ep) : null;
                const refHas = ref && all.some((e) => e.episode === th.ref_ep);
                return (
                  <li key={th.label + th.text.slice(0, 16)} className="thread-item" data-dir={th.direction}>
                    <span className="thread-item__k">{th.direction === "pays" ? "PAYS OFF" : "PLANTS"}</span>
                    <div>
                      <strong>{th.label}</strong>
                      {ref && (
                        <>
                          {" "}
                          {refHas ? (
                            <a href={epPath(series.slug, ref.season, ref.number)}>
                              (S{ref.season}E{ref.number})
                            </a>
                          ) : (
                            <span>(S{ref.season}E{ref.number})</span>
                          )}
                        </>
                      )}
                      <p>{th.text}</p>
                    </div>
                  </li>
                );
              })}
            </ul>
          </section>
        )}

        {ep.questions.length > 0 && (
          <section className="panel">
            <h2>Open Questions After &ldquo;{ep.title}&rdquo;</h2>
            <ol className="question-list">
              {ep.questions.map((q) => (
                <li key={q}>{q}</li>
              ))}
            </ol>
          </section>
        )}

        <nav className="ep-nav" aria-label="Episode navigation">
          {prev ? (
            <a href={epPath(series.slug, prev.season, prev.number)} className="ep-nav__prev">
              ← S{prev.season}E{prev.number} {prev.title}
            </a>
          ) : (
            <span />
          )}
          {next ? (
            <a href={epPath(series.slug, next.season, next.number)} className="ep-nav__next">
              S{next.season}E{next.number} {next.title} →
            </a>
          ) : (
            <a href={`/series/${series.slug}/s${ep.season}/`} className="ep-nav__next">
              Season {ep.season} verdict →
            </a>
          )}
        </nav>

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/s${ep.season}/`}>
            {t} Season {ep.season} review
          </a>
          <a href={`/series/${series.slug}/`}>All seasons of {t}</a>
          <a href="/series/">Back to Series</a>
        </nav>
      </section>
    </DeskTint>
  );
}
