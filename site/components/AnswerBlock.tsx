function clampWords(value: string, maxWords = 60): string {
  const words = value.trim().split(/\s+/);
  if (words.length <= maxWords) {
    return value;
  }
  return `${words.slice(0, maxWords).join(" ")}...`;
}

export function AnswerBlock({ children }: { children: string }) {
  return <p className="answer-block">{clampWords(children, 60)}</p>;
}
