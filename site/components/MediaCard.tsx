import type { MediaItem } from "../lib/home";
import { PosterImage } from "./PosterImage";
import { SeasonVerdict } from "./SeasonVerdict";
import { VerdictMeter } from "./VerdictMeter";

// ONE card for film AND series. Reads a normalized MediaItem so the homepage rails never
// branch on type in markup. Fallback-safe: a missing poster renders an in-DOM, desk-tinted
// placeholder (so the card frame inherits the accent and carries no off-token hex), and the
// plate still carries title + type + desk + score.
export function MediaCard({ item }: { item: MediaItem }) {
  const posterless = !item.poster.src || item.poster.src.includes("_fallback");

  return (
    <a className="media-card" data-desk={item.desk} href={item.href}>
      <span className="media-card__frame">
        {posterless ? (
          <span className="one-sheet" aria-hidden="true">
            <span className="one-sheet__top">
              <span>{item.deskLabel}</span>
              <span>{item.recency.slice(0, 4)}</span>
            </span>
            <span className="one-sheet__title">{item.title}</span>
            <span className="one-sheet__foot">BollyAI Edition</span>
          </span>
        ) : (
          <PosterImage
            className="media-card__poster"
            src={item.poster.src}
            alt={item.poster.alt}
            width="342"
            height="513"
            loading="lazy"
            avifSrcSet={item.poster.variants?.avifSrcSet}
            webpSrcSet={item.poster.variants?.webpSrcSet}
            sizes="(max-width: 640px) 150px, 200px"
          />
        )}
        <span className={`media-card__type media-card__type--${item.kind}`}>{item.kind === "film" ? "Film" : "Series"}</span>
        {item.fresh && <span className="media-card__fresh">New</span>}
        {item.score !== null && (
          <span className="media-card__score">
            {item.score.toFixed(1)}
            <small>/10</small>
          </span>
        )}
      </span>
      <span className="media-card__plate">
        <span className="media-card__desk">{item.deskLabel}</span>
        <strong className="media-card__title">{item.title}</strong>
        <span className="media-card__meta">{item.meta}</span>
        <span className="media-card__meter">
          {item.kind === "series" ? (
            <SeasonVerdict rung={item.seriesRung ?? null} compact />
          ) : (
            <VerdictMeter rung={item.filmRung ?? null} tracking={item.filmTracking ?? true} compact />
          )}
        </span>
      </span>
    </a>
  );
}
