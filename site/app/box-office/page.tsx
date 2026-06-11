import type { Metadata } from "next";
import { AnswerBlock } from "../../components/AnswerBlock";
import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import {
  boxOfficeItemListJsonLd,
  decideBoxOfficeFigure,
  getCurrentBoxOfficeBoard,
  uniqueFigureSources,
  type BoxOfficeFigure,
  type BoxOfficeRecord,
  type BoxOfficeSource
} from "../../lib/boxoffice";
import { formatCrore, formatDate } from "../../lib/data";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "India Box Office Tracker - Weekly Trade Board",
  description:
    "Current-week India box-office tracker with South-first ordering, source attribution, and conservative trade publishing rules.",
  ...pageSeo({ path: "/box-office/" })
};

export default function BoxOfficeHubPage() {
  const board = getCurrentBoxOfficeBoard();

  return (
    <main className="page-shell box-office-hub" data-desk="tollywood">
      <JsonLd data={boxOfficeItemListJsonLd(board)} />
      <section className="section-head box-office-head">
        <p className="eyebrow">Box office desk</p>
        <h1>India Box Office</h1>
        <AnswerBlock>
          Current-week theatrical tracking for India. A rupee figure appears only after independent trade sources clear
          BollyAI&apos;s publish rule, so unverified rows stay in tracking.
        </AnswerBlock>
        <DateModified value={board.generated_at} />
      </section>

      {board.DATA_PENDING && (
        <section className="panel bo-alert" aria-label="Data status">
          <p className="eyebrow">Data pending</p>
          <h2>Tracking before totals</h2>
          <p>
            Live sources are linked below, but the current weekly amounts are withheld until two independent same-metric
            readings agree closely enough. Missing numbers are the honest state.
          </p>
        </section>
      )}

      <section className="panel bo-board-panel">
        <header className="bo-panel-head">
          <div>
            <p className="eyebrow">{board.week.label}</p>
            <h2>Current Week Board</h2>
          </div>
          <span className="pill">{board.territory}</span>
        </header>
        <div className="table-wrap">
          <table className="day-wise-table bo-board">
            <thead>
              <tr>
                <th>Film</th>
                <th>Industry</th>
                <th>Week</th>
                <th>India nett</th>
                <th>Worldwide gross</th>
                <th>Sources</th>
              </tr>
            </thead>
            <tbody>
              {board.records.map((record) => (
                <tr key={`${record.industry}-${record.film.slug ?? record.film.title}`}>
                  <td className="bo-film-cell">
                    <strong>{record.film.url ? <a href={record.film.url}>{record.film.title}</a> : record.film.title}</strong>
                    <span>
                      {record.language} | {record.territory}
                    </span>
                  </td>
                  <td>{industryLabel(record.industry)}</td>
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
      </section>

      <section className="bo-method-grid" aria-label="Box office methodology">
        <article className="panel">
          <p className="eyebrow">Publish rule</p>
          <h2>When a number appears</h2>
          <p>
            Two independent readings within 10 percent render as a trade estimate. If readings differ by 10 to 25
            percent, only the lower figure is shown with a caveat. Wider divergence, single-source data, and PR-only
            pairs stay as tracking.
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">What is excluded</p>
          <h2>No budgets or salaries</h2>
          <p>
            Budgets, salaries, and platform view counts are not auto-published here. The board is only for attributed
            theatrical collection readings that can be checked against the rule.
          </p>
        </article>
      </section>
    </main>
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
    bollywood: "Bollywood",
    hollywood: "Hollywood",
    kollywood: "Kollywood",
    mollywood: "Mollywood",
    sandalwood: "Sandalwood",
    streaming: "Streaming",
    tollywood: "Tollywood"
  }[industry] ?? industry;
}
