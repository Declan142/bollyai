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
    <main className="page-shell" data-desk="bollywood">
      <section className="section-head">
        <p className="eyebrow">Search</p>
        <h1>Search BollyAI</h1>
      </section>
      <SearchClient />
    </main>
  );
}
