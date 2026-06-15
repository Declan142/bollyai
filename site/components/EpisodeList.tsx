"use client";

import { useState } from "react";
import type { EpisodeReview } from "../lib/series";
import styles from "./EpisodeList.module.css";

function bollyColor(score: number): string {
  const hue = Math.round(25 + (score / 10) * 125);
  return `oklch(74% .17 ${hue})`;
}

// EpisodeList - craft-grade standout-episode breakdown with a spoiler-free <-> full toggle.
// Spoiler-free (default) shows only BollyAI's spoiler-light read; full reveals "the moment" and
// the craft one-liner. No first-person viewing claims, no fabricated episode (honesty gate #1).
export function EpisodeList({
  slug,
  seasonNumber,
  episodes
}: {
  slug: string;
  seasonNumber: number;
  episodes: EpisodeReview[];
}) {
  const [full, setFull] = useState(false);
  if (!episodes || episodes.length === 0) return null;

  // Only offer the toggle when Full mode actually reveals more - otherwise it is a dead control.
  const hasSpoilerContent = episodes.some((ep) => ep.the_moment || ep.verdict?.one_liner);
  const showFull = full && hasSpoilerContent;

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <h2 className={styles.kicker}>Standout episodes</h2>
        {hasSpoilerContent && (
        <div className={styles.switch} role="group" aria-label="Spoiler mode">
          <button
            type="button"
            className={!full ? styles.active : ""}
            aria-pressed={!full}
            onClick={() => setFull(false)}
          >
            Spoiler-free
          </button>
          <button
            type="button"
            className={full ? styles.active : ""}
            aria-pressed={full}
            onClick={() => setFull(true)}
          >
            Full
          </button>
        </div>
        )}
      </div>

      {episodes.map((ep) => {
        const hasRich = Boolean(ep.review_body);
        const href = `/series/${slug}/s${seasonNumber}/e${ep.number}/`;
        return (
          <article className={styles.row} key={ep.number}>
            <span className={styles.n}>{ep.number.toString().padStart(2, "0")}</span>
            <div>
              <h3 className={styles.epTitle}>
                {hasRich ? <a href={href}>{ep.title}</a> : ep.title}
                {ep.air_date && <span className={styles.airdate}>{ep.air_date}</span>}
              </h3>
              <p className={styles.body}>{ep.spoiler_free}</p>

              {showFull && ep.the_moment && (
                <p className={styles.moment}>
                  <span className={styles.momentK}>The moment</span>
                  {ep.the_moment}
                </p>
              )}
              {showFull && ep.verdict?.one_liner && <p className={styles.oneLiner}>&ldquo;{ep.verdict.one_liner}&rdquo;</p>}

              {hasRich && (
                <a className={styles.readmore} href={href}>
                  Full episode review →
                </a>
              )}
            </div>
            {ep.bollymeter != null && (
              <span className={styles.chip} style={{ color: bollyColor(ep.bollymeter) }}>
                {ep.bollymeter.toFixed(1)}
              </span>
            )}
          </article>
        );
      })}
    </div>
  );
}
