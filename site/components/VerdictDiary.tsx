"use client";

import { useState } from "react";
import { useDiary, useMounted, type DiaryStatus } from "./diaryStore";
import styles from "./VerdictDiary.module.css";

const STATUSES: { key: DiaryStatus; label: string }[] = [
  { key: "watchlist", label: "Watchlist" },
  { key: "watching", label: "Watching" },
  { key: "watched", label: "Watched" }
];

type Filter = "all" | DiaryStatus;

function bollyColor(score: number): string {
  const hue = Math.round(25 + (score / 10) * 125);
  return `oklch(74% .17 ${hue})`;
}

// VerdictDiary - the device-local watch diary. Reads the localStorage store, lets the visitor
// set their own status + 0-10 rating + a free-text note per saved title, and contrasts their
// score against BollyAI's snapshot. Nothing is sent anywhere - it is the reader's private notebook.
export function VerdictDiary() {
  const mounted = useMounted();
  const { entries, patch, remove, clearAll } = useDiary();
  const [filter, setFilter] = useState<Filter>("all");

  // Pre-mount placeholder so the static HTML never flashes an empty diary as the final state.
  if (!mounted) {
    return (
      <main className={`page-shell ${styles.shell}`} data-desk="streaming">
        <header className={styles.head}>
          <span className={styles.eyebrow}>BollyAI · Your Diary</span>
          <h1>Verdict Diary</h1>
          <p className={styles.lede}>Loading your diary from this device...</p>
        </header>
      </main>
    );
  }

  const shown = filter === "all" ? entries : entries.filter((e) => e.status === filter);
  const counts = {
    all: entries.length,
    watchlist: entries.filter((e) => e.status === "watchlist").length,
    watching: entries.filter((e) => e.status === "watching").length,
    watched: entries.filter((e) => e.status === "watched").length
  };
  const rated = entries.filter((e) => e.myRating != null);
  const avgMine = rated.length
    ? (rated.reduce((sum, e) => sum + (e.myRating ?? 0), 0) / rated.length).toFixed(1)
    : null;

  return (
    <main className={`page-shell ${styles.shell}`} data-desk="streaming">
      <header className={styles.head}>
        <span className={styles.eyebrow}>BollyAI · Your Diary</span>
        <h1 className={styles.title}>Verdict Diary</h1>
        <p className={styles.lede}>
          The shows you are tracking, with your own verdict beside BollyAI&rsquo;s. Saved on this
          device only - no account, nothing leaves your browser.
        </p>

        {entries.length > 0 && (
          <div className={styles.stats}>
            <span className={styles.stat}>
              <span className={styles.statN}>{counts.all}</span>
              <span className={styles.statK}>Tracked</span>
            </span>
            <span className={styles.stat}>
              <span className={styles.statN}>{counts.watched}</span>
              <span className={styles.statK}>Watched</span>
            </span>
            <span className={styles.stat}>
              <span className={styles.statN}>{avgMine ?? "-"}</span>
              <span className={styles.statK}>Your avg</span>
            </span>
          </div>
        )}
      </header>

      {entries.length === 0 ? (
        <div className={styles.empty}>
          <h2 className={styles.emptyTitle}>Your diary is empty</h2>
          <p className={styles.emptyText}>
            Open any series and tap <strong>Save to Diary</strong> to start tracking it. Your
            watchlist, your ratings, your notes - all kept privately on this device.
          </p>
          <a className={styles.emptyCta} href="/series/">
            Browse series <span aria-hidden="true">→</span>
          </a>
        </div>
      ) : (
        <>
          <div className={styles.tabs} role="group" aria-label="Filter by status">
            <button
              type="button"
              className={filter === "all" ? styles.active : ""}
              aria-pressed={filter === "all"}
              onClick={() => setFilter("all")}
            >
              All · {counts.all}
            </button>
            {STATUSES.map((s) => (
              <button
                key={s.key}
                type="button"
                className={filter === s.key ? styles.active : ""}
                aria-pressed={filter === s.key}
                onClick={() => setFilter(s.key)}
              >
                {s.label} · {counts[s.key]}
              </button>
            ))}
          </div>

          <div className={styles.list}>
            {shown.map((e) => (
              <article className={styles.card} key={e.slug}>
                <a className={styles.poster} href={`/series/${e.slug}/`} aria-label={`Open ${e.title}`}>
                  <img src={e.poster} alt="" loading="lazy" decoding="async" />
                </a>
                <div className={styles.body}>
                  <div className={styles.cardTop}>
                    <h3 className={styles.cardTitle}>
                      <a href={`/series/${e.slug}/`}>{e.title}</a>
                    </h3>
                  </div>
                  <p className={styles.meta}>
                    {e.platform}
                    {e.desk ? ` · ${e.desk}` : ""}
                  </p>

                  <div className={styles.scores}>
                    <span className={styles.scoreCell}>
                      <span
                        className={`${styles.scoreV} ${e.bollyScore == null ? styles.dim : ""}`}
                        style={e.bollyScore != null ? { color: bollyColor(e.bollyScore) } : undefined}
                      >
                        {e.bollyScore != null ? e.bollyScore.toFixed(1) : "n/a"}
                      </span>
                      <span className={styles.scoreK}>BollyMeter</span>
                    </span>
                    <span className={styles.scoreCell}>
                      <span className={`${styles.scoreV} ${e.myRating == null ? styles.dim : ""}`}>
                        {e.myRating != null ? e.myRating.toFixed(1) : "-"}
                      </span>
                      <span className={styles.scoreK}>Your score</span>
                    </span>
                  </div>

                  <div className={styles.statusPills} role="group" aria-label="Status">
                    {STATUSES.map((s) => (
                      <button
                        key={s.key}
                        type="button"
                        className={e.status === s.key ? styles.active : ""}
                        aria-pressed={e.status === s.key}
                        onClick={() => patch(e.slug, { status: s.key })}
                      >
                        {s.label}
                      </button>
                    ))}
                  </div>

                  <div className={styles.rateRow}>
                    <span className={styles.rateLabel}>Your score</span>
                    <span className={styles.ratePips}>
                      {Array.from({ length: 10 }, (_, i) => i + 1).map((n) => (
                        <button
                          key={n}
                          type="button"
                          className={`${styles.pip} ${e.myRating != null && n <= e.myRating ? styles.on : ""}`}
                          aria-label={`Rate ${n} out of 10`}
                          onClick={() => patch(e.slug, { myRating: e.myRating === n ? null : n })}
                        >
                          {n}
                        </button>
                      ))}
                    </span>
                  </div>

                  <textarea
                    className={styles.note}
                    placeholder="Your verdict, a line you loved, where it lost you..."
                    value={e.note}
                    onChange={(ev) => patch(e.slug, { note: ev.target.value })}
                  />

                  <div className={styles.cardActions}>
                    <button type="button" className={styles.remove} onClick={() => remove(e.slug)}>
                      Remove
                    </button>
                  </div>
                </div>
              </article>
            ))}
          </div>

          <div className={styles.foot}>
            <p className={styles.footNote}>
              BollyAI has not watched anything. This diary is yours - your scores, your notes, on
              this device only. Clearing your browser data clears it.
            </p>
            <button
              type="button"
              className={styles.clear}
              onClick={() => {
                if (window.confirm("Clear your entire Verdict Diary on this device?")) clearAll();
              }}
            >
              Clear diary
            </button>
          </div>
        </>
      )}
    </main>
  );
}
