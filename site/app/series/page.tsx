import { DateModified } from "../../components/DateModified";
import { SeasonVerdict } from "../../components/SeasonVerdict";
import { getAllSeries, latestSeason } from "../../lib/series";

export const metadata = {
  title: "Series & OTT shows — BollyAI verdicts",
  description: "BollyAI reads the room on web series across India, Korea, and global OTT: season verdicts, renewal odds, and where to watch."
};

export default function SeriesIndex() {
  const series = getAllSeries();
  return (
    <main className="page-shell" data-desk="streaming">
      <section className="section-head">
        <p className="eyebrow">Series desk · India · Korea · global OTT</p>
        <h1>Series &amp; OTT</h1>
        <p className="answer-block">
          Season-by-season verdicts on web series across Indian OTT, Korean drama, and global streaming. Money never
          decides a series here; word of mouth, craft, and renewal signal do. BollyAI reads every review so you do not
          have to gamble a weekend.
        </p>
        <DateModified value={series[0]?.date_modified ?? "2026-06-08T00:00:00+05:30"} />
      </section>

      <section className="series-grid">
        {series.map((s) => {
          const season = latestSeason(s);
          return (
            <a className="series-card" data-desk={s.canonical_industry} href={`/series/${s.slug}/`} key={s.slug}>
              <img src={s.poster.src} alt={s.poster.alt} width="342" height="513" loading="lazy" />
              <span className="series-card__body">
                <span className="series-card__origin">{s.origin}</span>
                <strong>{s.title.value}</strong>
                <span className="series-card__plat">{s.platform.value}</span>
                {season && <SeasonVerdict rung={season.verdict} compact />}
              </span>
            </a>
          );
        })}
      </section>
    </main>
  );
}
