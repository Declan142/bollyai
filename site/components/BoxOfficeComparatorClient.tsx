"use client";

import { useEffect, useMemo, useState } from "react";
import {
  alignComparisonRows,
  buildComparatorLine,
  formatCrRange,
  formatToolDate,
  type AlignedComparisonRow,
  type ComparatorFilmOption,
  type CompareMode
} from "../lib/tool-math";

function labelForFilm(film: ComparatorFilmOption | undefined): string {
  return film?.optionLabel ?? "";
}

function defaultComparisonTarget(
  films: ComparatorFilmOption[],
  aFilm: ComparatorFilmOption | undefined
): ComparatorFilmOption | undefined {
  if (!aFilm) {
    return undefined;
  }
  const aDays = new Set(aFilm.dayPoints.map((point) => point.day));
  return (
    films.find((film) => film.slug !== aFilm.slug && film.dayPoints.some((point) => aDays.has(point.day))) ??
    films.find((film) => film.slug !== aFilm.slug) ??
    aFilm
  );
}

function findFilm(films: ComparatorFilmOption[], value: string): ComparatorFilmOption | undefined {
  const normalized = value.trim().toLowerCase();
  return films.find(
    (film) =>
      film.optionLabel.toLowerCase() === normalized ||
      film.title.toLowerCase() === normalized ||
      film.slug.toLowerCase() === normalized
  );
}

function pointFor(rowIndex: number, rowCount: number, value: number, maxValue: number): { x: number; y: number } {
  const x = 48 + (rowIndex / Math.max(rowCount - 1, 1)) * 544;
  const y = 220 - (value / Math.max(maxValue, 1)) * 160;
  return { x, y };
}

function midpoint(low: number, high: number): number {
  return (low + high) / 2;
}

function ComparatorSvg({
  rows,
  aFilm,
  bFilm
}: {
  rows: AlignedComparisonRow[];
  aFilm: ComparatorFilmOption;
  bFilm: ComparatorFilmOption;
}) {
  const rowCount = Math.max(rows.length, 1);
  const maxValue = Math.max(
    ...rows.flatMap((row) => [
      row.a?.cumulativeRange.high ?? 0,
      row.b?.cumulativeRange.high ?? 0
    ]),
    1
  );
  const aPoints = rows
    .map((row, index) =>
      row.a ? { ...pointFor(index, rowCount, row.a.cumulativeRange.high, maxValue), row } : null
    )
    .filter((point): point is { x: number; y: number; row: AlignedComparisonRow } => point !== null);
  const bPoints = rows
    .map((row, index) =>
      row.b ? { ...pointFor(index, rowCount, row.b.cumulativeRange.high, maxValue), row } : null
    )
    .filter((point): point is { x: number; y: number; row: AlignedComparisonRow } => point !== null);
  const lineFor = (points: Array<{ x: number; y: number }>) =>
    points.length > 1 ? points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ") : "";

  return (
    <figure className="comparator-chart">
      <svg viewBox="0 0 640 280" role="img" aria-label={`${aFilm.title} versus ${bFilm.title} box office comparison`}>
        <title>{`${aFilm.title} versus ${bFilm.title} box office comparison`}</title>
        <rect x="0" y="0" width="640" height="280" rx="4" fill="var(--surface)" />
        {[0, 1, 2, 3].map((tick) => {
          const y = 60 + tick * 50;
          return <line key={tick} x1="48" y1={y} x2="592" y2={y} stroke="var(--border-hair)" />;
        })}
        {aPoints.length > 1 && <polyline points={lineFor(aPoints)} fill="none" stroke="var(--accent)" strokeWidth="4" />}
        {bPoints.length > 1 && <polyline points={lineFor(bPoints)} fill="none" stroke="var(--accent-2)" strokeWidth="4" />}
        {aPoints.map((point) => (
          <circle key={`a-${point.row.key}`} cx={point.x} cy={point.y} r="6" fill="var(--accent)" />
        ))}
        {bPoints.map((point) => (
          <circle key={`b-${point.row.key}`} cx={point.x} cy={point.y} r="6" fill="var(--accent-2)" />
        ))}
        {rows.map((row, index) => {
          const x = pointFor(index, rowCount, 0, maxValue).x;
          return (
            <text key={row.key} x={x} y="252" textAnchor="middle" className="svg-kicker">
              {row.label}
            </text>
          );
        })}
        <text x="48" y="34" className="svg-kicker">
          CUMULATIVE INDIA NETT
        </text>
      </svg>
      <figcaption>
        The chart uses cumulative highs from published day-wise India nett ranges. Missing days remain blank.
      </figcaption>
    </figure>
  );
}

export function BoxOfficeComparatorClient({ films }: { films: ComparatorFilmOption[] }) {
  const defaultA = films[0];
  const defaultB = defaultComparisonTarget(films, defaultA);
  const [aSlug, setASlug] = useState(defaultA?.slug ?? "");
  const [bSlug, setBSlug] = useState(defaultB?.slug ?? "");
  const [aInput, setAInput] = useState(labelForFilm(defaultA));
  const [bInput, setBInput] = useState(labelForFilm(defaultB));
  const [mode, setMode] = useState<CompareMode>("day");

  const aFilm = useMemo(() => films.find((film) => film.slug === aSlug) ?? defaultA, [aSlug, defaultA, films]);
  const bFilm = useMemo(() => films.find((film) => film.slug === bSlug) ?? defaultB, [bSlug, defaultB, films]);

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const queryA = params.get("a");
    const queryB = params.get("b");
    const nextA = queryA ? films.find((film) => film.slug === queryA) : null;
    const nextB = queryB ? films.find((film) => film.slug === queryB) : null;
    if (nextA) {
      setASlug(nextA.slug);
      setAInput(labelForFilm(nextA));
    }
    if (nextB) {
      setBSlug(nextB.slug);
      setBInput(labelForFilm(nextB));
    }
  }, [films]);

  if (!aFilm || !bFilm) {
    return (
      <section className="tool-panel tool-panel--focus">
        <h2>Tracking</h2>
        <p>No day-wise film rows are available for comparison yet.</p>
      </section>
    );
  }

  const rows = alignComparisonRows(aFilm, bFilm, mode);
  const answerLine = buildComparatorLine(aFilm, bFilm, rows);

  function updateFilm(value: string, side: "a" | "b") {
    const found = findFilm(films, value);
    if (side === "a") {
      setAInput(value);
      if (found) {
        setASlug(found.slug);
      }
      return;
    }
    setBInput(value);
    if (found) {
      setBSlug(found.slug);
    }
  }

  return (
    <section className="tool-layout tool-layout--wide" aria-label="Box office comparator">
      <form className="tool-panel tool-form" onSubmit={(event) => event.preventDefault()}>
        <div className="tool-control-grid">
          <label className="tool-field">
            <span>Film A</span>
            <input
              list="box-office-film-options"
              value={aInput}
              onChange={(event) => updateFilm(event.target.value, "a")}
            />
          </label>
          <label className="tool-field">
            <span>Film B</span>
            <input
              list="box-office-film-options"
              value={bInput}
              onChange={(event) => updateFilm(event.target.value, "b")}
            />
          </label>
        </div>
        <datalist id="box-office-film-options">
          {films.map((film) => (
            <option value={film.optionLabel} key={film.slug} />
          ))}
        </datalist>

        <div className="tool-toggle-group" aria-label="Alignment mode">
          <button type="button" className={mode === "day" ? "is-active" : ""} onClick={() => setMode("day")}>
            Day-aligned
          </button>
          <button type="button" className={mode === "calendar" ? "is-active" : ""} onClick={() => setMode("calendar")}>
            Calendar-aligned
          </button>
        </div>

        <div className="tool-toggle-group" aria-label="Metric">
          <button type="button" className="is-active">
            India nett
          </button>
          <button type="button" disabled>
            Worldwide tracking
          </button>
          <button type="button" disabled>
            Footfalls tracking
          </button>
        </div>
      </form>

      <section className="tool-panel tool-panel--focus">
        <p className="eyebrow">Comparison output</p>
        <h2>{mode === "day" ? "Day-aligned race" : "Calendar-aligned view"}</h2>
        <p className="tool-result-line">{answerLine}</p>
        <ComparatorSvg rows={rows} aFilm={aFilm} bFilm={bFilm} />
      </section>

      <section className="tool-panel">
        <h2>Published Rows</h2>
        <div className="table-wrap">
          <table className="day-wise-table comparator-table">
            <thead>
              <tr>
                <th>{mode === "day" ? "Day" : "Date"}</th>
                <th>{aFilm.title}</th>
                <th>{bFilm.title}</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => {
                const aMid = row.a ? midpoint(row.a.cumulativeRange.low, row.a.cumulativeRange.high) : null;
                const bMid = row.b ? midpoint(row.b.cumulativeRange.low, row.b.cumulativeRange.high) : null;
                const status =
                  aMid !== null && bMid !== null
                    ? aMid >= bMid
                      ? `${aFilm.title} leads`
                      : `${bFilm.title} leads`
                    : "Data pending";
                return (
                  <tr key={row.key}>
                    <td>{row.label}</td>
                    <td>
                      {row.a ? (
                        <>
                          <span className="num">{formatCrRange(row.a.cumulativeRange)}</span>
                          <span className="source-line">{row.a.sourceNames.join(" + ")}</span>
                        </>
                      ) : (
                        "Pending"
                      )}
                    </td>
                    <td>
                      {row.b ? (
                        <>
                          <span className="num">{formatCrRange(row.b.cumulativeRange)}</span>
                          <span className="source-line">{row.b.sourceNames.join(" + ")}</span>
                        </>
                      ) : (
                        "Pending"
                      )}
                    </td>
                    <td>{status}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <nav className="mesh-links tool-mesh" aria-label="Selected film links">
          <a href={aFilm.trackerPath}>{aFilm.title} tracker</a>
          <a href={bFilm.trackerPath}>{bFilm.title} tracker</a>
          <a href="/tools/hit-flop-calculator/">Hit-flop calculator</a>
        </nav>
      </section>

      <section className="tool-panel tool-data-note">
        <h2>Data Window</h2>
        <dl className="tool-facts">
          <div>
            <dt>{aFilm.title}</dt>
            <dd>
              {aFilm.dayPoints.length} day row{aFilm.dayPoints.length === 1 ? "" : "s"} from{" "}
              {formatToolDate(aFilm.dayPoints[0].date)}
            </dd>
          </div>
          <div>
            <dt>{bFilm.title}</dt>
            <dd>
              {bFilm.dayPoints.length} day row{bFilm.dayPoints.length === 1 ? "" : "s"} from{" "}
              {formatToolDate(bFilm.dayPoints[0].date)}
            </dd>
          </div>
        </dl>
      </section>
    </section>
  );
}
