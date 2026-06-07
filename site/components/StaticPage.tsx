import { DateModified } from "./DateModified";

export function StaticPage({
  title,
  answer,
  dateModified,
  children
}: {
  title: string;
  answer: string;
  dateModified: string;
  children: React.ReactNode;
}) {
  return (
    <main className="page-shell static-page" data-desk="bombay">
      <section className="section-head">
        <p className="eyebrow">BollyAI policy</p>
        <h1>{title}</h1>
        <p className="answer-block">{answer}</p>
        <DateModified value={dateModified} />
      </section>
      <div className="prose">{children}</div>
    </main>
  );
}
