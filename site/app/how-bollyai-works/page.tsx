import { StaticPage } from "../../components/StaticPage";

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
