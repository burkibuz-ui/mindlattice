import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from "react";
import { api } from "./api";
import type { Student } from "./types";

const STORAGE_KEY = "mindlattice.studentId";

interface StudentContextValue {
  students: Student[];
  current: Student | null;
  select: (id: number) => void;
  create: (name: string) => Promise<void>;
  error: string | null;
}

const StudentContext = createContext<StudentContextValue | null>(null);

function readStoredId(): number | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return raw ? Number(raw) : null;
  } catch {
    return null;
  }
}

function storeId(id: number) {
  try {
    localStorage.setItem(STORAGE_KEY, String(id));
  } catch {
    // storage unavailable: selection just won't persist
  }
}

export function StudentProvider({ children }: { children: ReactNode }) {
  const [students, setStudents] = useState<Student[]>([]);
  const [currentId, setCurrentId] = useState<number | null>(readStoredId);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api.students()
      .then((list) => {
        setStudents(list);
        setCurrentId((id) => (id !== null && list.some((s) => s.id === id) ? id : list[0]?.id ?? null));
      })
      .catch((e: Error) => setError(e.message));
  }, []);

  const select = useCallback((id: number) => {
    setCurrentId(id);
    storeId(id);
  }, []);

  const create = useCallback(async (name: string) => {
    const student = await api.createStudent(name);
    setStudents((list) => [...list, student]);
    select(student.id);
  }, [select]);

  const current = students.find((s) => s.id === currentId) ?? null;
  return (
    <StudentContext.Provider value={{ students, current, select, create, error }}>
      {children}
    </StudentContext.Provider>
  );
}

export function useStudent(): StudentContextValue {
  const value = useContext(StudentContext);
  if (!value) throw new Error("useStudent must be used inside <StudentProvider>");
  return value;
}
