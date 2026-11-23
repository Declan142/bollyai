export type OttRelease = {
  title: string;
  platform: string;
  release_date: string;
  type: "film" | "series";
  sources: { name: string; url: string }[];
  verdict_line: string;
};
export type OttEdition = {
  generated_at: string;
  window: { start: string; end: string };
  entries: OttRelease[];
};
export const OTT_FEED_URL: string;
export function parseOttFeed(raw: unknown): OttEdition | null;
export function newerOttEdition(raw: unknown, published: Pick<OttEdition, "generated_at" | "window">, now?: Date): OttEdition | null;
