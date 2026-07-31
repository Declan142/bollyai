import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../../../components/AnswerBlock";
import { DateModified } from "../../../../../components/DateModified";
import { DeskTint } from "../../../../../components/DeskTint";
import { JsonLd } from "../../../../../components/JsonLd";
import { ReviewBody } from "../../../../../components/ReviewBody";
import { formatDate } from "../../../../../lib/data";
import {
  getAllSeries,
  getSeries,
  getEpisodeReview,
  getRichEpisodeParams,
  resolvePublicImage
} from "../../../../../lib/series";
import { getEpisodeBreakdowns, getEpisodeBreakdown, epPath, parseEpId } from "../../../../../lib/episodes";
import { breadcrumbJsonLd } from "../../../../../lib/jsonld";
import { ogImage, pageSeo } from "../../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  // Breakdown pages (data/episodes/<slug>/*.json)
  const breakdownParams = getAllSeries().flatMap((s) =>
    getEpisodeBreakdowns(s.slug).map((ep) => ({
      slug: s.slug,
      season: `s${ep.season}`,
      episode: `e${ep.number}`
    }))
  );
  // Rich review pages (series.seasons[].episode_reviews[].review_body)
  const richParams = getAllSeries().flatMap((s) => getRichEpisodeParams(s));
  // Deduplicate by key
  const seen = new Set<string>();
  const all = [...breakdownParams, ...richParams];
  return all.filter((p) => {
    const k = `${p.slug}/${p.season}/${p.episode}`;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

type Params = { slug: string; season: string; episode: string };

function nums(params: Params) {
  return { season: Number(params.season.replace(/^s/, "")), number: Number(params.episode.replace(/^e/, "")) };
}

export async function generateMetadata(props: { params: Promise<Params> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  if (!series) return {};
  const { season, number } = nums(params);
  const t = series.title.value;

  // Prefer rich review fields for metadata
  const richEp = getEpisodeReview(params.slug, season, number);
  const ep = getEpisodeBreakdown(params.slug, season, number);

  const title_str = richEp?.title ?? ep?.title ?? `Episode ${number}`;
  const score = richEp?.verdict?.score ?? richEp?.bollymeter ?? ep?.bollymeter;
  const scoreStr = score != null ? `, BollyMeter ${Number(score).toFixed(1)}/10` : "";
  const pageTitle = `${t} S${season}E${number}: "${title_str}" Review${scoreStr}`;

  const verdictLine = richEp?.verdict?.one_liner ?? ep?.verdict_line ?? richEp?.spoiler_free ?? "";
  const description = (`${t} S${season}E${number} "${title_str}" review and analysis. ` + verdictLine)
    .slice(0, 158)
    .replace(/\s+\S*$/, "");

  return {
    title: pageTitle,
    description,
    ...pageSeo({ path: epPath(params.slug, season, number), image: ogImage(params.slug, season) ?? ogImage(params.slug) ?? series.poster.src, type: "article" })
  };
}

export default async function EpisodePage(props: { params: Promise<Params> }) {
  const params = await props.params;
  const series = getSeries(params.slug);
  if (!series) notFound();
  const { season, number } = nums(params);

  const richEp = getEpisodeReview(params.slug, season, number);
  const ep = getEpisodeBreakdown(params.slug, season, number);

  if (!richEp && !ep) notFound();

  const allBreakdowns = getEpisodeBreakdowns(params.slug);
  const t = series.title.value;

  // Navigation: build combined nav from both sources, deduplicated
  const navItems = generateStaticParams()
    .filter((p) => p.slug === params.slug)
    .map((p) => {
      const s = Number(p.season.replace(/^s/, ""));
      const n = Number(p.episode.replace(/^e/, ""));
      return { season: s, number: n, title: getEpisodeReview(params.slug, s, n)?.title ?? getEpisodeBreakdown(params.slug, s, n)?.title ?? `E${n}` };
    })
    .sort((a, b) => a.season - b.season || a.number - b.number);

  const idx = navItems.findIndex((e) => e.season === season && e.number === number);
  const prev = idx > 0 ? navItems[idx - 1] : null;
  const next = idx < navItems.length - 1 ? navItems[idx + 1] : null;

  const title_str = richEp?.title ?? ep?.title ?? `Episode ${number}`;
  const scoreVal = richEp?.verdict?.score ?? richEp?.bollymeter ?? ep?.bollymeter ?? null;
  const heroImg = resolvePublicImage(richEp?.hero_image, series.poster.src);

  const reviewLd = {
    "@context": "https://schema.org",
    "@type": "Review",
    itemReviewed: {
      "@type": "TVEpisode",
      name: title_str,
      episodeNumber: number,
      partOfSeason: { "@type": "TVSeason", seasonNumber: season },
      partOfSeries: { "@type": "TVSeries", name: t }
    },
    ...(scoreVal != null
      ? { reviewRating: { "@type": "Rating", ratingValue: scoreVal, bestRating: 10, worstRating: 0 } }
      : {}),
    author: { "@type": "Organization", name: "BollyAI", url: "https://bollyai.in" },
    reviewBody: richEp?.verdict?.one_liner ?? richEp?.spoiler_free ?? ep?.verdict_line ?? ""
  };

  // Rich review layout
  if (richEp?.review_body) {
    const pullQuote = richEp.pull_quote;
    const verdict = richEp.verdict;
    const the_moment = richEp.the_moment;
    const air_date = richEp.air_date;

    return (
      <DeskTint desk={series.canonical_industry} className="film-page">
        <JsonLd data={reviewLd} />
        <JsonLd
          data={breadcrumbJsonLd([
            { name: "Home", url: "/" },
            { name: "Series", url: "/browse/" },
            { name: t, url: `/series/${series.slug}/` },
            { name: `Season ${season}`, url: `/series/${series.slug}/s${season}/` },
            { name: `Episode ${number}`, url: epPath(series.slug, season, number) }
          ])}
        />

        {/* Hero — poster + verdict box */}
        <section className="rich-ep-hero">
          {heroImg && (
            <div className="rich-ep-hero__poster">
              <img src={heroImg} alt={`${t} Season ${season} poster`} width="185" height="278" loading="eager" fetchPriority="high" />
            </div>
          )}
          <div className="rich-ep-hero__copy">
            <p className="eyebrow">
              <a href={`/series/${series.slug}/`}>{t}</a>
              {" · "}
              <a href={`/series/${series.slug}/s${season}/`}>Season {season}</a>
              {" · Episode "}{number}
              {air_date && <> · {formatDate(air_date)}</>}
            </p>
            <h1>
              <span className="ep-hero__n">S{season}E{number}</span> {title_str}
            </h1>
            {verdict && (
              <div className="verdict-box">
                <span className="verdict-box__score">{Number(verdict.score).toFixed(1)}</span>
                <div className="verdict-box__right">
                  <span className="verdict-box__label">BollyAI Score</span>
                  <p className="verdict-box__line">{verdict.one_liner}</p>
                </div>
              </div>
            )}
            {the_moment && (
              <p className="the-moment">
                <span className="the-moment__k">THE MOMENT</span> {the_moment}
              </p>
            )}
            {richEp.spoiler_free && <AnswerBlock>{richEp.spoiler_free}</AnswerBlock>}
            <p className="spoiler-warning">Full episode analysis below. Spoiler-light verdict above.</p>
            <DateModified value={series.date_modified} />
          </div>
        </section>

        {/* Rich review body */}
        <section className="content-sections">
          <section className="panel review-panel">
            <ReviewBody markdown={richEp.review_body} />
          </section>

          {/* Pull quote callout */}
          {pullQuote && (
            <section className="panel">
              <blockquote className="pull-quote-callout">
                <p className="pull-quote-callout__text">"{pullQuote.text}"</p>
                <cite className="pull-quote-callout__cite">
                  <a href={pullQuote.url} rel="noopener noreferrer">{pullQuote.source}</a>
                </cite>
              </blockquote>
            </section>
          )}

          <nav className="ep-nav" aria-label="Episode navigation">
            {prev ? (
              <a href={epPath(series.slug, prev.season, prev.number)} className="ep-nav__prev">
                &larr; S{prev.season}E{prev.number} {prev.title}
              </a>
            ) : (
              <span />
            )}
            {next ? (
              <a href={epPath(series.slug, next.season, next.number)} className="ep-nav__next">
                S{next.season}E{next.number} {next.title} &rarr;
              </a>
            ) : (
              <a href={`/series/${series.slug}/s${season}/`} className="ep-nav__next">
                Season {season} verdict &rarr;
              </a>
            )}
          </nav>

          <nav className="mesh-links" aria-label="Series links">
            <a href={`/series/${series.slug}/s${season}/`}>{t} Season {season} review</a>
            <a href={`/series/${series.slug}/`}>All seasons of {t}</a>
            <a href="/browse/">Back to Series</a>
          </nav>
        </section>
      </DeskTint>
    );
  }

  // Fallback: classic EpisodeBreakdown layout
  if (!ep) notFound();

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={reviewLd} />
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/browse/" },
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
                const refHas = ref && allBreakdowns.some((e) => e.episode === th.ref_ep);
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
              &larr; S{prev.season}E{prev.number} {prev.title}
            </a>
          ) : (
            <span />
          )}
          {next ? (
            <a href={epPath(series.slug, next.season, next.number)} className="ep-nav__next">
              S{next.season}E{next.number} {next.title} &rarr;
            </a>
          ) : (
            <a href={`/series/${series.slug}/s${ep.season}/`} className="ep-nav__next">
              Season {ep.season} verdict &rarr;
            </a>
          )}
        </nav>

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/s${ep.season}/`}>
            {t} Season {ep.season} review
          </a>
          <a href={`/series/${series.slug}/`}>All seasons of {t}</a>
          <a href="/browse/">Back to Series</a>
        </nav>
      </section>
    </DeskTint>
  );
}
