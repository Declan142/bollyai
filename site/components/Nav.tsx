"use client";

import { usePathname } from "next/navigation";
import { useEffect, useRef, useState } from "react";
import { HeaderSearch } from "./HeaderSearch";
import styles from "./Nav.module.css";

const PRIMARY: { href: string; label: string }[] = [
  { href: "/watch/", label: "Watchlists" },
  { href: "/ott/calendar/", label: "OTT Calendar" },
  { href: "/browse/", label: "Browse" },
  { href: "/box-office/", label: "Box Office" },
  { href: "/series/diary/", label: "My Diary" }
];

export function Nav() {
  const pathname = usePathname();
  const [open, setOpen] = useState(false);
  const burgerRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setOpen(false);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;

    const previousOverflow = document.body.style.overflow;
    const onKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setOpen(false);
        burgerRef.current?.focus();
        return;
      }

      if (event.key !== "Tab" || !drawerRef.current || !burgerRef.current) return;
      const drawerControls = Array.from(
        drawerRef.current.querySelectorAll<HTMLElement>("a[href], button:not([disabled]), input:not([disabled])")
      );
      const focusable = [burgerRef.current, ...drawerControls];
      const first = focusable[0];
      const last = focusable.at(-1);

      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault();
        last?.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault();
        first.focus();
      }
    };

    document.body.style.overflow = "hidden";
    document.addEventListener("keydown", onKeyDown);
    window.requestAnimationFrame(() => drawerRef.current?.querySelector<HTMLAnchorElement>("a")?.focus());

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [open]);

  const closeAndRestoreFocus = () => {
    setOpen(false);
    burgerRef.current?.focus();
  };

  return (
    <header className={`${styles.header}${open ? ` ${styles.open}` : ""}`}>
      <a href="/" className={styles.brand} aria-label="BollyAI home">
        <b>BollyAI</b>
        <small>Har Friday ka faisla.</small>
      </a>

      <button
        ref={burgerRef}
        className={styles.burger}
        type="button"
        aria-expanded={open}
        aria-controls="site-nav-drawer"
        aria-label={open ? "Close navigation menu" : "Open navigation menu"}
        onClick={() => setOpen((current) => !current)}
      >
        <span />
        <span />
        <span />
      </button>

      <button
        className={styles.overlay}
        type="button"
        aria-label="Close navigation menu"
        tabIndex={-1}
        onClick={closeAndRestoreFocus}
      />

      <div
        className={styles.drawer}
        id="site-nav-drawer"
        ref={drawerRef}
        role={open ? "dialog" : undefined}
        aria-modal={open || undefined}
        aria-label={open ? "Site navigation" : undefined}
      >
        <nav className={styles.primary} aria-label="Primary navigation">
          <a
            className={styles.ask}
            href="/ask/"
            aria-current={pathname.startsWith("/ask/") ? "page" : undefined}
            onClick={() => setOpen(false)}
          >
            <span className={styles.askSpark} aria-hidden="true">✦</span>
            Ask BollyAI
          </a>
          {PRIMARY.map((item) => {
            const current = pathname === item.href || pathname.startsWith(item.href);
            return (
              <a
                className={styles.link}
                href={item.href}
                key={item.href}
                aria-current={current ? "page" : undefined}
                onClick={() => setOpen(false)}
              >
                {item.label}
              </a>
            );
          })}
        </nav>
        <form className="site-search site-search--drawer" action="/search/" method="get" role="search">
          <input
            type="search"
            name="q"
            placeholder="Search titles and verdicts..."
            aria-label="Search BollyAI"
            autoComplete="off"
          />
          <button type="submit" aria-label="Search">↵</button>
        </form>
      </div>

      <div className={styles.searchSlot}>
        <HeaderSearch />
      </div>
    </header>
  );
}
