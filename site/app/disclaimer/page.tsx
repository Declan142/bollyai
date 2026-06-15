import type { Metadata } from "next";
import { LegalPage } from "../../components/LegalPage";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Disclaimer",
  description: "BollyAI publishes entertainment analysis and trade-estimate framing, not official financial certification. Numbers carry source rows and confidence labels.",
  ...pageSeo({ path: "/disclaimer/" })
};

export default function DisclaimerPage() {
  return (
    <LegalPage
      eyebrow="BollyAI policy"
      title="Disclaimer"
      dateModified="2026-06-07T00:00:00+05:30"
      lead="BollyAI publishes entertainment analysis and trade-estimate framing, not official financial certification."
    >
      <h2>Box-office numbers are estimates</h2>
      <p>
        Indian box-office numbers are trade estimates unless an official source states otherwise. BollyAI keeps ranges,
        labels, and source rows visible so readers can see the uncertainty rather than a falsely precise figure. A number
        appears only when independent readings agree under the publish rule.
      </p>
      <h2>Metadata and availability</h2>
      <p>
        Movie and series metadata is keyed on Wikidata QIDs. OTT availability is shown only as attributed official,
        social, or trade-announcement fact, never as an invented view count, because Indian platforms do not publish
        per-title viewership.
      </p>
      <h2>Disclosed AI</h2>
      <p>
        BollyAI is a disclosed AI critic. It has not watched the titles it covers; it reads critics and audiences and
        writes in the third person. Read <a href="/how-bollyai-works/">how the method works</a> for the full picture.
      </p>
    </LegalPage>
  );
}
