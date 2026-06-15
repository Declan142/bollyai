import type { Metadata } from "next";
import { AskClient } from "../../components/AskClient";
import { JsonLd } from "../../components/JsonLd";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: { absolute: "Ask BollyAI - Grounded Verdicts for Indian & Global OTT" },
  description:
    "Ask a real question - is it worth watching, the best in a genre, where to stream - and get a verdict assembled only from BollyAI's grounded critic, audience and subtitle data. No invented scores.",
  ...pageSeo({ path: "/ask/" })
};

export default function AskPage() {
  return (
    <main className="page-shell ask-page" data-desk="bollywood">
      <section className="section-head ask-head">
        <p className="eyebrow">The answer engine</p>
        <h1>Ask BollyAI</h1>
        <p className="ask-head__sub">
          One question - is it worth watching, the best in a genre, where it streams - answered from
          grounded verdicts only. BollyAI has not watched anything; it has read everyone who has.
        </p>
      </section>

      <AskClient />

      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "WebApplication",
          name: "Ask BollyAI",
          applicationCategory: "EntertainmentApplication",
          operatingSystem: "Web",
          url: "https://bollyai.in/ask/",
          description:
            "Client-side answer engine returning BollyAI verdicts assembled from grounded critic, audience and subtitle data."
        }}
      />
    </main>
  );
}
