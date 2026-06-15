"use client";

import { useState } from "react";
import type { Series, SeriesSeason } from "../lib/series";
import styles from "./VerdictReceipt.module.css";

// VerdictReceipt - the honesty fences turned into a feature. Tap to reveal the receipt: every
// line of the verdict traces to a real, cited source (the BollyMeter basis, the critic sample,
// the audience source, real attributed pull-quotes, the renewal source). Nothing is invented;
// a field with no grounding simply does not print a line.
export function VerdictReceipt({ series, season }: { series: Series; season: SeriesSeason | undefined }) {
  const [open, setOpen] = useState(false);
  if (!season) return null;

  const quotes = season.critic?.pull_quotes ?? [];
  const hasContent =
    Boolean(season.bollymeter?.basis) ||
    season.critic?.sample != null ||
    Boolean(season.audience) ||
    quotes.length > 0;
  if (!hasContent) return null;

  return (
    <div className={styles.receipt}>
      <button
        type="button"
        className={styles.toggle}
        aria-expanded={open}
        onClick={() => setOpen((v) => !v)}
      >
        <span className={styles.tag}>Receipt</span>
        <span>
          <span className={styles.label}>How this verdict is grounded</span>
          <span className={styles.sub}>Season {season.number} · every score traces to a cited source</span>
        </span>
        <span className={styles.open}>{open ? "Hide −" : "Show +"}</span>
      </button>

      <div className={`${styles.panel} ${open ? styles.shown : ""}`}>
        <div className={styles.panelInner}>
          <div className={styles.tape}>
            {season.bollymeter?.basis && (
              <div className={styles.line}>
                <span className={styles.k}>BollyMeter {season.bollymeter.score.toFixed(1)}</span>
                <span className={styles.v}>{season.bollymeter.basis}</span>
              </div>
            )}

            {season.critic?.positive_pct != null && (
              <div className={styles.line}>
                <span className={styles.k}>Critics {season.critic.positive_pct}%</span>
                <span className={styles.v}>
                  {season.critic.sample != null
                    ? `Positive across a sample of ${season.critic.sample} reviews.`
                    : "Critic consensus."}
                </span>
              </div>
            )}

            {season.audience?.rating != null && (
              <div className={styles.line}>
                <span className={styles.k}>Audience {season.audience.rating.toFixed(1)}/{season.audience.scale}</span>
                <span className={styles.v}>
                  <a href={season.audience.source_url}>{season.audience.source}</a> user rating.
                </span>
              </div>
            )}

            {quotes.map((q) => (
              <div className={styles.line} key={q.url}>
                <span className={styles.k}>Quoted</span>
                <span className={styles.v}>
                  <span className={styles.quote}>&ldquo;{q.text}&rdquo;</span>
                  <span className={styles.cite}>
                    <a href={q.url}>{q.source}</a>
                  </span>
                </span>
              </div>
            ))}

            <div className={styles.line}>
              <span className={styles.k}>Renewal</span>
              <span className={styles.v}>
                {series.renewal.note} <a href={series.renewal.source_url}>({series.renewal.source})</a>
              </span>
            </div>

            <p className={styles.foot}>
              BollyAI has not watched anything. BollyAI has read everyone who has.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
