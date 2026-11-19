import { useEffect, useState } from "react";
import { Link, useParams, useSearchParams } from "react-router-dom";
import { api } from "../api";
import { useStudent } from "../student";
import type { AnswerResult, Diagnosis, Exercise } from "../types";

export function PracticePage() {
  const { conceptId } = useParams();
  const [params] = useSearchParams();
  const target = params.get("target");
  const { current } = useStudent();

  const [exercises, setExercises] = useState<Exercise[]>([]);
  const [index, setIndex] = useState(0);
  const [answer, setAnswer] = useState<AnswerResult | null>(null);
  const [picked, setPicked] = useState<string | null>(null);
  const [correctCount, setCorrectCount] = useState(0);
  const [after, setAfter] = useState<Diagnosis | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!current || !conceptId) return;
    setIndex(0);
    setAnswer(null);
    setPicked(null);
    setCorrectCount(0);
    setAfter(null);
    api.practice(current.id, conceptId).then(setExercises).catch((e: Error) => setError(e.message));
  }, [current?.id, conceptId]);

  const done = exercises.length > 0 && index >= exercises.length;

  useEffect(() => {
    if (done && current && target) {
      api.diagnosis(current.id, target).then(setAfter).catch((e: Error) => setError(e.message));
    }
  }, [done, current?.id, target]);

  if (!conceptId) {
    return (
      <div className="page">
        <h1>Micro exercises</h1>
        <p className="muted">Get a diagnosis first, then practise its root cause. <Link to="/">Go to diagnosis</Link></p>
      </div>
    );
  }
  if (!current) return <div className="page"><p className="muted">Pick a student first.</p></div>;

  const exercise = exercises[index];

  async function pick(option: string) {
    if (!current || !exercise || answer) return;
    setPicked(option);
    try {
      const result = await api.answer(current.id, exercise.id, option);
      setAnswer(result);
      if (result.correct) setCorrectCount((n) => n + 1);
    } catch (e) {
      setError((e as Error).message);
    }
  }

  function next() {
    setIndex((i) => i + 1);
    setAnswer(null);
    setPicked(null);
  }

  return (
    <div className="page page--narrow">
      <header className="page-header">
        <p className="eyebrow">Target: {conceptId.replace(/-/g, " ")}{target && ` · then: ${target.replace(/-/g, " ")}`}</p>
        <h1>Micro exercises</h1>
        <div className="progress" aria-label={`Exercise ${Math.min(index + 1, exercises.length)} of ${exercises.length}`}>
          {exercises.map((e, i) => (
            <span key={e.id} className={i < index || (i === index && answer) ? "progress-step done" : "progress-step"} />
          ))}
        </div>
      </header>

      {error && <p className="error">{error}</p>}

      {exercise && (
        <section className="card">
          <div className="card-header">
            <span className="eyebrow">{index + 1} / {exercises.length} · {exercise.kind.replace("_", " ")}</span>
          </div>
          <h2>{exercise.question}</h2>
          {exercise.code && <pre className="code">{exercise.code}</pre>}
          <div className="options">
            {exercise.options.map((option) => {
              let state = "";
              if (answer) {
                if (option === answer.correct_answer) state = "option--correct";
                else if (option === picked) state = "option--wrong";
              }
              return (
                <button key={option} className={`option ${state}`} onClick={() => pick(option)}
                  disabled={answer !== null} aria-pressed={picked === option}>
                  {option}
                </button>
              );
            })}
          </div>
          {answer && (
            <div className={answer.correct ? "feedback feedback--good" : "feedback feedback--bad"}>
              <strong>{answer.correct ? "Correct! " : "Not quite. "}</strong>
              {answer.explanation}
              <div className="feedback-score">
                Mastery: {Math.round(answer.old_score * 100)}% → {Math.round(answer.new_score * 100)}%
              </div>
            </div>
          )}
          {answer && (
            <button className="button" onClick={next}>
              {index + 1 < exercises.length ? "Next exercise" : "Finish"}
            </button>
          )}
        </section>
      )}

      {done && (
        <section className="card">
          <h2>Done: {correctCount} / {exercises.length} correct</h2>
          {after && (
            <p>
              {after.root_cause.id === conceptId
                ? <>{after.root_cause.name} still needs work. Try the set again.</>
                : after.root_cause.id === after.target.id
                  ? <>The gap under {after.target.name} looks fixed. Now retry the task.</>
                  : <>Next gap under {after.target.name}: <strong>{after.root_cause.name}</strong>.</>}
            </p>
          )}
          <Link className="button" to="/">Back to the task</Link>
        </section>
      )}
    </div>
  );
}
