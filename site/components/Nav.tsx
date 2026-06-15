import { HeaderSearch } from "./HeaderSearch";
import styles from "./Nav.module.css";

// Nav (browse-lane revamp 2026-06-16): collapses the old 11-item bar down to 5 primary
// destinations. The full 6-section IA (Verdicts / OTT Calendar / Browse / Box Office /
// Desks / About) is expressed in full in the Footer; the top bar keeps only the five the
// reader reaches for, plus live search. CSS-only off-canvas drawer on mobile.
const PRIMARY: { href: string; label: string }[] = [
  { href: "/watch/", label: "Verdicts" },
  { href: "/ott/calendar/", label: "OTT Calendar" },
  { href: "/browse/", label: "Browse" },
  { href: "/box-office/", label: "Box Office" },
  { href: "/about/", label: "About" }
];

export function Nav() {
  return (
    <header className={styles.header}>
      {/* CSS-only drawer toggle */}
      <input type="checkbox" id="nav-toggle" className={styles.toggle} aria-hidden="true" tabIndex={-1} />

      <a href="/" className={styles.brand} aria-label="BollyAI home">
        <b>BollyAI</b>
        <small>Har Friday ka faisla.</small>
      </a>

      <label htmlFor="nav-toggle" className={styles.burger} aria-label="Toggle navigation menu">
        <span />
        <span />
        <span />
      </label>

      <label htmlFor="nav-toggle" className={styles.overlay} aria-hidden="true" />

      <div className={styles.drawer}>
        <nav className={styles.primary} aria-label="Primary navigation">
          {/* the flagship: a grounded answer engine. Given the one high-signal CTA slot in
              the bar so it leads the IA without diluting the five plain links to six. */}
          <a className={styles.ask} href="/ask/" aria-label="Ask BollyAI, the grounded answer engine">
            <span className={styles.askSpark} aria-hidden="true">✦</span>
            Ask BollyAI
          </a>
          {PRIMARY.map((item) => (
            <a className={styles.link} href={item.href} key={item.href}>
              {item.label}
            </a>
          ))}
        </nav>
        {/* mobile-only search lives inside the drawer (desktop search renders in the bar) */}
        <form className="site-search site-search--drawer" action="/search/" method="get" role="search">
          <input type="search" name="q" placeholder="Search films, series, endings…" aria-label="Search BollyAI" autoComplete="off" />
          <button type="submit" aria-label="Search">↵</button>
        </form>
      </div>

      <div className={styles.searchSlot}>
        <HeaderSearch />
      </div>
    </header>
  );
}
