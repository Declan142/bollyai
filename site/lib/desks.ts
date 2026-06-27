export type DeskSlug =
  | "hollywood"
  | "streaming";

export type Desk = {
  slug: DeskSlug;
  label: string;
  industryName: string;
  tint: string;
  answer: string;
};

export const DESKS: Desk[] = [
  {
    slug: "hollywood",
    label: "Hollywood",
    industryName: "Hollywood",
    tint: "moonstone",
    answer: "Hollywood desk covers Western theatrical releases, weekend charts, and franchise-scale comparisons."
  },
  {
    slug: "streaming",
    label: "Streaming",
    industryName: "OTT",
    tint: "peach",
    answer: "Streaming desk answers what arrives on OTT, where it lands, and what is worth the weekend."
  }
];

export const DESK_SLUGS = DESKS.map((desk) => desk.slug);

export function getDesk(slug: string): Desk | undefined {
  return DESKS.find((desk) => desk.slug === slug);
}
