import type { Metadata } from "next";
import { BoxOfficeBoardTable } from "../../components/BoxOfficeBoardTable";
import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import { SectionHero } from "../../components/SectionHero";
import {
  boxOfficeDatasetJsonLd,
  boxOfficeItemListJsonLd,
  getBoxOfficeClubs,
  getCurrentBoxOfficeBoard,
  getYearScoreboardParams
} from "../../lib/boxoffice";
import { getDesk } from "../../lib/desks";
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
      <JsonLd
        data={boxOfficeDatasetJsonLd({
          name: `India box office tracker: ${board.week.label}`,
          description: "Current-week India box-office dataset with conservative source-gated publishing.",
          url: "/box-office/",
          dateModified: board.generated_at,
          records: board.records
        })}
      />
      <JsonLd data={boxOfficeItemListJsonLd(board)} />
      <SectionHero
        eyebrow="Box office desk"
        title="India box office, the conservative read"
        lede={
          <>
            Current-week theatrical tracking for India. A rupee figure appears <b>only after independent trade
            sources clear the publish rule,</b> so unverified rows stay in tracking rather than guessing.
          </>
        }
        stats={[
          { value: String(board.records.length), label: "Films tracked" },
          { value: board.week.label, label: "Trade week" },
          { value: board.territory, label: "Territory" }
        ]}
      >
        <DateModified value={board.generated_at} />
      </SectionHero>

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
        <BoxOfficeBoardTable records={board.records} />
      </section>

      <section className="bo-link-grid" aria-label="Box office scoreboards">
        {getBoxOfficeClubs().map((club) => (
          <a className="bo-link-card" href={`/box-office/${club.slug}/`} key={club.slug}>
            <span className="eyebrow">Cross-industry club</span>
            <strong>{club.label}</strong>
            <span>Only films with a publishable conservative figure cross the line.</span>
          </a>
        ))}
        {getYearScoreboardParams().map((scoreboard) => {
          const desk = getDesk(scoreboard.industry);
          return (
            <a className="bo-link-card" href={`/${scoreboard.industry}/box-office/${scoreboard.year}/`} key={`${scoreboard.industry}-${scoreboard.year}`}>
              <span className="eyebrow">Year scoreboard</span>
              <strong>
                {desk?.label ?? scoreboard.industry} {scoreboard.year}
              </strong>
              <span>{desk?.industryName ?? "Industry"} tracker rows for the year.</span>
            </a>
          );
        })}
      </section>

      <section className="bo-method-grid" aria-label="Box office methodology">
        <article className="panel">
          <p className="eyebrow">Publish rule</p>
          <h2>When a number appears</h2>
          <p>
            Two independent readings within 10 percent render the lower reading as a trade estimate. If readings differ
            by 10 to 25 percent, only the lower figure is shown with a caveat. Wider divergence, single-source data, and
            PR-only pairs stay as tracking.
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
