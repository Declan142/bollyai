import type { Metadata } from "next";
import { StaticPage } from "../../components/StaticPage";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Contact BollyAI",
  description: "Reach BollyAI for corrections, takedown requests, source disputes, and editorial feedback at contact@bollyai.in.",
  ...pageSeo({ path: "/contact/" })
};

export default function ContactPage() {
  return (
    <StaticPage
      title="Contact"
      answer="Contact BollyAI for corrections, takedown requests, source disputes, and editorial feedback."
      dateModified="2026-06-07T00:00:00+05:30"
    >
      <p>Email channel: contact@bollyai.in once domain mail routing is live.</p>
      <p>For urgent takedown matters, include the page URL and the exact material being disputed.</p>
    </StaticPage>
  );
}
