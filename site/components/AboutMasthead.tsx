import { DESKS } from "../lib/desks";
import styles from "./AboutMasthead.module.css";

// AboutMasthead (browse-lane revamp 2026-06-16): the hero-tier About body. Carries the
// disclosed-AI thesis, the BollyMeter-vs-verdict-ladder model, the two desks, the
// honesty fences the build actually enforces, and the editor identity card that is the
// visible anchor for the site Person entity (E-E-A-T). Scoped CSS only.

const LADDER: { rung: string; color: string }[] = [
  { rung: "MUST-WATCH", color: "oklch(86% .16 150)" },
  { rung: "WORTH-IT", color: "var(--accent-2)" },
  { rung: "ONE-TIME WATCH", color: "var(--text-dim)" },
  { rung: "SKIP", color: "oklch(76% .15 45)" },
  { rung: "DISASTER DROP", color: "oklch(66% .2 25)" }
];

const FENCES: { t: string; d: string }[] = [
  { t: "No invented OTT numbers", d: "Indian platforms do not publish per-title viewership, so BollyAI never fabricates one. Unverifiable means omitted." },
  { t: "Source-gated box office", d: "A rupee figure appears only after two independent trade readings agree closely. Otherwise the row stays in tracking." },
  { t: "Disclosed, never first-person", d: "BollyAI has not watched anything. It reads critics and audiences and writes in the third person, with citations." },
  { t: "Real quotes, real takedown", d: "Pull quotes are attributed to a real source and URL. A takedown page sits one click away on every page." }
];

export function AboutMasthead() {
  return (
    <div className={styles.body}>
      <section className={styles.section}>
        <p className={styles.thesis}>
          BollyAI has not watched anything. BollyAI has read everyone who has, and turns that into one
          straight answer per release.
        </p>
        <p className={styles.lead}>
          It exists to answer the question people actually ask after every Friday and every OTT drop:
          <b> is it worth the time, is it making money, and where can I watch it now.</b> One brain, two
          desks, and a verdict system that keeps craft separate from commerce.
        </p>
      </section>

      <section className={styles.section}>
        <span className={styles.kicker}>How a verdict is built</span>
        <h2 className={styles.h2}>Craft and commerce are scored separately</h2>
        <div className={styles.twoUp}>
          <div className={styles.card}>
            <h3>BollyMeter <em>0 to 10</em></h3>
            <p>
              The craft score. It reads the room across critics and audiences and lands a single number with a
              grounded one-line basis. If reception is too thin to ground, BollyMeter is left null rather than guessed.
            </p>
          </div>
          <div className={styles.card}>
            <h3>The verdict ladder</h3>
            <p>The trade-and-time call. A film can flop and still be good cinema, so the ladder answers worth-your-time, not box office.</p>
            <div className={styles.ladder}>
              {LADDER.map((l) => (
                <span className={styles.rung} key={l.rung}>
                  <i style={{ background: l.color }} />
                  {l.rung}
                </span>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className={styles.section}>
        <span className={styles.kicker}>One brain, two desks</span>
        <h2 className={styles.h2}>Hollywood and Streaming, one source-first standard</h2>
        <p className={styles.lead}>Western film and Western TV get their own desk each, so weekend box office and OTT drops are never graded on the same curve. Each desk is a doorway into the same source-first verdict engine.</p>
        <nav className={styles.desks} aria-label="Desks">
          {DESKS.map((desk) => (
            <a className={styles.desk} href={desk.slug === "streaming" ? "/browse/" : `/${desk.slug}/`} key={desk.slug}>
              <strong>{desk.label}</strong>
              <span>{desk.industryName}</span>
            </a>
          ))}
        </nav>
      </section>

      <section className={styles.section}>
        <span className={styles.kicker}>The fences we will not cross</span>
        <h2 className={styles.h2}>The honesty rules are build gates, not promises</h2>
        <p className={styles.lead}>Each of these is enforced by the test suite and the validator. A violation breaks the build, which is the point.</p>
        <div className={styles.fences}>
          {FENCES.map((f) => (
            <div className={styles.fence} key={f.t}>
              <strong>{f.t}</strong>
              <p>{f.d}</p>
            </div>
          ))}
        </div>
      </section>

      <section className={styles.section}>
        <span className={styles.kicker}>Who signs the verdicts</span>
        <div className={styles.editor}>
          <div className={styles.avatar} aria-hidden="true">AS</div>
          <div className={styles.editorMain}>
            <div className={styles.editorName}>
              <strong>Aditya Sharma</strong>
              <span>Founder &amp; Editor</span>
            </div>
            <p>
              Every verdict on BollyAI is edited and signed by Aditya Sharma. The drafting is disclosed AI; the
              judgement, the source checks, and the byline are human. When a number cannot be verified against a
              primary source, it does not get published.
            </p>
            <div className={styles.links}>
              <a href="https://x.com/aditya14" rel="me noopener" target="_blank">x.com/aditya14</a>
              <a href="https://github.com/Declan142" rel="me noopener" target="_blank">github.com/Declan142</a>
              <a href="/how-bollyai-works/">How BollyAI works</a>
              <a href="/takedown/">Takedown policy</a>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
