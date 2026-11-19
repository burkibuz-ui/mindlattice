"""Request and response bodies (Pydantic)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ConceptOut(ORM):
    id: str
    name: str
    description: str
    prerequisites: list[str] = []


class GraphOut(BaseModel):
    nodes: list[ConceptOut]
    edges: list[dict[str, str]]  # {"from": prerequisite, "to": concept}


class ProblemOut(ORM):
    id: str
    title: str
    prompt: str
    concept_id: str
    starter_code: str
    expected_output: str


class StudentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class StudentOut(ORM):
    id: int
    name: str
    created_at: datetime


class MasteryOut(BaseModel):
    concept_id: str
    concept_name: str
    score: float | None
    evidence_count: int


class AttemptCreate(BaseModel):
    problem_id: str
    code: str = Field(max_length=20_000)


class FindingOut(BaseModel):
    rule: str
    concept_id: str
    line: int | None
    message: str
    hint: str


class ScoreChangeOut(BaseModel):
    concept_id: str
    old: float
    new: float


class ConceptNode(BaseModel):
    id: str
    name: str
    score: float | None
    evidence_count: int


class DiagnosisOut(BaseModel):
    target: ConceptNode
    root_cause: ConceptNode
    chain: list[ConceptNode]
    confidence: float
    confidence_label: str
    weak_concepts: list[ConceptNode]
    probe_concepts: list[ConceptNode]
    explanation: str
    evidence: FindingOut | None


class AttemptResultOut(BaseModel):
    attempt_id: int
    passed: bool
    findings: list[FindingOut]
    score_changes: list[ScoreChangeOut]
    diagnosis: DiagnosisOut


class ExerciseOut(ORM):
    """Sent to the student: no answer, no explanation."""

    id: int
    concept_id: str
    kind: str
    question: str
    code: str
    options: list[str]


class PracticeRequest(BaseModel):
    concept_id: str


class AnswerCreate(BaseModel):
    answer: str = Field(max_length=200)


class AnswerResultOut(BaseModel):
    correct: bool
    correct_answer: str
    explanation: str
    concept_id: str
    old_score: float
    new_score: float


class NamedRef(BaseModel):
    id: str
    name: str


class StudentRow(BaseModel):
    student_id: int
    name: str
    topic: NamedRef | None
    root_cause: NamedRef | None
    status: str  # on_track | practicing | needs_help | no_data


class RootCauseCount(BaseModel):
    id: str
    name: str
    count: int


class ClassOverviewOut(BaseModel):
    students: list[StudentRow]
    root_causes: list[RootCauseCount]
