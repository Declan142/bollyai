import type { ReactNode } from "react";
import { DateModified } from "./DateModified";
import styles from "./UtilityPage.module.css";

// LegalPage (browse-lane coverage pass 2026-06-16): a clean, on-brand layout for the legal
// trio (privacy, disclaimer, takedown). No hero - just branded type, a constrained reading
// measure, and the same nav/footer chrome as everything else, so these pages never read
// like an unstyled stub. Scoped CSS only.
export function LegalPage({
  eyebrow,
  title,
  lead,
  dateModified,
  children
}: {
  eyebrow: string;
  title: string;
  lead: ReactNode;
  dateModified: string;
  children: ReactNode;
}) {
  return (
    <main className="page-shell" data-desk="bollywood">
      <article className={styles.legal}>
        <header className={styles.legalHead}>
          <p className={styles.eyebrow}>{eyebrow}</p>
          <h1 className={styles.title}>{title}</h1>
          <DateModified value={dateModified} />
        </header>
        <p className={styles.legalLead}>{lead}</p>
        <div className={styles.prose}>{children}</div>
      </article>
    </main>
  );
}
