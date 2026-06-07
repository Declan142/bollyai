import { StaticPage } from "../../components/StaticPage";

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
        Movie metadata may use TMDB API data with attribution. BollyAI is not endorsed or certified by TMDB.
      </p>
    </StaticPage>
  );
}
