import type { DnaEpisode } from "../lib/dna";
import { topMentioned } from "../lib/dna";

/* Dialogue DNA - BollyAI's owned data-art, computed from the dialogue corpus.
   Two figures: SeasonPulse (per-episode dialogue-density curves with the longest
   hush marked) and TalkHeatmap (who the town talks about, episode by episode).
   Inline SVG so it inherits site fonts + desk accent tokens. */

function fmtClock(sec: number): string {
  const m = Math.floor(sec / 60);
  const s = Math.round(sec % 60);
  return `${m}:${String(s).padStart(2, "0")}`;
}

export function SeasonPulse({ eps }: { eps: DnaEpisode[] }) {
  if (eps.length === 0) return null;
  const colW = 86;
  const gap = 18;
  const h = 132;
  const plotH = 78;
  const top = 26;
  const w = eps.length * (colW + gap) - gap;
  const max = Math.max(...eps.flatMap((e) => e.curve), 1);
  const quietest = eps.reduce((a, b) => (b.longest_silence_sec > a.longest_silence_sec ? b : a));

  return (
    <figure className="dna-figure">
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Dialogue pace, episode by episode" className="dna-pulse">
        {eps.map((e, i) => {
          const x0 = i * (colW + gap);
          const pts = e.curve.map((v, j) => {
            const x = x0 + (j / (e.curve.length - 1)) * colW;
            const y = top + plotH - (v / max) * plotH;
            return `${x.toFixed(1)},${y.toFixed(1)}`;
          });
          const area = `M ${x0},${top + plotH} L ${pts.join(" L ")} L ${x0 + colW},${top + plotH} Z`;
          const isQuietest = e.ep === quietest.ep && e.longest_silence_sec >= 45;
          return (
            <g key={e.ep}>
              <path d={area} fill="var(--accent)" opacity="0.16" />
              <polyline points={pts.join(" ")} fill="none" stroke="var(--accent)" strokeWidth="1.6" />
              <line x1={x0} x2={x0 + colW} y1={top + plotH} y2={top + plotH} stroke="var(--border-hair)" />
              <text x={x0} y={top + plotH + 22} className="dna-label">E{e.n}</text>
              <text x={x0 + colW} y={top + plotH + 22} textAnchor="end" className="dna-label dna-label--dim">
                {Math.round(e.wpm)}wpm
              </text>
              {isQuietest && (
                <text x={x0} y={top - 10} className="dna-label dna-label--accent">
                  ◼ {Math.round(e.longest_silence_sec)}s hush
                </text>
              )}
            </g>
          );
        })}
      </svg>
      <figcaption>
        Words per minute across each hour. The flat valleys are the show holding its breath
        {quietest.longest_silence_sec >= 45 && quietest.longest_silence_at != null && (
          <>
            {" "}- the longest is a {Math.round(quietest.longest_silence_sec)}-second hush in E{quietest.n} at{" "}
            {fmtClock(quietest.longest_silence_at)}
          </>
        )}
        .
      </figcaption>
    </figure>
  );
}

export function TalkHeatmap({ eps }: { eps: DnaEpisode[] }) {
  if (eps.length === 0) return null;
  const names = topMentioned(eps, 9);
  if (names.length < 3) return null;
  const cell = 30;
  const cellGap = 5;
  const labelW = 86;
  const top = 30;
  const w = labelW + eps.length * (cell + cellGap);
  const h = top + names.length * (cell + cellGap) + 8;
  const max = Math.max(...eps.flatMap((e) => names.map((n) => e.mentions[n] ?? 0)), 1);

  return (
    <figure className="dna-figure">
      <svg viewBox={`0 0 ${w} ${h}`} role="img" aria-label="Who the town talks about, episode by episode" className="dna-heatmap">
        {eps.map((e, i) => (
          <text key={e.ep} x={labelW + i * (cell + cellGap) + cell / 2} y={top - 12} textAnchor="middle" className="dna-label">
            {e.n}
          </text>
        ))}
        {names.map((name, r) => (
          <g key={name}>
            <text x={labelW - 10} y={top + r * (cell + cellGap) + cell / 2 + 4} textAnchor="end" className="dna-name">
              {name}
            </text>
            {eps.map((e, c) => {
              const v = e.mentions[name] ?? 0;
              const t = v / max;
              return (
                <rect
                  key={e.ep}
                  x={labelW + c * (cell + cellGap)}
                  y={top + r * (cell + cellGap)}
                  width={cell}
                  height={cell}
                  rx="3"
                  fill={v === 0 ? "var(--border-hair)" : "var(--accent)"}
                  opacity={v === 0 ? 0.35 : 0.18 + t * 0.82}
                >
                  <title>{`${name}, E${e.n}: spoken ${v} time${v === 1 ? "" : "s"}`}</title>
                </rect>
              );
            })}
          </g>
        ))}
      </svg>
      <figcaption>
        How often each name is spoken aloud per episode. Watch who the town stops talking about, and who it
        suddenly cannot stop.
      </figcaption>
    </figure>
  );
}
