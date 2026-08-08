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
import { projectBoxOfficePublicState } from "../../lib/boxoffice-public-state.mjs";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Worldwide Box Office Tracker - Weekly USD Board",
  description:
    "Verified closed-week worldwide theatrical gross appears only when current exact-period independent-source consensus is available.",
  ...pageSeo({ path: "/box-office/" })
};

export default function BoxOfficeHubPage() {
  const board = getCurrentBoxOfficeBoard();
  const publicState = projectBoxOfficePublicState(board);
  const weekLabel = publicState.expectedWeek.label;

  return (
    <main className="page-shell box-office-hub" data-desk="hollywood">
      {publicState.showStructuredData && (
        <>
          <JsonLd
            data={boxOfficeDatasetJsonLd({
              name: `Box office tracker: ${weekLabel}`,
              description:
                "Exact closed-week box-office dataset with conservative independent-source consensus.",
              url: "/box-office/",
              dateModified: board.generated_at,
              period: board.week,
              records: publicState.jsonLdRecords
            })}
          />
          <JsonLd
            data={boxOfficeItemListJsonLd({
              ...board,
              records: publicState.jsonLdRecords
            })}
          />
        </>
      )}
      <SectionHero
        eyebrow="Box office desk"
        title="Worldwide box office"
        lede={
          <>
            Verified closed-week worldwide theatrical gross in USD appears only with current evidence.
            <b> Figures appear only when the current closed week clears the source contract.</b> No lifetime totals,
            invented estimates, or stale-week relabelling.
          </>
        }
        stats={[
          { value: String(publicState.boardRecords.length), label: "Films tracked" },
          { value: weekLabel, label: "Closed week" },
          { value: board.territory, label: "Territory" }
        ]}
      >
        {!publicState.noCurrentData && <DateModified value={board.generated_at} />}
      </SectionHero>

      {publicState.noCurrentData && (
        <section className="panel bo-alert" aria-label="Data status">
          <p className="eyebrow">Data unavailable</p>
          <h2>No current box-office data</h2>
          {publicState.stale ? (
            <p>
              The available snapshot covers {publicState.observedWeek.label}, while the current closed-week slot
              expects {publicState.expectedWeek.label}. Its rows and structured data are withheld instead of being
              relabelled as current.
            </p>
          ) : (
            <p>
              No operational source pair has cleared the exact-period contract for {publicState.expectedWeek.label}.
              Partial, cumulative, empty, and mismatched-period results remain unpublished.
            </p>
          )}
        </section>
      )}

      {publicState.rankedRecords.length > 0 && (
        <BoxOfficeLeaderboard records={publicState.boardRecords} />
      )}

      <section className="panel bo-board-panel">
        <header className="bo-panel-head">
          <div>
            <p className="eyebrow">{weekLabel}</p>
            <h2>{publicState.noCurrentData ? "Current Closed-Week Availability" : "Latest Verified Closed Week"}</h2>
          </div>
          <span className="pill">{board.territory}</span>
        </header>
        <BoxOfficeBoardTable
          records={publicState.boardRecords}
          emptyState="No current exact-week figures have cleared the publication contract."
        />
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
