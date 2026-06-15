import { DateModified } from "../../components/DateModified";
import { JsonLd } from "../../components/JsonLd";
import { SectionHero } from "../../components/SectionHero";
import { breadcrumbJsonLd } from "../../lib/jsonld";
import { getAllWatchLists } from "../../lib/recommendations";
import { pageSeo } from "../../lib/seo";

export const metadata = {
  title: "What to Watch - Curated Streaming Picks for India",
  description:
    "Curated watch lists across Indian cinema, OTT, and Korean drama. What is actually worth a weekend, where it streams, and why - BollyAI reads the room so you don't gamble the night.",
  ...pageSeo({ path: "/watch/" })
};

export default function WatchIndex() {
  const lists = getAllWatchLists();
  const totalPicks = lists.reduce((sum, list) => sum + list.picks.length, 0);
  return (
    <main className="page-shell" data-desk="streaming">
      <JsonLd
        data={breadcrumbJsonLd([
          { name: "Home", url: "/" },
          { name: "What to Watch", url: "/watch/" }
        ])}
      />
      <SectionHero
        eyebrow="Recommendations · theatres · OTT · K-drama"
        title="What to Watch"
        lede={
          <>
            Not a star-rating dump. <b>Curated lists for a specific mood, platform, or weekend,</b> each pick naming
            where it streams and earning its slot on craft and word of mouth. BollyAI has not watched these. BollyAI
            has read everyone who has.
          </>
        }
        stats={[
          { value: String(lists.length), label: "Curated lists" },
          { value: String(totalPicks), label: "Picks" }
        ]}
      >
        <DateModified value={lists[0]?.updated ?? "2026-06-08T00:00:00+05:30"} />
      </SectionHero>

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
