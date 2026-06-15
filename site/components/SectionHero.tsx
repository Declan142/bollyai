import type { ReactNode } from "react";
import styles from "./SectionHero.module.css";

// SectionHero (browse-lane revamp 2026-06-16): one cinematic header shared by the primary
// nav destinations (OTT Calendar, Box Office, About) so each opens on the same editorial
// note as the 9.4 OTT hero. Ambient art + stats + a CTA are all optional. Scoped CSS only.
export type HeroStat = { value: string; label: string };

export function SectionHero({
  eyebrow,
  title,
  lede,
  stats,
  ambient,
  cta,
  children
}: {
  eyebrow: string;
  title: string;
  lede?: ReactNode;
  stats?: HeroStat[];
  ambient?: string | null;
  cta?: { href: string; label: string };
  children?: ReactNode;
}) {
  return (
    <section className={styles.hero}>
      {ambient && (
        <div className={styles.ambient} aria-hidden="true">
          <img src={ambient} alt="" decoding="async" />
        </div>
      )}
      <div className={styles.inner}>
        <p className={styles.eyebrow}>{eyebrow}</p>
        <h1 className={styles.title}>{title}</h1>
        {lede && <p className={styles.lede}>{lede}</p>}
        {stats && stats.length > 0 && (
          <div className={styles.stats}>
            {stats.map((s) => (
              <div className={styles.stat} key={s.label}>
                <b>{s.value}</b>
                <span>{s.label}</span>
              </div>
            ))}
          </div>
        )}
        {(cta || children) && (
          <div className={styles.foot}>
            {cta && (
              <a className={styles.cta} href={cta.href}>
                {cta.label} <span aria-hidden="true">-&gt;</span>
              </a>
            )}
            {children}
          </div>
        )}
      </div>
    </section>
  );
}
