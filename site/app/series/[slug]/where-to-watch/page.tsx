import { notFound } from "next/navigation";
import { DeskTint } from "../../../../components/DeskTint";
import { JsonLd } from "../../../../components/JsonLd";
import { DateModified } from "../../../../components/DateModified";
import { SeasonVerdict } from "../../../../components/SeasonVerdict";
import {
  getAllSeries,
  getSeries,
  peakSeason,
  latestSeason,
  totalEpisodes,
  moreOnPlatform,
  whereToWatchFaq,
  qualifiesForWhereToWatch
} from "../../../../lib/series";
import { platformSlug, ottPageSlug } from "../../../../lib/data";
import { platformInfo, isFreeInIndia } from "../../../../lib/platforms";
import { hasEnding } from "../../../../lib/endings";
import { breadcrumbJsonLd, seriesJsonLd, seriesFaqJsonLd } from "../../../../lib/jsonld";
import { pageSeo } from "../../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  // Standalone streaming guide only where it adds real value over the hub
  // (see qualifiesForWhereToWatch). The thin tail stays on the hub.
  return getAllSeries()
    .filter(qualifiesForWhereToWatch)
    .map((s) => ({ slug: s.slug }));
}

export function generateMetadata({ params }: { params: { slug: string } }) {
  const series = getSeries(params.slug);
  if (!series) return {};
  const t = series.title.value;
  const plat = series.platform.value;
  const n = series.seasons.length;
  const free = isFreeInIndia(plat);
  const title = `Where to Watch ${t} in India — ${free ? `Free on ${plat}` : `Stream on ${plat}`}`;
  const description = `Watch ${t} on ${plat} in India — ${
    free ? "free with ads" : "subscription needed"
  }, ${n} season${n === 1 ? "" : "s"}, where to start, is it worth it, and what to stream next on ${plat}.`
    .slice(0, 158)
    .replace(/\s+\S*$/, "");
  return {
    title,
    description,
    ...pageSeo({ path: `/series/${params.slug}/where-to-watch/`, image: series.poster.src, type: "article" })
  };
}

export default function WhereToWatchPage({ params }: { params: { slug: string } }) {
  const series = getSeries(params.slug);
  if (!series) notFound();

  const t = series.title.value;
  const plat = series.platform.value;
  const info = platformInfo(plat);
  const free = isFreeInIndia(plat);
  const peak = peakSeason(series);
  const latest = latestSeason(series);
  const n = series.seasons.length;
  const eps = totalEpisodes(series);
  const faq = whereToWatchFaq(series);
  const faqLd = seriesFaqJsonLd(faq);
  const cohort = moreOnPlatform(series, 6);
  const seasonsAsc = [...series.seasons].sort((a, b) => a.number - b.number);
  const worthIt = peak?.verdict === "MUST-WATCH" || peak?.verdict === "WORTH-IT";
  const foreign = !["en", "hi"].includes(series.original_language.value.toLowerCase());
  const ottSlug = ottPageSlug(plat);
  const accessPhrase = free ? "free with ads" : `included with a ${plat} subscription`;
  const renewalLine =
    series.renewal.state === "renewed"
      ? `Another season of ${t} has been confirmed.`
      : series.renewal.state === "ended" || series.renewal.state === "limited"
        ? `${t} is complete — no further seasons are planned.`
        : series.renewal.state === "final-season"
          ? `${t} is in its final season.`
          : `A new season of ${t} has not been confirmed yet.`;

  return (
    <DeskTint desk={series.canonical_industry} className="film-page">
      <JsonLd data={seriesJsonLd(series)} />
      {faqLd && <JsonLd data={faqLd} />}
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "Series", url: "/series/" },
          { name: t, url: `/series/${series.slug}/` },
          { name: "Where to Watch", url: `/series/${series.slug}/where-to-watch/` }
        ])}
      />

      <section className="film-hero" data-desk={series.canonical_industry}>
        <div className="poster-frame">
          <img src={series.poster.src} alt={series.poster.alt} width="342" height="513" loading="eager" />
        </div>
        <div className="film-hero__copy">
          <p className="eyebrow">{series.origin} · Streaming Guide</p>
          <h1>Where to Watch {t} in India</h1>
          <p className="answer-block">
            <strong>{t}</strong> streams on <strong>{plat}</strong> in India
            {n
              ? `, all ${n} season${n === 1 ? "" : "s"}${eps ? ` (${eps} episodes)` : ""} ${accessPhrase}`
              : ` ${accessPhrase}`}
            .
            {peak?.verdict
              ? ` BollyAI verdict: ${peak.verdict}${peak.bollymeter ? `, BollyMeter ${peak.bollymeter.score.toFixed(1)}/10` : ""}.`
              : " Verdict still tracking."}
          </p>
          {latest && <SeasonVerdict rung={latest.verdict} />}
          <DateModified value={series.date_modified} />
        </div>
      </section>

      <section className="content-sections">
        <section className="panel">
          <h2>How to Watch {t} in India</h2>
          <dl className="watch-faq">
            <div>
              <dt>Platform</dt>
              <dd>{ottSlug ? <a href={`/ott/${ottSlug}/`}>{plat}</a> : plat} (India)</dd>
            </div>
            <div>
              <dt>Cost</dt>
              <dd>
                {free ? "Free, ad-supported" : "Paid subscription"} — {info.note}
              </dd>
            </div>
            <div>
              <dt>Seasons</dt>
              <dd>
                {n} season{n === 1 ? "" : "s"}
                {eps ? `, ${eps} episodes total` : ""}
              </dd>
            </div>
            <div>
              <dt>Where to start</dt>
              <dd>
                Season 1{seasonsAsc[0]?.year ? ` (${seasonsAsc[0].year})` : ""} — {t} is best watched in order.
              </dd>
            </div>
            <div>
              <dt>Language</dt>
              <dd>
                {series.original_language.value.toUpperCase()} original
                {foreign ? `, subtitled / often dubbed on ${plat}` : ""}
              </dd>
            </div>
          </dl>
        </section>

        {seasonsAsc.length > 0 && (
          <section className="panel">
            <h2>Every Season of {t}, in Order</h2>
            <ol className="season-list">
              {seasonsAsc.map((s) => (
                <li key={s.number} className="season-row">
                  <a href={`/series/${series.slug}/s${s.number}/`}>
                    <span className="season-row__n">Season {s.number}</span>
                    <span className="season-row__meta">
                      {s.year} · {s.episodes} ep{s.episodes === 1 ? "" : "s"} · on {plat}
                    </span>
                    <span className="season-row__verdict">{s.verdict ?? "still dropping"}</span>
                  </a>
                </li>
              ))}
            </ol>
          </section>
        )}

        <section className="panel">
          <h2>Is {t} Worth {free ? "Your Time" : `the ${plat} Subscription`}?</h2>
          <p>
            {peak?.verdict
              ? `BollyAI's read: ${peak.verdict}${
                  peak.bollymeter ? ` at BollyMeter ${peak.bollymeter.score.toFixed(1)}/10` : ""
                }${peak.number ? ` (Season ${peak.number}, its strongest)` : ""}. ${
                  worthIt ? `${t} earns the binge` : `Worth a look if the genre is your thing`
                }.`
              : `${t} is still being tracked — BollyAI opens a verdict once a season finishes.`}{" "}
            <a href={`/series/${series.slug}/`}>Read the full {t} review →</a>
          </p>
        </section>

        <section className="panel">
          <h2>Will There Be More {t}?</h2>
          <p>
            {renewalLine} <a href={`/series/${series.slug}/`}>Full renewal status →</a>
          </p>
          {hasEnding(series.slug) && (
            <p>
              <a href={`/series/${series.slug}/ending-explained/`}>How does {t} end? Read the ending explained →</a>
            </p>
          )}
        </section>

        {cohort.length > 0 && (
          <section className="panel">
            <h2>More to Watch on {plat}</h2>
            <div className="poster-wall">
              {cohort.map((s) => {
                const cp = peakSeason(s);
                const href = qualifiesForWhereToWatch(s)
                  ? `/series/${s.slug}/where-to-watch/`
                  : `/series/${s.slug}/`;
                return (
                  <a className="poster-card" data-desk="streaming" href={href} key={s.slug}>
                    <img src={s.poster.src} alt={s.poster.alt} width="342" height="513" loading="lazy" />
                    <span className="poster-card__plate">
                      <strong>{s.title.value}</strong>
                      <span className="poster-card__money">{s.platform.value}</span>
                      {cp && <SeasonVerdict rung={cp.verdict} compact />}
                    </span>
                  </a>
                );
              })}
            </div>
          </section>
        )}

        <section className="panel">
          <h2>{t} — Where to Watch FAQ</h2>
          <dl className="watch-faq">
            {faq.map((f) => (
              <div key={f.q}>
                <dt>{f.q}</dt>
                <dd>{f.a}</dd>
              </div>
            ))}
          </dl>
        </section>

        <p className="standing-line">
          BollyAI tracks {t} on {plat} in India and lists attributed availability only. BollyAI hasn&apos;t watched
          this — BollyAI has read the room around it.
        </p>

        <nav className="mesh-links" aria-label="Series links">
          <a href={`/series/${series.slug}/`}>Full {t} review</a>
          {ottSlug && <a href={`/ott/${ottSlug}/`}>What&apos;s new on {plat}</a>}
          <a href="/series/">Browse all series</a>
        </nav>
      </section>
    </DeskTint>
  );
}
