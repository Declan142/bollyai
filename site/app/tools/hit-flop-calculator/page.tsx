import { AnswerBlock } from "../../../components/AnswerBlock";
import { HitFlopCalculatorClient } from "../../../components/HitFlopCalculatorClient";
import { JsonLd } from "../../../components/JsonLd";
import { getCalculatorFilmOptions, latestToolDate } from "../../../lib/tool-data";
import { pageSeo } from "../../../lib/seo";

export const metadata = {
  title: "Hit-Flop Verdict Calculator India",
  description:
    "Calculate an honest Indian box-office hit or flop band from budget, gross, GST and distributor-share assumptions.",
  ...pageSeo({ path: "/tools/hit-flop-calculator/" })
};

export default function HitFlopCalculatorPage() {
  const films = getCalculatorFilmOptions();
  const filmsWithInputs = films.filter((film) => film.worldwideGrossCr || film.indiaNetCr).slice(0, 12);
  const dateModified = latestToolDate(films);
  const answer =
    "BollyAI's hit-flop calculator converts gross to nett, applies an editable distributor-share ratio, and maps recovery to the 9-rung trade ladder. Estimated budgets or default share ratios render a verdict band, not fake precision.";

  return (
    <main className="page-shell tool-shell" data-desk="bollywood">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "ItemList",
          name: "Films with BollyAI hit-flop calculator inputs",
          dateModified,
          numberOfItems: filmsWithInputs.length,
          itemListElement: filmsWithInputs.map((film, index) => ({
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
        <h1>Hit-Flop Verdict Calculator</h1>
        <AnswerBlock>{answer}</AnswerBlock>
      </section>

      <HitFlopCalculatorClient films={films} />

      <section className="content-sections">
        <section className="panel tool-method">
          <h2>Methodology</h2>
          <p>
            The calculator follows the Seat 08 trade path: gross is adjusted by the selected tax rate, the resulting nett
            estimate is multiplied by the distributor-share ratio, and that share is divided by budget. The 0.45 share
            ratio and the exact rung edges are BollyAI house assumptions, so the output widens to a band whenever the
            inputs are estimated.
          </p>
          <p>
            Trade verdicts are fundamentally about distributor recovery, not a universal gross multiplier. See the{" "}
            <a href="/how-bollyai-works/">BollyAI methodology</a>, the{" "}
            <a href="https://www.boxofficeindia.com/content.php?pagekey=glossary">Box Office India glossary</a>, and the{" "}
            <a href="https://cleartax.in/s/media-entertainment-taxation-gst">ClearTax GST explainer</a>.
          </p>
        </section>

        <section className="panel">
          <h2>Live Inputs</h2>
          <p>
            Repo film records currently expose pair-verified box-office ranges more often than first-party budgets.
            When a film budget is undisclosed, the calculator waits for the user to enter a sourced or trade-estimated
            budget instead of publishing a made-up verdict.
          </p>
          <nav className="mesh-links" aria-label="Tool links">
            <a href="/tools/box-office-comparator/">Compare day-wise box office</a>
            <a href="/hollywood/">Hollywood desk</a>
            <a href="/ott/calendar/">OTT calendar</a>
          </nav>
        </section>
      </section>
    </main>
  );
}
