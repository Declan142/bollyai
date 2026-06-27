import { AnswerBlock } from "../../../components/AnswerBlock";
import { BoxOfficeComparatorClient } from "../../../components/BoxOfficeComparatorClient";
import { JsonLd } from "../../../components/JsonLd";
import { getComparatorFilmOptions, latestToolDate } from "../../../lib/tool-data";
import { pageSeo } from "../../../lib/seo";

export const metadata = {
  title: "X vs Y Box Office Comparator",
  description:
    "Compare Hollywood box-office runs day by day using BollyAI's published day-wise trade-estimate rows.",
  ...pageSeo({ path: "/tools/box-office-comparator/" })
};

export default function BoxOfficeComparatorPage() {
  const films = getComparatorFilmOptions();
  const dateModified = latestToolDate(films);
  const answer =
    `BollyAI's box-office comparator currently has ${films.length} films with published day-wise box-office rows. It defaults to day-aligned comparisons and keeps missing days blank until the two-source publish rule clears.`;

  return (
    <main className="page-shell tool-shell" data-desk="hollywood">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          name: "Films available in the BollyAI box-office comparator",
          dateModified,
          numberOfItems: films.length,
          itemListElement: films.map((film, index) => ({
            "@type": "ListItem",
            position: index + 1,
            item: {
              "@type": "Movie",
              name: film.title,
              datePublished: film.releaseDate,
              url: `https://bollyai.in${film.trackerPath}`
            }
          }))
        }}
      />
      <section className="section-head tool-head">
        <p className="eyebrow">Interactive tools</p>
        <h1>Box Office Comparator</h1>
        <AnswerBlock>{answer}</AnswerBlock>
      </section>

      <BoxOfficeComparatorClient films={films} />

      <section className="content-sections">
        <section className="panel tool-method">
          <h2>Methodology</h2>
          <p>
            Day-aligned mode compares Day 1 with Day 1, Day 2 with Day 2, and so on. That is the trade-correct view
            for films released on different dates. Calendar-aligned mode is retained for live clashes that share the
            same release window.
          </p>
          <p>
            The comparator uses only published box-office ranges from repo film JSON. Worldwide day-wise gross and
            footfalls remain in tracking state until Seat 03 emits those fields, so the disabled metric buttons stay
            visible but unavailable.
          </p>
        </section>

        <section className="panel">
          <h2>Internal Mesh</h2>
          <p>
            Every selected film links back to its box-office tracker. The companion calculator handles verdict math
            from budget and gross inputs, while this page handles the trajectory race.
          </p>
          <nav className="mesh-links" aria-label="Tool links">
            <a href="/tools/hit-flop-calculator/">Hit-flop calculator</a>
            <a href="/hollywood/box-office/dune-part-two/">Dune Part Two tracker</a>
            <a href="/hollywood/box-office/deadpool-wolverine/">Deadpool and Wolverine tracker</a>
            <a href="/hollywood/box-office/conclave/">Conclave tracker</a>
          </nav>
        </section>
      </section>
    </main>
  );
}
