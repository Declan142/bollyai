import type { Metadata } from "next";
import { StaticPage } from "../../components/StaticPage";

export const metadata: Metadata = {
  title: "Disclaimer",
  description: "BollyAI publishes entertainment analysis and trade-estimate framing, not official financial certification. Numbers carry source rows and confidence labels."
};

export default function DisclaimerPage() {
  return (
    <StaticPage
      title="Disclaimer"
      answer="BollyAI publishes entertainment analysis and trade-estimate framing, not official financial certification."
      dateModified="2026-06-07T00:00:00+05:30"
    >
      <p>
        Indian box-office numbers are trade estimates unless an official source states otherwise. BollyAI keeps ranges,
        labels, and source rows visible so readers can see the uncertainty.
      </p>
      <p>
        Movie metadata is keyed on Wikidata QIDs, and OTT availability is shown only as attributed official,
        social, or trade-announcement fact.
      </p>
    </StaticPage>
  );
}
