import { Link } from "react-router-dom";
import type { Diagnosis } from "../types";
import { ChainView } from "./ChainView";

export function DiagnosisCard({ diagnosis }: { diagnosis: Diagnosis }) {
  const { target, root_cause: root } = diagnosis;
  const differentRoot = root.id !== target.id;

  return (
    <section className="card">
      <div className="card-header">
        <h2>Diagnosis</h2>
        <span className={`badge badge--${diagnosis.confidence_label}`}>
          Confidence: {diagnosis.confidence_label}
        </span>
      </div>

      <p className="headline">
        {differentRoot ? (
          <>The real problem isn't {target.name.toLowerCase()}, it's <em>{root.name.toLowerCase()}</em>.</>
        ) : (
          <>Focus on <em>{target.name.toLowerCase()}</em> itself.</>
        )}
      </p>
      <p className="muted">{diagnosis.explanation}</p>

      <ChainView chain={diagnosis.chain} rootId={root.id} targetId={target.id} />

      {diagnosis.probe_concepts.length > 0 && (
        <p className="muted small">
          Not tested yet: {diagnosis.probe_concepts.map((c) => c.name).join(", ")}. A few quick questions on
          these would make the diagnosis sharper.
        </p>
      )}

      <div className="cta">
        <p>Micro exercises for <strong>{root.name}</strong> are ready.</p>
        <Link className="button" to={`/practice/${root.id}?target=${target.id}`}>Start practice</Link>
      </div>
    </section>
  );
}
