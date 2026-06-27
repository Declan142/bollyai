import type { Metadata } from "next";
import { BoxOfficeBoardTable } from "../../components/BoxOfficeBoardTable";
import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import { SectionHero } from "../../components/SectionHero";
import { BoxOfficeLeaderboard } from "../../components/BoxOfficeLeaderboard";
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
  title: "Worldwide Box Office Tracker - Weekly USD Board",
  description:
    "Current-week worldwide theatrical box-office tracker with source-attributed USD gross figures from Wikidata and TMDB.",
  ...pageSeo({ path: "/box-office/" })
};

export default function BoxOfficeHubPage() {
  const board = getCurrentBoxOfficeBoard();
  const weekLabel = board.week?.label ?? "Current week";

  return (
    <main className="page-shell box-office-hub" data-desk="hollywood">
      <JsonLd
        data={boxOfficeDatasetJsonLd({
          name: `Box office tracker: ${weekLabel}`,
          description: "Current-week box-office dataset with conservative source-gated publishing.",
          url: "/box-office/",
          dateModified: board.generated_at,
          records: board.records
        })}
      />
      <JsonLd data={boxOfficeItemListJsonLd(board)} />
      <SectionHero
        eyebrow="Box office desk"
        title="Worldwide box office"
        lede={
          <>
            Current-week worldwide theatrical gross in USD. Figures are sourced from Wikidata P2142 and TMDB -
            <b> only real attributed data appears here.</b> No invented or extrapolated numbers.
          </>
        }
        stats={[
          { value: String(board.records.length), label: "Films tracked" },
          { value: weekLabel, label: "Trade week" },
          { value: board.territory, label: "Territory" }
        ]}
      >
        <DateModified value={board.generated_at} />
      </SectionHero>

      {board.DATA_PENDING && (
        <section className="panel bo-alert" aria-label="Data status">
          <p className="eyebrow">Data pending</p>
          <h2>No sourced figures yet</h2>
          <p>
            Wikidata P2142 or TMDB have not returned current-week records yet. The board updates automatically when
            the scheduled refresh runs. Missing data is the honest state.
          </p>
        </section>
      )}

      {!board.DATA_PENDING && board.records.length > 0 && (
        <BoxOfficeLeaderboard records={board.records} />
      )}

      <section className="panel bo-board-panel">
        <header className="bo-panel-head">
          <div>
            <p className="eyebrow">{weekLabel}</p>
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
          <p className="eyebrow">Data sources</p>
          <h2>Where figures come from</h2>
          <p>
            Worldwide gross figures are sourced from Wikidata P2142 (box office gross property, USD) and the TMDB
            revenue field. Both are public attributed sources. Each figure carries a source URL so you can verify it
            directly.
          </p>
        </article>
        <article className="panel">
          <p className="eyebrow">What is excluded</p>
          <h2>No budgets or invented figures</h2>
          <p>
            Budgets, salaries, and streaming view counts are not published here. If a film does not have a sourced
            worldwide gross in Wikidata or TMDB, it does not appear on this board.
          </p>
        </article>
      </section>
    </main>
  );
}
