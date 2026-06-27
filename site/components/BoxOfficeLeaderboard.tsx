import { getPublishedWorldwideGrossUsd, type BoxOfficeRecord } from "../lib/boxoffice";
import styles from "./BoxOfficeLeaderboard.module.css";

export function BoxOfficeLeaderboard({ records }: { records: BoxOfficeRecord[] }) {
  type Ranked = { record: BoxOfficeRecord; usdM: number };
  const ranked: Ranked[] = records
    .map((r) => ({ record: r, usdM: (getPublishedWorldwideGrossUsd(r) ?? 0) / 1_000_000 }))
    .filter((x) => x.usdM > 0)
    .sort((a, b) => b.usdM - a.usdM);

  const tracking = records.filter((r) => !getPublishedWorldwideGrossUsd(r));

  if (ranked.length === 0) {
    return (
      <div className={styles.wrap}>
        <header className={styles.head}>
          <h2>Worldwide gross, this week</h2>
          <span>Source-attributed USD</span>
        </header>
        <p className={styles.note}>
          No sourced worldwide gross figures yet. Once Wikidata or TMDB supply a verified USD figure, the leaderboard
          fills in here.
        </p>
      </div>
    );
  }

  const max = ranked[0].usdM;

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <h2>Worldwide gross, this week</h2>
        <span>{ranked.length} with sourced USD figure</span>
      </header>

      <div className={styles.chart}>
        {ranked.map(({ record, usdM }, i) => {
          const pct = Math.max(6, Math.round((usdM / max) * 100));
          const displayM = usdM.toLocaleString("en-US", { maximumFractionDigits: 1 });
          const inner = (
            <>
              <span className={styles.rank}>{i + 1}</span>
              <span className={styles.track}>
                <span className={styles.label}>
                  <span className={styles.film}>{record.film.title} <span className={styles.lang}>{record.language.toUpperCase()}</span></span>
                  <span className={styles.figure}>${displayM}M<small>worldwide gross</small></span>
                </span>
                <span className={styles.meter}>
                  <span className={styles.fill} style={{ width: `${pct}%` }} />
                </span>
              </span>
            </>
          );
          return record.film.url ? (
            <a className={styles.bar} href={record.film.url} key={`${record.industry}-${record.film.title}`}>{inner}</a>
          ) : (
            <div className={styles.bar} key={`${record.industry}-${record.film.title}`}>{inner}</div>
          );
        })}
      </div>

      {tracking.length > 0 && (
        <div className={styles.tracking}>
          <span className={styles.trackingHead}>No sourced figure yet</span>
          {tracking.map((record) => (
            <div className={styles.trackingRow} key={`${record.industry}-${record.film.title}`}>
              <b>{record.film.title}</b>
              <span className={styles.lang}>{record.language.toUpperCase()}</span>
              <span className={styles.trackingTag}>pending</span>
            </div>
          ))}
        </div>
      )}

      <p className={styles.note}>
        Bars show worldwide gross USD from Wikidata P2142 or TMDB revenue field, both public attributed sources. No
        invented or extrapolated figures.
      </p>
    </div>
  );
}
