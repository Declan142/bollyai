import type { Metadata } from "next";
import { SectionHero } from "../../components/SectionHero";
import styles from "../../components/UtilityPage.module.css";
import { pageSeo } from "../../lib/seo";

export const metadata: Metadata = {
  title: "BollyAI Tools - Hit or Flop & Box Office Comparator",
  description:
    "Free BollyAI tools: estimate whether a film is a hit or flop from budget versus collection, and compare two films on trade-estimate box office, with the same conservative publish rule.",
  ...pageSeo({ path: "/tools/" })
};

const TOOLS: { href: string; kicker: string; title: string; desc: string }[] = [
  {
    href: "/tools/hit-flop-calculator/",
    kicker: "Verdict math",
    title: "Hit or Flop Calculator",
    desc: "Put in a budget and a collection and see where a film lands on the trade ladder. It shows the working, not just a label, and never pretends a guess is a number."
  },
  {
    href: "/tools/box-office-comparator/",
    kicker: "Head to head",
    title: "Box Office Comparator",
    desc: "Line up two films on trade-estimate box office, under the same publish rule the trackers use. Unverified figures stay marked as tracking, not inflated."
  }
];

export default function ToolsPage() {
  return (
    <main className="page-shell" data-desk="tollywood">
      <SectionHero
        eyebrow="BollyAI tools"
        title="Run the numbers yourself"
        lede={
          <>
            Small, honest calculators built on the same conservative rules as the trackers. <b>They show the working
            and refuse to invent a figure</b> when the sources do not support one.
          </>
        }
      />

      <div className={styles.sections}>
        <section className={styles.section}>
          <div className={styles.cards}>
            {TOOLS.map((t) => (
              <a className={styles.card} href={t.href} key={t.href}>
                <span className={styles.cardKicker}>{t.kicker}</span>
                <h3>{t.title}</h3>
                <p>{t.desc}</p>
                <span className={styles.cardArrow}>Open tool -&gt;</span>
              </a>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
