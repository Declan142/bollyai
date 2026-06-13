import type { Metadata } from "next";
import { DateModified } from "../components/DateModified";
import { pageSeo } from "../lib/seo";

export const metadata: Metadata = {
  title: { absolute: "BollyAI - Is It Worth Watching? OTT & Movie Verdicts for India" },
  description: "Verdicts, live box-office trackers, OTT release dates, and BollyMeter scores for Indian cinema. Har Friday ka faisla.",
  ...pageSeo({ path: "/" })
};
import { FeaturedMosaic } from "../components/FeaturedMosaic";
import { JsonLd } from "../components/JsonLd";
import { MediaCard } from "../components/MediaCard";
import { PosterImage } from "../components/PosterImage";
import { getYearScoreboardParams } from "../lib/boxoffice";
import { DESKS, getDesk } from "../lib/desks";
import { formatCrore, formatDate, getAllFilms, getLatestModified, getOttCalendar, type Film } from "../lib/data";
import { getNewestEpisodeReviews } from "../lib/series";
import { getAllWatchLists } from "../lib/recommendations";
import { bigThisWeek, catalogueStats, deskCounts, justDropped, mosaicSecondary } from "../lib/home";

function bestFigure(film: Film): { label: string; text: string } | null {
  const net = film.box_office.totals.india_net_inr_cr?.value;
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value;
  if (ww) return { label: "WW GROSS", text: formatCrore(ww) };
  if (net) return { label: "INDIA NETT", text: formatCrore(net) };
  return null;
}

// Friendly freshness label for the liveness ribbon. "Updated today" only when the newest
// merge is actually today's date in IST - never a fabricated freshness.
function freshnessLabel(iso: string): string {
  const today = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date());
  const modified = new Intl.DateTimeFormat("en-CA", { timeZone: "Asia/Kolkata" }).format(new Date(iso));
  return modified === today ? "Updated today" : `Updated ${formatDate(iso)}`;
}

export default function HomePage() {
  const films = getAllFilms();
  const lead = films[0];
  const latestModified = getLatestModified();
  const stats = catalogueStats();
  const updated = freshnessLabel(latestModified);

  const drops = justDropped(16);
  const trending = bigThisWeek(14);
  const counts = deskCounts();

  const board = [...films]
    .filter((film) => film.box_office.totals.worldwide_gross_inr_cr?.value)
    .sort(
      (a, b) =>
        (b.box_office.totals.worldwide_gross_inr_cr?.value?.high ?? 0) -
        (a.box_office.totals.worldwide_gross_inr_cr?.value?.high ?? 0)
    )
    .slice(0, 5);
  const boardMax = board[0]?.box_office.totals.worldwide_gross_inr_cr?.value?.high ?? 1;

  const ticker = films
    .map((film) => ({ film, fig: bestFigure(film) }))
    .filter((item) => item.fig)
    .slice(0, 12);

  const ott = getOttCalendar()
    .entries.filter((entry) => entry.release_date >= "2026-06-01")
    .slice(0, 8);

  const episodeReviews = getNewestEpisodeReviews(10);
  const watchLists = getAllWatchLists().slice(0, 6);
  const yearScoreboards = getYearScoreboardParams();

  const leadFig = lead ? bestFigure(lead) : null;
  // Lead routes by lifecycle so the door is always a live page (theatrical -> box-office,
  // already-on-OTT -> reviews, not-yet-out -> upcoming).
  const leadSurface = lead?.status === "upcoming" ? "upcoming" : lead?.status === "ott" ? "reviews" : "box-office";
  const leadHref = lead ? `/${lead.canonical_industry}/${leadSurface}/${lead.slug}/` : "/";
  const mosaicTiles = lead ? mosaicSecondary(lead.slug, 8) : [];

  // Desk quick-nav: collapse the five cinema desks + Streaming into a scannable strip.
  const deskNav = DESKS.map((desk) => ({ ...desk, count: counts[desk.slug] ?? 0 }));

  return (
    <main className="page-shell home-hub" data-desk="bollywood">
      {lead && (
        <FeaturedMosaic
          lead={lead}
          leadHref={leadHref}
          leadFig={leadFig}
          tiles={mosaicTiles}
          stats={stats}
          desksLive={DESKS.length}
          updated={updated}
        />
      )}

      <section className="ticker full-bleed" aria-label="Trade ticker">
        <div className="ticker__track">
          {[0, 1].map((copy) => (
            <span className="ticker__group" aria-hidden={copy === 1} key={copy}>
              {ticker.map(({ film, fig }) => (
                <a href={`/${film.canonical_industry}/box-office/${film.slug}/`} key={`${copy}-${film.slug}`}>
                  <strong>{film.title.value.toUpperCase()}</strong> {fig!.text.toUpperCase()} {fig!.label}
                  <span className="ticker__sep">◆</span>
                </a>
              ))}
            </span>
          ))}
        </div>
      </section>

      <section className="hub-block">
        <header className="home-section-head home-section-head--rail">
          <div>
            <span className="eyebrow">Films &amp; series · one feed</span>
            <h2>Just Dropped</h2>
            <p>The newest titles to land, theatrical and OTT side by side. BollyAI reads the room the moment it forms.</p>
          </div>
          <a className="home-section-head__more" href="/series/">
            Browse all →
          </a>
        </header>
        <div className="media-rail full-bleed">
          {drops.map((item) => (
            <MediaCard item={item} key={`drop-${item.kind}-${item.slug}`} />
          ))}
        </div>
      </section>

      <section className="desk-nav" aria-label="BollyAI desks">
        {deskNav.map((desk) => (
          <a className="desk-nav__tile" href={`/${desk.slug}/`} data-desk={desk.slug} key={desk.slug}>
            <span className="desk-nav__name">{desk.label}</span>
            <span className="desk-nav__count">{desk.count} titles</span>
          </a>
        ))}
      </section>

      <section className="hub-block">
        <header className="home-section-head home-section-head--rail">
          <div>
            <span className="eyebrow">High signal · this week</span>
            <h2>Big This Week</h2>
            <p>The theatrical runs in cinemas now and the highest-scored drops of the season, mixed. Order is real box office and real BollyMeter, never hype.</p>
          </div>
          <a className="home-section-head__more" href="/bollywood/box-office/2026/">
            Box-office boards →
          </a>
        </header>
        <div className="media-rail full-bleed">
          {trending.map((item) => (
            <MediaCard item={item} key={`trend-${item.kind}-${item.slug}`} />
          ))}
        </div>
      </section>

      <section className="board-split">
        <div className="big-board">
          <header className="home-section-head">
            <h2>Box Office Now</h2>
            <p>2026 worldwide gross, pair-verified. The whole year on one wall.</p>
          </header>
          <ol>
            {board.map((film, index) => {
              const ww = film.box_office.totals.worldwide_gross_inr_cr!.value!;
              const width = Math.max(8, Math.round((ww.high / boardMax) * 100));
              return (
                <li key={film.slug} data-desk={film.canonical_industry}>
                  <a href={`/${film.canonical_industry}/box-office/${film.slug}/`}>
                    <span className="big-board__rank">{index + 1}</span>
                    <span className="big-board__body">
                      <strong>{film.title.value}</strong>
                      <span className="big-board__bar" style={{ width: `${width}%` }} />
                    </span>
                    <span className="big-board__money">{formatCrore(ww)}</span>
                  </a>
                </li>
              );
            })}
          </ol>
        </div>
        <aside className="ott-rail" aria-label="Streaming this week">
          <header className="home-section-head">
            <h2>OTT This Week</h2>
            <p>Confirmed drops, attributed announcements.</p>
          </header>
          <ul>
            {ott.map((entry) => (
              <li key={`${entry.title}-${entry.platform}`} data-desk={entry.industry}>
                <time dateTime={entry.release_date}>{formatDate(entry.release_date)}</time>
                <span className="ott-rail__title">
                  {entry.slug ? <a href={`/${entry.industry}/box-office/${entry.slug}/`}>{entry.title}</a> : entry.title}
                </span>
                <span className="pill">{entry.platform}</span>
              </li>
            ))}
          </ul>
          <a className="ott-rail__more" href="/ott/calendar/">
            Full OTT calendar →
          </a>
        </aside>
      </section>

      {episodeReviews.length > 0 && (
        <section className="hub-block" data-desk="streaming">
          <header className="home-section-head">
            <h2>Naye Episode Reviews</h2>
            <p>Standout hours from across the catalogue, freshest first. Premieres, finales, and the turning-point episodes critics argue about.</p>
          </header>
          <div className="ep-review-rail">
            {episodeReviews.map((card) => {
              const ep = card.episode;
              const badge = `S${String(card.season_number).padStart(2, "0")}E${String(ep.number).padStart(2, "0")}`;
              return (
                <a
                  className="ep-review-card"
                  data-desk={card.canonical_industry}
                  href={`/series/${card.slug}/`}
                  key={`epr-${card.slug}-s${card.season_number}e${ep.number}`}
                >
                  <PosterImage
                    src={card.poster.src}
                    alt={card.poster.alt}
                    width="210"
                    height="200"
                    loading="lazy"
                    avifSrcSet={card.poster.variants?.avifSrcSet}
                    webpSrcSet={card.poster.variants?.webpSrcSet}
                  />
                  <div className="ep-review-card__plate">
                    <span className="ep-review-card__badge">{badge}</span>
                    <span className="ep-review-card__ep-title">{ep.title}</span>
                    <span className="ep-review-card__series">{card.title}</span>
                    {ep.spoiler_free && <p className="ep-review-card__hook">{ep.spoiler_free}</p>}
                  </div>
                </a>
              );
            })}
          </div>
        </section>
      )}

      {watchLists.length > 0 && (
        <section className="hub-block">
          <header className="home-section-head">
            <h2>What to Watch</h2>
            <p>Curated for a mood, a platform, or a weekend - not a star-rating dump. Indian cinema, global OTT, K-drama, anime.</p>
          </header>
          <div className="watch-rail full-bleed">
            {watchLists.map((list) => (
              <a className="watch-rail__card" data-desk="streaming" href={`/watch/${list.slug}/`} key={list.slug}>
                <span className="watch-rail__kicker">{list.kicker}</span>
                <strong>{list.title}</strong>
                <span className="watch-rail__count">{list.picks.length} picks →</span>
              </a>
            ))}
          </div>
          <a className="ott-rail__more" href="/watch/">
            All watch lists →
          </a>
        </section>
      )}

      <section className="hub-block">
        <header className="home-section-head">
          <h2>2026 Yearboards</h2>
          <p>Seven desk scoreboards, ranked by verified India nett when the two-source rule clears.</p>
        </header>
        <div className="bo-link-grid">
          {yearScoreboards.map((scoreboard) => {
            const desk = getDesk(scoreboard.industry);
            return (
              <a className="bo-link-card" href={`/${scoreboard.industry}/box-office/${scoreboard.year}/`} key={`${scoreboard.industry}-${scoreboard.year}`}>
                <span className="eyebrow">{desk?.industryName ?? "Industry"}</span>
                <strong>
                  {desk?.label ?? scoreboard.industry} {scoreboard.year}
                </strong>
                <span>Open the {scoreboard.year} board →</span>
              </a>
            );
          })}
        </div>
      </section>

      <section className="desk-strip" aria-label="BollyAI desks in depth">
        {DESKS.map((desk) => (
          <a className="desk-tile" href={`/${desk.slug}/`} data-desk={desk.slug} key={desk.slug}>
            <strong>{desk.label}</strong>
            <span>{desk.answer}</span>
          </a>
        ))}
      </section>

      <DateModified value={latestModified} />

      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: "BollyAI - pan-India cinema and OTT verdicts",
          description: `Live verdicts and BollyMeter scores across ${stats.series} series and ${stats.films} films.`,
          url: "https://bollyai.in/"
        }}
      />
    </main>
  );
}
