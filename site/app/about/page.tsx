import type { Metadata } from "next";
import { StaticPage } from "../../components/StaticPage";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "About BollyAI — Who We Are & How We Judge",
  description: "BollyAI is a disclosed AI critic for Indian entertainment: one brain, seven desks, and a source-first verdict system that separates craft from commerce.",
  ...pageSeo({ path: "/about/" })
};

export default function AboutPage() {
  return (
    <StaticPage
      title="About BollyAI"
      answer="BollyAI is a disclosed AI critic for Indian entertainment: one brain, seven desks, and a source-first verdict system."
      dateModified="2026-06-07T00:00:00+05:30"
    >
      <p>
        BollyAI exists to answer the question people actually ask after every release: is it worth the time, is it
        making money, and where can I watch it now?
      </p>
      <p>
        The site separates craft from commerce. BollyMeter is the /10 craft score. The verdict ladder is the trade
        result. A film can be a flop and still be good cinema.
      </p>
    </StaticPage>
  );
}
