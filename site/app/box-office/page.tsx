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

// The board is published only when real rows clear the two-independent-source contract.
// Until then this page must not dress an empty dataset up as a live tracker: no Dataset /
// ItemList JSON-LD, no "0 films tracked" scoreboard, no empty table, and no place in the
// index. See SOURCE-PROCUREMENT-20260809.md - the blocker is supplier procurement, not code.
const board = getCurrentBoxOfficeBoard();
const boardIsPublished = board.status === "ready" && board.records.length > 0;

export const metadata: Metadata = boardIsPublished
  ? {
      title: "Worldwide Box Office Tracker - Weekly USD Board",
      description:
        "Latest verified closed-week worldwide theatrical gross, published only after exact-period independent-source consensus.",
      ...pageSeo({ path: "/box-office/" })
    }
  : {
      title: "Worldwide Box Office - No Verified Board Published",
      description:
        "BollyAI is not publishing a weekly worldwide box-office board. No licensed pair of independent sources currently clears the exact-week publication contract, so there is no data to show.",
      robots: { index: false, follow: true },
      ...pageSeo({ path: "/box-office/" })
    };

export default function BoxOfficeHubPage() {
  const weekLabel = board.week.label;

  if (!boardIsPublished) {
    return <BoxOfficeUnavailable weekLabel={weekLabel} />;
  }

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

      <BoxOfficeLeaderboard records={board.records} />

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

/**
 * Honest empty state. The weekly board has no rows, so this page says exactly that and
 * publishes nothing that could be read as data: no structured-data Dataset, no scoreboard
 * stats, no table. It stays reachable (the nav links here) but is kept out of the index.
 */
function BoxOfficeUnavailable({ weekLabel }: { weekLabel: string }) {
  return (
    <main className="page-shell box-office-hub" data-desk="hollywood" data-board-state="unavailable">
      <SectionHero
        eyebrow="Box office desk"
        title="No verified box-office board"
        lede={
          <>
            BollyAI publishes a weekly worldwide gross only when two independent sources report the same
            Monday-to-Sunday period. <b>No licensed source pair currently clears that contract</b>, so there is no
            board to show - and an empty scoreboard is not a board.
          </>
        }
      >
        <p className="source-line">Last attempted closed week: {weekLabel}. Nothing cleared.</p>
      </SectionHero>

      <section className="panel bo-alert" aria-label="Why this board is empty">
        <p className="eyebrow">Data unavailable</p>
        <h2>This is a supply problem, not an outage</h2>
        <p>
          Every candidate feed we assessed either forbids public commercial display, covers the wrong period or
          territory, or traces back to the same upstream tracker as its supposed independent counterpart - which
          would make a two-source check meaningless. Until a genuinely independent, publishable pair is licensed,
          this desk publishes nothing rather than a single-source number dressed as consensus.
        </p>
        <p>
          Fabricating, estimating, or extrapolating rows to fill the table is not an option we will take. Missing
          evidence stays missing.
        </p>
      </section>

      <section className="bo-method-grid" aria-label="Box office methodology">
        <article className="panel">
          <p className="eyebrow">Publication contract</p>
          <h2>What would clear the board</h2>
          <p>
            At least two independent source groups reporting USD gross for the same Monday-to-Sunday period and
            Worldwide territory. Within 10 percent, the lower reading is a trade estimate. From 10 to 25 percent,
            only the lower figure appears with that conservative label. Wider disagreement stays in tracking.
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">What is excluded</p>
          <h2>No scope substitution</h2>
          <p>
            Lifetime and cumulative revenue, opening-weekend totals, week-to-date readings, budgets, salaries, and
            streaming view counts cannot stand in for an exact-week worldwide figure - not even to make the page
            look populated.
          </p>
        </article>
      </section>
    </main>
  );
}
