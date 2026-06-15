import type { Metadata } from "next";
import { SectionHero } from "../../components/SectionHero";
import { DateModified } from "../../components/DateModified";
import styles from "../../components/UtilityPage.module.css";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "Contact BollyAI",
  description: "Reach BollyAI for corrections, takedown requests, source disputes, and editorial feedback at contact@bollyai.in.",
  ...pageSeo({ path: "/contact/" })
};

const dateModified = "2026-06-16T00:00:00+05:30";

export default function ContactPage() {
  return (
    <main className="page-shell" data-desk="bollywood">
      <SectionHero
        eyebrow="Contact"
        title="Get a correction in front of the editor"
        lede={
          <>
            BollyAI would rather be corrected than be wrong. <b>Corrections, source disputes, takedown requests, and
            editorial feedback</b> all reach a human who signs the work.
          </>
        }
      >
        <DateModified value={dateModified} />
      </SectionHero>

      <div className={styles.sections}>
        <section className={styles.section}>
          <div className={styles.cards}>
            <div className={styles.card}>
              <span className={styles.cardKicker}>Corrections and sources</span>
              <h3>Get a fact fixed</h3>
              <p>
                Spotted a wrong number, date, or source row? Send the page URL and the exact detail in dispute to
                <a href="mailto:contact@bollyai.in"> contact@bollyai.in</a> (live once domain mail routing is in place).
              </p>
            </div>
            <div className={styles.card}>
              <span className={styles.cardKicker}>Rights and takedown</span>
              <h3>Image or rights issue</h3>
              <p>
                Rights holders should use the dedicated channel with proof of authority. It targets a 36-hour first
                response.
              </p>
              <a href="/takedown/">Read the takedown policy</a>
            </div>
            <div className={styles.card}>
              <span className={styles.cardKicker}>Editorial</span>
              <h3>Feedback and tips</h3>
              <p>
                Thoughts on a verdict, a desk worth adding, or a release BollyAI missed? The editorial inbox is
                <a href="mailto:contact@bollyai.in"> contact@bollyai.in</a>.
              </p>
            </div>
            <a className={styles.card} href="https://x.com/aditya14" rel="me noopener" target="_blank">
              <span className={styles.cardKicker}>In public</span>
              <h3>The editor on X</h3>
              <p>Aditya Sharma signs every verdict and is reachable in the open.</p>
              <span className={styles.cardArrow}>x.com/aditya14 -&gt;</span>
            </a>
          </div>
        </section>
      </div>
    </main>
  );
}
