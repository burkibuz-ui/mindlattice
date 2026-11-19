import { useCallback, useEffect, useState } from "react";
import { api } from "../api";
import type { ClassOverview, StudentStatus } from "../types";

const STATUS_LABEL: Record<StudentStatus, string> = {
  needs_help: "Needs help",
  practicing: "Practising",
  on_track: "On track",
  no_data: "No data",
};

export function TeacherPage() {
  const [overview, setOverview] = useState<ClassOverview | null>(null);
  const [filter, setFilter] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(() => {
    api.classOverview().then(setOverview).catch((e: Error) => setError(e.message));
  }, []);
  useEffect(load, [load]);

  const max = Math.max(1, ...(overview?.root_causes.map((c) => c.count) ?? [1]));
  const rows = overview?.students.filter((s) => !filter || s.root_cause?.id === filter) ?? [];

  return (
    <div className="page">
      <header className="page-header page-header--row">
        <div>
          <p className="eyebrow">Teacher dashboard</p>
          <h1>Why is the class stuck?</h1>
        </div>
        <button className="button button--ghost" onClick={load}>Refresh</button>
      </header>
      {error && <p className="error">{error}</p>}

      <section className="card">
        <div className="card-header">
          <h2>Most common root causes</h2>
          <span className="muted small">Click one to filter</span>
        </div>
        {overview?.root_causes.length === 0 && <p className="muted">Nobody is stuck right now.</p>}
        <div className="causes">
          {overview?.root_causes.map((cause) => (
            <button key={cause.id} className={`cause ${filter === cause.id ? "cause--active" : ""}`}
              aria-pressed={filter === cause.id}
              onClick={() => setFilter(filter === cause.id ? null : cause.id)}>
              <span className="cause-name">{cause.name}</span>
              <span className="cause-track"><span className="cause-fill" style={{ width: `${(cause.count / max) * 100}%` }} /></span>
              <span className="cause-count">{cause.count} {cause.count === 1 ? "student" : "students"}</span>
            </button>
          ))}
        </div>
      </section>

      <section className="card">
        <div className="card-header">
          <h2>Students</h2>
          <span className="muted small">{filter ? "Filtered" : "All students"}</span>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr><th>Student</th><th>Stuck on</th><th>Root cause</th><th>Status</th></tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.student_id}>
                  <td className="strong">{row.name}</td>
                  <td>{row.topic?.name ?? "—"}</td>
                  <td className="root">{row.root_cause?.name ?? "—"}</td>
                  <td><span className={`pill pill--${row.status}`}>{STATUS_LABEL[row.status]}</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
    </div>
  );
}
