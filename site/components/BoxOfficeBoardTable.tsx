import {
  uniqueWeekGrossSources,
  type BoxOfficeRecord,
  type WeekGrossSource
} from "../lib/boxoffice";
import { formatDate } from "../lib/data";

export function BoxOfficeBoardTable({
  records,
  emptyState = "No box-office rows have cleared the publish rule yet.",
  showIndustry = true
}: {
  records: BoxOfficeRecord[];
  emptyState?: string;
  showIndustry?: boolean;
}) {
  if (records.length === 0) {
    return (
      <div className="bo-empty">
        <p>{emptyState}</p>
      </div>
    );
  }

  return (
    <div className="table-wrap">
      <table className="day-wise-table bo-board">
        <thead>
          <tr>
            <th>Film</th>
            {showIndustry && <th>Industry</th>}
            <th>Release</th>
            <th>Closed-week gross (USD)</th>
            <th>Sources</th>
          </tr>
        </thead>
        <tbody>
          {records.map((record) => (
            <tr key={`${record.industry}-${record.film.slug ?? record.film.title}`}>
              <td className="bo-film-cell">
                <strong>{record.film.url ? <a href={record.film.url}>{record.film.title}</a> : record.film.title}</strong>
                <span>
                  {record.language} | {record.territory}
                </span>
              </td>
              {showIndustry && <td>{industryLabel(record.industry)}</td>}
              <td>{record.release_date ? formatDate(record.release_date) : "-"}</td>
              <UsdGrossCell record={record} />
              <td>
                <SourceStack sources={uniqueWeekGrossSources(record)} record={record} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function UsdGrossCell({ record }: { record: BoxOfficeRecord }) {
  const usd = record.week_gross_usd;
  if (usd.value === null) {
    return (
      <td>
        <span className="bo-metric" data-state="tracking">
          <strong>tracking</strong>
          <span>consensus pending</span>
        </span>
      </td>
    );
  }
  const displayM = (usd.value / 1_000_000).toLocaleString("en-US", { maximumFractionDigits: 1 });
  return (
    <td>
      <span className="bo-metric" data-state="published">
        <strong>${displayM}M</strong>
        <span>{usd.label}</span>
        <small>{formatDate(usd.period.start)} to {formatDate(usd.period.end)}</small>
      </span>
    </td>
  );
}

function SourceStack({
  sources,
  record
}: {
  sources: WeekGrossSource[];
  record: BoxOfficeRecord;
}) {
  if (sources.length === 0) {
    return <span className="source-line">Sources pending.</span>;
  }

  return (
    <span className="bo-source-stack">
      {sources.map((source) => (
        <a href={source.url} key={`${record.film.title}-${source.name}-${source.url}`} rel="noopener" target="_blank">
          {source.name}
          {source.as_of ? ` as of ${formatDate(source.as_of)}` : ""}
        </a>
      ))}
    </span>
  );
}

function industryLabel(industry: string): string {
  return {
    hollywood: "Hollywood",
    streaming: "Streaming"
  }[industry] ?? industry;
}
