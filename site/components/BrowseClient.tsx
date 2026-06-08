"use client";

import { useMemo, useState, type ReactNode } from "react";

export type BrowseItem = {
  slug: string;
  t: string;        // title
  p: string;        // poster src
  o: string;        // origin / country
  pl: string;       // platform
  st: string;       // status
  g: string[];      // genres
  yr: number | null; // latest year
  v: string | null;  // peak verdict
  sc: number | null; // peak BollyMeter
  r: string;        // recency (ISO date)
  fr: boolean;      // fresh
};

type SortKey = "recent" | "rated" | "az" | "oldest";
const SORTS: { k: SortKey; label: string }[] = [
  { k: "recent", label: "Just dropped" },
  { k: "rated", label: "Top rated" },
  { k: "az", label: "A–Z" },
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

export function BrowseClient({ items }: { items: BrowseItem[] }) {
  const [q, setQ] = useState("");
  const [sort, setSort] = useState<SortKey>("recent");
  const [genres, setGenres] = useState<Set<string>>(new Set());
  const [plats, setPlats] = useState<Set<string>>(new Set());
  const [origins, setOrigins] = useState<Set<string>>(new Set());
  const [statuses, setStatuses] = useState<Set<string>>(new Set());
  const [decades, setDecades] = useState<Set<string>>(new Set());
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

  const activeCount = genres.size + plats.size + origins.size + statuses.size + decades.size + (q.trim() ? 1 : 0);

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
      // rated: score desc, nulls last
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
    <button type="button" className="browse-chip" data-on={on} onClick={onClick}>
      {children}{typeof n === "number" && <span className="browse-chip__n">{n}</span>}
    </button>
  );

  return (
    <div className="browse">
      <div className="browse__bar">
        <input
          className="browse__search"
          type="search"
          value={q}
          placeholder={`Search ${items.length} shows by title…`}
          aria-label="Search shows by title"
          onChange={(e) => setQ(e.target.value)}
        />
        <div className="browse__sorts" role="group" aria-label="Sort">
          {SORTS.map((s) => (
            <button key={s.k} type="button" className="browse-sort" data-on={sort === s.k} onClick={() => setSort(s.k)}>
              {s.label}
            </button>
          ))}
        </div>
      </div>

      <div className="browse__facets">
        <div className="browse-facet">
          <span className="browse-facet__label">Genre</span>
          <div className="browse-facet__chips">
            {genreChips.map((g) => (
              <Chip key={g.name} on={genres.has(g.name)} n={g.n} onClick={() => toggle(genres, setGenres, g.name)}>{g.name}</Chip>
            ))}
            {facets.genres.length > 16 && (
              <button type="button" className="browse-chip browse-chip--more" onClick={() => setShowAllGenres((v) => !v)}>
                {showAllGenres ? "− less" : `+${facets.genres.length - 16} more`}
              </button>
            )}
          </div>
        </div>

        <div className="browse-facet">
          <span className="browse-facet__label">Platform</span>
          <div className="browse-facet__chips">
            {facets.plats.slice(0, 14).map((p) => (
              <Chip key={p.name} on={plats.has(p.name)} n={p.n} onClick={() => toggle(plats, setPlats, p.name)}>{p.name}</Chip>
            ))}
          </div>
        </div>

        <div className="browse-facet">
          <span className="browse-facet__label">Country</span>
          <div className="browse-facet__chips">
            {facets.origins.slice(0, 14).map((o) => (
              <Chip key={o.name} on={origins.has(o.name)} n={o.n} onClick={() => toggle(origins, setOrigins, o.name)}>{o.name}</Chip>
            ))}
          </div>
        </div>

        <div className="browse-facet browse-facet--inline">
          <span className="browse-facet__label">Status</span>
          <div className="browse-facet__chips">
            {facets.statuses.map((s) => (
              <Chip key={s.name} on={statuses.has(s.name)} onClick={() => toggle(statuses, setStatuses, s.name)}>{STATUS_LABEL[s.name] ?? s.name}</Chip>
            ))}
          </div>
          <span className="browse-facet__label">Era</span>
          <div className="browse-facet__chips">
            {facets.decades.map((d) => (
              <Chip key={d.name} on={decades.has(d.name)} onClick={() => toggle(decades, setDecades, d.name)}>{d.name}</Chip>
            ))}
          </div>
        </div>
      </div>

      <div className="browse__meta">
        <strong>{results.length}</strong> {results.length === 1 ? "show" : "shows"}
        {activeCount > 0 && (
          <button type="button" className="browse__clear" onClick={clearAll}>Clear {activeCount} filter{activeCount === 1 ? "" : "s"}</button>
        )}
      </div>

      <div className="series-grid">
        {results.map((s) => (
          <a className="series-card" data-desk="streaming" href={`/series/${s.slug}/`} key={s.slug}>
            <span className="series-card__media">
              <img src={s.p} alt={`${s.t} poster`} width="342" height="513" loading="lazy" />
              {s.fr && <span className="series-card__fresh">NEW</span>}
              {s.sc != null && <span className="series-card__score">{s.sc.toFixed(1)}</span>}
            </span>
            <span className="series-card__body">
              <span className="series-card__origin">{s.o}</span>
              <strong>{s.t}</strong>
              <span className="series-card__plat">{s.pl}</span>
              {s.v && <span className="browse-verdict" data-rung={s.v}>{s.v}</span>}
            </span>
          </a>
        ))}
      </div>

      {results.length === 0 && (
        <p className="browse__empty">No shows match these filters. <button type="button" onClick={clearAll}>Clear filters</button></p>
      )}
    </div>
  );
}
