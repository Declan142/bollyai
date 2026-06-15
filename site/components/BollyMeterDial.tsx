// BollyMeterDial - the signature verdict object (revamp 2026-06-15, 10-Opus team consensus:
// promote BollyMeter from a buried badge to the hero medallion the whole stage orbits). A
// conic-gradient ring filled to the 0-10 score, temperature-coloured (red -> amber -> green),
// with the arc sweeping up on scroll-into-view (pure CSS @property, gated; see globals.css).
export function BollyMeterDial({
  score,
  size = "card",
  showLabel = true
}: {
  score: number;
  size?: "hero" | "card";
  showLabel?: boolean;
}) {
  const pct = Math.max(0, Math.min(100, (score / 10) * 100));
  const hue = Math.round(25 + (score / 10) * 125); // 25 (red, harsh) -> 150 (green, rave)
  const color = `oklch(74% .17 ${hue})`;
  return (
    <div
      className={`bm-dial bm-dial--${size}`}
      style={{ "--dial-target": `${pct}%`, "--dial-color": color } as React.CSSProperties}
      aria-label={`BollyMeter ${score.toFixed(1)} out of 10`}
      role="img"
    >
      <div className="bm-dial__ring" aria-hidden="true">
        <div className="bm-dial__hole">
          <span className="bm-dial__score">{score.toFixed(1)}</span>
          <span className="bm-dial__scale">/10</span>
        </div>
      </div>
      {showLabel && <span className="bm-dial__label">BollyMeter</span>}
    </div>
  );
}
