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
      answer="Rights holders can request correction or removal of image, attribution, or factual material at takedown@bollyai.in."
      dateModified="2026-06-12T00:00:00+05:30"
    >
      <p>
        Email <a href="mailto:takedown@bollyai.in">takedown@bollyai.in</a> with the page URL, the disputed material,
        proof of rights or authority, and the requested action. BollyAI targets a 36-hour first response for valid image
        and attribution complaints.
      </p>
      <p>Images are used sparingly for criticism and review, with attribution stored beside self-hosted files.</p>
    </StaticPage>
  );
}
