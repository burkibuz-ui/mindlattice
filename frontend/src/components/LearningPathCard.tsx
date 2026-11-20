import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../api";
import type { LearningPath, PathStep } from "../types";

interface Props {
  studentId: number;
  targetId: string;
}

const STATUS_TEXT: Record<PathStep["status"], string> = {
  weak: "Needs work",
  untested: "Not tested yet",
  practicing: "Almost there",
  mastered: "Mastered",
};

function describe(step: PathStep): string {
  const parts = [STATUS_TEXT[step.status]];
  if (step.score !== null) parts.push(`${Math.round(step.score * 100)}% mastery`);
  if (step.exercises_needed > 0) {
    parts.push(`about ${step.exercises_needed} correct exercise${step.exercises_needed === 1 ? "" : "s"} to master`);
  }
  return parts.join(" · ");
}

/** Ordered study plan from the root cause up to the target concept. */
export function LearningPathCard({ studentId, targetId }: Props) {
  const [path, setPath] = useState<LearningPath | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    api.learningPath(studentId, targetId)
      .then((p) => { if (!cancelled) setPath(p); })
      .catch((e: Error) => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [studentId, targetId]);

  if (error) return <section className="card"><p className="error">{error}</p></section>;
  if (!path) return null;

  return (
    <section className="card">
      <div className="card-header">
        <h2>Your learning path</h2>
        {path.total_exercises > 0 && (
          <span className="badge badge--low">≈ {path.total_exercises} exercises to {path.target.name}</span>
        )}
      </div>
      <p className="muted">Work through these in order. Each step builds on the one before it, so fixing the
        root cause first makes everything above it easier.</p>

      <ol className="path" aria-label="Learning path">
        {path.steps.map((step, index) => (
          <li key={step.concept_id} className={`path-step path-step--${step.status}`}>
            <div className="path-rail" aria-hidden="true">
              <span className="path-dot">{step.status === "mastered" ? "✓" : index + 1}</span>
              {index < path.steps.length - 1 && <span className="path-line" />}
            </div>
            <div className="path-body">
              <div className="path-info">
                <span className="path-title">
                  {step.name}
                  {step.is_root_cause && <span className="path-tag path-tag--root">Root cause</span>}
                  {step.is_target && <span className="path-tag path-tag--target">Goal</span>}
                </span>
                <span className="path-meta">{describe(step)}</span>
              </div>
              {step.status !== "mastered" && (
                <Link className={`button${index === 0 ? "" : " button--ghost"}`}
                  to={`/practice/${step.concept_id}?target=${path.target.id}`}>
                  {index === 0 ? "Start here" : "Practice"}
                </Link>
              )}
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
}
