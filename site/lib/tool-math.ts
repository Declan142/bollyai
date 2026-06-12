export const DEFAULT_GST_RATE = 18;
export const DEFAULT_SHARE_RATIO = 0.45;

export const TOOL_VERDICT_RUNGS = [
  "DISASTER",
  "FLOP",
  "BELOW AVERAGE",
  "AVERAGE",
  "SEMI-HIT",
  "HIT",
  "SUPER-HIT",
  "BLOCKBUSTER",
  "ALL-TIME BLOCKBUSTER"
] as const;

export type ToolVerdictRung = (typeof TOOL_VERDICT_RUNGS)[number];

export type ToolMoneyRange = {
  low: number;
  high: number;
};

export type ToolFilmOption = {
  slug: string;
  title: string;
  year: string;
  industry: string;
  releaseDate: string;
  dateModified: string;
  status: string;
  posterSrc: string;
  posterAlt: string;
  reviewPath: string;
  trackerPath: string;
  budgetCr: number | null;
  budgetConfidence: string | null;
  budgetIsFirstParty: boolean;
  indiaNetCr: ToolMoneyRange | null;
  worldwideGrossCr: ToolMoneyRange | null;
  totalsAsOf: string;
  grossConfidence: string | null;
};

export type ComparatorDayPoint = {
  day: number;
  date: string;
  label: string;
  range: ToolMoneyRange;
  cumulativeRange: ToolMoneyRange;
  sourceNames: string[];
};

export type ComparatorFilmOption = ToolFilmOption & {
  optionLabel: string;
  dayPoints: ComparatorDayPoint[];
};

export type CompareMode = "day" | "calendar";

export type AlignedComparisonRow = {
  key: string;
  label: string;
  a: ComparatorDayPoint | null;
  b: ComparatorDayPoint | null;
};

export type HitFlopResult =
  | {
      status: "needs_budget" | "needs_gross";
    }
  | {
      status: "ready";
      taxPct: number;
      nettCr: number;
      distributorShareCr: number;
      recoveryRatio: number;
      centerIndex: number;
      lowIndex: number;
      highIndex: number;
      centerRung: ToolVerdictRung;
      lowRung: ToolVerdictRung;
      highRung: ToolVerdictRung;
      isBand: boolean;
    };

const RUNG_CUTOFFS: Array<{ rung: ToolVerdictRung; min: number }> = [
  { rung: "DISASTER", min: 0 },
  { rung: "FLOP", min: 0.4 },
  { rung: "BELOW AVERAGE", min: 0.75 },
  { rung: "AVERAGE", min: 1 },
  { rung: "SEMI-HIT", min: 1.25 },
  { rung: "HIT", min: 1.75 },
  { rung: "SUPER-HIT", min: 2.25 },
  { rung: "BLOCKBUSTER", min: 3 },
  { rung: "ALL-TIME BLOCKBUSTER", min: 4 }
];

export function rangeMidpoint(range: ToolMoneyRange): number {
  return (range.low + range.high) / 2;
}

export function formatCrValue(value: number): string {
  return `Rs ${value.toFixed(1)} cr`;
}

export function formatCrRange(range: ToolMoneyRange): string {
  if (range.low === range.high) {
    return formatCrValue(range.low);
  }
  return `Rs ${range.low.toFixed(1)}-${range.high.toFixed(1)} cr`;
}

export function formatRatio(value: number): string {
  return `${value.toFixed(2)}x`;
}

export function formatPct(value: number): string {
  return `${value.toFixed(1)}%`;
}

export function formatToolDate(value: string): string {
  return new Intl.DateTimeFormat("en-IN", {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "Asia/Kolkata"
  }).format(new Date(`${value}T00:00:00+05:30`));
}

export function verdictIndexForRatio(ratio: number): number {
  const cleanRatio = Number.isFinite(ratio) ? Math.max(0, ratio) : 0;
  let index = 0;
  RUNG_CUTOFFS.forEach((cutoff, cutoffIndex) => {
    if (cleanRatio >= cutoff.min) {
      index = cutoffIndex;
    }
  });
  return index;
}

export function calculateHitFlop(input: {
  budgetCr: number;
  grossCr: number;
  taxPct: number;
  shareRatio: number;
  budgetIsEstimated: boolean;
  shareIsAssumption: boolean;
}): HitFlopResult {
  if (!Number.isFinite(input.budgetCr) || input.budgetCr <= 0) {
    return { status: "needs_budget" };
  }
  if (!Number.isFinite(input.grossCr) || input.grossCr <= 0) {
    return { status: "needs_gross" };
  }

  const taxPct = Number.isFinite(input.taxPct) ? Math.max(0, input.taxPct) : DEFAULT_GST_RATE;
  const shareRatio = Number.isFinite(input.shareRatio)
    ? Math.min(0.65, Math.max(0.2, input.shareRatio))
    : DEFAULT_SHARE_RATIO;
  const nettCr = input.grossCr / (1 + taxPct / 100);
  const distributorShareCr = nettCr * shareRatio;
  const recoveryRatio = distributorShareCr / input.budgetCr;
  const centerIndex = verdictIndexForRatio(recoveryRatio);
  const uncertain = input.budgetIsEstimated || input.shareIsAssumption;
  const lowIndex = uncertain ? Math.max(0, centerIndex - 1) : centerIndex;
  const highIndex = uncertain ? Math.min(TOOL_VERDICT_RUNGS.length - 1, centerIndex + 1) : centerIndex;

  return {
    status: "ready",
    taxPct,
    nettCr,
    distributorShareCr,
    recoveryRatio,
    centerIndex,
    lowIndex,
    highIndex,
    centerRung: TOOL_VERDICT_RUNGS[centerIndex],
    lowRung: TOOL_VERDICT_RUNGS[lowIndex],
    highRung: TOOL_VERDICT_RUNGS[highIndex],
    isBand: lowIndex !== highIndex
  };
}

export function buildCalculatorLine(title: string, budgetCr: number, grossCr: number, result: HitFlopResult): string {
  if (result.status !== "ready") {
    return "Enter budget and gross to calculate a trade estimate.";
  }
  const verdictText = result.isBand ? `${result.lowRung} to ${result.highRung} band` : result.centerRung;
  return `${title} on a ${formatCrValue(budgetCr)} budget against ${formatCrValue(
    grossCr
  )} gross returns an estimated distributor share of ${formatCrValue(
    result.distributorShareCr
  )}. Recovery is ${formatRatio(result.recoveryRatio)}, landing in the ${verdictText}.`;
}

export function alignComparisonRows(
  aFilm: ComparatorFilmOption,
  bFilm: ComparatorFilmOption,
  mode: CompareMode
): AlignedComparisonRow[] {
  const keyFor = (point: ComparatorDayPoint) => (mode === "day" ? String(point.day) : point.date);
  const labelFor = (key: string) => (mode === "day" ? `Day ${key}` : formatToolDate(key));
  const aMap = new Map(aFilm.dayPoints.map((point) => [keyFor(point), point]));
  const bMap = new Map(bFilm.dayPoints.map((point) => [keyFor(point), point]));
  const keys = Array.from(new Set([...aMap.keys(), ...bMap.keys()])).sort((left, right) => {
    if (mode === "day") {
      return Number(left) - Number(right);
    }
    return left.localeCompare(right);
  });

  return keys.map((key) => ({
    key,
    label: labelFor(key),
    a: aMap.get(key) ?? null,
    b: bMap.get(key) ?? null
  }));
}

export function latestCommonRow(rows: AlignedComparisonRow[]): AlignedComparisonRow | null {
  return rows.filter((row) => row.a && row.b).at(-1) ?? null;
}

export function buildComparatorLine(aFilm: ComparatorFilmOption, bFilm: ComparatorFilmOption, rows: AlignedComparisonRow[]): string {
  const row = latestCommonRow(rows);
  if (!row?.a || !row.b) {
    return `${aFilm.title} and ${bFilm.title} do not yet have a shared published comparison point. Missing days stay pending.`;
  }

  const aValue = rangeMidpoint(row.a.cumulativeRange);
  const bValue = rangeMidpoint(row.b.cumulativeRange);
  const leader = aValue >= bValue ? aFilm : bFilm;
  const trailer = aValue >= bValue ? bFilm : aFilm;
  const leaderValue = Math.max(aValue, bValue);
  const trailerValue = Math.min(aValue, bValue);
  const gap = trailerValue > 0 ? ((leaderValue - trailerValue) / trailerValue) * 100 : 0;

  return `Through ${row.label}, ${leader.title} leads ${trailer.title} at the India box office, ${formatCrValue(
    leaderValue
  )} vs ${formatCrValue(trailerValue)}, a ${formatPct(gap)} gap. Figures are day-aligned trade estimates.`;
}
