"use client";

import { useDiary, useMounted, type DiaryStatus } from "./diaryStore";
import styles from "./SaveToDiary.module.css";

const STATUSES: { key: DiaryStatus; label: string }[] = [
  { key: "watchlist", label: "Watchlist" },
  { key: "watching", label: "Watching" },
  { key: "watched", label: "Watched" }
];

// SaveToDiary - the entry point into the device-local Verdict Diary from any title page.
// Save once (defaults to Watchlist), then quick-set status; the full notes + personal rating
// live on /series/diary/. Nothing persists server-side - this is the reader's private device.
export function SaveToDiary({
  slug,
  title,
  poster,
  desk,
  platform,
  bollyScore
}: {
  slug: string;
  title: string;
  poster: string;
  desk: string;
  platform: string;
  bollyScore: number | null;
}) {
  const mounted = useMounted();
  const { entries, upsert, patch, remove } = useDiary();
  const entry = mounted ? entries.find((e) => e.slug === slug) ?? null : null;

  // Pre-mount (and SSR) render a stable, non-interactive shell so hydration never mismatches.
  if (!mounted) {
    return (
      <span className={styles.wrap}>
        <span className={styles.save} aria-hidden="true">
          <span className={styles.plus}>+</span> Save to Diary
        </span>
      </span>
    );
  }

  const save = () => {
    if (entry) {
      remove(slug);
      return;
    }
    upsert({
      slug,
      title,
      poster,
      desk,
      platform,
      bollyScore,
      status: "watchlist",
      myRating: null,
      note: "",
      savedAt: new Date().toISOString()
    });
  };

  return (
    <span className={styles.wrap}>
      <button
        type="button"
        className={`${styles.save} ${entry ? styles.saved : ""}`}
        onClick={save}
        aria-pressed={Boolean(entry)}
      >
        {entry ? (
          <>
            <span className={styles.tick}>✓</span> In your Diary
          </>
        ) : (
          <>
            <span className={styles.plus}>+</span> Save to Diary
          </>
        )}
      </button>

      {entry && (
        <span className={styles.statusRow}>
          {STATUSES.map((s) => (
            <button
              key={s.key}
              type="button"
              className={entry.status === s.key ? styles.active : ""}
              aria-pressed={entry.status === s.key}
              onClick={() => patch(slug, { status: s.key })}
            >
              {s.label}
            </button>
          ))}
          <a className={styles.open} href="/series/diary/">
            Open diary →
          </a>
        </span>
      )}

      {!entry && <span className={styles.priv}>Saved on this device only. No account.</span>}
    </span>
  );
}
