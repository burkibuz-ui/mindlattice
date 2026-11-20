import type {
  AnswerResult, AttemptResult, ClassOverview, Diagnosis, Exercise, LearningPath, MasteryRow, Problem,
  Student,
} from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "";

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${BASE}${path}`, {
    ...init,
    headers: { "Content-Type": "application/json", ...init?.headers },
  });
  if (!response.ok) {
    let detail = response.statusText;
    try {
      const body = await response.json();
      detail = typeof body.detail === "string" ? body.detail : JSON.stringify(body.detail);
    } catch {
      // keep statusText
    }
    throw new ApiError(response.status, detail);
  }
  return response.json() as Promise<T>;
}

const post = <T>(path: string, body: unknown) =>
  request<T>(path, { method: "POST", body: JSON.stringify(body) });

export const api = {
  students: () => request<Student[]>("/api/students"),
  createStudent: (name: string) => post<Student>("/api/students", { name }),
  problems: () => request<Problem[]>("/api/problems"),
  mastery: (studentId: number) => request<MasteryRow[]>(`/api/students/${studentId}/mastery`),
  submitAttempt: (studentId: number, problemId: string, code: string) =>
    post<AttemptResult>(`/api/students/${studentId}/attempts`, { problem_id: problemId, code }),
  diagnosis: (studentId: number, conceptId: string) =>
    request<Diagnosis>(`/api/students/${studentId}/diagnosis/${conceptId}`),
  learningPath: (studentId: number, conceptId: string) =>
    request<LearningPath>(`/api/students/${studentId}/learning-path/${conceptId}`),
  practice: (studentId: number, conceptId: string) =>
    post<Exercise[]>(`/api/students/${studentId}/practice`, { concept_id: conceptId }),
  answer: (studentId: number, exerciseId: number, answer: string) =>
    post<AnswerResult>(`/api/students/${studentId}/exercises/${exerciseId}/answer`, { answer }),
  classOverview: () => request<ClassOverview>("/api/teacher/overview"),
};
