import { CountUp } from "./CountUp";
import { PosterImage } from "./PosterImage";
import { VerdictMeter } from "./VerdictMeter";
import type { Film } from "../lib/data";
import type { MediaItem } from "../lib/home";

// Up to two leading initials for a posterless tile - mirrors MediaCard so a tile with no
// real artwork yet still reads as designed, not as an empty loading slot.
function initials(title: string): string {
  const words = title.replace(/[^A-Za-z0-9\s]/g, "").trim().split(/\s+/).filter(Boolean);
  if (words.length === 0) return "BA";
  if (words.length === 1) return words[0].slice(0, 2).toUpperCase();
  return (words[0][0] + words[1][0]).toUpperCase();
}

// One overlay tile for a secondary door (film OR series). The artwork fills the cell and the
// plate sits on top of a scrim, so the same tile reads cleanly at any bento aspect ratio
// (tall poster, square, or wide streaming-strip). Fallback-safe: no poster -> tinted mark.
function MosaicTile({ item, slot }: { item: MediaItem; slot: string }) {
  const posterless = !item.poster.src || item.poster.src.includes("_fallback");
  return (
    <a className={`mosaic-tile ${slot}`} data-desk={item.desk} href={item.href}>
      <span className="mosaic-tile__art">
        {posterless ? (
          <span className="mosaic-tile__placeholder" aria-hidden="true">
            <span className="mosaic-tile__placeholder-mark">{initials(item.title)}</span>
          </span>
        ) : (
          <PosterImage
            className="mosaic-tile__poster"
            src={item.poster.src}
            alt={item.poster.alt}
            width="342"
            height="513"
            loading="lazy"
            avifSrcSet={item.poster.variants?.avifSrcSet}
            webpSrcSet={item.poster.variants?.webpSrcSet}
            sizes="(max-width: 560px) 92vw, (max-width: 900px) 46vw, 300px"
          />
        )}
      </span>
      <span className="mosaic-tile__scrim" aria-hidden="true" />
      <span className={`mosaic-tile__type mosaic-tile__type--${item.kind}`}>
        {item.kind === "film" ? "Film" : "Series"}
      </span>
      {item.fresh && <span className="mosaic-tile__fresh">New</span>}
      {item.score !== null && (
        <span className="mosaic-tile__score">
          {item.score.toFixed(1)}
          <small>/10</small>
        </span>
      )}
      <span className="mosaic-tile__plate">
        <span className="mosaic-tile__desk">{item.deskLabel}</span>
        <strong className="mosaic-tile__title">{item.title}</strong>
        <span className="mosaic-tile__meta">{item.meta}</span>
      </span>
    </a>
  );
}

// The above-the-fold FEATURED MOSAIC. Replaces the single full-bleed hero with a bento wall:
// one contained LEAD verdict tile + a films+series mix of secondary doors, then the live
// catalogue counts ribbon. "The whole alive empire at a glance, many doors in."
export function FeaturedMosaic({
  lead,
  leadHref,
  leadFig,
  tiles,
  stats,
  desksLive,
  updated
}: {
  lead: Film;
  leadHref: string;
  leadFig: { label: string; text: string } | null;
  tiles: MediaItem[];
  stats: { films: number; series: number };
  desksLive: number;
  updated: string;
}) {
  // Deterministic bento placement: 8 secondary doors mapped to fixed slots around the lead.
  const slots = [
    "mosaic-tile--tall",
    "mosaic-tile--tall",
    "mosaic-tile--cell",
    "mosaic-tile--cell",
    "mosaic-tile--cell",
    "mosaic-tile--cell",
    "mosaic-tile--wide",
    "mosaic-tile--wide"
  ];

  return (
    <section className="featured-mosaic" aria-label="Featured verdicts and trending titles">
      <div className="featured-mosaic__grid">
        <a className="mosaic-lead" data-desk={lead.canonical_industry} href={leadHref}>
          <span className="mosaic-lead__art">
            <img
              className="mosaic-lead__backdrop"
              src={lead.backdrop?.src ?? lead.poster.src}
              alt={lead.backdrop?.alt ?? lead.poster.alt}
              fetchPriority="high"
              loading="eager"
              width="960"
              height="540"
            />
          </span>
          <span className="mosaic-lead__scrim" aria-hidden="true" />
          <span className="mosaic-lead__body">
            <span className="mosaic-lead__brand">
              BollyAI <span>Har Friday ka faisla</span>
            </span>
            <span className="mosaic-lead__eyebrow">
              Today&apos;s big verdict · {lead.canonical_industry} desk
            </span>
            <strong className="mosaic-lead__title">{lead.title.value}</strong>
            {leadFig && (
              <span className="mosaic-lead__money">
                <span className="mosaic-lead__money-figure">{leadFig.text}</span>
                <span className="mosaic-lead__money-label">{leadFig.label} · TRADE ESTIMATE</span>
              </span>
            )}
            <span className="mosaic-lead__meter">
              <VerdictMeter rung={lead.verdict.ladder_rung} tracking={lead.verdict.tracking} compact />
            </span>
          </span>
        </a>

        {tiles.map((item, index) => (
          <MosaicTile item={item} slot={slots[index] ?? "mosaic-tile--cell"} key={`mosaic-${item.kind}-${item.slug}`} />
        ))}
      </div>

      <dl className="live-stats live-stats--mosaic" aria-label="What BollyAI is tracking right now">
        <div className="live-stats__cell">
          <dt>Series tracked</dt>
          <dd>
            <CountUp value={stats.series} />
          </dd>
        </div>
        <div className="live-stats__cell">
          <dt>Films tracked</dt>
          <dd>
            <CountUp value={stats.films} />
          </dd>
        </div>
        <div className="live-stats__cell">
          <dt>Desks live</dt>
          <dd>
            <CountUp value={desksLive} />
          </dd>
        </div>
        <div className="live-stats__cell live-stats__cell--pulse">
          <dt>Freshness</dt>
          <dd>
            <span className="live-dot" aria-hidden="true" />
            {updated}
          </dd>
        </div>
      </dl>
    </section>
  );
}
