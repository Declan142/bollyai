import type { Metadata } from "next";
import { StaticPage } from "../../components/StaticPage";

export const metadata: Metadata = {
  title: "How BollyAI Works — Our Verdict & BollyMeter Method",
  description: "How BollyAI reads verified metadata, trade estimates, and OTT signals before publishing a verdict. Source rows, confidence labels, and generation gates explained."
};

export default function HowPage() {
  return (
    <StaticPage
      title="How BollyAI Works"
      answer="BollyAI reads verified metadata, trade estimates, OTT provider signals, and human-edited policy gates before publishing an answer."
      dateModified="2026-06-07T00:00:00+05:30"
    >
      <p>
        Every external value is stored with a source, fetch time, and confidence label. Box-office numbers publish only
        when the agreement rule allows them; otherwise the page says early estimates awaited.
      </p>
      <p>
        First-person viewing claims are blocked by a generation gate. The standing line is simple: BollyAI has not
        watched the film; BollyAI has read the room around it.
      </p>
      <p>Budgets and salaries are never auto-published. Without a cited first-party source, the rendered answer is undisclosed.</p>
    </StaticPage>
  );
}
