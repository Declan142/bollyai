import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import { breadcrumbJsonLd } from "../../lib/jsonld";
import { getAllWatchLists } from "../../lib/recommendations";
import { pageSeo } from "../../lib/seo";

export const metadata = {
  title: "What to Watch — Curated Streaming Picks for India",
  description:
    "Curated watch lists across Indian cinema, OTT, and Korean drama. What is actually worth a weekend, where it streams, and why — BollyAI reads the room so you don't gamble the night.",
  ...pageSeo({ path: "/watch/" })
};

export default function WatchIndex() {
  const lists = getAllWatchLists();
  return (
    <main className="page-shell" data-desk="streaming">
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "What to Watch", url: "/watch/" }
        ])}
      />
      <section className="section-head">
        <p className="eyebrow">Recommendations · theatres · OTT · K-drama</p>
        <h1>What to Watch</h1>
        <p className="answer-block">
          Not a star rating dump — curated lists for a specific mood, platform, or weekend. Every pick names where it
          streams and earns its slot on craft and word of mouth. BollyAI hasn&apos;t watched these. BollyAI has read
          everyone who has.
        </p>
        <DateModified value={lists[0]?.updated ?? "2026-06-08T00:00:00+05:30"} />
      </section>

      <section className="watch-grid">
        {lists.map((list) => (
          <a className="watch-card" data-desk={list.desk ?? "streaming"} href={`/watch/${list.slug}/`} key={list.slug}>
            <span className="watch-card__kicker">{list.kicker}</span>
            <strong>{list.title}</strong>
            <span className="watch-card__intro">{list.intro}</span>
            <span className="watch-card__count">{list.picks.length} picks →</span>
          </a>
        ))}
      </section>
    </main>
  );
}
