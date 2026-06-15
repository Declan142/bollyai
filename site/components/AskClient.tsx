"use client";

import { useEffect, useMemo, useState } from "react";

// ============================================================================
// Ask BollyAI - the client-side answer engine.
// Reads the prebuilt /ask-index.json (grounded verdicts only) and assembles an
// answer from it. HONESTY FENCE: it can ONLY surface fields that exist in the
// grounded index. There is no generation step and no number is ever computed -
// every score/verdict/quote is copied from grounded data. If nothing grounded
// matches, it says so and never invents a verdict.
// ============================================================================

type Rec = {
  t: string;
  u: string;
  k: "Series" | "Film";
  o: string | null;
  l: string | null;
  g: string[];
  p: string | null;
  v: string | null;
  sc: number | null;
  b: string | null;
  sn: string | null;
  y: number | null;
  e: boolean;
  pp: boolean;
  wtw: string | null;
};

const FILLER = new Set([
  "is", "the", "a", "an", "of", "to", "i", "should", "watch", "watching", "worth",
  "it", "good", "review", "reviews", "how", "about", "me", "do", "you", "think",
  "any", "now", "right", "currently", "this", "that", "for", "on", "in", "at",
  "and", "or", "with", "best", "top", "great", "recommend", "recommendation",
  "suggest", "what", "which", "are", "some", "show", "shows", "series", "movie",
  "movies", "film", "films", "ott", "streaming", "stream", "really", "very", "so"
]);

// region word -> { country match, language codes }
const REGIONS: { keys: string[]; country?: string; langs?: string[]; label: string }[] = [
  { keys: ["indian", "india", "desi", "bollywood"], country: "India", langs: ["hi", "ta", "te", "ml", "kn", "bn", "mr", "pa"], label: "Indian" },
  { keys: ["korean", "korea", "kdrama", "k-drama"], country: "South Korea", langs: ["ko"], label: "Korean" },
  { keys: ["japanese", "japan", "anime"], country: "Japan", langs: ["ja"], label: "Japanese" },
  { keys: ["british", "britain", "uk", "english"], country: "United Kingdom", label: "British" },
  { keys: ["american", "america", "us", "hollywood"], country: "United States", label: "American" },
  { keys: ["spanish", "spain"], country: "Spain", langs: ["es"], label: "Spanish" },
  { keys: ["hindi"], langs: ["hi"], label: "Hindi" },
  { keys: ["tamil"], langs: ["ta"], label: "Tamil" },
  { keys: ["telugu"], langs: ["te"], label: "Telugu" },
  { keys: ["malayalam"], langs: ["ml"], label: "Malayalam" }
];

// genre word / synonym -> canonical token tested against record.g (case-insensitive)
const GENRE_SYN: Record<string, string[]> = {
  crime: ["crime"],
  thriller: ["thriller", "thrilling"],
  drama: ["drama", "dramatic"],
  comedy: ["comedy", "comedies", "funny", "sitcom", "hilarious"],
  romance: ["romance", "romantic", "love"],
  horror: ["horror", "scary", "slasher"],
  mystery: ["mystery", "whodunit"],
  "sci-fi": ["sci-fi", "scifi", "science fiction", "sci fi"],
  action: ["action"],
  survival: ["survival"],
  historical: ["historical", "period"],
  psychological: ["psychological"],
  fantasy: ["fantasy"],
  adventure: ["adventure"],
  war: ["war"],
  heist: ["heist"],
  family: ["family"]
};

const norm = (s: string) =>
  s.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();

const RUNG_BLURB: Record<string, string> = {
  "MUST-WATCH": "a front-of-queue watch",
  "WORTH-IT": "worth your time",
  "ONE-TIME WATCH": "a one-time watch",
  "SKIP": "one to skip",
  "DISASTER DROP": "a disaster drop"
};

type Answer =
  | { kind: "verdict"; rec: Rec }
  | { kind: "spoiler"; rec: Rec }
  | { kind: "rank"; label: string; list: Rec[] }
  | { kind: "none"; q: string };

function matchEntity(qNorm: string, index: Rec[]): Rec | null {
  let best: Rec | null = null;
  let bestLen = 0;
  for (const r of index) {
    const tn = norm(r.t);
    if (tn.length < 2) continue;
    // contiguous-substring title match, weighted by how much of the title is present
    if (qNorm === tn || qNorm.includes(tn)) {
      if (tn.length > bestLen) {
        best = r;
        bestLen = tn.length;
      }
    }
  }
  if (best) return best;
  // fallback: strong token overlap (all significant title tokens present in the query)
  const qTokens = new Set(qNorm.split(" ").filter((w) => w && !FILLER.has(w)));
  let bestScore = 0;
  for (const r of index) {
    const tTokens = norm(r.t).split(" ").filter((w) => w.length > 1);
    if (tTokens.length === 0) continue;
    const hit = tTokens.filter((w) => qTokens.has(w)).length;
    const ratio = hit / tTokens.length;
    if (hit >= 1 && ratio >= 0.75 && hit > bestScore) {
      bestScore = hit;
      best = r;
    }
  }
  return best;
}

function detectRegion(qNorm: string) {
  const words = new Set(qNorm.split(" "));
  for (const reg of REGIONS) {
    if (reg.keys.some((k) => words.has(k) || qNorm.includes(k))) return reg;
  }
  return null;
}

function detectGenres(qNorm: string): string[] {
  const out: string[] = [];
  for (const [canon, syns] of Object.entries(GENRE_SYN)) {
    if (syns.some((s) => qNorm.includes(s))) out.push(canon);
  }
  return out;
}

function answerFor(raw: string, index: Rec[]): Answer {
  const q = raw.trim();
  const qNorm = norm(q);
  if (!qNorm) return { kind: "none", q };

  const isBest = /\b(best|top|greatest|recommend|suggest|good)\b/.test(qNorm) || /^what.*watch/.test(qNorm);
  const isSpoiler = /\bspoiler/.test(qNorm);
  const isWhere = /\bwhere\b/.test(qNorm) || /\b(stream|streaming|available)\b.*\?|\bon (netflix|prime|jiohotstar|sonyliv|zee5|hotstar)\b/.test(qNorm);

  // Spoiler intent first - this is a graceful, no-fabrication branch.
  if (isSpoiler) {
    const rec = matchEntity(qNorm, index);
    if (rec) return { kind: "spoiler", rec };
    return { kind: "none", q };
  }

  // Best / recommendation intent -> ranking from grounded scores.
  if (isBest) {
    const region = detectRegion(qNorm);
    const genres = detectGenres(qNorm);
    let pool = index.filter((r) => r.sc !== null);
    if (region) {
      pool = pool.filter(
        (r) =>
          (region.country && r.o === region.country) ||
          (region.langs && r.l && region.langs.includes(r.l))
      );
    }
    if (genres.length) {
      pool = pool.filter((r) => r.g.some((g) => genres.includes(g.toLowerCase())));
    }
    const wantsNow = /\b(now|right now|currently|latest|2026|2025|new|recent)\b/.test(qNorm);
    pool = pool.sort((a, b) => (b.sc! - a.sc!) || ((b.y ?? 0) - (a.y ?? 0)));
    if (wantsNow) pool = [...pool].sort((a, b) => ((b.y ?? 0) - (a.y ?? 0)) || (b.sc! - a.sc!));
    const list = pool.slice(0, 5);
    if (list.length === 0) return { kind: "none", q };
    const bits = [genres.map((g) => g.replace("-", " ")).join(" "), region?.label].filter(Boolean);
    const label = `Best ${bits.join(" ") || "grounded"} ${list.length > 1 ? "titles" : "title"}${wantsNow ? ", newest first" : ""}`.replace(/\s+/g, " ");
    return { kind: "rank", label, list };
  }

  // Where-to-watch + worth-watching both resolve to a single grounded title card.
  const rec = matchEntity(qNorm, index);
  if (rec) return { kind: "verdict", rec };

  // No entity, but a genre/region was named -> treat as an implicit "best" query.
  const region = detectRegion(qNorm);
  const genres = detectGenres(qNorm);
  if (region || genres.length) {
    return answerFor(`best ${q}`, index);
  }

  return { kind: "none", q };
}

const EXAMPLES = [
  "Is The Glory worth watching?",
  "Best Indian crime thriller right now",
  "Where to watch Squid Game",
  "Best Korean thriller"
];

function Stars({ score }: { score: number }) {
  return (
    <span className="ask-score">
      <strong>{score.toFixed(1)}</strong>
      <span className="ask-score__scale">/10</span>
    </span>
  );
}

function VerdictCard({ rec }: { rec: Rec }) {
  const meta = [rec.o, rec.p, rec.g.slice(0, 2).join(" · ")].filter(Boolean).join("  ·  ");
  return (
    <article className="ask-answer" data-desk={rec.k === "Series" ? "streaming" : "bollywood"}>
      <header className="ask-answer__head">
        <div>
          <span className="ask-answer__kind">{rec.k}{rec.y ? ` · ${rec.y}` : ""}</span>
          <h2 className="ask-answer__title">
            <a href={rec.u}>{rec.t}</a>
          </h2>
          {meta && <p className="ask-answer__meta">{meta}</p>}
        </div>
        {rec.v && (
          <div className="ask-answer__verdict">
            <span className="ask-rung" data-rung={rec.v}>{rec.v}</span>
            {rec.sc !== null ? <Stars score={rec.sc} /> : <span className="ask-score__none">BollyMeter not published</span>}
          </div>
        )}
      </header>

      <p className="ask-answer__lead">
        {rec.v
          ? <>BollyAI calls {rec.t} <strong>{RUNG_BLURB[rec.v] ?? rec.v.toLowerCase()}</strong>{rec.sc !== null ? <>, BollyMeter <strong>{rec.sc.toFixed(1)}</strong>.</> : "."}</>
          : <>Here is what BollyAI has on {rec.t}.</>}
      </p>

      {rec.b && (
        <blockquote className="ask-answer__basis">
          <span className="ask-answer__basis-label">The grounded basis</span>
          {rec.b}
        </blockquote>
      )}
      {rec.sn && rec.sn !== rec.b && <p className="ask-answer__snip">{rec.sn}</p>}

      <nav className="ask-answer__links">
        <a className="ask-answer__cta" href={rec.u}>Read the full verdict &rarr;</a>
        {rec.wtw && <a className="ask-answer__link" href={rec.wtw}>Where to watch</a>}
        {rec.e && <a className="ask-answer__link" href={`${rec.u}ending-explained/`}>Ending explained</a>}
      </nav>
    </article>
  );
}

function SpoilerCard({ rec }: { rec: Rec }) {
  return (
    <article className="ask-answer" data-desk="streaming">
      <header className="ask-answer__head">
        <div>
          <span className="ask-answer__kind">{rec.k}{rec.y ? ` · ${rec.y}` : ""}</span>
          <h2 className="ask-answer__title"><a href={rec.u}>{rec.t}</a></h2>
        </div>
      </header>
      <p className="ask-answer__lead">
        BollyAI keeps its episode write-ups <strong>spoiler-free</strong> by design and parks the
        plot turns on the ending-explained page. It does not score how spoiler-heavy a title is,
        so there is no grounded number to give here.
      </p>
      <nav className="ask-answer__links">
        <a className="ask-answer__cta" href={rec.u}>Spoiler-free verdict &rarr;</a>
        {rec.e && <a className="ask-answer__link" href={`${rec.u}ending-explained/`}>Ending explained (spoilers)</a>}
      </nav>
    </article>
  );
}

function RankCard({ label, list }: { label: string; list: Rec[] }) {
  return (
    <article className="ask-answer ask-answer--rank" data-desk="streaming">
      <header className="ask-answer__head">
        <h2 className="ask-answer__title">{label}</h2>
      </header>
      <ol className="ask-rank">
        {list.map((r, i) => (
          <li key={r.u}>
            <a href={r.u}>
              <span className="ask-rank__n">{i + 1}</span>
              <span className="ask-rank__body">
                <strong>{r.t}</strong>
                {r.b && <span className="ask-rank__basis">{r.b}</span>}
              </span>
              <span className="ask-rank__right">
                {r.sc !== null && <Stars score={r.sc} />}
                {r.v && <span className="ask-rung ask-rung--mini" data-rung={r.v}>{r.v}</span>}
              </span>
            </a>
          </li>
        ))}
      </ol>
    </article>
  );
}

function NoAnswer({ q }: { q: string }) {
  return (
    <article className="ask-answer ask-answer--none">
      <h2 className="ask-answer__title">No grounded verdict for that yet</h2>
      <p className="ask-answer__lead">
        BollyAI only answers from titles it has actually graded against critics, audiences and
        the subtitles. {q ? <>Nothing in the catalogue matches &ldquo;{q.slice(0, 80)}&rdquo;.</> : null} It will not
        invent a verdict or a number to fill the gap.
      </p>
      <nav className="ask-answer__links">
        <a className="ask-answer__cta" href={`/search/?q=${encodeURIComponent(q)}`}>Search the catalogue &rarr;</a>
        <a className="ask-answer__link" href="/series/">Browse every series</a>
      </nav>
    </article>
  );
}

export function AskClient() {
  const [index, setIndex] = useState<Rec[] | null>(null);
  const [q, setQ] = useState("");
  const [asked, setAsked] = useState("");

  useEffect(() => {
    const params = new URLSearchParams(window.location.search);
    const seed = params.get("q") ?? "";
    setQ(seed);
    setAsked(seed);
    fetch("/ask-index.json")
      .then((r) => r.json())
      .then((data: Rec[]) => setIndex(data))
      .catch(() => setIndex([]));
  }, []);

  const answer = useMemo(() => {
    if (!index || !asked.trim()) return null;
    return answerFor(asked, index);
  }, [index, asked]);

  const submit = (e?: React.FormEvent) => {
    e?.preventDefault();
    setAsked(q);
  };

  return (
    <div className="ask">
      <form className="ask__bar" onSubmit={submit} role="search">
        <span className="ask__spark" aria-hidden="true">◆</span>
        <input
          className="ask__input"
          type="search"
          value={q}
          autoFocus
          enterKeyHint="search"
          placeholder="Is The Glory worth watching?"
          aria-label="Ask BollyAI a question"
          onChange={(e) => setQ(e.target.value)}
        />
        <button className="ask__go" type="submit" aria-label="Ask">Ask</button>
      </form>

      <div className="ask__examples" aria-label="Example questions">
        {EXAMPLES.map((ex) => (
          <button
            type="button"
            className="ask__chip"
            key={ex}
            onClick={() => { setQ(ex); setAsked(ex); }}
          >
            {ex}
          </button>
        ))}
      </div>

      {index === null && <p className="ask__status">Loading BollyAI&rsquo;s grounded verdicts…</p>}

      {answer && (
        <div className="ask__result">
          {answer.kind === "verdict" && <VerdictCard rec={answer.rec} />}
          {answer.kind === "spoiler" && <SpoilerCard rec={answer.rec} />}
          {answer.kind === "rank" && <RankCard label={answer.label} list={answer.list} />}
          {answer.kind === "none" && <NoAnswer q={answer.q} />}
          <p className="ask__fence">
            BollyAI has not watched anything. It has read everyone who has. Every verdict, score
            and line above is assembled from grounded critic, audience and subtitle data - never invented.
          </p>
        </div>
      )}
    </div>
  );
}
