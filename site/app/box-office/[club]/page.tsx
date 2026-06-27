import { notFound } from "next/navigation";
import { AnswerBlock } from "../../../components/AnswerBlock";
import { BoxOfficeBoardTable } from "../../../components/BoxOfficeBoardTable";
import { DateModified } from "../../../components/DateModified";
import { JsonLd } from "../../../components/JsonLd";
import {
  boxOfficeDatasetJsonLd,
  boxOfficeRecordsItemListJsonLd,
  getBoxOfficeClub,
  getBoxOfficeClubs,
  getClubRecords,
  getCurrentBoxOfficeBoard
} from "../../../lib/boxoffice";
import { pageSeo } from "../../../lib/seo";

export const dynamicParams = false;

export function generateStaticParams() {
  return getBoxOfficeClubs().map((club) => ({ club: club.slug }));
}

export function generateMetadata({ params }: { params: { club: string } }) {
  const club = getBoxOfficeClub(params.club);
  if (!club) return {};
  return {
    title: `${club.label} - Box Office Tracker`,
    description: `${club.label} tracker, publishing only source-gated trade figures.`,
    ...pageSeo({ path: `/box-office/${club.slug}/` })
  };
}

export default function BoxOfficeClubPage({ params }: { params: { club: string } }) {
  const club = getBoxOfficeClub(params.club);
  if (!club) {
    notFound();
  }

  const board = getCurrentBoxOfficeBoard();
  const records = getClubRecords(club.tier);
  const answer = `This club lists films with a sourced worldwide gross at or above $${club.tier}M USD from Wikidata P2142 or TMDB. No invented or extrapolated figures qualify.`;

  return (
    <main className="page-shell box-office-hub" data-desk="hollywood">
      <JsonLd
        data={boxOfficeDatasetJsonLd({
          name: `${club.label} tracker`,
          description: `${club.label} cross-industry box-office dataset using conservative source-gated figures.`,
          url: `/box-office/${club.slug}/`,
          dateModified: board.generated_at,
          records
        })}
      />
      <JsonLd
        data={boxOfficeRecordsItemListJsonLd({
          name: `${club.label} entries`,
          description: `Films that have cleared the ${club.label} threshold under BollyAI publish rules.`,
          records
        })}
      />
      <section className="section-head box-office-head">
        <p className="eyebrow">Cross-industry club</p>
        <h1>{club.label}</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <DateModified value={board.generated_at} />
      </section>

      <section className="panel bo-board-panel">
        <header className="bo-panel-head">
          <div>
            <p className="eyebrow">Verified entries</p>
            <h2>Club Board</h2>
          </div>
          <span className="pill">${club.tier}M USD threshold</span>
        </header>
        <BoxOfficeBoardTable
          records={records}
          emptyState="No film has cleared this club threshold under the renderer publish rule yet."
        />
      </section>
    </main>
  );
}
