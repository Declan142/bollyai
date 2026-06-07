import type { SeriesSeason } from "../lib/series";

export function CriticConsensus({ season }: { season: SeriesSeason }) {
  const { audience } = season;
  const critic = season.critic ?? { positive_pct: null, sample: null, pull_quotes: [] };
  const pullQuotes = critic.pull_quotes ?? [];
  return (
    <div className="critic-consensus">
      <div className="critic-consensus__meters">
        {critic.positive_pct !== null && (
          <span className="critic-stat">
            <strong>{critic.positive_pct}%</strong>
            <span>critics positive{critic.sample ? ` · n=${critic.sample}` : ""}</span>
          </span>
        )}
        {audience && audience.rating !== null && (
          <span className="critic-stat">
            <strong>
              {audience.rating}
              <small>/{audience.scale}</small>
            </strong>
            <span>
              <a href={audience.source_url}>{audience.source}</a> audience
            </span>
          </span>
        )}
      </div>
      {pullQuotes.length > 0 && (
        <ul className="pull-quotes">
          {pullQuotes.map((q) => (
            <li key={q.url}>
              <blockquote>&ldquo;{q.text}&rdquo;</blockquote>
              <cite>
                <a href={q.url}>{q.source}</a>
              </cite>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
