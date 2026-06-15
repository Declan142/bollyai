import type { Film } from "../lib/data";
import { budgetDisplay, formatCrore, formatDate } from "../lib/data";
import { BollyMeterDial } from "./BollyMeterDial";
import { DateModified } from "./DateModified";
import { VerdictMeter } from "./VerdictMeter";
import styles from "./FilmHero.module.css";

// FilmHero - elevated to the series TitleHero bar (capstone 2026-06-16). Same dark-cinema stage,
// adapted to film fields: BollyMeter dial + India-net box-office figure (trade-estimate framed,
// honesty fence #7) + the box-office verdict ladder. Props unchanged so the [desk] review /
// box-office / upcoming routes consume it without edits. Component-scoped CSS, no globals touched.
export function FilmHero({
  film,
  eyebrow,
  answer,
  showMeter = true
}: {
  film: Film;
  eyebrow: string;
  answer: string;
  showMeter?: boolean;
}) {
  const indiaNet = film.box_office.totals.india_net_inr_cr?.value ?? null;
  const hasBo = indiaNet != null;
  const budget = budgetDisplay(film);

  return (
    <section className={styles.hero} data-desk={film.canonical_industry} aria-label={`${film.title.value} verdict`}>
      <div className={styles.ambient} aria-hidden="true">
        <img src={film.poster.src} alt="" decoding="async" loading="eager" />
      </div>
      <div className={styles.scrim} aria-hidden="true" />

      <div className={styles.inner}>
        <div className={`${styles.body} reveal`}>
          <span className={styles.masthead}>
            <span className={styles.brand}>BollyAI</span>
            <span className={styles.sep} aria-hidden="true">/</span>
            <span>The Verdict</span>
            <time className={styles.date} dateTime={film.date_modified}>
              {formatDate(film.date_modified)}
            </time>
          </span>

          <span className={styles.eyebrow}>{eyebrow}</span>

          <h1 className={styles.title}>{film.title.value}</h1>

          <p className={styles.answer}>{answer}</p>

          {(showMeter && film.bollymeter) || hasBo ? (
            <div className={styles.cluster}>
              {showMeter && film.bollymeter && (
                <div className={styles.dialWrap}>
                  <BollyMeterDial score={film.bollymeter.score} size="hero" showLabel={false} />
                  <span className={styles.dialCaption}>BollyMeter</span>
                </div>
              )}
              {hasBo && (
                <div className={styles.figure}>
                  <span className={styles.figureValue}>{formatCrore(indiaNet)}</span>
                  <span className={styles.figureLabel}>India net</span>
                  <span className={styles.figureMeta}>
                    trade estimate · as of {formatDate(film.box_office.totals.as_of)}
                  </span>
                </div>
              )}
            </div>
          ) : null}

          <div className={styles.meterRow}>
            <VerdictMeter rung={film.verdict.ladder_rung} tracking={film.verdict.tracking} compact />
          </div>

          <div className={styles.facts}>
            <span>{formatDate(film.release_date.value)}</span>
            <span>{film.original_language.value.toUpperCase()}</span>
            <span>Budget {budget}</span>
          </div>

          <ul className={styles.honesty} aria-label="Why you can trust this">
            <li>Disclosed AI critic</li>
            <li>Cited box office</li>
            <li>No fake ratings</li>
          </ul>

          <DateModified value={film.date_modified} />
        </div>

        <div className={styles.art}>
          <span className={styles.frame}>
            <img
              src={film.poster.src}
              alt={film.poster.alt}
              width={342}
              height={513}
              fetchPriority="high"
              loading="eager"
              decoding="async"
            />
          </span>
          {!film.bollymeter && film.verdict.ladder_rung && (
            <span className={`${styles.stamp} verdict-stamp`} data-rung={film.verdict.ladder_rung}>
              {film.verdict.ladder_rung}
            </span>
          )}
        </div>
      </div>
    </section>
  );
}
