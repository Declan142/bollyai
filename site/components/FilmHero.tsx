import type { Film } from "../lib/data";
import { budgetDisplay, formatDate } from "../lib/data";
import { AnswerBlock } from "./AnswerBlock";
import { BollyMeter } from "./BollyMeter";
import { DateModified } from "./DateModified";
import { VerdictMeter } from "./VerdictMeter";

export function FilmHero({
  film,
  eyebrow,
  answer,
  showMeter = true
}: {
  film: Film;
  eyebrow: string;
  answer: string;
  showMeter?: boolean;
}) {
  return (
    <section className="film-hero">
      <div className="poster-frame">
        <img src={film.poster.src} alt={film.poster.alt} width="342" height="513" fetchPriority="high" loading="eager" />
      </div>
      <div className="film-hero__copy">
        <p className="eyebrow">{eyebrow}</p>
        <h1>{film.title.value}</h1>
        <AnswerBlock>{answer}</AnswerBlock>
        <div className="hero-facts">
          <span>{formatDate(film.release_date.value)}</span>
          <span>{film.original_language.value.toUpperCase()}</span>
          <span>Budget {budgetDisplay(film)}</span>
        </div>
        <VerdictMeter rung={film.verdict.ladder_rung} />
        {showMeter && <BollyMeter score={film.bollymeter.score} basis={film.bollymeter.basis} />}
        <DateModified value={film.date_modified} />
      </div>
    </section>
  );
}
