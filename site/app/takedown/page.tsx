import type { Metadata } from "next";
import { LegalPage } from "../../components/LegalPage";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Content Takedown & Fair-Dealing Policy",
  description: "Rights holders can request correction or removal of image, attribution, or factual material. BollyAI targets a 36-hour first response for valid complaints.",
  ...pageSeo({ path: "/takedown/" })
};

export default function TakedownPage() {
  return (
    <LegalPage
      eyebrow="BollyAI policy"
      title="Takedown"
      dateModified="2026-06-12T00:00:00+05:30"
      lead="Rights holders can request correction or removal of image, attribution, or factual material, and BollyAI acts on valid complaints quickly."
    >
      <h2>How to file</h2>
      <p>
        Email <a href="mailto:takedown@bollyai.in">takedown@bollyai.in</a> with the page URL, the disputed material,
        proof of rights or authority, and the requested action. The more specific the complaint, the faster it can be
        actioned.
      </p>
      <h2>Response time</h2>
      <p>
        BollyAI targets a 36-hour first response for valid image and attribution complaints. Genuine rights issues are
        resolved by correction or removal, not delay.
      </p>
      <h2>How images are used</h2>
      <p>
        Images are used sparingly for criticism and review, with attribution stored beside self-hosted files. BollyAI
        does not rehost third-party galleries or redistribute subtitle text; dialogue is quoted only briefly, with a
        citation, in service of analysis.
      </p>
    </LegalPage>
  );
}
