import type { Metadata } from "next";
import { LegalPage } from "../../components/LegalPage";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "BollyAI is a static site. No accounts, no uploads, no sensitive data collection. Analytics tools, when enabled, will be disclosed here.",
  ...pageSeo({ path: "/privacy/" })
};

export default function PrivacyPage() {
  return (
    <LegalPage
      eyebrow="BollyAI policy"
      title="Privacy"
      dateModified="2026-06-07T00:00:00+05:30"
      lead="BollyAI is a static site. It does not need account data to serve reviews, trackers, or the OTT calendar, so it does not ask for any."
    >
      <h2>What is not collected</h2>
      <p>
        The v1 site is static. It does not ask readers to create accounts, upload private files, or submit sensitive
        personal information. There is no login, no profile, and no server-side store of who you are.
      </p>
      <h2>Analytics and advertising</h2>
      <p>
        If advertising or analytics tools are enabled later, they will be disclosed here by provider name and purpose
        before they go live. Until then, this page is the honest current state.
      </p>
      <h2>Questions</h2>
      <p>
        Privacy questions can go to <a href="/contact/">the contact page</a>. Corrections and rights matters are handled
        through <a href="/takedown/">the takedown policy</a>.
      </p>
    </LegalPage>
  );
}
