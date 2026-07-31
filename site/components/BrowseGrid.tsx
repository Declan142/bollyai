"use client";

import { useSearchParams } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";
import { PosterImage } from "./PosterImage";
import styles from "./BrowseGrid.module.css";

// BrowseGrid (browse-lane revamp 2026-06-16): the editorial catalogue. Same filter logic
// the old BrowseClient earned its keep on, rebuilt around a poster-led card that carries
// the verdict rung + BollyMeter over the art, a calmer segmented control bar, per-poster
// loading shimmer, and a real empty state. Component-scoped CSS only.
export type BrowseItem = {
  slug: string;
  t: string;          // title
  p: string;          // poster src
  pa?: string;        // AVIF poster srcset
  pw?: string;        // WebP poster srcset
  o: string;          // origin / country
  pl: string;         // platform
  st: string;         // status
  g: string[];        // genres
  yr: number | null;  // latest year
  v: string | null;   // peak verdict rung
  sc: number | null;  // peak BollyMeter score
  r: string;          // recency (ISO date)
  fr: boolean;        // fresh
};

type SortKey = "recent" | "rated" | "az" | "oldest";
const SORTS: { k: SortKey; label: string }[] = [
  { k: "recent", label: "Just dropped" },
  { k: "rated", label: "Top rated" },
  { k: "az", label: "A-Z" },
  { k: "oldest", label: "Oldest" }
];

const STATUS_LABEL: Record<string, string> = {
  running: "Airing", returning: "Returning", ended: "Ended", limited: "Limited"
};

function decadeOf(yr: number | null): string | null {
  if (!yr) return null;
  return `${Math.floor(yr / 10) * 10}s`;
}

function counted(values: string[]): { name: string; n: number }[] {
  const m = new Map<string, number>();
  for (const v of values) if (v) m.set(v, (m.get(v) ?? 0) + 1);
  return [...m.entries()].map(([name, n]) => ({ name, n })).sort((a, b) => b.n - a.n || a.name.localeCompare(b.name));
}

export function BrowseGridSkeleton({ count = 12 }: { count?: number }) {
  return (
    <div className={styles.grid} aria-hidden="true">
      {Array.from({ length: count }).map((_, i) => (
        <div className={styles.skelCard} key={i}>
          <div className={styles.skelMedia} />
          <div className={styles.skelBody}>
            <span className={`${styles.skelLine} ${styles.short}`} />
            <span className={styles.skelLine} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function BrowseGrid({ items }: { items: BrowseItem[] }) {
  const searchParams = useSearchParams();
  const initialSort = searchParams.get("sort");
  const [q, setQ] = useState(() => searchParams.get("q") ?? "");
  const [sort, setSort] = useState<SortKey>(() => SORTS.some((item) => item.k === initialSort) ? initialSort as SortKey : "recent");
  const [genres, setGenres] = useState<Set<string>>(() => new Set(searchParams.getAll("genre")));
  const [plats, setPlats] = useState<Set<string>>(() => new Set(searchParams.getAll("platform")));
  const [origins, setOrigins] = useState<Set<string>>(() => new Set(searchParams.getAll("country")));
  const [statuses, setStatuses] = useState<Set<string>>(() => new Set(searchParams.getAll("status")));
  const [decades, setDecades] = useState<Set<string>>(() => new Set(searchParams.getAll("era")));
  const [filtersOpen, setFiltersOpen] = useState(() => ["genre", "platform", "country", "status", "era"].some((key) => searchParams.has(key)));
  const [showAllGenres, setShowAllGenres] = useState(false);

  const facets = useMemo(() => ({
    genres: counted(items.flatMap((i) => i.g)),
    plats: counted(items.map((i) => i.pl)),
    origins: counted(items.map((i) => i.o)),
    decades: counted(items.map((i) => decadeOf(i.yr) ?? "").filter(Boolean)).sort((a, b) => b.name.localeCompare(a.name)),
    statuses: counted(items.map((i) => i.st))
  }), [items]);

  const toggle = (set: Set<string>, setter: (s: Set<string>) => void, v: string) => {
    const next = new Set(set);
    next.has(v) ? next.delete(v) : next.add(v);
    setter(next);
  };

  const facetCount = genres.size + plats.size + origins.size + statuses.size + decades.size;
  const activeCount = facetCount + (q.trim() ? 1 : 0);

  useEffect(() => {
    const next = new URLSearchParams();
    if (q.trim()) next.set("q", q.trim());
    if (sort !== "recent") next.set("sort", sort);
    const add = (key: string, values: Set<string>) => [...values].sort().forEach((value) => next.append(key, value));
    add("genre", genres);
    add("platform", plats);
    add("country", origins);
    add("status", statuses);
    add("era", decades);
    const query = next.toString();
    const url = `${window.location.pathname}${query ? `?${query}` : ""}${window.location.hash}`;
    window.history.replaceState(window.history.state, "", url);
  }, [q, sort, genres, plats, origins, statuses, decades]);

  const results = useMemo(() => {
    const needle = q.trim().toLowerCase();
    let out = items.filter((i) => {
      if (needle && !i.t.toLowerCase().includes(needle)) return false;
      if (genres.size && !i.g.some((g) => genres.has(g))) return false;
      if (plats.size && !plats.has(i.pl)) return false;
      if (origins.size && !origins.has(i.o)) return false;
      if (statuses.size && !statuses.has(i.st)) return false;
      if (decades.size && !decades.has(decadeOf(i.yr) ?? "")) return false;
      return true;
    });
    out = [...out].sort((a, b) => {
      if (sort === "recent") return a.r < b.r ? 1 : a.r > b.r ? -1 : a.t.localeCompare(b.t);
      if (sort === "oldest") return a.r > b.r ? 1 : a.r < b.r ? -1 : a.t.localeCompare(b.t);
      if (sort === "az") return a.t.localeCompare(b.t);
      const as = a.sc ?? -1, bs = b.sc ?? -1;
      return bs - as || a.t.localeCompare(b.t);
    });
    return out;
  }, [items, q, sort, genres, plats, origins, statuses, decades]);

  const clearAll = () => {
    setQ(""); setGenres(new Set()); setPlats(new Set());
    setOrigins(new Set()); setStatuses(new Set()); setDecades(new Set());
  };

  const genreChips = showAllGenres ? facets.genres : facets.genres.slice(0, 16);

  const Chip = ({ on, onClick, children, n }: { on: boolean; onClick: () => void; children: ReactNode; n?: number }) => (
    <button type="button" className={styles.chip} data-on={on} onClick={onClick}>
      {children}{typeof n === "number" && <span className={styles.chipN}>{n}</span>}
    </button>
  );

  // no data shipped (build-time) - show the loading skeleton rather than an empty wall
  if (items.length === 0) {
    return (
      <div className={styles.root}>
        <BrowseGridSkeleton />
      </div>
    );
  }

  return (
    <div className={styles.root}>
      <div className={styles.bar}>
        <input
          className={styles.search}
          type="search"
          value={q}
          placeholder={`Search ${items.length} shows by title…`}
          aria-label="Search shows by title"
          onChange={(e) => setQ(e.target.value)}
        />
        <div className={styles.sorts} role="group" aria-label="Sort">
          {SORTS.map((s) => (
            <button key={s.k} type="button" className={styles.sort} data-on={sort === s.k} onClick={() => setSort(s.k)}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className={styles.filterDock}>
        <div className={styles.quickFilters} aria-label="Quick genre filters">
          <span className={styles.quickLabel}>Quick cuts</span>
          {facets.genres.slice(0, 6).map((genre) => (
            <Chip key={genre.name} on={genres.has(genre.name)} onClick={() => toggle(genres, setGenres, genre.name)}>
              {genre.name}
            </Chip>
          ))}
        </div>
        <button
          type="button"
          className={styles.filterToggle}
          aria-controls="browse-filter-panel"
          aria-expanded={filtersOpen}
          onClick={() => setFiltersOpen((open) => !open)}
        >
          All filters {facetCount > 0 && <span>{facetCount}</span>}
          <b aria-hidden="true">{filtersOpen ? "−" : "+"}</b>
        </button>
      </div>

      <div className={styles.facets} id="browse-filter-panel" hidden={!filtersOpen}>
        <div className={styles.facet}>
          <span className={styles.facetLabel}>Genre</span>
          <div className={styles.chips}>
            {genreChips.map((g) => (
              <Chip key={g.name} on={genres.has(g.name)} n={g.n} onClick={() => toggle(genres, setGenres, g.name)}>{g.name}</Chip>
            ))}
            {facets.genres.length > 16 && (
              <button type="button" className={`${styles.chip} ${styles.more}`} onClick={() => setShowAllGenres((v) => !v)}>
                {showAllGenres ? "- less" : `+${facets.genres.length - 16} more`}
              </button>
            )}
          </div>
        </div>

        <div className={styles.facet}>
          <span className={styles.facetLabel}>Platform</span>
          <div className={styles.chips}>
            {facets.plats.slice(0, 14).map((p) => (
              <Chip key={p.name} on={plats.has(p.name)} n={p.n} onClick={() => toggle(plats, setPlats, p.name)}>{p.name}</Chip>
            ))}
          </div>
        </div>

        <div className={styles.facet}>
          <span className={styles.facetLabel}>Country</span>
          <div className={styles.chips}>
            {facets.origins.slice(0, 14).map((o) => (
              <Chip key={o.name} on={origins.has(o.name)} n={o.n} onClick={() => toggle(origins, setOrigins, o.name)}>{o.name}</Chip>
            ))}
          </div>
        </div>

        <div className={styles.inlineRow}>
          <div className={styles.facet}>
            <span className={styles.facetLabel}>Status</span>
            <div className={styles.chips}>
              {facets.statuses.map((s) => (
                <Chip key={s.name} on={statuses.has(s.name)} onClick={() => toggle(statuses, setStatuses, s.name)}>{STATUS_LABEL[s.name] ?? s.name}</Chip>
              ))}
            </div>
          </div>
          <div className={styles.facet}>
            <span className={styles.facetLabel}>Era</span>
            <div className={styles.chips}>
              {facets.decades.map((d) => (
                <Chip key={d.name} on={decades.has(d.name)} onClick={() => toggle(decades, setDecades, d.name)}>{d.name}</Chip>
              ))}
            </div>
          </div>
        </div>
      </div>

      <div className={styles.meta}>
        <span><b>{results.length}</b> {results.length === 1 ? "show" : "shows"}</span>
        {activeCount > 0 && (
          <button type="button" className={styles.clear} onClick={clearAll}>
            Clear {activeCount} refinement{activeCount === 1 ? "" : "s"}
          </button>
        )}
      </div>

      {results.length === 0 ? (
        <div className={styles.empty}>
          <span className={styles.emptyGlyph} aria-hidden="true">∅</span>
          <h3>Nothing matches yet</h3>
          <p>No show in the catalogue fits this exact mix of filters. Loosen one, or clear them all to see the full wall.</p>
          <button type="button" className={styles.emptyBtn} onClick={clearAll}>Clear filters</button>
        </div>
      ) : (
        <div className={styles.grid}>
          {results.map((s) => (
            <div className={styles.cell} key={s.slug}>
            <a className={styles.card} data-desk="streaming" data-rung={s.v ?? undefined} href={`/series/${s.slug}/`}>
              <span className={styles.media}>
                <PosterImage
                  src={s.p}
                  alt={`${s.t} poster`}
                  width="342"
                  height="513"
                  loading="lazy"
                  avifSrcSet={s.pa}
                  webpSrcSet={s.pw}
                />
                {s.fr && <span className={styles.fresh}>NEW</span>}
                {s.sc != null && <span className={styles.score}>{s.sc.toFixed(1)}<s>/10</s></span>}
                {s.v && <span className={styles.verdict} data-rung={s.v}>{s.v}</span>}
              </span>
              <span className={styles.body}>
                <span className={styles.kicker}>
                  <span className={styles.dot} data-st={s.st} />
                  {s.o}
                </span>
                <strong className={styles.title}>{s.t}</strong>
                <span className={styles.plat}>{s.pl}</span>
              </span>
            </a>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
