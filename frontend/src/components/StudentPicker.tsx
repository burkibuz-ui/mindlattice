import { useState, type FormEvent } from "react";
import { useStudent } from "../student";

export function StudentPicker() {
  const { students, current, select, create, error } = useStudent();
  const [name, setName] = useState("");
  const [busy, setBusy] = useState(false);

  async function onCreate(event: FormEvent) {
    event.preventDefault();
    if (!name.trim()) return;
    setBusy(true);
    try {
      await create(name.trim());
      setName("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="picker">
      <label className="picker-label" htmlFor="student-select">Student</label>
      <select id="student-select" value={current?.id ?? ""} onChange={(e) => select(Number(e.target.value))}>
        {students.length === 0 && <option value="">No students yet</option>}
        {students.map((s) => (
          <option key={s.id} value={s.id}>{s.name}</option>
        ))}
      </select>
      <form onSubmit={onCreate} className="picker-form">
        <label className="visually-hidden" htmlFor="new-student">New student name</label>
        <input id="new-student" placeholder="New student" value={name} onChange={(e) => setName(e.target.value)} />
        <button type="submit" disabled={busy || !name.trim()}>Add</button>
      </form>
      {error && <p className="picker-error">API not reachable: {error}</p>}
    </div>
  );
}
