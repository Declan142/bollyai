import { BrowseClient, type BrowseItem } from "../../components/BrowseClient";
import { DateModified } from "../../components/DateModified";
import { getSeriesByRecency, peakSeason, seriesRecency, isFreshSeries } from "../../lib/series";

export const metadata = {
  title: "Browse Series & OTT Shows by Genre, Platform & Year",
  description:
    "Filter and sort BollyAI verdicts on Korean drama, anime, Indian OTT and global streaming by genre, platform, country and year. Newest drops surface first."
};

export default function SeriesIndex() {
  const all = getSeriesByRecency();
  const now = Date.now();
  const items: BrowseItem[] = all.map((s) => {
    const peak = peakSeason(s);
    const years = s.seasons.map((x) => x.year).filter(Boolean);
    const latestYear = years.length ? Math.max(...years) : null;
    return {
      slug: s.slug,
      t: s.title.value,
      p: s.poster.src,
      o: s.origin,
      pl: s.platform.value,
      st: s.status,
      g: s.genres ?? [],
      yr: latestYear,
      v: peak?.verdict ?? null,
      sc: peak?.bollymeter?.score ?? null,
      r: seriesRecency(s),
      fr: isFreshSeries(s, now)
    };
  });

  return (
    <main className="page-shell" data-desk="streaming">
      <section className="section-head">
        <p className="eyebrow">Series desk · {all.length} shows · India · Korea · anime · global OTT</p>
        <h1>Browse Series &amp; OTT</h1>
        <p className="answer-block">
          Every web series BollyAI has read the room on, in one filterable wall. Sort by what just dropped, by BollyMeter,
          or A to Z; narrow by genre, platform, country, or era. Money never decides a series here, word of mouth and craft do.
        </p>
        <DateModified value={all[0]?.date_modified ?? "2026-06-09T00:00:00+05:30"} />
      </section>

      <BrowseClient items={items} />
    </main>
  );
}
