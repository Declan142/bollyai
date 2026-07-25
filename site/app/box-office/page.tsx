import type { Metadata } from "next";
import { BoxOfficeBoardTable } from "../../components/BoxOfficeBoardTable";
import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import { SectionHero } from "../../components/SectionHero";
import { BoxOfficeLeaderboard } from "../../components/BoxOfficeLeaderboard";
import {
  boxOfficeDatasetJsonLd,
  boxOfficeItemListJsonLd,
  getCurrentBoxOfficeBoard
} from "../../lib/boxoffice";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Worldwide Box Office Tracker - Weekly USD Board",
  description:
    "Latest verified closed-week worldwide theatrical gross, published only after exact-period independent-source consensus.",
  ...pageSeo({ path: "/box-office/" })
};

export default function BoxOfficeHubPage() {
  const board = getCurrentBoxOfficeBoard();
  const weekLabel = board.week.label;

  return (
    <main className="page-shell box-office-hub" data-desk="hollywood">
      <JsonLd
        data={boxOfficeDatasetJsonLd({
          name: `Box office tracker: ${weekLabel}`,
          description:
            "Exact closed-week box-office dataset with conservative independent-source consensus.",
          url: "/box-office/",
          dateModified: board.generated_at,
          period: board.week,
          records: board.records
        })}
      />
      <JsonLd data={boxOfficeItemListJsonLd(board)} />
      <SectionHero
        eyebrow="Box office desk"
        title="Worldwide box office"
        lede={
          <>
            Latest verified closed-week worldwide theatrical gross in USD.
            <b> Every published number covers the displayed seven-day period.</b> No lifetime totals, invented
            estimates, or stale-week relabelling.
          </>
        }
        stats={[
          { value: String(board.records.length), label: "Films tracked" },
          { value: weekLabel, label: "Closed week" },
          { value: board.territory, label: "Territory" }
        ]}
      >
        <DateModified value={board.generated_at} />
      </SectionHero>

      {board.status === "data_pending" && (
        <section className="panel bo-alert" aria-label="Data status">
          <p className="eyebrow">Data pending</p>
          <h2>No exact-week consensus yet</h2>
          <p>
            No operational source pair has cleared the exact-period contract for this closed week. The last verified
            board is never overwritten by a partial, cumulative, or mismatched-period candidate.
          </p>
        </section>
      )}

      {board.status === "ready" && board.records.length > 0 && (
        <BoxOfficeLeaderboard records={board.records} />
      )}

      <section className="panel bo-board-panel">
        <header className="bo-panel-head">
          <div>
            <p className="eyebrow">{weekLabel}</p>
            <h2>Latest Verified Closed Week</h2>
          </div>
          <span className="pill">{board.territory}</span>
        </header>
        <BoxOfficeBoardTable records={board.records} />
      </section>

      <section className="bo-method-grid" aria-label="Box office methodology">
        <article className="panel">
          <p className="eyebrow">Publication contract</p>
          <h2>What clears the board</h2>
          <p>
            At least two independent source groups must report USD gross for the same Monday-to-Sunday period and
            Worldwide territory. Within 10 percent, the lower reading is a trade estimate. From 10 to 25 percent,
            only the lower figure appears with that conservative label. Wider disagreement stays in tracking.
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">What is excluded</p>
          <h2>No scope substitution</h2>
          <p>
            Lifetime and cumulative revenue, opening-weekend totals, week-to-date readings, budgets, salaries, and
            streaming view counts cannot enter this weekly dataset. Missing exact-week evidence remains missing.
          </p>
        </article>
      </section>
    </main>
  );
}
