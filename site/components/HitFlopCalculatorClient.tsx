"use client";

import { useEffect, useMemo, useState, type CSSProperties } from "react";
import {
  DEFAULT_GST_RATE,
  DEFAULT_SHARE_RATIO,
  TOOL_VERDICT_RUNGS,
  buildCalculatorLine,
  calculateHitFlop,
  formatCrRange,
  formatCrValue,
  formatRatio,
  rangeMidpoint,
  type ToolFilmOption
} from "../lib/tool-math";

function initialGross(film: ToolFilmOption | undefined): string {
  if (!film?.worldwideGrossCr) {
    return "";
  }
  return rangeMidpoint(film.worldwideGrossCr).toFixed(1);
}

function initialBudget(film: ToolFilmOption | undefined): string {
  if (film?.budgetCr === null || film?.budgetCr === undefined) {
    return "";
  }
  return film.budgetCr.toFixed(1);
}

function rungPct(index: number): number {
  return (index / Math.max(TOOL_VERDICT_RUNGS.length - 1, 1)) * 100;
}

export function HitFlopCalculatorClient({ films }: { films: ToolFilmOption[] }) {
  const firstFilm = films[0];
  const [filmSlug, setFilmSlug] = useState(firstFilm?.slug ?? "");
  const selectedFilm = useMemo(
    () => films.find((film) => film.slug === filmSlug) ?? firstFilm,
    [filmSlug, films, firstFilm]
  );
  const [budgetCr, setBudgetCr] = useState(initialBudget(firstFilm));
  const [grossCr, setGrossCr] = useState(initialGross(firstFilm));
  const [budgetSource, setBudgetSource] = useState<"trade_estimate" | "first_party">(
    firstFilm?.budgetIsFirstParty ? "first_party" : "trade_estimate"
  );
  const [taxPct, setTaxPct] = useState(String(DEFAULT_GST_RATE));
  const [shareRatio, setShareRatio] = useState(DEFAULT_SHARE_RATIO);

  useEffect(() => {
    const queryFilm = new URLSearchParams(window.location.search).get("film");
    if (queryFilm && films.some((film) => film.slug === queryFilm)) {
      setFilmSlug(queryFilm);
    }
  }, [films]);

  useEffect(() => {
    if (!selectedFilm) {
      return;
    }
    setBudgetCr(initialBudget(selectedFilm));
    setGrossCr(initialGross(selectedFilm));
    setBudgetSource(selectedFilm.budgetIsFirstParty ? "first_party" : "trade_estimate");
    setShareRatio(DEFAULT_SHARE_RATIO);
    setTaxPct(String(DEFAULT_GST_RATE));
  }, [selectedFilm]);

  if (!selectedFilm) {
    return (
      <section className="tool-panel tool-panel--focus">
        <h2>Tracking</h2>
        <p>No film records are available for the calculator yet.</p>
      </section>
    );
  }

  const parsedBudget = Number.parseFloat(budgetCr);
  const parsedGross = Number.parseFloat(grossCr);
  const parsedTax = Number.parseFloat(taxPct);
  const shareIsAssumption = Math.abs(shareRatio - DEFAULT_SHARE_RATIO) < 0.001;
  const result = calculateHitFlop({
    budgetCr: parsedBudget,
    grossCr: parsedGross,
    taxPct: parsedTax,
    shareRatio,
    budgetIsEstimated: budgetSource !== "first_party",
    shareIsAssumption
  });
  const answerLine = buildCalculatorLine(selectedFilm.title, parsedBudget, parsedGross, result);
  const barStyle: CSSProperties | undefined =
    result.status === "ready"
      ? ({
          "--marker": `${rungPct(result.centerIndex)}%`,
          "--band-start": `${rungPct(result.lowIndex)}%`,
          "--band-width": `${rungPct(result.highIndex) - rungPct(result.lowIndex)}%`
        } as CSSProperties)
      : undefined;

  return (
    <section className="tool-layout" aria-label="Hit flop verdict calculator">
      <form className="tool-panel tool-form" onSubmit={(event) => event.preventDefault()}>
        <label className="tool-field">
          <span>Film</span>
          <select value={selectedFilm.slug} onChange={(event) => setFilmSlug(event.target.value)}>
            {films.map((film) => (
              <option value={film.slug} key={film.slug}>
                {film.title} ({film.year})
              </option>
            ))}
          </select>
        </label>

        <div className="tool-control-grid">
          <label className="tool-field">
            <span>Budget Rs cr</span>
            <input
              inputMode="decimal"
              type="number"
              min="0"
              step="0.1"
              value={budgetCr}
              placeholder="Undisclosed"
              onChange={(event) => setBudgetCr(event.target.value)}
            />
          </label>
          <label className="tool-field">
            <span>Budget source</span>
            <select
              value={budgetSource}
              onChange={(event) => setBudgetSource(event.target.value as "trade_estimate" | "first_party")}
            >
              <option value="trade_estimate">Trade estimate</option>
              <option value="first_party">First-party cited</option>
            </select>
          </label>
          <label className="tool-field">
            <span>Worldwide gross Rs cr</span>
            <input
              inputMode="decimal"
              type="number"
              min="0"
              step="0.1"
              value={grossCr}
              placeholder="Awaiting pair-verified gross"
              onChange={(event) => setGrossCr(event.target.value)}
            />
          </label>
          <label className="tool-field">
            <span>GST or tax %</span>
            <input
              inputMode="decimal"
              type="number"
              min="0"
              max="40"
              step="0.1"
              value={taxPct}
              onChange={(event) => setTaxPct(event.target.value)}
            />
          </label>
        </div>

        <details className="tool-advanced">
          <summary>Advanced trade assumptions</summary>
          <label className="tool-field">
            <span>Distributor share ratio {(shareRatio * 100).toFixed(0)}%</span>
            <input
              type="range"
              min="0.35"
              max="0.55"
              step="0.01"
              value={shareRatio}
              onChange={(event) => setShareRatio(Number.parseFloat(event.target.value))}
            />
          </label>
          <p>
            Default share ratio is an assumption. Change it only when a film-specific trade source gives a better cut.
          </p>
        </details>
      </form>

      <section className="tool-panel tool-panel--focus" aria-live="polite">
        <p className="eyebrow">Verdict output</p>
        {result.status === "ready" ? (
          <>
            <h2>{result.isBand ? `${result.lowRung} to ${result.highRung}` : result.centerRung}</h2>
            <div className="ratio-bar" style={barStyle}>
              <div className="ratio-bar__track" />
              <div className="ratio-bar__band" />
              <div className="ratio-bar__marker" />
            </div>
            <p className="tool-result-line">{answerLine}</p>
            <div className="stat-grid">
              <span>
                <strong>{formatCrValue(result.nettCr)}</strong>
                Nett estimate
              </span>
              <span>
                <strong>{formatCrValue(result.distributorShareCr)}</strong>
                Distributor share
              </span>
              <span>
                <strong>{formatRatio(result.recoveryRatio)}</strong>
                Recovery ratio
              </span>
            </div>
            <p className="tool-note">
              {result.isBand
                ? "Estimated inputs render as a band. BollyAI avoids a fake single verdict when budget or share ratio is not sourced."
                : "Point verdict shown because the budget and share input are marked as sourced."}
            </p>
          </>
        ) : (
          <>
            <h2>Tracking</h2>
            <p className="tool-result-line">
              {result.status === "needs_budget"
                ? "Budget is undisclosed in the repo for this film. Enter a sourced or trade-estimated budget to calculate the band."
                : "Pair-verified worldwide gross is not available for this film yet. Enter a sourced gross to calculate the band."}
            </p>
          </>
        )}
      </section>

      <section className="tool-panel tool-data-note">
        <h2>{selectedFilm.title}</h2>
        <dl className="tool-facts">
          <div>
            <dt>Worldwide gross</dt>
            <dd>{selectedFilm.worldwideGrossCr ? formatCrRange(selectedFilm.worldwideGrossCr) : "Tracking"}</dd>
          </div>
          <div>
            <dt>India nett</dt>
            <dd>{selectedFilm.indiaNetCr ? formatCrRange(selectedFilm.indiaNetCr) : "Tracking"}</dd>
          </div>
          <div>
            <dt>Budget</dt>
            <dd>{selectedFilm.budgetCr ? formatCrValue(selectedFilm.budgetCr) : "Undisclosed"}</dd>
          </div>
        </dl>
        <nav className="mesh-links" aria-label={`${selectedFilm.title} links`}>
          <a href={selectedFilm.trackerPath}>Box-office tracker</a>
          <a href={selectedFilm.reviewPath}>Review verdict</a>
        </nav>
      </section>
    </section>
  );
}
