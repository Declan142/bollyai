import type { MediaItem } from "../lib/home";
import { PosterImage } from "./PosterImage";
import { SeasonVerdict } from "./SeasonVerdict";
import { VerdictMeter } from "./VerdictMeter";

// Up to two leading initials for the composed placeholder shown when a title has no real
// poster yet (many newly authored films/series do not). Keeps a posterless card looking
// intentional rather than like an empty loading slot.
function initials(title: string): string {
  const words = title.replace(/[^A-Za-z0-9\s]/g, "").trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "BA";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

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
          <span className="media-card__placeholder" aria-hidden="true">
            <span className="media-card__placeholder-mark">{initials(item.title)}</span>
            <span className="media-card__placeholder-brand">BollyAI</span>
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
