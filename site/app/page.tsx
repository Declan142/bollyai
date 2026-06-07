import { DateModified } from "../components/DateModified";
import { FilmCard } from "../components/FilmCard";
import { JsonLd } from "../components/JsonLd";
import { VerdictMeter } from "../components/VerdictMeter";
import { DESKS } from "../lib/desks";
import { SeasonVerdict } from "../components/SeasonVerdict";
import { formatCrore, formatDate, getAllFilms, getLatestModified, getOttCalendar, type Film } from "../lib/data";
import { getAllSeries, latestSeason } from "../lib/series";
import { webSiteJsonLd } from "../lib/jsonld";

function bestFigure(film: Film): { label: string; text: string } | null {
  const net = film.box_office.totals.india_net_inr_cr?.value;
  const ww = film.box_office.totals.worldwide_gross_inr_cr?.value;
  if (ww) return { label: "WW GROSS", text: formatCrore(ww) };
  if (net) return { label: "INDIA NETT", text: formatCrore(net) };
  return null;
}

export default function HomePage() {
  const films = getAllFilms();
  const lead = films[0];
  const wall = films.slice(1, 11);
  const latestModified = getLatestModified();

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

  // Series rail: prefer scored seasons (MUST-WATCH/WORTH-IT lead), cap at 12.
  const seriesRail = getAllSeries()
    .map((s) => ({ s, season: latestSeason(s) }))
    .sort((a, b) => (b.season?.bollymeter?.score ?? 0) - (a.season?.bollymeter?.score ?? 0))
    .slice(0, 12);

  const leadFig = lead ? bestFigure(lead) : null;

  return (
    <main className="page-shell home-marquee" data-desk="bombay">
      <JsonLd data={webSiteJsonLd()} />

      {lead && (
        <section className="hero-marquee full-bleed" data-desk={lead.canonical_industry}>
          <img
            className="hero-marquee__backdrop"
            src={lead.backdrop?.src ?? lead.poster.src}
            alt={lead.backdrop?.alt ?? lead.poster.alt}
            fetchPriority="high"
            loading="eager"
          />
          <div className="hero-marquee__scrim" aria-hidden="true" />
          <div className="hero-marquee__inner">
            <p className="hero-marquee__brand">
              BollyAI <span>Har Friday ka faisla</span>
            </p>
            <p className="eyebrow">Today&apos;s big verdict · {lead.canonical_industry} desk</p>
            <h1>
              <a href={`/${lead.canonical_industry}/box-office/${lead.slug}/`}>{lead.title.value}</a>
            </h1>
            {leadFig && (
              <p className="hero-marquee__money">
                <span className="hero-marquee__money-figure">{leadFig.text}</span>
                <span className="hero-marquee__money-label">{leadFig.label} · TRADE ESTIMATE</span>
              </p>
            )}
            <div className="hero-marquee__meter">
              <VerdictMeter rung={lead.verdict.ladder_rung} tracking={lead.verdict.tracking} />
            </div>
            <DateModified value={lead.date_modified} />
          </div>
        </section>
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

      <section className="poster-wall-block">
        <header className="home-section-head">
          <h2>Now Running</h2>
          <p>The poster wall. Every plate carries a verified number, not a press release.</p>
        </header>
        <div className="poster-wall full-bleed">
          {wall.map((film) => {
            const fig = bestFigure(film);
            return (
              <a
                className="poster-card"
                data-desk={film.canonical_industry}
                href={`/${film.canonical_industry}/box-office/${film.slug}/`}
                key={film.slug}
              >
                <img src={film.poster.src} alt={film.poster.alt} width="342" height="513" loading="lazy" />
                <span className="poster-card__plate">
                  <strong>{film.title.value}</strong>
                  <span className="poster-card__money">{fig ? fig.text : "figures under verification"}</span>
                  <VerdictMeter rung={film.verdict.ladder_rung} tracking={film.verdict.tracking} compact />
                </span>
              </a>
            );
          })}
        </div>
      </section>

      <section className="board-split">
        <div className="big-board">
          <header className="home-section-head">
            <h2>The Big Board</h2>
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
            <h2>On OTT</h2>
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

      <section className="poster-wall-block">
        <header className="home-section-head">
          <h2>Binge Verdicts</h2>
          <p>India, Korea, and global OTT, season by season. BollyAI reads the room so you don&apos;t gamble a weekend.</p>
        </header>
        <div className="poster-wall full-bleed">
          {seriesRail.map(({ s, season }) => (
            <a className="poster-card" data-desk="streaming" href={`/series/${s.slug}/`} key={s.slug}>
              <img src={s.poster.src} alt={s.poster.alt} width="342" height="513" loading="lazy" />
              <span className="poster-card__plate">
                <span className="poster-card__origin-tag">{s.origin}</span>
                <strong>{s.title.value}</strong>
                <span className="poster-card__money">{s.platform.value}</span>
                {season && <SeasonVerdict rung={season.verdict} compact />}
              </span>
            </a>
          ))}
        </div>
        <a className="ott-rail__more" href="/series/">
          All series &amp; OTT verdicts →
        </a>
      </section>

      <section className="desk-strip" aria-label="BollyAI desks">
        {DESKS.map((desk) => (
          <a className="desk-tile" href={`/${desk.slug}/`} data-desk={desk.slug} key={desk.slug}>
            <strong>{desk.label}</strong>
            <span>{desk.answer}</span>
          </a>
        ))}
      </section>

      <section className="content-sections">
        <div className="ad-slot">Reserved ad slot</div>
        <section>
          <header className="home-section-head">
            <h2>Fresh Reviews</h2>
            <p>Money on one axis, craft on the other. BollyAI reads the whole room before scoring.</p>
          </header>
          <div className="film-grid">
            {films.slice(0, 8).map((film) => (
              <FilmCard key={`review-${film.slug}`} film={film} type="review" />
            ))}
          </div>
        </section>
        <DateModified value={latestModified} />
      </section>
    </main>
  );
}
