import { BollyMeterDial } from "./BollyMeterDial";
import type { SeriesSeason } from "../lib/series";
import styles from "./ScoreStack.module.css";

// ScoreStack - critic / audience / BollyMeter-composite as one layered number cluster.
// The BollyMeter is BollyAI's grounded composite verdict (the dial); the critic % and the
// audience rating are the two real source signals it reconciles. Every cell is omitted unless
// the underlying number is real (honesty fence #3/#4): no invented composite, no fake percent.
export function ScoreStack({ season }: { season: SeriesSeason }) {
  const bolly = season.bollymeter;
  const criticPct = season.critic?.positive_pct ?? null;
  const criticSample = season.critic?.sample ?? null;
  const audience = season.audience;

  // Nothing real to stack - render nothing rather than a hollow widget.
  if (bolly == null && criticPct == null && (audience?.rating == null)) return null;

  return (
    <div className={styles.stack} role="group" aria-label="Reception scores">
      {criticPct != null && (
        <div className={styles.cell}>
          <span className={styles.value}>
            {criticPct}
            <span className={styles.unit}>%</span>
          </span>
          <span className={styles.label}>Critics</span>
          {criticSample != null && <span className={styles.meta}>{criticSample} reviews positive</span>}
        </div>
      )}

      {bolly != null && (
        <div className={styles.dialWrap}>
          <BollyMeterDial score={bolly.score} size="hero" showLabel={false} />
          <span className={styles.composite}>BollyMeter composite</span>
        </div>
      )}

      {audience?.rating != null && (
        <div className={styles.cell}>
          <span className={styles.value}>
            {audience.rating.toFixed(1)}
            <span className={styles.unit}>/{audience.scale}</span>
          </span>
          <span className={styles.label}>Audience</span>
          <span className={styles.meta}>
            <a href={audience.source_url}>{audience.source}</a>
          </span>
        </div>
      )}
    </div>
  );
}
