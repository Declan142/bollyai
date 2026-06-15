import { formatDate } from "../lib/data";
import { OTT_RUNGS, ottIndex, type Series, type SeriesSeason } from "../lib/series";
import styles from "./BoxOfficeTable.module.css";

// Rung pill colour - same temperature ramp the SeasonVerdict meter uses (red -> green).
const RUNG_STOPS = [
  "oklch(60% .16 30)",
  "oklch(70% .15 55)",
  "oklch(80% .14 90)",
  "oklch(74% .15 150)",
  "oklch(74% .17 162)"
];

function bollyColor(score: number): string {
  const hue = Math.round(25 + (score / 10) * 125);
  return `oklch(74% .17 ${hue})`;
}

// BoxOfficeTable - season-by-season RECEPTION ledger for a streaming title. Box-office is the
// film analogue; for OTT the honest, citable performance signal is reception (no platform
// publishes per-title streams - honesty fence #3), so this ledger tracks BollyMeter + critic %
// + audience + verdict, then a per-episode BollyMeter rhythm strip for the standout season.
export function BoxOfficeTable({ series }: { series: Series }) {
  const seasons = [...series.seasons].sort((a, b) => a.number - b.number);
  if (seasons.length === 0) return null;

  // If not a single season carries any reception signal (no BollyMeter, no critic %, no audience,
  // no verdict rung), a table of dashes is a dead void - render a grounded empty-state instead.
  const anySignal = seasons.some(
    (s) => s.bollymeter != null || s.critic?.positive_pct != null || s.audience?.rating != null || s.verdict != null
  );
  if (!anySignal) {
    return (
      <div className={styles.wrap}>
        <div className={styles.head}>
          <h2 className={styles.kicker}>Reception ledger</h2>
        </div>
        <p className={styles.empty}>
          Reception is still landing. BollyAI does not score a title until enough real critic and
          audience reaction exists to ground a verdict - no number gets invented to fill the gap.
        </p>
      </div>
    );
  }

  // Pick the season with the richest scored-episode set for the rhythm strip.
  const scoredEps = (s: SeriesSeason) => (s.episode_reviews ?? []).filter((e) => e.bollymeter != null);
  const rhythmSeason = [...seasons].sort((a, b) => scoredEps(b).length - scoredEps(a).length)[0];
  const eps = scoredEps(rhythmSeason);

  return (
    <div className={styles.wrap}>
      <div className={styles.head}>
        <h2 className={styles.kicker}>Reception ledger</h2>
        <p className={styles.note}>
          Indian OTT platforms do not publish per-title streams. This tracks reception across the run, not viewership.
        </p>
      </div>

      <table className={styles.table}>
        <thead>
          <tr>
            <th>Season</th>
            <th className={styles.hideSm}>Released</th>
            <th className="num">BollyMeter</th>
            <th className="num">Critics</th>
            <th className="num">Audience</th>
            <th>Verdict</th>
          </tr>
        </thead>
        <tbody>
          {seasons.map((s) => {
            const idx = s.verdict ? ottIndex(s.verdict) : null;
            return (
              <tr key={s.number}>
                <td>
                  <span className={styles.season}>Season {s.number}</span>
                  <span className={styles.seasonMeta}>
                    {s.year} · {s.episodes} ep{s.episodes === 1 ? "" : "s"}
                  </span>
                </td>
                <td className={styles.hideSm}>{formatDate(s.release_date.value)}</td>
                <td className="num">
                  {s.bollymeter ? (
                    <span className={styles.metric} style={{ color: bollyColor(s.bollymeter.score) }}>
                      {s.bollymeter.score.toFixed(1)}
                    </span>
                  ) : (
                    <span className={styles.dim}>n/a</span>
                  )}
                </td>
                <td className="num">
                  {s.critic?.positive_pct != null ? (
                    <span className={styles.metric}>{s.critic.positive_pct}%</span>
                  ) : (
                    <span className={styles.dim}>n/a</span>
                  )}
                </td>
                <td className="num">
                  {s.audience?.rating != null ? (
                    <span className={styles.metric}>
                      {s.audience.rating.toFixed(1)}
                      <span className={styles.dim} style={{ fontSize: "0.7em" }}>
                        /{s.audience.scale}
                      </span>
                    </span>
                  ) : (
                    <span className={styles.dim}>n/a</span>
                  )}
                </td>
                <td>
                  {s.verdict && idx != null ? (
                    <span className={styles.rung} style={{ background: RUNG_STOPS[idx] }}>
                      {s.verdict}
                    </span>
                  ) : (
                    <span className={styles.dim}>still dropping</span>
                  )}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>

      {eps.length >= 3 && (
        <div className={styles.rhythm}>
          <p className={styles.rhythmHead}>
            Season {rhythmSeason.number} · episode BollyMeter rhythm
          </p>
          <div className={styles.bars} role="img" aria-label={`Per-episode BollyMeter for season ${rhythmSeason.number}`}>
            {eps.map((ep) => {
              const score = ep.bollymeter as number;
              return (
                <div className={styles.bar} key={ep.number}>
                  <span className={styles.barNum}>{score.toFixed(1)}</span>
                  <span className={styles.barTrack}>
                    <span
                      className={styles.barFill}
                      style={{ height: `${(score / 10) * 100}%`, background: bollyColor(score) }}
                    />
                  </span>
                  <span className={styles.barEp}>E{ep.number}</span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
