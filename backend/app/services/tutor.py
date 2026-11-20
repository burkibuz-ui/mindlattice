"""Use cases that tie the graph, the student model, the diagnosis and the LLM together.

Routers stay thin and call these functions; tests can call them directly.
"""

from collections import Counter
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Attempt, Concept, ConceptDependency, Exercise, Problem, Student
from . import mastery as m
from .code_analysis import Finding, ProblemSpec
from .diagnosis import ConceptState, Diagnosis, confidence_label, diagnose
from .graph import ConceptGraph
from .learning_path import build_learning_path
from .llm import LLMProvider

RECENT_ATTEMPTS = 10
EXERCISES_PER_SESSION = 3


class NotFound(LookupError):
    pass


def load_graph(db: Session) -> ConceptGraph:
    concept_ids = db.scalars(select(Concept.id).order_by(Concept.id)).all()
    edges = db.execute(select(ConceptDependency.concept_id, ConceptDependency.prerequisite_id)).all()
    return ConceptGraph(concept_ids, [(c, p) for c, p in edges])


def concept_names(db: Session) -> dict[str, str]:
    return {c.id: c.name for c in db.scalars(select(Concept))}


def get_student(db: Session, student_id: int) -> Student:
    student = db.get(Student, student_id)
    if student is None:
        raise NotFound(f"Student {student_id} not found")
    return student


def spec_for(problem: Problem) -> ProblemSpec:
    return ProblemSpec(concept_id=problem.concept_id, required_construct=problem.required_construct,
                       range_stop=problem.range_stop, single_output=problem.single_output)


# --- code attempts -----------------------------------------------------------


@dataclass
class AttemptResult:
    attempt: Attempt
    findings: list[Finding]
    changes: list[m.ScoreChange]


def submit_attempt(db: Session, llm: LLMProvider, student_id: int, problem_id: str, code: str) -> AttemptResult:
    get_student(db, student_id)
    problem = db.get(Problem, problem_id)
    if problem is None:
        raise NotFound(f"Problem '{problem_id}' not found")

    findings = llm.analyze_code(code, spec_for(problem))
    passed = not findings
    target = problem.concept_id
    changes: list[m.ScoreChange] = []

    if passed:
        changes.append(m.apply_evidence(db, student_id, target, 1.0, m.RATE_PASS))
        for prereq in load_graph(db).prerequisites(target):
            changes.append(m.apply_evidence(db, student_id, prereq, 1.0, m.RATE_PASS_PREREQ))
    else:
        blamed = list(dict.fromkeys(f.concept_id for f in findings))  # unique, in order
        for concept_id in blamed:
            changes.append(m.apply_evidence(db, student_id, concept_id, 0.0, m.RATE_MISCONCEPTION))
        if target not in blamed:
            changes.append(m.apply_evidence(db, student_id, target, 0.0, m.RATE_FAIL_EXPLAINED))

    attempt = Attempt(student_id=student_id, problem_id=problem_id, code=code, passed=passed,
                      findings=[f.to_dict() for f in findings])
    db.add(attempt)
    db.commit()
    return AttemptResult(attempt, findings, changes)


# --- diagnosis ---------------------------------------------------------------


def _states(db: Session, student_id: int) -> dict[str, ConceptState]:
    return {cid: ConceptState(row.score, row.evidence_count)
            for cid, row in m.get_scores(db, student_id).items()}


def _recent_attempts(db: Session, student_id: int) -> list[Attempt]:
    return list(db.scalars(select(Attempt).where(Attempt.student_id == student_id)
                           .order_by(Attempt.id.desc()).limit(RECENT_ATTEMPTS)))


def run_diagnosis(db: Session, student_id: int, target_id: str) -> tuple[Diagnosis, list[Attempt]]:
    get_student(db, student_id)
    graph = load_graph(db)
    if target_id not in graph:
        raise NotFound(f"Concept '{target_id}' not found")
    attempts = _recent_attempts(db, student_id)
    misconceptions = Counter(f["concept_id"] for a in attempts for f in a.findings)
    return diagnose(graph, _states(db, student_id), target_id, misconceptions), attempts


def diagnosis_report(db: Session, llm: LLMProvider, student_id: int, target_id: str) -> dict:
    result, attempts = run_diagnosis(db, student_id, target_id)
    names = concept_names(db)
    states = _states(db, student_id)

    evidence = None
    for attempt in attempts:  # newest first
        for f in attempt.findings:
            if f["concept_id"] in result.chain:
                evidence = Finding(**f)
                break
        if evidence:
            break

    def node(cid: str) -> dict:
        s = states.get(cid)
        return {"id": cid, "name": names[cid], "score": s.score if s else None,
                "evidence_count": s.evidence_count if s else 0}

    return {
        "target": node(result.target_id),
        "root_cause": node(result.root_cause_id),
        "chain": [node(cid) for cid in result.chain],
        "confidence": result.confidence,
        "confidence_label": confidence_label(result.confidence),
        "weak_concepts": [node(cid) for cid in result.weak_concepts],
        "probe_concepts": [node(cid) for cid in result.probe_concepts],
        "explanation": llm.explain_diagnosis(names[result.target_id], names[result.root_cause_id],
                                             [names[c] for c in result.chain], evidence),
        "evidence": evidence.to_dict() if evidence else None,
    }


def learning_path_report(db: Session, student_id: int, target_id: str) -> dict:
    result, _ = run_diagnosis(db, student_id, target_id)
    names = concept_names(db)
    steps = build_learning_path(load_graph(db), _states(db, student_id), target_id, result.root_cause_id)
    return {
        "target": {"id": target_id, "name": names[target_id]},
        "root_cause": {"id": result.root_cause_id, "name": names[result.root_cause_id]},
        "total_exercises": sum(step.exercises_needed for step in steps),
        "steps": [{"concept_id": step.concept_id, "name": names[step.concept_id], "status": step.status,
                   "score": step.score, "exercises_needed": step.exercises_needed,
                   "is_root_cause": step.is_root_cause, "is_target": step.is_target} for step in steps],
    }


# --- micro exercises ---------------------------------------------------------


def practice_set(db: Session, llm: LLMProvider, student_id: int, concept_id: str) -> list[Exercise]:
    get_student(db, student_id)
    if db.get(Concept, concept_id) is None:
        raise NotFound(f"Concept '{concept_id}' not found")
    bank = list(db.scalars(select(Exercise).where(Exercise.concept_id == concept_id)))
    return llm.select_exercises(concept_id, bank, EXERCISES_PER_SESSION)


def answer_exercise(db: Session, student_id: int, exercise_id: int, answer: str) -> dict:
    get_student(db, student_id)
    exercise = db.get(Exercise, exercise_id)
    if exercise is None:
        raise NotFound(f"Exercise {exercise_id} not found")
    correct = answer.strip() == exercise.answer.strip()
    change = m.apply_evidence(db, student_id, exercise.concept_id, 1.0 if correct else 0.0, m.RATE_EXERCISE)
    db.commit()
    return {"correct": correct, "correct_answer": exercise.answer, "explanation": exercise.explanation,
            "concept_id": exercise.concept_id, "old_score": change.old, "new_score": change.new}


# --- teacher view ------------------------------------------------------------


def student_status(diagnosis: Diagnosis, root_score: float | None) -> str:
    if not diagnosis.weak_concepts:
        return "on_track"
    if root_score is not None and root_score < 0.35:
        return "needs_help"
    return "practicing"


def class_overview(db: Session) -> dict:
    names = concept_names(db)
    rows = []
    causes: Counter = Counter()
    for student in db.scalars(select(Student).order_by(Student.id)):
        latest = db.scalars(select(Attempt).where(Attempt.student_id == student.id)
                            .order_by(Attempt.id.desc()).limit(1)).first()
        if latest is None:
            rows.append({"student_id": student.id, "name": student.name, "topic": None,
                         "root_cause": None, "status": "no_data"})
            continue
        problem = db.get(Problem, latest.problem_id)
        result, _ = run_diagnosis(db, student.id, problem.concept_id)
        root_row = m.get_scores(db, student.id).get(result.root_cause_id)
        status = student_status(result, root_row.score if root_row else None)
        if status != "on_track":
            causes[result.root_cause_id] += 1
        rows.append({
            "student_id": student.id, "name": student.name,
            "topic": {"id": problem.concept_id, "name": names[problem.concept_id]},
            "root_cause": ({"id": result.root_cause_id, "name": names[result.root_cause_id]}
                           if status != "on_track" else None),
            "status": status,
        })
    return {
        "students": rows,
        "root_causes": [{"id": cid, "name": names[cid], "count": n} for cid, n in causes.most_common()],
    }
