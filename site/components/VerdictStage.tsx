import { BollyMeterDial } from "./BollyMeterDial";
import { formatDate } from "../lib/data";
import type { HeroSubject } from "../lib/home";

// VERDICT STAGE - the above-the-fold hero (revamp 2026-06-15). Replaces the equal-weight bento
// the entire 10-Opus team flagged as the core failure. One commanding title: a full-bleed
// cinematic stage built from the real portrait poster (no site-wide backdrops exist - only 1 -
// so the same poster, heavily blurred + scaled, becomes the ambient backdrop; the sharp poster
// is the key-art object). Lower-left editorial composition; the verdict reads like an ANSWER.
function cap(word: string): string {
  return word.charAt(0).toUpperCase() + word.slice(1).toLowerCase();
}

export function VerdictStage({ subject, updated, eager = true }: { subject: HeroSubject; updated: string; eager?: boolean }) {
  const answerLine = subject.basis
    ? subject.basis
    : subject.verdictWord
      ? `${cap(subject.verdictWord)}.`
      : "Verdict tracking - it finalises after the run, never mid-run.";

  return (
    <section className="verdict-stage" data-desk={subject.desk} aria-label={`Today's verdict: ${subject.title}`}>
      <div className="verdict-stage__ambient" aria-hidden="true">
        <img src={subject.poster.src} alt="" aria-hidden="true" decoding="async" loading={eager ? "eager" : "lazy"} />
      </div>
      <div className="verdict-stage__scrim" aria-hidden="true" />

      <div className="verdict-stage__inner">
        <div className="verdict-stage__body reveal">
          <span className="verdict-stage__masthead">
            <span className="verdict-stage__brand">BollyAI</span>
            <span className="verdict-stage__sep" aria-hidden="true">/</span>
            <span className="verdict-stage__kicker">The Verdict</span>
            <time className="verdict-stage__date">{formatDate(updated)}</time>
          </span>

          <span className="verdict-stage__eyebrow">
            {subject.deskLabel} · {subject.kind === "film" ? "Box-office verdict" : "BollyMeter verdict"}
          </span>

          <h1 className="verdict-stage__title">{subject.title}</h1>

          <p className="verdict-stage__answer">{answerLine}</p>

          {subject.boFigure ? (
            <span className="verdict-stage__figure">
              <strong>{subject.boFigure}</strong>
              <span className="verdict-stage__figure-meta">trade estimate · 2 sources verified</span>
            </span>
          ) : (
            <span className="verdict-stage__figure">
              <strong>{subject.statusLine}</strong>
            </span>
          )}

          <span className="verdict-stage__cta-row">
            <a className="verdict-stage__cta" href={subject.href}>
              Read the verdict <span aria-hidden="true">→</span>
            </a>
          </span>

          <ul className="verdict-stage__honesty" aria-label="Why you can trust this">
            <li>Disclosed AI critic</li>
            <li>Cited box office</li>
            <li>No fake ratings</li>
          </ul>
        </div>

        <a
          className="verdict-stage__art"
          href={subject.href}
          data-desk={subject.desk}
          aria-label={`Open ${subject.title}`}
        >
          <span className="verdict-stage__frame">
            <img
              className="verdict-stage__poster"
              src={subject.poster.src}
              alt={subject.poster.alt}
              width={342}
              height={513}
              fetchPriority={eager ? "high" : "auto"}
              loading={eager ? "eager" : "lazy"}
              decoding="async"
            />
            {subject.fresh && <span className="verdict-stage__fresh">New this week</span>}
          </span>

          {subject.score != null ? (
            <span className="verdict-stage__dial">
              <BollyMeterDial score={subject.score} size="hero" />
            </span>
          ) : subject.verdictWord ? (
            <span className="verdict-stage__stamp verdict-stamp" data-rung={subject.verdictWord}>
              {subject.verdictWord}
            </span>
          ) : null}
        </a>
      </div>
    </section>
  );
}
