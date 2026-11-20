interface Props {
  score: number | null;
}

export function ScoreBar({ score }: Props) {
  if (score === null) {
    return <span className="score-unknown">Mastery: not tested yet</span>;
  }
  const percent = Math.round(score * 100);
  const level = score < 0.45 ? "weak" : score < 0.7 ? "mid" : "strong";
  return (
    <div className="score">
      <div className="score-track" role="meter" aria-valuemin={0} aria-valuemax={100} aria-valuenow={percent}
        aria-label="Mastery">
        <div className={`score-fill score-fill--${level}`} style={{ width: `${percent}%` }} />
      </div>
      <span className="score-label">Mastery: {percent}%</span>
    </div>
  );
}
