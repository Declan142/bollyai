import { getAllFilms, type Film, type MoneyRange } from "./data";
import type { ComparatorDayPoint, ComparatorFilmOption, ToolFilmOption, ToolMoneyRange } from "./tool-math";

function toToolRange(range: MoneyRange | null | undefined): ToolMoneyRange | null {
  if (!range || !Number.isFinite(range.low) || !Number.isFinite(range.high)) {
    return null;
  }
  return { low: range.low, high: range.high };
}

function filmYear(film: Film): string {
  return film.release_date.value.slice(0, 4);
}

function baseFilmOption(film: Film): ToolFilmOption {
  return {
    slug: film.slug,
    title: film.title.value,
    year: filmYear(film),
    industry: film.canonical_industry,
    releaseDate: film.release_date.value,
    dateModified: film.date_modified,
    status: film.status,
    posterSrc: film.poster.src,
    posterAlt: film.poster.alt,
    reviewPath: `/${film.canonical_industry}/reviews/${film.slug}/`,
    trackerPath: `/${film.canonical_industry}/box-office/${film.slug}/`,
    budgetCr: film.budget?.value ?? null,
    budgetConfidence: film.budget?.confidence ?? null,
    budgetIsFirstParty: film.budget?.first_party === true,
    indiaNetCr: toToolRange(film.box_office.totals.india_net_inr_cr.value),
    worldwideGrossCr: toToolRange(film.box_office.totals.worldwide_gross_inr_cr.value),
    totalsAsOf: film.box_office.totals.as_of,
    grossConfidence: film.box_office.totals.worldwide_gross_inr_cr.confidence
  };
}

function filmToolRank(film: ToolFilmOption): number {
  const liveBoost = film.status === "live" ? 1_000_000 : 0;
  const ww = film.worldwideGrossCr?.high ?? 0;
  const india = film.indiaNetCr?.high ?? 0;
  const budgetBoost = film.budgetCr !== null ? 10_000 : 0;
  return liveBoost + budgetBoost + Math.max(ww, india);
}

export function getCalculatorFilmOptions(): ToolFilmOption[] {
  return getAllFilms()
    .map(baseFilmOption)
    .sort((a, b) => filmToolRank(b) - filmToolRank(a) || a.title.localeCompare(b.title));
}

function dayPointsForFilm(film: Film): ComparatorDayPoint[] {
  let cumulativeLow = 0;
  let cumulativeHigh = 0;

  return film.box_office.day_rows
    .filter((row) => row.day > 0 && row.net_inr_cr.value !== null)
    .sort((a, b) => a.day - b.day)
    .map((row) => {
      const range = toToolRange(row.net_inr_cr.value);
      if (!range) {
        return null;
      }
      cumulativeLow += range.low;
      cumulativeHigh += range.high;
      return {
        day: row.day,
        date: row.date,
        label: row.label,
        range,
        cumulativeRange: { low: cumulativeLow, high: cumulativeHigh },
        sourceNames: Array.from(new Set(row.sources.map((source) => source.name)))
      };
    })
    .filter((point): point is ComparatorDayPoint => point !== null);
}

export function getComparatorFilmOptions(): ComparatorFilmOption[] {
  return getAllFilms()
    .map((film) => ({
      ...baseFilmOption(film),
      optionLabel: `${film.title.value} (${filmYear(film)})`,
      dayPoints: dayPointsForFilm(film)
    }))
    .filter((film) => film.dayPoints.length > 0)
    .sort(
      (a, b) =>
        b.dayPoints.length - a.dayPoints.length ||
        (b.indiaNetCr?.high ?? 0) - (a.indiaNetCr?.high ?? 0) ||
        a.title.localeCompare(b.title)
    );
}

export function latestToolDate(films: Array<{ dateModified: string }>): string {
  return films.map((film) => film.dateModified).sort().at(-1) ?? "2026-06-08T00:00:00+05:30";
}
