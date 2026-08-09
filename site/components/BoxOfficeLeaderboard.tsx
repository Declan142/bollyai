import { getPublishedWeekGrossUsd, type BoxOfficeRecord } from "../lib/boxoffice";
import styles from "./BoxOfficeLeaderboard.module.css";

export function BoxOfficeLeaderboard({ records }: { records: BoxOfficeRecord[] }) {
  type Ranked = { record: BoxOfficeRecord; usdM: number };
  const ranked: Ranked[] = records
    .map((r) => ({ record: r, usdM: (getPublishedWeekGrossUsd(r) ?? 0) / 1_000_000 }))
    .filter((x) => x.usdM > 0)
    .sort((a, b) => b.usdM - a.usdM);

  const tracking = records.filter((r) => getPublishedWeekGrossUsd(r) === null);

  if (ranked.length === 0) {
    return (
      <div className={styles.wrap}>
        <header className={styles.head}>
          <h2>Gross during the closed week</h2>
          <span>Exact-period source consensus</span>
        </header>
        <p className={styles.note}>
          No figure has cleared the exact-week two-source rule yet. Missing data stays missing until independent
          sources agree on the same period, metric, currency, and territory.
        </p>
      </div>
    );
  }

  const max = ranked[0].usdM;

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <h2>Gross during the closed week</h2>
        <span>{ranked.length} with verified weekly USD</span>
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
                  <span className={styles.figure}>${displayM}M<small>gross in this exact week</small></span>
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
        Bars show gross earned only inside the displayed closed week. At least two independent source groups must
        report the same scope; BollyAI publishes the lower reading and never substitutes lifetime revenue.
      </p>
    </div>
  );
}
