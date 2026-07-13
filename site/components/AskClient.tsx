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
  kw?: string;
};

const FILLER = new Set([
  "is", "the", "a", "an", "of", "to", "i", "should", "watch", "watching", "worth",
  "it", "good", "review", "reviews", "how", "about", "me", "do", "you", "think",
  "any", "now", "right", "currently", "this", "that", "for", "on", "in", "at",
  "and", "or", "with", "best", "top", "great", "recommend", "recommendation",
  "suggest", "what", "which", "are", "some", "show", "shows", "series", "movie",
  "movies", "film", "films", "ott", "streaming", "stream", "really", "very", "so",
  "like", "something", "anything", "one", "where", "can", "there", "new", "please",
  "gimme", "give", "find", "looking", "thats", "whats", "set", "based", "story"
]);

// region word -> { country match, language codes }
const REGIONS: { keys: string[]; country?: string; langs?: string[]; label: string }[] = [
  { keys: ["british", "britain", "uk"], country: "United Kingdom", label: "British" },
  { keys: ["american", "america", "us", "hollywood"], country: "United States", label: "American" },
  { keys: ["spanish", "spain"], country: "Spain", langs: ["es"], label: "Spanish" },
  { keys: ["french", "france"], country: "France", langs: ["fr"], label: "French" },
  { keys: ["german", "germany"], country: "Germany", langs: ["de"], label: "German" },
  { keys: ["italian", "italy"], country: "Italy", langs: ["it"], label: "Italian" },
  { keys: ["canadian", "canada"], country: "Canada", label: "Canadian" },
  { keys: ["australian", "australia"], country: "Australia", label: "Australian" }
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

// mood / vibe word -> facet token tested against the record keyword blob (record.kw).
// These are vocabulary users type that are not literal genres ("mind bending", "feel good").
const MOOD_SYN: Record<string, string[]> = {
  mindbending: ["mind bending", "mind-bending", "mindbending", "twisty", "cerebral", "trippy"],
  feelgood: ["feel good", "feel-good", "feelgood", "wholesome", "comfort", "cosy", "cozy", "heartwarming"],
  funny: ["funny", "hilarious", "laugh", "lighthearted"],
  dark: ["dark", "gritty", "bleak", "disturbing", "grim"],
  revenge: ["revenge", "vengeance", "vengeful"],
  scary: ["scary", "creepy", "terrifying", "horror"],
  heist: ["heist"],
  intense: ["intense", "gripping", "edge of", "tense"]
};

const norm = (s: string) =>
  s.toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();

// light suffix stemmer so bullied/bullying, revenge/avenging, killer/killing align
const stem = (w: string): string => {
  if (w.length > 5) {
    if (w.endsWith("ing")) return w.slice(0, -3);
    if (w.endsWith("ied")) return w.slice(0, -3) + "y";
    if (w.endsWith("ed")) return w.slice(0, -2);
  }
  return w.length > 4 && w.endsWith("s") ? w.slice(0, -1) : w;
};

const RUNG_BLURB: Record<string, string> = {
  "MUST-WATCH": "a front-of-queue watch",
  "WORTH-IT": "worth your time",
  "ONE-TIME WATCH": "a one-time watch",
  "SKIP": "one to skip",
  "DISASTER DROP": "a disaster drop"
};

type Answer =
  | { kind: "verdict"; rec: Rec; where?: boolean }
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

// genres are canonical tokens that appear in record.g; moods are tokens that live in record.kw
function detectFacets(qNorm: string): { genres: string[]; moods: string[] } {
  const genres: string[] = [];
  const moods: string[] = [];
  for (const [canon, syns] of Object.entries(GENRE_SYN)) {
    if (syns.some((s) => qNorm.includes(s))) genres.push(canon);
  }
  for (const [canon, syns] of Object.entries(MOOD_SYN)) {
    if (syns.some((s) => qNorm.includes(s))) moods.push(canon);
  }
  return { genres, moods };
}

const regionMatch = (rec: Rec, reg: { country?: string; langs?: string[] }) =>
  Boolean((reg.country && rec.o === reg.country) || (reg.langs && rec.l && reg.langs.includes(rec.l)));

// Pre-tokenised record for recall: title tokens (tt), genre tokens (gt), keyword-blob tokens (kt).
type Aug = { r: Rec; tt: Set<string>; gt: Set<string>; kt: Set<string> };
function buildAug(index: Rec[]): Aug[] {
  return index.map((r) => ({
    r,
    tt: new Set(norm(r.t).split(" ").filter((w) => w.length > 1).map(stem)),
    gt: new Set((r.g || []).flatMap((g) => norm(g).split(" ")).map(stem)),
    kt: new Set(norm(r.kw || "").split(" ").filter((w) => w.length > 2).map(stem))
  }));
}

const FACET_STOP = new Set<string>([
  ...REGIONS.flatMap((r) => r.keys),
  ...Object.values(GENRE_SYN).flat().flatMap((s) => s.split(" ")),
  ...Object.values(MOOD_SYN).flat().flatMap((s) => s.split(" "))
]);

// The recall engine: region as a hard filter + boost, genre/mood facets, then keyword overlap.
// Pure ranking over the grounded index - it can only return titles that exist, never a new fact.
function recall(aug: Aug[], qNorm: string): { r: Rec; s: number }[] {
  const region = detectRegion(qNorm);
  const { genres, moods } = detectFacets(qNorm);
  const facets = [...genres, ...moods];
  const qtok = [...new Set(qNorm.split(" "))]
    .filter((w) => w.length > 2 && !FILLER.has(w) && !FACET_STOP.has(w))
    .map(stem);
  const out: { r: Rec; s: number }[] = [];
  for (const a of aug) {
    if (region && !regionMatch(a.r, region)) continue;
    let s = 0;
    if (region) s += 3;
    for (const f of facets) {
      if (a.gt.has(f)) s += 3;
      else if (a.kt.has(f)) s += 1.5;
    }
    for (const w of qtok) {
      if (a.tt.has(w)) s += 4;
      else if (a.kt.has(w)) s += 1.5;
    }
    if (s > 0) {
      if (a.r.sc != null) s += a.r.sc * 0.02; // tiny quality tiebreak, never decisive alone
      out.push({ r: a.r, s });
    }
  }
  out.sort((x, y) => y.s - x.s);
  return out;
}

// A title is only accepted as a direct hit when the query actually contains it (not just a
// loose token overlap) - keeps "is the glory worth watching" exact while letting oblique
// phrasings fall through to recall.
function strongTitle(qNorm: string, index: Rec[]): Rec | null {
  const rec = matchEntity(qNorm, index);
  if (rec && qNorm.includes(norm(rec.t)) && norm(rec.t).length >= 3) return rec;
  return null;
}

function answerFor(raw: string, aug: Aug[]): Answer {
  const q = raw.trim();
  const qNorm = norm(q);
  if (!qNorm) return { kind: "none", q };
  const index = aug.map((a) => a.r);

  const isBest = /\b(best|top|greatest|recommend|suggest|good|favourite|favorite)\b/.test(qNorm) || /^what.*watch/.test(qNorm);
  const isSpoiler = /\bspoiler/.test(qNorm);
  const isWhere = /\bwhere\b/.test(qNorm) || /\b(stream|streaming|available)\b/.test(qNorm) || /\bon (netflix|prime|jiohotstar|sonyliv|zee5|hotstar)\b/.test(qNorm);

  // Spoiler intent first - graceful, no-fabrication branch.
  if (isSpoiler) {
    const rec = strongTitle(qNorm, index) || recall(aug, qNorm)[0]?.r || null;
    if (rec) return { kind: "spoiler", rec };
    return { kind: "none", q };
  }

  // A named title beats a "best/good" reading - "is squid game good" wants the Squid Game
  // verdict, not a generic chart. Checked before the ranking branch.
  const titleRec = strongTitle(qNorm, index);
  if (titleRec) return { kind: "verdict", rec: titleRec, where: isWhere };

  // Best / recommendation intent -> ranking from grounded scores, filtered by region + facets.
  if (isBest) {
    const region = detectRegion(qNorm);
    const { genres, moods } = detectFacets(qNorm);
    const hasFacet = genres.length > 0 || moods.length > 0;
    const contentTok = qNorm.split(" ").filter((w) => w.length > 2 && !FILLER.has(w) && !FACET_STOP.has(w));
    // Rank when the ask is generic ("best shows") or scoped by region/facet. A best-query that
    // names unresolved specifics ("is xyzzy good") instead falls to recall, then graceful none.
    if (region || hasFacet || contentTok.length === 0) {
      const wantsNow = /\b(now|currently|latest|2026|2025|recent|these days)\b/.test(qNorm);
      let pool = aug.filter((a) => a.r.sc !== null);
      if (region) pool = pool.filter((a) => regionMatch(a.r, region));
      if (hasFacet) {
        pool = pool.filter((a) => genres.some((g) => a.gt.has(g)) || moods.some((m) => a.gt.has(m) || a.kt.has(m)));
      }
      let list = pool.map((a) => a.r).sort((x, y) => (y.sc! - x.sc!) || ((y.y ?? 0) - (x.y ?? 0)));
      if (wantsNow) list = [...list].sort((x, y) => ((y.y ?? 0) - (x.y ?? 0)) || (y.sc! - x.sc!));
      list = list.slice(0, 5);
      if (list.length > 0) {
        const facetLabel = [...genres, ...moods].map((g) => g.replace("mindbending", "mind-bending").replace("feelgood", "feel-good")).join(" ");
        const bits = [region?.label, facetLabel].filter(Boolean);
        const label = `Best ${bits.join(" ") || "grounded"} ${list.length > 1 ? "titles" : "title"}${wantsNow ? ", newest first" : ""}`.replace(/\s+/g, " ");
        return { kind: "rank", label, list };
      }
    }
    // nothing fit - fall through to keyword recall rather than dead-ending
  }

  // Oblique question -> keyword recall over names / plot / mood facets in the grounded blob.
  const scored = recall(aug, qNorm);
  if (scored.length > 0) {
    const top = scored[0];
    const second = scored[1]?.s ?? 0;
    // a clearly dominant single match becomes a direct verdict
    if (top.s >= 4.5 && (scored.length < 2 || top.s >= second + 2)) {
      return { kind: "verdict", rec: top.r, where: isWhere };
    }
    if (top.s >= 3) {
      return { kind: "rank", label: "Closest grounded matches", list: scored.slice(0, 5).map((x) => x.r) };
    }
  }

  // Loose title overlap as a last resort before declining.
  const loose = matchEntity(qNorm, index);
  if (loose) return { kind: "verdict", rec: loose, where: isWhere };

  return { kind: "none", q };
}

const EXAMPLES = [
  "Is Severance worth watching?",
  "Best crime thriller right now",
  "Where to watch The Crown",
  "Best procedural drama",
  "Best comedy series",
  "Is The Last of Us spoiler-heavy?"
];

function Stars({ score }: { score: number }) {
  return (
    <span className="ask-score">
      <strong>{score.toFixed(1)}</strong>
      <span className="ask-score__scale">/10</span>
    </span>
  );
}

function VerdictCard({ rec, where }: { rec: Rec; where?: boolean }) {
  const meta = [rec.o, rec.g.slice(0, 2).join(" · ")].filter(Boolean).join("  ·  ");
  return (
    <article className="ask-answer" data-desk={rec.k === "Series" ? "streaming" : "hollywood"}>
      <header className="ask-answer__head">
        <div>
          <span className="ask-answer__kind">{rec.k}{rec.y ? ` · ${rec.y}` : ""}</span>
          <h2 className="ask-answer__title">
            <a href={rec.u}>{rec.t}</a>
          </h2>
          {rec.p && <span className="ask-answer__platform" data-where={where ? "" : undefined}>{where ? "Streams on " : ""}{rec.p}</span>}
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
        {where && rec.p
          ? <>{rec.t} streams on <strong>{rec.p}</strong>{rec.o ? ` (${rec.o})` : ""}{rec.v ? <>. BollyAI calls it <strong>{RUNG_BLURB[rec.v] ?? rec.v.toLowerCase()}</strong>{rec.sc !== null ? <>, BollyMeter <strong>{rec.sc.toFixed(1)}</strong>.</> : "."}</> : "."}</>
          : rec.v
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

function NoAnswer({ q, onPick }: { q: string; onPick: (s: string) => void }) {
  return (
    <article className="ask-answer ask-answer--none">
      <h2 className="ask-answer__title">No grounded verdict for that yet</h2>
      <p className="ask-answer__lead">
        BollyAI only answers from titles it has actually graded against critics, audiences and
        the subtitles. {q ? <>Nothing in the catalogue matches &ldquo;{q.slice(0, 80)}&rdquo;.</> : null} It will not
        invent a verdict or a number to fill the gap.
      </p>
      <div className="ask-answer__try">
        <span className="ask-answer__try-label">Try one of these</span>
        <div className="ask__examples">
          {EXAMPLES.slice(0, 4).map((ex) => (
            <button type="button" className="ask__chip" key={ex} onClick={() => onPick(ex)}>{ex}</button>
          ))}
        </div>
      </div>
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

  const aug = useMemo(() => (index ? buildAug(index) : null), [index]);

  const answer = useMemo(() => {
    if (!aug || !asked.trim()) return null;
    return answerFor(asked, aug);
  }, [aug, asked]);

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
          placeholder="Is Severance worth watching?"
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
          {answer.kind === "verdict" && <VerdictCard rec={answer.rec} where={answer.where} />}
          {answer.kind === "spoiler" && <SpoilerCard rec={answer.rec} />}
          {answer.kind === "rank" && <RankCard label={answer.label} list={answer.list} />}
          {answer.kind === "none" && <NoAnswer q={answer.q} onPick={(s) => { setQ(s); setAsked(s); }} />}
          <p className="ask__fence">
            BollyAI has not watched anything. It has read everyone who has. Every verdict, score
            and line above is assembled from grounded critic, audience and subtitle data - never invented.
          </p>
        </div>
      )}
    </div>
  );
}
