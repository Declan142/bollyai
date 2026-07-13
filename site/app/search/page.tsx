import { SearchClient } from "../../components/SearchClient";
import { pageSeo } from "../../lib/seo";

export const metadata = {
  title: "Search",
  description: "Search BollyAI films, series, ending explainers and watch lists.",
  ...pageSeo({ path: "/search/" }),
  // Search results are a utility surface, never an indexable destination.
  robots: { index: false, follow: true }
};

export default function SearchPage() {
  return (
    <main className="page-shell" data-desk="streaming">
      <section className="section-head search-head">
        <p className="eyebrow">Answer engine</p>
        <h1>Search BollyAI</h1>
        <p className="search-head__sub">One field over every desk - films, series, ending explainers and watch lists, each with the verdict attached.</p>
      </section>
      <SearchClient />
    </main>
  );
}
