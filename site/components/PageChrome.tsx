import { DESKS } from "../lib/desks";

export function SiteHeader() {
  return (
    <header className="site-header">
      <a href="/" className="brand-lockup" aria-label="BollyAI home">
        <span>BollyAI</span>
        <small>Har Friday ka faisla.</small>
      </a>
      <nav aria-label="Primary navigation">
        {DESKS.map((desk) => (
          <a href={`/${desk.slug}/`} key={desk.slug}>
            {desk.label}
          </a>
        ))}
        <a href="/series/">Series</a>
        <a href="/ott/calendar/">OTT Calendar</a>
      </nav>
    </header>
  );
}

export function SiteFooter() {
  return (
    <footer className="site-footer">
      <p>Written by an AI that has seen it all. Edited by a human who signs his name to it.</p>
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
