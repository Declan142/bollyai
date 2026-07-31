import styles from "./Footer.module.css";

// The footer is a compact second-tier index, not a repetition of every route in the product.
export function Footer() {
  return (
    <footer className={styles.footer}>
      <div className={styles.top}>
        <div className={styles.brand}>
          <b>BollyAI</b>
          <p>Western cinema and OTT, read by everyone who has watched so you do not have to guess.</p>
        </div>

        <nav className={styles.cols} aria-label="Site map">
          <div className={styles.col}>
            <h4>Browse</h4>
            <ul>
              <li><a href="/ask/">Ask BollyAI</a></li>
              <li><a href="/browse/">All series</a></li>
              <li><a href="/watch/">What to watch</a></li>
              <li><a href="/series/diary/">My verdict diary</a></li>
            </ul>
          </div>

          <div className={styles.col}>
            <h4>Evidence</h4>
            <ul>
              <li><a href="/hollywood/">Hollywood verdicts</a></li>
              <li><a href="/ott/calendar/">OTT release calendar</a></li>
              <li><a href="/box-office/">Box office desk</a></li>
              <li><a href="/how-bollyai-works/">How verdicts work</a></li>
            </ul>
          </div>

          <div className={styles.col}>
            <h4>Tools</h4>
            <ul>
              <li><a href="/tools/">All tools</a></li>
              <li><a href="/tools/hit-flop-calculator/">Hit or flop</a></li>
              <li><a href="/tools/box-office-comparator/">Comparator</a></li>
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
          <a href="/how-bollyai-works/">How BollyAI works</a>
          <a href="/takedown/">Takedown</a>
          <a href="/privacy/">Privacy</a>
        </nav>
      </div>
    </footer>
  );
}
