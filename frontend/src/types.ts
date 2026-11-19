// Mirrors the backend's Pydantic schemas (backend/app/schemas.py).

export interface Student {
  id: number;
  name: string;
  created_at: string;
}

export interface Problem {
  id: string;
  title: string;
  prompt: string;
  concept_id: string;
  starter_code: string;
  expected_output: string;
}

export interface ConceptNode {
  id: string;
  name: string;
  score: number | null;
  evidence_count: number;
}

export interface Finding {
  rule: string;
  concept_id: string;
  line: number | null;
  message: string;
  hint: string;
}

export interface Diagnosis {
  target: ConceptNode;
  root_cause: ConceptNode;
  chain: ConceptNode[];
  confidence: number;
  confidence_label: "low" | "medium" | "high";
  weak_concepts: ConceptNode[];
  probe_concepts: ConceptNode[];
  explanation: string;
  evidence: Finding | null;
}

export interface ScoreChange {
  concept_id: string;
  old: number;
  new: number;
}

export interface AttemptResult {
  attempt_id: number;
  passed: boolean;
  findings: Finding[];
  score_changes: ScoreChange[];
  diagnosis: Diagnosis;
}

export interface Exercise {
  id: number;
  concept_id: string;
  kind: "predict_output" | "spot_bug" | "concept_check";
  question: string;
  code: string;
  options: string[];
}

export interface AnswerResult {
  correct: boolean;
  correct_answer: string;
  explanation: string;
  concept_id: string;
  old_score: number;
  new_score: number;
}

export interface MasteryRow {
  concept_id: string;
  concept_name: string;
  score: number | null;
  evidence_count: number;
}

export type StudentStatus = "on_track" | "practicing" | "needs_help" | "no_data";

export interface StudentRow {
  student_id: number;
  name: string;
  topic: { id: string; name: string } | null;
  root_cause: { id: string; name: string } | null;
  status: StudentStatus;
}

export interface ClassOverview {
  students: StudentRow[];
  root_causes: { id: string; name: string; count: number }[];
}
