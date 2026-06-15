import { PosterImage } from "./PosterImage";
import { ScoreStack } from "./ScoreStack";
import { SeasonVerdict } from "./SeasonVerdict";
import { formatDate } from "../lib/data";
import { isFreshSeries, type Series, type SeriesSeason } from "../lib/series";
import styles from "./TitleHero.module.css";

// TitleHero - the above-the-fold answer for a single title. The peak season frames the headline
// verdict (so a declined latest season never headlines the franchise); the answer line is the
// grounded bollymeter basis when there is one, else the rung word. No fabricated copy.
function deriveAnswer(series: Series, peak: SeriesSeason | undefined): string {
  if (peak?.bollymeter?.basis) return peak.bollymeter.basis;
  if (peak?.verdict) return `BollyAI rung: ${peak.verdict}. ${series.logline}`;
  return series.logline;
}

export function TitleHero({
  series,
  peak,
  latest
}: {
  series: Series;
  peak: SeriesSeason | undefined;
  latest: SeriesSeason | undefined;
}) {
  const fresh = isFreshSeries(series);
  const ctaSeason = latest ?? peak;
  const genreLine = series.genres?.slice(0, 2).join(" · ");

  return (
    <section className={styles.hero} data-desk={series.canonical_industry} aria-label={`${series.title.value} verdict`}>
      <div className={styles.ambient} aria-hidden="true">
        <img src={series.poster.src} alt="" decoding="async" loading="eager" />
      </div>
      <div className={styles.scrim} aria-hidden="true" />

      <div className={styles.inner}>
        <div className={`${styles.body} reveal`}>
          <span className={styles.masthead}>
            <span className={styles.brand}>BollyAI</span>
            <span className={styles.sep} aria-hidden="true">/</span>
            <span>The Verdict</span>
            <time className={styles.date} dateTime={series.date_modified}>
              {formatDate(series.date_modified)}
            </time>
          </span>

          <span className={styles.eyebrow}>
            {series.origin} · {series.platform.value}
            {genreLine ? ` · ${genreLine}` : ""}
          </span>

          <h1 className={styles.title}>{series.title.value}</h1>

          <p className={styles.answer}>{deriveAnswer(series, peak)}</p>

          {peak && (
            <div className={styles.scoreRow}>
              <ScoreStack season={peak} />
            </div>
          )}

          {peak && (
            <div className={styles.meterRow}>
              <SeasonVerdict rung={peak.verdict} compact />
            </div>
          )}

          {ctaSeason && (
            <div className={styles.ctaRow}>
              <a className={styles.cta} href={`/series/${series.slug}/s${ctaSeason.number}/`}>
                Read the full verdict <span aria-hidden="true">→</span>
              </a>
            </div>
          )}

          <p className={styles.renewal}>
            <strong>Renewal:</strong> {series.renewal.note}{" "}
            <a href={series.renewal.source_url}>({series.renewal.source})</a>
          </p>

          <ul className={styles.honesty} aria-label="Why you can trust this">
            <li>Disclosed AI critic</li>
            <li>Cited reception</li>
            <li>No fake ratings</li>
          </ul>
        </div>

        <a
          className={styles.art}
          href={ctaSeason ? `/series/${series.slug}/s${ctaSeason.number}/` : `/series/${series.slug}/`}
          aria-label={`Open ${series.title.value}`}
        >
          <span className={styles.frame}>
            <PosterImage
              src={series.poster.src}
              alt={series.poster.alt}
              width={342}
              height={513}
              fetchPriority="high"
              loading="eager"
              decoding="async"
              avifSrcSet={series.poster.variants?.avifSrcSet}
              webpSrcSet={series.poster.variants?.webpSrcSet}
              sizes="(max-width: 760px) 60vw, 17rem"
            />
            {fresh && <span className={styles.fresh}>New this season</span>}
          </span>
          {peak?.bollymeter == null && peak?.verdict && (
            <span className={`${styles.stamp} verdict-stamp`} data-rung={peak.verdict}>
              {peak.verdict}
            </span>
          )}
        </a>
      </div>
    </section>
  );
}
