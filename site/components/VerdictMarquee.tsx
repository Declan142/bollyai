"use client";

import { Children, useEffect, useState, type ReactNode } from "react";
import type { HeroSubject } from "../lib/home";

// VERDICT MARQUEE - the rotating multi-title hero (revamp 2026-06-15, round 2: Aditya wanted the
// stage ALIVE and multi-poster, not one calm static title). The slides are SERVER-rendered
// <VerdictStage> elements passed as children (keeps lib/data + its node:fs out of the client
// bundle); this client shell only owns the active index - a CSS transform track, prev/next
// arrows, dots, and a clickable poster filmstrip. `subjects` carries the data the controls need.
// Auto-advances (pauses on hover / focus / hidden tab), respects prefers-reduced-motion.
export function VerdictMarquee({ subjects, children }: { subjects: HeroSubject[]; children: ReactNode }) {
  const slides = Children.toArray(children);
  const n = slides.length;
  const [active, setActive] = useState(0);
  const [paused, setPaused] = useState(false);

  const go = (i: number) => setActive(((i % n) + n) % n);

  useEffect(() => {
    if (n <= 1 || paused) return;
    if (typeof window !== "undefined" && window.matchMedia?.("(prefers-reduced-motion: reduce)").matches) return;
    const id = window.setInterval(() => setActive((i) => (i + 1) % n), 6500);
    return () => window.clearInterval(id);
  }, [n, paused]);

  useEffect(() => {
    const onVis = () => setPaused(document.hidden);
    document.addEventListener("visibilitychange", onVis);
    return () => document.removeEventListener("visibilitychange", onVis);
  }, []);

  if (n === 0) return null;

  return (
    <section
      className="verdict-marquee"
      aria-roledescription="carousel"
      aria-label="This week's verdicts"
      onMouseEnter={() => setPaused(true)}
      onMouseLeave={() => setPaused(false)}
      onFocusCapture={() => setPaused(true)}
      onBlurCapture={() => setPaused(false)}
    >
      <div className="verdict-marquee__track" style={{ transform: `translateX(-${active * 100}%)` }}>
        {slides.map((slide, i) => (
          <div className="verdict-marquee__slide" key={i} aria-hidden={i !== active}>
            {slide}
          </div>
        ))}
      </div>

      {n > 1 && (
        <>
          <button
            className="verdict-marquee__arrow verdict-marquee__arrow--prev"
            type="button"
            aria-label="Previous verdict"
            onClick={() => go(active - 1)}
          >
            <span aria-hidden="true">‹</span>
          </button>
          <button
            className="verdict-marquee__arrow verdict-marquee__arrow--next"
            type="button"
            aria-label="Next verdict"
            onClick={() => go(active + 1)}
          >
            <span aria-hidden="true">›</span>
          </button>

          <div className="verdict-marquee__strip" aria-label="Jump to a verdict">
            {subjects.map((s, i) => (
              <button
                key={`thumb-${s.kind}-${s.slug}`}
                type="button"
                aria-label={s.title}
                aria-current={i === active}
                className={`verdict-marquee__thumb${i === active ? " is-active" : ""}`}
                data-desk={s.desk}
                onClick={() => go(i)}
              >
                <img src={s.poster.src} alt="" aria-hidden="true" loading="lazy" decoding="async" />
                {s.score != null && <span className="verdict-marquee__thumb-score">{s.score.toFixed(1)}</span>}
              </button>
            ))}
          </div>

          <div className="verdict-marquee__dots" aria-hidden="true">
            {slides.map((_, i) => (
              <span key={`dot-${i}`} className={i === active ? "is-active" : ""} />
            ))}
          </div>
        </>
      )}
    </section>
  );
}
