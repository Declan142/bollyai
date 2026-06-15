"use client";

import { useRef } from "react";
import type { OttCalItem } from "../lib/home";

// OTT CALENDAR HERO (revamp 2026-06-15, round 3: Aditya wanted the hero to be an OTT release
// calendar - "click karke series pe ajaye"). A date-ordered rail of what is dropping this week +
// what just landed on OTT, each card clickable to its page. Cinematic dark stage with an ambient
// backdrop from the lead poster. Client only for the scroll arrows; the rail is native scroll.
function parts(iso: string): { day: string; mon: string; dow: string } {
  const d = new Date(`${iso}T00:00:00+05:30`);
  const f = (opt: Intl.DateTimeFormatOptions) => new Intl.DateTimeFormat("en-IN", { timeZone: "Asia/Kolkata", ...opt }).format(d);
  return { day: f({ day: "2-digit" }), mon: f({ month: "short" }).toUpperCase(), dow: f({ weekday: "short" }).toUpperCase() };
}

export function OttCalendarHero({ items }: { items: OttCalItem[] }) {
  const railRef = useRef<HTMLDivElement>(null);
  if (items.length === 0) return null;
  const ambient = items.find((i) => i.poster)?.poster ?? null;
  const nudge = (dir: number) => railRef.current?.scrollBy({ left: dir * 360, behavior: "smooth" });

  return (
    <section className="ott-hero" aria-label="New and coming on OTT">
      {ambient && (
        <div className="ott-hero__ambient" aria-hidden="true">
          <img src={ambient.src} alt="" aria-hidden="true" decoding="async" />
        </div>
      )}
      <div className="ott-hero__scrim" aria-hidden="true" />

      <div className="ott-hero__inner">
        <header className="ott-hero__head reveal">
          <span className="ott-hero__eyebrow">BollyAI · OTT Calendar</span>
          <h1 className="ott-hero__title">New &amp; Coming on OTT</h1>
          <p className="ott-hero__sub">
            What is dropping this week and what just landed, across every platform. Tap any title for the verdict.
          </p>
          <a className="ott-hero__all" href="/ott/calendar/">
            Full calendar <span aria-hidden="true">→</span>
          </a>
        </header>

        <div className="ott-hero__railwrap">
          <button className="ott-hero__arrow ott-hero__arrow--prev" type="button" aria-label="Scroll back" onClick={() => nudge(-1)}>
            <span aria-hidden="true">‹</span>
          </button>

          <div className="ott-hero__rail" ref={railRef}>
            {items.map((item, i) => {
              const { day, mon, dow } = parts(item.date);
              const inner = (
                <>
                  <span className={`ottc-card__date${item.upcoming ? " is-upcoming" : ""}`}>
                    <span className="ottc-card__dow">{item.upcoming ? dow : "ON OTT"}</span>
                    <strong>{day}</strong>
                    <span className="ottc-card__mon">{mon}</span>
                  </span>
                  <span className="ottc-card__art">
                    {item.poster ? (
                      <img src={item.poster.src} alt="" aria-hidden="true" loading={i < 4 ? "eager" : "lazy"} decoding="async" />
                    ) : (
                      <span className="one-sheet" aria-hidden="true">
                        <span className="one-sheet__top">
                          <span>{item.platform}</span>
                          <span>{item.date.slice(0, 4)}</span>
                        </span>
                        <span className="one-sheet__title">{item.title}</span>
                        <span className="one-sheet__foot">BollyAI Edition</span>
                      </span>
                    )}
                    {item.score != null && <span className="ottc-card__score">{item.score.toFixed(1)}</span>}
                    {item.upcoming && <span className="ottc-card__soon">Coming</span>}
                  </span>
                  <span className="ottc-card__plate">
                    <span className="ottc-card__platform">{item.platform}</span>
                    <strong className="ottc-card__title">{item.title}</strong>
                  </span>
                </>
              );
              const key = `${item.kind}-${item.title}-${item.date}`;
              return item.href ? (
                <a className="ottc-card" data-desk="streaming" href={item.href} key={key}>
                  {inner}
                </a>
              ) : (
                <div className="ottc-card ottc-card--announce" key={key}>
                  {inner}
                </div>
              );
            })}
          </div>

          <button className="ott-hero__arrow ott-hero__arrow--next" type="button" aria-label="Scroll forward" onClick={() => nudge(1)}>
            <span aria-hidden="true">›</span>
          </button>
        </div>
      </div>
    </section>
  );
}
