"use client";

// diaryStore - the entire persistence layer for the Verdict Diary (title lane, 2026-06-16).
// 100% client-side: localStorage only, no backend, static-CF-Pages safe. SSR-safe (every access
// is guarded for `window`), versioned key, and cross-tab synced via the storage event so two
// open tabs never drift. This is the visitor's PRIVATE device-local notebook - it never leaves
// the browser, which is also the honesty line shown in the UI.
//
// A module-level cache holds the parsed array so getSnapshot returns a STABLE reference until a
// real write happens - without this, useSyncExternalStore would tear (fresh array every render).
import { useCallback } from "react";
import { useSyncExternalStore } from "react";

export const DIARY_KEY = "bollyai.diary.v1";
const LOCAL_EVENT = "bollyai-diary-change";

export type DiaryStatus = "watchlist" | "watching" | "watched";

export type DiaryEntry = {
  slug: string;
  title: string;
  poster: string;
  desk: string;
  platform: string;
  bollyScore: number | null; // BollyAI's verdict snapshot at save time (for "you vs BollyAI")
  status: DiaryStatus;
  myRating: number | null; // the visitor's own 0-10, null until set
  note: string;
  savedAt: string; // ISO
};

const EMPTY: DiaryEntry[] = [];
let cache: DiaryEntry[] = EMPTY;
let hydrated = false;

function load(): DiaryEntry[] {
  if (typeof window === "undefined") return EMPTY;
  try {
    const raw = window.localStorage.getItem(DIARY_KEY);
    const parsed = raw ? JSON.parse(raw) : [];
    cache = Array.isArray(parsed) ? (parsed as DiaryEntry[]) : EMPTY;
  } catch {
    cache = EMPTY;
  }
  hydrated = true;
  return cache;
}

function getSnapshot(): DiaryEntry[] {
  if (!hydrated) return load();
  return cache;
}

const listeners = new Set<() => void>();

function emit() {
  listeners.forEach((l) => l());
}

function write(next: DiaryEntry[]) {
  cache = next;
  hydrated = true;
  if (typeof window !== "undefined") {
    try {
      window.localStorage.setItem(DIARY_KEY, JSON.stringify(next));
    } catch {
      /* quota / private-mode - fail silent, UI just won't persist this session */
    }
    window.dispatchEvent(new Event(LOCAL_EVENT));
  }
  emit();
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  const onStorage = (e: StorageEvent) => {
    if (e.key === DIARY_KEY) {
      load();
      cb();
    }
  };
  const onLocal = () => cb();
  window.addEventListener("storage", onStorage);
  window.addEventListener(LOCAL_EVENT, onLocal);
  return () => {
    listeners.delete(cb);
    window.removeEventListener("storage", onStorage);
    window.removeEventListener(LOCAL_EVENT, onLocal);
  };
}

export function useDiary() {
  const entries = useSyncExternalStore(subscribe, getSnapshot, () => EMPTY);

  const upsert = useCallback((entry: DiaryEntry) => {
    const i = cache.findIndex((e) => e.slug === entry.slug);
    if (i === -1) write([entry, ...cache]);
    else {
      const next = [...cache];
      next[i] = { ...next[i], ...entry };
      write(next);
    }
  }, []);

  const patch = useCallback((slug: string, fields: Partial<DiaryEntry>) => {
    const i = cache.findIndex((e) => e.slug === slug);
    if (i === -1) return;
    const next = [...cache];
    next[i] = { ...next[i], ...fields };
    write(next);
  }, []);

  const remove = useCallback((slug: string) => {
    write(cache.filter((e) => e.slug !== slug));
  }, []);

  const clearAll = useCallback(() => write([]), []);

  return { entries, upsert, patch, remove, clearAll };
}

// Guard against hydration mismatch: diary-dependent UI should only show after mount (the server
// and first client paint both render the empty snapshot).
export function useMounted(): boolean {
  return useSyncExternalStore(
    (cb) => {
      cb();
      return () => {};
    },
    () => true,
    () => false
  );
}
