import type { Metadata } from "next";
import { StaticPage } from "../../components/StaticPage";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Content Takedown & Fair-Dealing Policy",
  description: "Rights holders can request correction or removal of image, attribution, or factual material. BollyAI targets a 36-hour first response for valid complaints.",
  ...pageSeo({ path: "/takedown/" })
};

export default function TakedownPage() {
  return (
    <StaticPage
      title="Takedown"
      answer="Rights holders can request correction or removal of image, attribution, or factual material through the BollyAI contact channel."
      dateModified="2026-06-07T00:00:00+05:30"
    >
      <p>
        Send the URL, the disputed material, proof of rights or authority, and the requested action. BollyAI targets a
        36-hour first response for valid image and attribution complaints.
      </p>
      <p>Until a dedicated mailbox is provisioned, use the contact page for takedown requests.</p>
    </StaticPage>
  );
}
