"use client";

import { useEffect, useMemo, useState } from "react";

type Entry = { t: string; u: string; k: string; d?: string };

const KIND_ORDER = ["Film", "Series", "Ending", "List", "Desk"];

// Stable site sections - the designed starting points shown before a query is typed,
// so the search surface never reads as an empty box.
const DESK_JUMPS: { label: string; href: string }[] = [
  { label: "Hollywood", href: "/hollywood/" },
  { label: "Streaming", href: "/streaming/" }
];
const QUICK_JUMPS: { label: string; href: string }[] = [
  { label: "OTT Calendar", href: "/ott/calendar/" },
  { label: "What to Watch", href: "/watch/" },
  { label: "Box Office", href: "/box-office/" }
];

export function SearchClient() {
  const [index, setIndex] = useState<Entry[] | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    // Seed from the ?q= the header form submitted (read directly to avoid the
    // useSearchParams Suspense requirement under output:export).
    const params = new URLSearchParams(window.location.search);
    setQ(params.get("q") ?? "");
    fetch("/search-index.json")
      .then((r) => r.json())
      .then((data: Entry[]) => setIndex(data))
      .catch(() => setIndex([]));
  }, []);

  const results = useMemo(() => {
    if (!index) return [];
    const needle = q.trim().toLowerCase();
    if (needle.length < 2) return [];
    const scored = index
      .map((e) => {
        const t = e.t.toLowerCase();
        let score = -1;
        if (t === needle) score = 100;
        else if (t.startsWith(needle)) score = 80;
        else if (t.includes(needle)) score = 60;
        else if ((e.d ?? "").toLowerCase().includes(needle)) score = 30;
        return { e, score };
      })
      .filter((x) => x.score >= 0)
      .sort((a, b) => b.score - a.score || a.e.t.localeCompare(b.e.t))
      .slice(0, 60)
      .map((x) => x.e);
    return scored;
  }, [index, q]);

  const grouped = useMemo(() => {
    const m = new Map<string, Entry[]>();
    for (const e of results) {
      if (!m.has(e.k)) m.set(e.k, []);
      m.get(e.k)!.push(e);
    }
    return [...m.entries()].sort(
      (a, b) => KIND_ORDER.indexOf(a[0]) - KIND_ORDER.indexOf(b[0])
    );
  }, [results]);

  return (
    <div className="search-page">
      <input
        className="search-page__input"
        type="search"
        value={q}
        autoFocus
        placeholder="Search films, series, endings, lists…"
        aria-label="Search BollyAI"
        onChange={(e) => setQ(e.target.value)}
      />

      {index === null && <p className="search-page__hint">Loading the catalogue…</p>}

      {index !== null && q.trim().length < 2 && (
        <div className="search-intro">
          <p className="search-intro__lead">
            Type at least two letters to search every film, series, ending explainer and watch list. Or start from a desk.
          </p>
          <nav className="search-intro__group" aria-label="Browse by desk">
            {DESK_JUMPS.map((d) => (
              <a className="search-intro__chip" href={d.href} key={d.href}>{d.label}</a>
            ))}
          </nav>
          <nav className="search-intro__group search-intro__group--quiet" aria-label="Popular destinations">
            {QUICK_JUMPS.map((d) => (
              <a className="search-intro__chip search-intro__chip--ghost" href={d.href} key={d.href}>{d.label} &rarr;</a>
            ))}
          </nav>
        </div>
      )}

      {index !== null && q.trim().length >= 2 && results.length === 0 && (
        <p className="search-page__hint">No matches for &ldquo;{q}&rdquo;.</p>
      )}

      {grouped.map(([kind, items]) => (
        <section className="search-group" key={kind}>
          <h2 className="search-group__head">{kind === "Ending" ? "Ending Explained" : kind}</h2>
          <ul className="search-results">
            {items.map((e) => (
              <li key={e.u}>
                <a href={e.u} className="search-result">
                  <span className="search-result__t">{e.t}</span>
                  {e.d && <span className="search-result__d">{e.d}</span>}
                </a>
              </li>
            ))}
          </ul>
        </section>
      ))}
    </div>
  );
}
