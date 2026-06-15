"use client";

import { useEffect, useMemo, useRef, useState } from "react";

// HEADER SEARCH - live typeahead (revamp 2026-06-15, round 2: Aditya wanted titles to surface AS
// you type, e.g. "wid" -> matches, click straight to the page). Reuses the existing build-time
// /search-index.json (783 entries: {t,u,k,d}) - same prefix scoring as the /search page, but
// inline under the header pill. Lazy-loads the index on first focus; keyboard navigable; the
// native form still submits to /search/?q= as a no-JS fallback.
type Entry = { t: string; u: string; k: string; d?: string };

export function HeaderSearch() {
  const [index, setIndex] = useState<Entry[] | null>(null);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [active, setActive] = useState(0);
  const rootRef = useRef<HTMLFormElement>(null);

  const loadIndex = () => {
    if (index !== null) return;
    fetch("/search-index.json")
      .then((r) => r.json())
      .then((d: Entry[]) => setIndex(d))
      .catch(() => setIndex([]));
  };

  const results = useMemo(() => {
    if (!index) return [];
    const needle = q.trim().toLowerCase();
    if (needle.length < 2) return [];
    return index
      .map((e) => {
        const t = e.t.toLowerCase();
        let s = -1;
        if (t === needle) s = 100;
        else if (t.startsWith(needle)) s = 80;
        else if (t.includes(needle)) s = 55;
        else if ((e.d ?? "").toLowerCase().includes(needle)) s = 25;
        return { e, s };
      })
      .filter((x) => x.s >= 0)
      .sort((a, b) => b.s - a.s || a.e.t.localeCompare(b.e.t))
      .slice(0, 8)
      .map((x) => x.e);
  }, [index, q]);

  useEffect(() => {
    setActive(0);
  }, [q]);

  useEffect(() => {
    const onDoc = (ev: MouseEvent) => {
      if (rootRef.current && !rootRef.current.contains(ev.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", onDoc);
    return () => document.removeEventListener("mousedown", onDoc);
  }, []);

  const showMenu = open && q.trim().length >= 2;

  const onKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Escape") {
      setOpen(false);
      return;
    }
    if (!showMenu || results.length === 0) return;
    if (e.key === "ArrowDown") {
      e.preventDefault();
      setActive((i) => (i + 1) % results.length);
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setActive((i) => (i - 1 + results.length) % results.length);
    } else if (e.key === "Enter") {
      const sel = results[active];
      if (sel) {
        e.preventDefault();
        window.location.href = sel.u;
      }
    }
  };

  return (
    <form
      ref={rootRef}
      className="header-search site-search--desktop"
      action="/search/"
      method="get"
      role="search"
    >
      <input
        type="search"
        name="q"
        value={q}
        autoComplete="off"
        placeholder="Is it worth watching? Try a title…"
        aria-label="Search BollyAI titles"
        aria-expanded={showMenu}
        onFocus={() => {
          loadIndex();
          setOpen(true);
        }}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onKeyDown={onKeyDown}
      />
      <button type="submit" aria-label="Search">
        <span aria-hidden="true">↵</span>
      </button>

      {showMenu && (
        <div className="header-search__menu" role="listbox" aria-label="Search results">
          {results.length === 0 ? (
            <p className="header-search__empty">
              {index === null ? "Loading the catalogue…" : `No title matches “${q.trim()}” in the catalogue yet.`}
            </p>
          ) : (
            results.map((e, i) => (
              <a
                key={e.u}
                href={e.u}
                className={`header-search__item${i === active ? " is-active" : ""}`}
                role="option"
                aria-selected={i === active}
                onMouseEnter={() => setActive(i)}
              >
                <span className="header-search__t">{e.t}</span>
                <span className="header-search__k" data-kind={e.k}>
                  {e.k}
                </span>
              </a>
            ))
          )}
        </div>
      )}
    </form>
  );
}
