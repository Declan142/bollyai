import { DESKS } from "../lib/desks";

export function SiteHeader() {
  return (
    <header className="site-header">
      {/* hidden checkbox — CSS-only drawer toggle */}
      <input
        type="checkbox"
        id="nav-toggle"
        className="nav-toggle-input"
        aria-hidden="true"
        tabIndex={-1}
      />

      <a href="/" className="brand-lockup" aria-label="BollyAI home">
        <span>BollyAI</span>
        <small>Har Friday ka faisla.</small>
      </a>

      {/* hamburger button — visible only on mobile */}
      <label
        htmlFor="nav-toggle"
        className="nav-hamburger"
        aria-label="Toggle navigation menu"
      >
        <span className="nav-hamburger__bar" />
        <span className="nav-hamburger__bar" />
        <span className="nav-hamburger__bar" />
      </label>

      {/* drawer overlay — closes the menu when tapped outside */}
      <label htmlFor="nav-toggle" className="nav-overlay" aria-hidden="true" />

      {/* nav drawer */}
      <div className="nav-drawer">
        <nav aria-label="Primary navigation">
          {DESKS.map((desk) => (
            <a href={`/${desk.slug}/`} key={desk.slug}>
              {desk.label}
            </a>
          ))}
          <a href="/series/">Series</a>
          <a href="/watch/">What to Watch</a>
          <a href="/ott/calendar/">OTT Calendar</a>
        </nav>
        <form className="site-search site-search--drawer" action="/search/" method="get" role="search">
          <input
            type="search"
            name="q"
            placeholder="Search films, series, endings…"
            aria-label="Search BollyAI"
            autoComplete="off"
          />
          <button type="submit" aria-label="Search">↵</button>
        </form>
      </div>

      {/* desktop search — hidden on mobile (drawer has its own) */}
      <form className="site-search site-search--desktop" action="/search/" method="get" role="search">
        <input
          type="search"
          name="q"
          placeholder="Search films, series, endings…"
          aria-label="Search BollyAI"
          autoComplete="off"
        />
        <button type="submit" aria-label="Search">↵</button>
      </form>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <p>
        Edited and verified by{" "}
        <a href="https://x.com/aditya14" rel="me noopener" target="_blank">
          Aditya Sharma
        </a>
        , who signs his name to every verdict — drafted with disclosed AI, checked against primary sources.
      </p>
      <p>Metadata is keyed on Wikidata QIDs; OTT listings render attributed official and trade announcements.</p>
      <nav aria-label="Policy navigation">
        <a href="/about/">About</a>
        <a href="/how-bollyai-works/">How BollyAI works</a>
        <a href="/takedown/">Takedown</a>
        <a href="/privacy/">Privacy</a>
        <a href="/contact/">Contact</a>
        <a href="/disclaimer/">Disclaimer</a>
      </nav>
    </footer>
  );
}
