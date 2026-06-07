import { OTT_RUNGS, ottIndex, type OttRung } from "../lib/series";

const stops = [
  "oklch(45% .19 25)",
  "oklch(60% .16 40)",
  "oklch(76% .14 88)",
  "oklch(72% .14 150)",
  "oklch(72% .17 162)"
];

export function SeasonVerdict({ rung, compact = false }: { rung: OttRung | null; compact?: boolean }) {
  const open = rung === null;
  const label = rung ?? "STILL DROPPING";
  const index = open ? 0 : ottIndex(rung);
  const pct = (index / (OTT_RUNGS.length - 1)) * 100;
  const markerX = 20 + (pct / 100) * 320;
  const id = `ottRamp-${label.replaceAll(" ", "-")}-${compact ? "mini" : "full"}`;

  return (
    <figure className={compact ? "verdict-meter verdict-meter--compact" : "verdict-meter"}>
      <svg viewBox="0 0 360 86" role="img" aria-label={`${label} OTT verdict`}>
        <title>{label} OTT verdict</title>
        <defs>
          <linearGradient id={id} x1="0%" x2="100%" y1="0%" y2="0%">
            {stops.map((color, i) => (
              <stop key={color} offset={`${(i / (stops.length - 1)) * 100}%`} stopColor={color} />
            ))}
          </linearGradient>
        </defs>
        <rect x="20" y="22" width="320" height="16" rx="2" fill={`url(#${id})`} opacity="0.95" />
        <rect x="20" y="22" width="320" height="16" rx="2" fill="none" stroke="oklch(92% .02 80 / .32)" />
        {OTT_RUNGS.map((r, i) => {
          const x = 20 + (i / (OTT_RUNGS.length - 1)) * 320;
          return <line key={r} x1={x} x2={x} y1="18" y2="42" stroke="oklch(8% .03 280 / .6)" />;
        })}
        {!open && (
          <>
            <path d={`M ${markerX} 9 L ${markerX - 8} 18 L ${markerX + 8} 18 Z`} fill="var(--accent)" />
            <circle cx={markerX} cy="30" r={compact ? "5" : "7"} fill="var(--bg-deep)" stroke="var(--accent)" strokeWidth="3" />
          </>
        )}
        {open && (
          <text x="180" y="34" textAnchor="middle" className="svg-kicker" fill="var(--accent)">
            STILL DROPPING
          </text>
        )}
        <text x="20" y="66" className="svg-kicker">SKIP</text>
        <text x="340" y="66" textAnchor="end" className="svg-kicker">MUST-WATCH</text>
      </svg>
      {!compact && <figcaption>{open ? "Verdict opens once the season finishes dropping." : label}</figcaption>}
    </figure>
  );
}
