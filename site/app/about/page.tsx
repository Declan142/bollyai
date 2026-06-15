import type { Metadata } from "next";
import { SectionHero } from "../../components/SectionHero";
import { AboutMasthead } from "../../components/AboutMasthead";
import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import { FOUNDER, organizationJsonLd } from "../../lib/jsonld";
import { getAllSeries } from "../../lib/series";
import { DESKS } from "../../lib/desks";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "About BollyAI - Who We Are & How We Judge",
  description:
    "BollyAI is a disclosed AI critic for Indian entertainment: one brain, seven desks, and a source-first verdict system that separates craft from commerce, signed by editor Aditya Sharma.",
  ...pageSeo({ path: "/about/" })
};

const dateModified = "2026-06-16T00:00:00+05:30";

export default function AboutPage() {
  const seriesCount = getAllSeries().length;

  return (
    <main className="page-shell" data-desk="bollywood">
      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "AboutPage",
          name: "About BollyAI",
          url: "https://bollyai.in/about/",
          dateModified,
          mainEntity: { ...organizationJsonLd(), "@context": undefined },
          publisher: { "@id": "https://bollyai.in/#org" }
        }}
      />
      <JsonLd
        data={{
          "@context": "https://schema.org",
          ...FOUNDER,
          description:
            "Founder and editor of BollyAI. Signs and source-checks every verdict; the drafting is disclosed AI, the judgement is human.",
          worksFor: { "@id": "https://bollyai.in/#org" }
        }}
      />

      <SectionHero
        eyebrow="About BollyAI"
        title="The critic that reads the room, then signs its name"
        lede={
          <>
            A disclosed AI critic for pan-India cinema and OTT. <b>One brain, seven desks,</b> and a
            source-first verdict system that keeps craft separate from commerce.
          </>
        }
        stats={[
          { value: String(seriesCount), label: "Series read" },
          { value: String(DESKS.length), label: "Desks" },
          { value: "0", label: "Invented numbers" }
        ]}
        cta={{ href: "/how-bollyai-works/", label: "How BollyAI works" }}
      >
        <DateModified value={dateModified} />
      </SectionHero>

      <AboutMasthead />
    </main>
  );
}
