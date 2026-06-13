import { getRelatedSeries } from "../lib/links";
import { peakSeason, qualifiesForWhereToWatch } from "../lib/series";
import { PosterImage } from "./PosterImage";
import { SeasonVerdict } from "./SeasonVerdict";

// "Watch Next" - the inter-series link mesh, surfaced. Additive server component: it reads the
// centralized, precomputed mesh (lib/links.ts -> data/_state/series-links.json) and renders a
// horizontal poster wall of related titles, each with a one-line editorial hook (curated note
// or a computed reason like "More Korean thrillers"). Reuses the existing .poster-wall /
// .poster-card styling so it inherits the house aesthetic and adds zero new CSS surface.
//
// Honesty: the reason strings come from the mesh (real genre/language/platform/era signals or a
// hand-written curated note) - never a fabricated metric and never a first-person viewing claim.

export function RelatedSeries({ slug, limit = 8 }: { slug: string; limit?: number }) {
  const related = getRelatedSeries(slug, limit);
  if (related.length === 0) return null;

  return (
    <section className="panel watch-next">
      <h2>Watch Next</h2>
      <p className="panel-sub">If that landed, BollyAI points you here next.</p>
      <div className="poster-wall">
        {related.map(({ series, reason }) => {
          const cp = peakSeason(series);
          const href = qualifiesForWhereToWatch(series)
            ? `/series/${series.slug}/where-to-watch/`
            : `/series/${series.slug}/`;
          return (
            <a className="poster-card" data-desk="streaming" href={href} key={series.slug}>
              <PosterImage
                src={series.poster.src}
                alt={series.poster.alt}
                width="342"
                height="513"
                loading="lazy"
                avifSrcSet={series.poster.variants?.avifSrcSet}
                webpSrcSet={series.poster.variants?.webpSrcSet}
              />
              <span className="poster-card__plate">
                <strong>{series.title.value}</strong>
                <span className="poster-card__money">{reason}</span>
                {cp && <SeasonVerdict rung={cp.verdict} compact />}
              </span>
            </a>
          );
        })}
      </div>
    </section>
  );
}
