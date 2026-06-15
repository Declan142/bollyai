import { decideBoxOfficeFigure, type BoxOfficeRecord } from "../lib/boxoffice";
import { formatCrore } from "../lib/data";
import styles from "./BoxOfficeLeaderboard.module.css";

// BoxOfficeLeaderboard (browse-lane revamp 2026-06-16): an honest horizontal-bar read of
// the week's India-net collections. A film earns a bar and a number ONLY if its India-net
// figure cleared the publish rule (two independent same-metric readings). Films still in
// tracking are listed below with no bar and no invented number - the honesty fence as a
// design feature. Real data only, from lib/boxoffice; presentation here, scoped CSS.
const LANG_LABEL: Record<string, string> = {
  tollywood: "Telugu", kollywood: "Tamil", mollywood: "Malayalam",
  sandalwood: "Kannada", bollywood: "Hindi", hollywood: "Hollywood", streaming: "OTT"
};

export function BoxOfficeLeaderboard({ records }: { records: BoxOfficeRecord[] }) {
  const rows = records.map((r) => ({
    record: r,
    decision: decideBoxOfficeFigure(r.india_net_inr_cr)
  }));

  const published = rows
    .filter((x): x is { record: BoxOfficeRecord; decision: Extract<ReturnType<typeof decideBoxOfficeFigure>, { published: true }> } => x.decision.published)
    .sort((a, b) => b.decision.range.low - a.decision.range.low);

  const tracking = rows.filter((x) => !x.decision.published);

  // nothing has cleared the rule yet - say so plainly, never fabricate a chart
  if (published.length === 0) {
    return (
      <div className={styles.wrap}>
        <header className={styles.head}>
          <h2>India net, this week</h2>
          <span>Publish rule</span>
        </header>
        <p className={styles.note}>
          No film has cleared the publish rule for this week yet, so there is no chart to draw. The moment two
          independent same-metric trade readings agree, the leaderboard fills in here. The tracked titles are in the
          board below.
        </p>
      </div>
    );
  }

  const max = published[0].decision.range.low;

  return (
    <div className={styles.wrap}>
      <header className={styles.head}>
        <h2>India net, this week</h2>
        <span>{published.length} cleared the publish rule</span>
      </header>

      <div className={styles.chart}>
        {published.map(({ record, decision }, i) => {
          const lang = LANG_LABEL[record.industry] ?? record.language;
          const pct = Math.max(6, Math.round((decision.range.low / max) * 100));
          const inner = (
            <>
              <span className={styles.rank}>{i + 1}</span>
              <span className={styles.track}>
                <span className={styles.label}>
                  <span className={styles.film}>{record.film.title} <span className={styles.lang}>{lang}</span></span>
                  <span className={styles.figure}>{formatCrore(decision.range)}<small>{decision.label}</small></span>
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
          <span className={styles.trackingHead}>Still tracking (no published figure)</span>
          {tracking.map(({ record }) => (
            <div className={styles.trackingRow} key={`${record.industry}-${record.film.title}`}>
              <b>{record.film.title}</b>
              <span className={styles.lang}>{LANG_LABEL[record.industry] ?? record.language}</span>
              <span className={styles.trackingTag}>tracking</span>
            </div>
          ))}
        </div>
      )}

      <p className={styles.note}>
        Bars show India net collection where two independent same-metric readings agree within the publish rule. The
        lower reading is shown. Films in tracking carry no bar and no figure, because an unverified number is worse
        than none.
      </p>
    </div>
  );
}
