export function BollyMeter({ score, basis }: { score: number; basis: string }) {
  return (
    <div className="bollymeter" aria-label={`BollyMeter ${score.toFixed(1)} out of 10`}>
      <span className="bollymeter__label">BollyMeter</span>
      <span className="bollymeter__score">{score.toFixed(1)}</span>
      <span className="bollymeter__scale">/10</span>
      <span className="bollymeter__basis">{basis}</span>
    </div>
  );
}
