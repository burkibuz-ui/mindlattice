import { useEffect, useState } from "react";
import { api } from "../api";
import { DiagnosisCard } from "../components/DiagnosisCard";
import { useStudent } from "../student";
import type { AttemptResult, Problem } from "../types";

export function DiagnosisPage() {
  const { current } = useStudent();
  const [problems, setProblems] = useState<Problem[]>([]);
  const [problemId, setProblemId] = useState<string>("");
  const [code, setCode] = useState("");
  const [result, setResult] = useState<AttemptResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.problems()
      .then((list) => {
        setProblems(list);
        if (list[0]) choose(list[0]);
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  function choose(problem: Problem) {
    setProblemId(problem.id);
    setCode(problem.starter_code);
    setResult(null);
  }

  async function submit() {
    if (!current) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await api.submitAttempt(current.id, problemId, code));
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }

  const problem = problems.find((p) => p.id === problemId);

  return (
    <div className="page">
      <header className="page-header">
        <p className="eyebrow">Python basics</p>
        <h1>Why are you stuck?</h1>
        <p className="muted">Solve a task. MindLattice reads your code (it never runs it), finds the misconception
          and traces it back through the knowledge graph.</p>
      </header>

      <div className="grid-2">
        <section className="card">
          <div className="field">
            <label htmlFor="problem">Task</label>
            <select id="problem" value={problemId}
              onChange={(e) => { const p = problems.find((x) => x.id === e.target.value); if (p) choose(p); }}>
              {problems.map((p) => <option key={p.id} value={p.id}>{p.title}</option>)}
            </select>
          </div>
          {problem && (
            <>
              <p>{problem.prompt}</p>
              <p className="muted small">Expected: <code>{problem.expected_output}</code></p>
            </>
          )}
          <label className="visually-hidden" htmlFor="code">Your code</label>
          <textarea id="code" className="code-input" spellCheck={false} value={code} rows={10}
            onChange={(e) => setCode(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Tab") {
                e.preventDefault();
                const el = e.currentTarget;
                const { selectionStart: start, selectionEnd: end } = el;
                setCode(code.slice(0, start) + "    " + code.slice(end));
                requestAnimationFrame(() => el.setSelectionRange(start + 4, start + 4));
              }
            }} />
          <button className="button" onClick={submit} disabled={busy || !current || !code.trim()}>
            {busy ? "Analysing…" : "Check my code"}
          </button>
          {!current && <p className="muted small">Pick or add a student in the menu first.</p>}
          {error && <p className="error">{error}</p>}
        </section>

        <section className="card">
          <h2>Feedback</h2>
          {!result && <p className="muted">Submit your code to see feedback.</p>}
          {result?.passed && <p className="success">No misconceptions found. Nice work!</p>}
          {result && !result.passed && (
            <ul className="findings">
              {result.findings.map((f, i) => (
                <li key={i}>
                  {f.line !== null && <span className="line">Line {f.line}</span>}
                  <p>{f.message}</p>
                  <p className="muted small">Hint: {f.hint}</p>
                </li>
              ))}
            </ul>
          )}
        </section>
      </div>

      {result && !result.passed && <DiagnosisCard diagnosis={result.diagnosis} />}
    </div>
  );
}
