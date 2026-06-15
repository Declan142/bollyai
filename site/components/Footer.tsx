import { DESKS } from "../lib/desks";
import styles from "./Footer.module.css";

// Footer (browse-lane revamp 2026-06-16): the full 6-section information architecture lives
// here as a proper sitemap, which is what lets the top Nav collapse to five links. Six
// sections: Browse, Verdicts, OTT Calendar, Box Office, Desks, About. Same disclosed-AI
// editorial credit line BollyAI has always carried.
export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.top}>
        <div className={styles.brand}>
          <b>BollyAI</b>
          <p>Pan-India cinema and OTT, read by everyone who has watched so you do not have to guess.</p>
        </div>

        <nav className={styles.cols} aria-label="Site map">
          <div className={styles.col}>
            <h4>Browse</h4>
            <ul>
              <li><a href="/browse/">All series</a></li>
              <li><a href="/watch/">What to watch</a></li>
              <li><a href="/search/">Search</a></li>
            </ul>
          </div>

          <div className={styles.col}>
            <h4>Verdicts</h4>
            <ul>
              <li><a href="/bollywood/reviews/">Latest reviews</a></li>
              <li><a href="/bollywood/upcoming/">Upcoming</a></li>
              <li><a href="/how-bollyai-works/">How verdicts work</a></li>
            </ul>
          </div>

          <div className={styles.col}>
            <h4>OTT Calendar</h4>
            <ul>
              <li><a href="/ott/calendar/">Release calendar</a></li>
              <li><a href="/streaming/">Streaming desk</a></li>
              <li><a href="/watch/">Weekend picks</a></li>
            </ul>
          </div>

          <div className={styles.col}>
            <h4>Box Office</h4>
            <ul>
              <li><a href="/box-office/">Live trackers</a></li>
              <li><a href="/tools/hit-flop-calculator/">Hit or flop</a></li>
              <li><a href="/tools/box-office-comparator/">Comparator</a></li>
            </ul>
          </div>

          <div className={styles.col}>
            <h4>Desks</h4>
            <ul>
              {DESKS.map((desk) => (
                <li key={desk.slug}><a href={`/${desk.slug}/`}>{desk.label}</a></li>
              ))}
            </ul>
          </div>

          <div className={styles.col}>
            <h4>About</h4>
            <ul>
              <li><a href="/about/">About BollyAI</a></li>
              <li><a href="/contact/">Contact</a></li>
              <li><a href="/disclaimer/">Disclaimer</a></li>
            </ul>
          </div>
        </nav>
      </div>

      <div className={styles.legal}>
        <p>
          Edited and verified by{" "}
          <a href="https://x.com/aditya14" rel="me noopener" target="_blank">Aditya Sharma</a>, who signs his
          name to every verdict, drafted with disclosed AI and checked against primary sources.
        </p>
        <p>Metadata is keyed on Wikidata QIDs; OTT listings render attributed official and trade announcements.</p>
        <nav className={styles.policy} aria-label="Policy navigation">
          <a href="/about/">About</a>
          <a href="/how-bollyai-works/">How BollyAI works</a>
          <a href="/takedown/">Takedown</a>
          <a href="/privacy/">Privacy</a>
          <a href="/contact/">Contact</a>
          <a href="/disclaimer/">Disclaimer</a>
        </nav>
      </div>
    </footer>
  );
}
