import { VERDICT_RUNGS, type VerdictRung } from "../lib/data";

const stops = [
  "oklch(45% .19 25)",
  "oklch(55% .18 30)",
  "oklch(62% .14 45)",
  "oklch(72% .12 70)",
  "oklch(76% .14 88)",
  "oklch(78% .15 95)",
  "oklch(74% .16 140)",
  "oklch(70% .17 162)",
  "oklch(72% .17 162)"
];

export function verdictIndex(rung: VerdictRung): number {
  return Math.max(0, VERDICT_RUNGS.indexOf(rung));
}

export function VerdictMeter({ rung, compact = false }: { rung: VerdictRung; compact?: boolean }) {
  const index = verdictIndex(rung);
  const pct = (index / (VERDICT_RUNGS.length - 1)) * 100;
  const markerX = 20 + (pct / 100) * 320;
  const id = `verdictRamp-${rung.replaceAll(" ", "-")}-${compact ? "mini" : "full"}`;

  return (
    <figure className={compact ? "verdict-meter verdict-meter--compact" : "verdict-meter"}>
      <svg viewBox="0 0 360 86" role="img" aria-label={`${rung} verdict meter`}>
        <title>{rung} verdict meter</title>
        <defs>
          <linearGradient id={id} x1="0%" x2="100%" y1="0%" y2="0%">
            {stops.map((color, stopIndex) => (
              <stop
                key={color}
                offset={`${(stopIndex / (stops.length - 1)) * 100}%`}
                stopColor={color}
              />
            ))}
          </linearGradient>
        </defs>
        <rect x="20" y="22" width="320" height="16" rx="2" fill={`url(#${id})`} opacity="0.95" />
        <rect x="20" y="22" width="320" height="16" rx="2" fill="none" stroke="oklch(92% .02 80 / .32)" />
        {VERDICT_RUNGS.map((label, stopIndex) => {
          const x = 20 + (stopIndex / (VERDICT_RUNGS.length - 1)) * 320;
          return <line key={label} x1={x} x2={x} y1="18" y2="42" stroke="oklch(8% .03 280 / .65)" />;
        })}
        <path d={`M ${markerX} 9 L ${markerX - 8} 18 L ${markerX + 8} 18 Z`} fill="var(--accent)" />
        <circle cx={markerX} cy="30" r={compact ? "5" : "7"} fill="var(--bg-deep)" stroke="var(--accent)" strokeWidth="3" />
        <text x="20" y="66" className="svg-kicker">
          DISASTER
        </text>
        <text x="340" y="66" textAnchor="end" className="svg-kicker">
          ALL-TIME
        </text>
      </svg>
      {!compact && <figcaption>{rung}</figcaption>}
    </figure>
  );
}
