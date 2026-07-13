import type { Metadata } from "next";
import { DateModified } from "../components/DateModified";
import { JsonLd } from "../components/JsonLd";
import { PosterImage } from "../components/PosterImage";
import {
  catalogueStats,
  heroPick,
  latestSeries,
  latestCatalogueModified,
  ottCalendarDeck,
  type HeroSubject,
  type MediaItem,
  type OttCalItem
} from "../lib/home";
import { getAllWatchLists } from "../lib/recommendations";
import { pageSeo } from "../lib/seo";
import { getNewestEpisodeReviews } from "../lib/series";
import styles from "./home.module.css";

export const metadata: Metadata = {
  title: { absolute: "BollyAI - What Should You Watch Tonight?" },
  description:
    "Grounded Western film and series verdicts for viewers in India. Ask what is worth watching and choose your next great watch without fake ratings or paid hype.",
  ...pageSeo({ path: "/" })
};

const ASK_PROMPTS = [
  "Best mind-bending series",
  "Where can I watch Severance?",
  "Best British mysteries"
];

function verdictLabel(subject: HeroSubject): string {
  if (subject.verdictWord) return subject.verdictWord.replaceAll("-", " ");
  if (subject.score != null) return `${subject.score.toFixed(1)} / 10`;
  return subject.statusLine;
}

function latestSeriesSignal(item: MediaItem): string {
  if (item.score != null) return `${item.score.toFixed(1)} / 10`;
  if (item.seriesRung) return item.seriesRung.replaceAll("-", " ");
  return "Verdict pending";
}

function titleInitials(title: string): string {
  return title
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((word) => word[0])
    .join("")
    .toUpperCase();
}

function LatestSeriesCard({ item }: { item: MediaItem }) {
  const releaseDate = new Date(`${item.recency}T00:00:00+05:30`);
  const month = new Intl.DateTimeFormat("en-IN", { month: "short" }).format(releaseDate);
  const day = new Intl.DateTimeFormat("en-IN", { day: "2-digit" }).format(releaseDate);

  return (
    <a className={styles.latestCard} href={item.href} aria-label={`${item.title}, latest season released ${item.recency}`}>
      <span className={styles.latestDate} aria-hidden="true">
        <strong>{day}</strong>
        <span>{month}</span>
      </span>
      <span className={styles.latestBody}>
        <span>{item.meta} · Latest season</span>
        <strong>{item.title}</strong>
        <small>{latestSeriesSignal(item)}</small>
      </span>
      <span className={styles.rowArrow} aria-hidden="true">→</span>
    </a>
  );
}

function ReleaseCard({ item }: { item: OttCalItem }) {
  const label = item.upcoming ? "Coming" : "Now streaming";
  const href = item.href ?? "/ott/calendar/";
  const releaseDate = new Date(`${item.date}T00:00:00+05:30`);
  const day = new Intl.DateTimeFormat("en-IN", { day: "2-digit" }).format(releaseDate);
  const month = new Intl.DateTimeFormat("en-IN", { month: "short" }).format(releaseDate);
  const year = new Intl.DateTimeFormat("en-IN", { year: "numeric" }).format(releaseDate);

  return (
    <a className={styles.releaseCard} href={href} aria-label={`${item.title}, ${label}`}>
      <span className={styles.releaseDate} aria-hidden="true">
        <strong>{day}</strong>
        <span>{month}</span>
        <small>{year}</small>
      </span>
      <span className={styles.releaseBody}>
        <span className={styles.releaseMeta}>{label} · {item.kind}</span>
        <strong>{item.title}</strong>
        <span className={styles.releasePlatform}>{item.platform}</span>
        <span className={styles.releaseSignal}>{item.score != null ? `${item.score.toFixed(1)} / 10` : "Verified date"}</span>
      </span>
      <span className={styles.releaseArrow} aria-hidden="true">→</span>
    </a>
  );
}

export default function HomePage() {
  const stats = catalogueStats();
  const spotlight = heroPick();
  const newestSeries = latestSeries(8);
  const releases = ottCalendarDeck(4);
  const episodeReviews = getNewestEpisodeReviews(4);
  const watchLists = getAllWatchLists().slice(0, 4);
  const latestModified = latestCatalogueModified();

  return (
    <main className={styles.home}>
      <section className={styles.hero} aria-labelledby="home-title">
        <div className={styles.heroScrim} aria-hidden="true" />

        <div className={styles.heroInner}>
          <div className={styles.heroCopy}>
            <p className={styles.eyebrow}>Western film and TV, decoded for India</p>
            <h1 id="home-title">
              Know what deserves <span>your night.</span>
            </h1>
            <p className={styles.heroLede}>
              Ask one real question. Get one clear verdict assembled from published criticism, audience response, and
              source-checked release data. No paid hype. No invented score.
            </p>

            <form className={styles.askBar} action="/ask/" method="get" role="search">
              <span className={styles.askMark} aria-hidden="true">✦</span>
              <input
                type="search"
                name="q"
                placeholder="Is Severance worth my time?"
                aria-label="Ask BollyAI what to watch"
              />
              <button type="submit">Get the verdict</button>
            </form>

            <div className={styles.askPrompts} aria-label="Popular questions">
              {ASK_PROMPTS.map((prompt) => (
                <a href={`/ask/?q=${encodeURIComponent(prompt)}`} key={prompt}>
                  {prompt}
                </a>
              ))}
            </div>

            <dl className={styles.proof}>
              <div>
                <dt>Grounded title pages</dt>
                <dd>{stats.total}</dd>
              </div>
              <div>
                <dt>Editorial model</dt>
                <dd>Disclosed AI</dd>
              </div>
              <div>
                <dt>Invented ratings</dt>
                <dd>Zero</dd>
              </div>
            </dl>
          </div>

          {spotlight && (
            <a className={styles.spotlight} href={spotlight.href} data-desk={spotlight.desk}>
              <span className={styles.spotlightArt}>
                <PosterImage
                  src={spotlight.poster.src}
                  alt={spotlight.poster.alt}
                  width="420"
                  height="630"
                  loading="eager"
                  fetchPriority="high"
                  avifSrcSet={spotlight.poster.variants?.avifSrcSet}
                  webpSrcSet={spotlight.poster.variants?.webpSrcSet}
                  sizes="(max-width: 760px) 112px, 330px"
                />
                {spotlight.score != null && (
                  <span className={styles.spotlightScore}>
                    {spotlight.score.toFixed(1)} <small>/ 10</small>
                  </span>
                )}
              </span>
              <span className={styles.spotlightBody}>
                <span className={styles.spotlightKicker}>Tonight&apos;s spotlight</span>
                <strong>{spotlight.title}</strong>
                <span className={styles.spotlightVerdict}>{verdictLabel(spotlight)}</span>
                <span className={styles.spotlightBasis}>{spotlight.basis ?? spotlight.statusLine}</span>
                <span className={styles.spotlightLink}>Read the grounded verdict <span aria-hidden="true">→</span></span>
              </span>
            </a>
          )}
        </div>
      </section>

      {newestSeries.length > 0 && (
        <section className={styles.section} aria-labelledby="latest-series">
          <header className={styles.sectionHead}>
            <div>
              <p className={styles.eyebrow}>Current releases, no legacy filler</p>
              <h2 id="latest-series">Latest series, first</h2>
            </div>
            <p>
              Newest season premieres lead this rail. An older title only returns when a fresh season lands.
              <a className={styles.inlineLink} href="/series/"> All series →</a>
            </p>
          </header>
          <div className={styles.latestGrid}>
            {newestSeries.map((item) => (
              <LatestSeriesCard item={item} key={item.slug} />
            ))}
          </div>
        </section>
      )}

      {releases.length > 0 && (
        <section className={styles.section} aria-labelledby="new-and-next">
          <header className={styles.sectionHead}>
            <div>
              <p className={styles.eyebrow}>Verified release dates</p>
              <h2 id="new-and-next">New and next</h2>
            </div>
            <p>
              What just landed and what is coming across major platforms. Every announced date keeps its source trail.
              <a className={styles.inlineLink} href="/ott/calendar/"> Full calendar →</a>
            </p>
          </header>
          <div className={styles.releaseGrid}>
            {releases.map((item) => (
              <ReleaseCard item={item} key={`${item.kind}-${item.title}-${item.date}`} />
            ))}
          </div>
        </section>
      )}

      {(episodeReviews.length > 0 || watchLists.length > 0) && (
        <section className={`${styles.section} ${styles.discovery}`} aria-label="Explore BollyAI">
          {episodeReviews.length > 0 && (
            <div className={styles.deepReads}>
              <header className={styles.compactHead}>
                <p className={styles.eyebrow}>Fresh from the reading room</p>
                <h2>Go deeper</h2>
                <a href="/series/">All series →</a>
              </header>
              <div className={styles.episodeList}>
                {episodeReviews.map((card) => {
                  const episode = card.episode;
                  const badge = `S${String(card.season_number).padStart(2, "0")}E${String(episode.number).padStart(2, "0")}`;
                  const posterless = !card.poster.src || card.poster.src.includes("_fallback");
                  return (
                    <a
                      className={styles.episodeCard}
                      href={`/series/${card.slug}/s${card.season_number}/e${episode.number}/`}
                      key={`${card.slug}-${badge}`}
                    >
                      <span className={styles.episodeArt}>
                        {posterless ? (
                          <span className={styles.episodeFallback} aria-hidden="true">{titleInitials(card.title)}</span>
                        ) : (
                          <PosterImage
                            src={card.poster.src}
                            alt=""
                            width="120"
                            height="120"
                            loading="lazy"
                            avifSrcSet={card.poster.variants?.avifSrcSet}
                            webpSrcSet={card.poster.variants?.webpSrcSet}
                            sizes="84px"
                          />
                        )}
                      </span>
                      <span className={styles.episodeBody}>
                        <span className={styles.episodeMeta}>{badge} · {card.title}</span>
                        <strong>{episode.title}</strong>
                        {episode.spoiler_free && <span>{episode.spoiler_free}</span>}
                      </span>
                      <span className={styles.rowArrow} aria-hidden="true">→</span>
                    </a>
                  );
                })}
              </div>
            </div>
          )}

          {watchLists.length > 0 && (
            <aside className={styles.watchLists} aria-labelledby="pick-a-mood">
              <header className={styles.compactHead}>
                <p className={styles.eyebrow}>Curated, not infinite</p>
                <h2 id="pick-a-mood">Pick a mood</h2>
                <a href="/watch/">All collections →</a>
              </header>
              <div className={styles.watchGrid}>
                {watchLists.map((list) => (
                  <a className={styles.watchCard} href={`/watch/${list.slug}/`} key={list.slug}>
                    <span>{list.kicker}</span>
                    <strong>{list.title}</strong>
                    <small>{list.picks.length} considered picks</small>
                  </a>
                ))}
              </div>
            </aside>
          )}
        </section>
      )}

      <section className={styles.trust} aria-labelledby="trust-title">
        <div className={styles.trustInner}>
          <div className={styles.trustCopy}>
            <p className={styles.eyebrow}>The honesty contract</p>
            <h2 id="trust-title">BollyAI has not watched anything.</h2>
            <p>
              It has read everyone who has, then separated consensus from noise. Every score needs a basis, every number needs a source,
              and a missing answer stays missing.
            </p>
            <div className={styles.trustActions}>
              <a className={styles.primaryAction} href="/how-bollyai-works/">See how verdicts work</a>
              <a className={styles.secondaryAction} href="/series/diary/">Build your watch diary</a>
            </div>
          </div>
          <ul className={styles.principles}>
            <li><span>01</span><strong>Citations over vibes</strong><small>Published evidence stays attached to the answer.</small></li>
            <li><span>02</span><strong>Scores need a basis</strong><small>No grounded reception means no BollyMeter.</small></li>
            <li><span>03</span><strong>Gaps stay honest</strong><small>Unknown is better than a confident invention.</small></li>
          </ul>
        </div>
      </section>

      <div className={styles.modified}>
        <DateModified value={latestModified} />
      </div>

      <JsonLd
        data={{
          "@context": "https://schema.org",
          "@type": "CollectionPage",
          name: "BollyAI - grounded Western film and TV verdicts",
          description: `Grounded verdicts across ${stats.series} series and ${stats.films} films, with verified release dates and no invented ratings.`,
          url: "https://bollyai.in/"
        }}
      />
    </main>
  );
}
