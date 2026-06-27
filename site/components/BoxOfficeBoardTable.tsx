import {
  decideBoxOfficeFigure,
  uniqueFigureSources,
  type BoxOfficeFigure,
  type BoxOfficeRecord,
  type BoxOfficeSource
} from "../lib/boxoffice";
import { formatCrore, formatDate } from "../lib/data";

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
            <th>Week</th>
            <th>India nett</th>
            <th>Worldwide gross</th>
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
              <td>
                {formatDate(record.week.start)} to {formatDate(record.week.end)}
              </td>
              <MetricCell figure={record.india_net_inr_cr} />
              <MetricCell figure={record.worldwide_gross_inr_cr} />
              <td>
                <SourceStack sources={uniqueFigureSources(record)} record={record} />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function MetricCell({ figure }: { figure: BoxOfficeFigure }) {
  const decision = decideBoxOfficeFigure(figure);
  return (
    <td>
      <span className="bo-metric" data-state={decision.published ? "published" : "tracking"}>
        <strong>{decision.published ? formatCrore(decision.range) : "tracking"}</strong>
        <span>{decision.published ? decision.label : figure.label}</span>
        {decision.published && <small>Basis: {decision.basisSources.join(" + ")}</small>}
        {decision.caveat && <small>{decision.caveat}</small>}
      </span>
    </td>
  );
}

function SourceStack({ sources, record }: { sources: BoxOfficeSource[]; record: BoxOfficeRecord }) {
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
    streaming: "Streaming",
  }[industry] ?? industry;
}
