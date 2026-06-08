export type DeskSlug =
  | "bollywood"
  | "kollywood"
  | "tollywood"
  | "mollywood"
  | "sandalwood"
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
    slug: "bollywood",
    label: "Bollywood",
    industryName: "Hindi cinema",
    tint: "saffron",
    answer: "Bollywood desk tracks Hindi theatrical verdicts, opening weekends, and the films that turn PR noise into real trade numbers."
  },
  {
    slug: "kollywood",
    label: "Kollywood",
    industryName: "Tamil cinema",
    tint: "coral",
    answer: "Kollywood desk follows Tamil releases, live collections, and craft scores with an India-wide lens."
  },
  {
    slug: "tollywood",
    label: "Tollywood",
    industryName: "Telugu cinema",
    tint: "gold",
    answer: "Tollywood desk is built for day-wise trade estimates, pan-India splits, and blockbuster verdicts."
  },
  {
    slug: "mollywood",
    label: "Mollywood",
    industryName: "Malayalam cinema",
    tint: "sage",
    answer: "Mollywood desk reads Malayalam cinema through craft, word of mouth, and steady box-office legs."
  },
  {
    slug: "sandalwood",
    label: "Sandalwood",
    industryName: "Kannada cinema",
    tint: "brass",
    answer: "Sandalwood desk keeps Kannada releases visible without pretending a thin source is enough."
  },
  {
    slug: "hollywood",
    label: "Hollywood",
    industryName: "Hollywood in India",
    tint: "moonstone",
    answer: "Hollywood desk covers India-facing Hollywood releases, weekend charts, and franchise-scale comparisons."
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
