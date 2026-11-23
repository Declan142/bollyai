import type { OttRelease } from "../lib/ott-feed.mjs";
import styles from "./OttCalendarBoard.module.css";

function fmt(iso: string, options: Intl.DateTimeFormatOptions): string {
  return new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", ...options }).format(new Date(iso));
}

export function OttCalendarBoard({ entries, catalogueLinks }: { entries: OttRelease[]; catalogueLinks: Record<string, string> }) {
  if (entries.length === 0) {
    return (
      <div className={styles.empty}>
        <strong>No verified release dates in this window</strong>
        <p>A date appears once the platform announces it or two trade publications report it.</p>
      </div>
    );
  }
  const months = new Map<string, OttRelease[]>();
  for (const row of entries) {
    const month = row.release_date.slice(0, 7);
    const group = months.get(month);
    if (group) group.push(row);
    else months.set(month, [row]);
  }

  return (
    <div className={styles.board}>
      {Array.from(months, ([month, rows]) => (
        <section className={styles.month} key={month}>
          <header className={styles.monthHead}>
            <h2>{fmt(rows[0].release_date, { month: "long", year: "numeric" })}</h2>
            <span>{rows.length} {rows.length === 1 ? "release" : "releases"}</span>
          </header>
          <div className={styles.rows}>
            {rows.map((row) => {
              const href = catalogueLinks[`${row.type}:${row.title}`];
              return (
                <article className={styles.row} key={`${row.title}-${row.platform}-${row.release_date}`}>
                  <time className={styles.date} dateTime={row.release_date}>
                    <b>{fmt(row.release_date, { day: "2-digit" })}</b>
                    <span>{fmt(row.release_date, { weekday: "short" })}</span>
                  </time>
                  <div className={styles.main}>
                    <h3 className={styles.title}>{href ? <a href={href}>{row.title}</a> : row.title}</h3>
                    {row.verdict_line && <p className={styles.verdict}>{row.verdict_line}</p>}
                    <div className={styles.source}>
                      {row.sources.length === 1 ? "Source" : "Sources"}{" · "}
                      {row.sources.map((source, index) => (
                        <span key={source.url}>
                          {index > 0 && ", "}
                          <a href={source.url} rel="noopener noreferrer" target="_blank">{source.name}</a>
                        </span>
                      ))}
                    </div>
                  </div>
                  <div className={styles.tags}>
                    <span className={`${styles.tag} ${styles.platform}`}>{row.platform}</span>
                    <span className={styles.tag}>{row.type === "film" ? "Film" : "Series"}</span>
                  </div>
                </article>
              );
            })}
          </div>
        </section>
      ))}
    </div>
  );
}
