import type { Film } from "../lib/data";
import { formatCrore } from "../lib/data";
import { VerdictMeter } from "./VerdictMeter";

export function FilmCard({ film, type }: { film: Film; type: "review" | "box-office" | "upcoming" }) {
  const href = `/${film.canonical_industry}/${type === "box-office" ? "box-office" : type === "review" ? "reviews" : "upcoming"}/${film.slug}/`;
  const total = film.box_office.totals.india_net_inr_cr.value;

  return (
    <a href={href} className="film-card" data-desk={film.canonical_industry}>
      <img src={film.poster.src} alt={film.poster.alt} width="185" height="278" loading="lazy" />
      <span className="film-card__body">
        <span className="eyebrow">{type.replace("-", " ")}</span>
        <strong>{film.title.value}</strong>
        <span className="film-card__meta">{formatCrore(total)} India nett</span>
        <VerdictMeter rung={film.verdict.ladder_rung} compact />
      </span>
    </a>
  );
}
