import type { Metadata } from "next";
import { StaticPage } from "../../components/StaticPage";

export const metadata: Metadata = {
  title: "Privacy Policy",
  description: "BollyAI is a static site. No accounts, no uploads, no sensitive data collection. Analytics tools, when enabled, will be disclosed here."
};

export default function PrivacyPage() {
  return (
    <StaticPage
      title="Privacy"
      answer="BollyAI is a static site and does not need account data to serve reviews, trackers, or OTT calendar pages."
      dateModified="2026-06-07T00:00:00+05:30"
    >
      <p>
        The v1 site is static. It does not ask readers to create accounts, upload private files, or submit sensitive
        personal information.
      </p>
      <p>Advertising or analytics tools, when enabled, will be disclosed here with their provider names and purposes.</p>
    </StaticPage>
  );
}
