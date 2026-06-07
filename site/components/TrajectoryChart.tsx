import { formatCrore, type DayRow } from "../lib/data";

export function TrajectoryChart({ rows, title }: { rows: DayRow[]; title: string }) {
  const plotted = rows.filter((row) => row.net_inr_cr.value !== null);

  // A trajectory needs a line. Below 3 published rows, render the honest cumulative read instead of a lonely dot.
  if (plotted.length < 3) {
    const latest = plotted[plotted.length - 1];
    if (!latest) {
      return (
        <figure className="chart-panel">
          <p className="answer-block">No published trade rows yet. Early estimates awaited.</p>
          <figcaption>The trajectory chart appears once at least three day-wise rows clear the publish rule.</figcaption>
        </figure>
      );
    }
    return (
      <figure className="chart-panel">
        <svg viewBox="0 0 500 150" role="img" aria-label={`${title} cumulative box office`}>
          <title>{title} cumulative box office</title>
          <rect x="0" y="0" width="500" height="150" rx="4" fill="var(--surface)" />
          <text x="36" y="52" className="svg-kicker">
            {latest.label.toUpperCase()}
          </text>
          <text x="36" y="96" className="svg-num" style={{ fontSize: "34px" }}>
            {formatCrore(latest.net_inr_cr.value)}
          </text>
          <text x="36" y="126" className="svg-kicker">
            AS OF DAY {latest.day} · {latest.date}
          </text>
        </svg>
        <figcaption>
          Day-wise trajectory appears once at least three published rows exist; until then BollyAI shows the verified
          cumulative range, not a fake curve.
        </figcaption>
      </figure>
    );
  }

  const max = Math.max(...plotted.map((row) => row.net_inr_cr.value?.high ?? 0), 1);
  const points = plotted.map((row, index) => {
    const x = 36 + (index / Math.max(plotted.length - 1, 1)) * 430;
    const y = 190 - (((row.net_inr_cr.value?.high ?? 0) / max) * 150);
    return `${x.toFixed(1)},${y.toFixed(1)}`;
  });

  return (
    <figure className="chart-panel">
      <svg viewBox="0 0 500 240" role="img" aria-label={`${title} day-wise box office trajectory`}>
        <title>{title} day-wise box office trajectory</title>
        <desc>Inline static chart generated from published day-wise India nett trade estimate rows.</desc>
        <rect x="0" y="0" width="500" height="240" rx="4" fill="var(--surface)" />
        {[0, 1, 2, 3].map((tick) => {
          const y = 40 + tick * 50;
          return <line key={tick} x1="36" y1={y} x2="466" y2={y} stroke="var(--border-hair)" />;
        })}
        <polyline points={points.join(" ")} fill="none" stroke="var(--accent)" strokeWidth="4" />
        {plotted.map((row, index) => {
          const [x, y] = points[index].split(",").map(Number);
          // Clamp label anchoring so edge labels never clip outside the viewBox.
          const anchor = x < 90 ? "start" : x > 410 ? "end" : "middle";
          return (
            <g key={row.date}>
              <circle cx={x} cy={y} r="5" fill="var(--accent)" />
              {(index === 0 || index === plotted.length - 1) && (
                <text x={x} y={y - 12} textAnchor={anchor} className="svg-num">
                  {formatCrore(row.net_inr_cr.value)}
                </text>
              )}
              <text x={x} y="216" textAnchor="middle" className="svg-kicker">
                D{row.day}
              </text>
            </g>
          );
        })}
      </svg>
      <figcaption>
        Day-wise range chart uses published trade-estimate rows, so the number remains honest even when sources revise.
      </figcaption>
    </figure>
  );
}
