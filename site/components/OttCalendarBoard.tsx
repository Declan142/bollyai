import { DESKS } from "../lib/desks";
import styles from "./OttCalendarBoard.module.css";

// OttCalendarBoard (browse-lane revamp 2026-06-16): the /ott/calendar list rebuilt as a
// month-grouped editorial board with date chips, verdict lines, platform/desk tags and the
// mandatory source attribution per row. Graceful empty state if the window is quiet. The
// data still comes from lib/data getOttCalendar; this is presentation only, scoped CSS.
export type OttEntry = {
  release_date: string;
  title: string;
  platform: string;
  verdict_line: string;
  url?: string | null;
  source_url: string;
  source_type: string;
  industry: string;
  type: string;
};

function fmt(iso: string, opt: Intl.DateTimeFormatOptions): string {
  const d = new Date(`${iso}T00:00:00+05:30`);
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", ...opt }).format(d);
}

function monthKey(iso: string): string {
  return iso.slice(0, 7); // YYYY-MM, already date-ordered
}

export function OttCalendarBoard({ entries }: { entries: OttEntry[] }) {
  if (entries.length === 0) {
    return (
      <div className={styles.empty}>
        <strong>The window is quiet right now</strong>
        <p>No verified OTT release date sits inside the current tracking window. The moment a platform or trade source confirms one, it lands here with its attribution.</p>
      </div>
    );
  }

  const groups: { key: string; label: string; rows: OttEntry[] }[] = [];
  for (const e of entries) {
    const key = monthKey(e.release_date);
    let g = groups.find((x) => x.key === key);
    if (!g) {
      g = { key, label: fmt(e.release_date, { month: "long", year: "numeric" }), rows: [] };
      groups.push(g);
    }
    g.rows.push(e);
  }

  return (
    <div className={styles.board}>
      {groups.map((g) => (
        <section className={styles.month} key={g.key}>
          <header className={styles.monthHead}>
            <h2>{g.label}</h2>
            <span>{g.rows.length} {g.rows.length === 1 ? "release" : "releases"}</span>
          </header>
          <div className={styles.rows}>
            {g.rows.map((e) => {
              const desk = DESKS.find((d) => d.slug === e.industry);
              const inner = (
                <>
                  <span className={styles.date}>
                    <b>{fmt(e.release_date, { day: "2-digit" })}</b>
                    <span>{fmt(e.release_date, { weekday: "short" })}</span>
                  </span>
                  <span className={styles.main}>
                    <span className={styles.title}>{e.title}</span>
                    {e.verdict_line && <p className={styles.verdict}>{e.verdict_line}</p>}
                    <span className={styles.source}>
                      Source: <a href={e.source_url} rel="noopener" target="_blank">{e.source_url}</a> ({e.source_type})
                    </span>
                  </span>
                  <span className={styles.tags}>
                    <span className={`${styles.tag} ${styles.platform}`}>{e.platform}</span>
                    <span className={styles.tag}>{desk?.label ?? e.industry}</span>
                  </span>
                </>
              );
              const key = `${e.title}-${e.platform}-${e.release_date}`;
              return e.url ? (
                <a className={styles.row} data-desk={e.industry} href={e.url} key={key}>{inner}</a>
              ) : (
                <div className={`${styles.row} ${styles.rowStatic}`} data-desk={e.industry} key={key}>{inner}</div>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
