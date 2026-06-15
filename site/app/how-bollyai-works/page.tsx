import type { Metadata } from "next";
import { SectionHero } from "../../components/SectionHero";
import { DateModified } from "../../components/DateModified";
import styles from "../../components/UtilityPage.module.css";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "How BollyAI Works - Our Verdict & BollyMeter Method",
  description:
    "How BollyAI reads verified metadata, trade estimates, and OTT signals before publishing a verdict. Source rows, confidence labels, subtitle-grounding, and the honesty gates explained.",
  ...pageSeo({ path: "/how-bollyai-works/" })
};

const dateModified = "2026-06-16T00:00:00+05:30";

const STEPS: { t: string; d: string }[] = [
  { t: "Read verified metadata", d: "Every external value is stored with its source, fetch time, and a confidence label (verified or reported). Titles and people are keyed on Wikidata QIDs, never guessed." },
  { t: "Ground the reception, not an opinion", d: "BollyMeter reads what critics and audiences actually reported to land a /10 craft score with a grounded one-line basis. If reception is too thin to ground, the score is left null rather than invented." },
  { t: "Apply the box-office publish rule", d: "Two independent same-metric readings within 10 percent render the lower figure as a trade estimate. Ten to twenty-five percent apart shows the lower figure with a caveat. Wider, or single-source, stays in tracking." },
  { t: "Pass the honesty gates at build", d: "First-person viewing claims, invented OTT view counts, and unattributed quotes are blocked by build gates. A violation does not get softened; it breaks the build." },
  { t: "Human edit and sign", d: "Aditya Sharma edits and signs every verdict. The drafting is disclosed AI; the judgement, the source checks, and the byline are human." }
];

const FENCES: { t: string; d: string }[] = [
  { t: "No first-person viewing claims", d: "BollyAI has not watched anything. It writes in the third person about what critics and audiences reported, with citations." },
  { t: "No invented OTT numbers", d: "Indian platforms do not publish per-title viewership, so BollyAI never fabricates one. Unverifiable means omitted." },
  { t: "Source rows on every value", d: "Box-office figures and OTT dates carry their sources and confidence labels in the open, so you can see the uncertainty." },
  { t: "Real, attributed quotes only", d: "Pull quotes name a real source and URL and stay short. If a quote cannot be verified, it does not appear." }
];

export default function HowPage() {
  return (
    <main className="page-shell" data-desk="bollywood">
      <SectionHero
        eyebrow="How BollyAI works"
        title="How a verdict is built, and what it refuses to fake"
        lede={
          <>
            BollyAI reads verified metadata, trade estimates, and OTT signals through human-edited gates before it
            publishes a word. <b>The method is the product;</b> the refusals are the moat.
          </>
        }
        cta={{ href: "/about/", label: "About BollyAI" }}
      >
        <DateModified value={dateModified} />
      </SectionHero>

      <div className={styles.sections}>
        <section className={styles.section}>
          <span className={styles.kicker}>The pipeline</span>
          <h2 className={styles.h2}>Five steps from raw signal to a signed answer</h2>
          <div className={styles.steps}>
            {STEPS.map((s, i) => (
              <div className={styles.step} key={s.t}>
                <span className={styles.stepNum}>{String(i + 1).padStart(2, "0")}</span>
                <span className={styles.stepBody}>
                  <strong>{s.t}</strong>
                  <p>{s.d}</p>
                </span>
              </div>
            ))}
          </div>
        </section>

        <section className={styles.section}>
          <span className={styles.kicker}>The grounding</span>
          <h2 className={styles.h2}>Subtitles are fuel, not cargo</h2>
          <p className={styles.lead}>
            Subtitles and scripts are read to <b>ground</b> the work, the ending explainers, the recaps, the episode
            guides, so an explanation is anchored to what actually happens on screen rather than to a guess. They are
            never served back as text. A line of dialogue appears only as a short quote, under twenty-five words, with a
            citation, in service of the analysis. The fuel stays in the engine; only the verdict comes out.
          </p>
        </section>

        <section className={styles.section}>
          <span className={styles.kicker}>The fences that break the build</span>
          <h2 className={styles.h2}>The honesty rules are gates, not promises</h2>
          <div className={styles.fences}>
            {FENCES.map((f) => (
              <div className={styles.fence} key={f.t}>
                <strong>{f.t}</strong>
                <p>{f.d}</p>
              </div>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
