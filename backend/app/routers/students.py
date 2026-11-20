"""Student-facing endpoints: attempts, diagnosis and micro exercises."""

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import Problem, Student
from ..schemas import (
    AnswerCreate, AnswerResultOut, AttemptCreate, AttemptResultOut, DiagnosisOut, ExerciseOut,
    LearningPathOut, MasteryOut, PracticeRequest, ScoreChangeOut, StudentCreate, StudentOut,
)
from ..services import mastery, tutor
from ..services.llm import LLMProvider

router = APIRouter(prefix="/api/students", tags=["students"])


def get_llm(request: Request) -> LLMProvider:
    return request.app.state.llm


@router.post("", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(body: StudentCreate, db: Session = Depends(get_db)):
    student = Student(name=body.name.strip())
    db.add(student)
    db.commit()
    return student


@router.get("", response_model=list[StudentOut])
def list_students(db: Session = Depends(get_db)):
    return db.scalars(select(Student).order_by(Student.id)).all()


@router.get("/{student_id}", response_model=StudentOut)
def get_student(student_id: int, db: Session = Depends(get_db)):
    return tutor.get_student(db, student_id)


@router.get("/{student_id}/mastery", response_model=list[MasteryOut])
def get_mastery(student_id: int, db: Session = Depends(get_db)):
    tutor.get_student(db, student_id)
    scores = mastery.get_scores(db, student_id)
    names = tutor.concept_names(db)
    return [MasteryOut(concept_id=cid, concept_name=names[cid],
                       score=scores[cid].score if cid in scores else None,
                       evidence_count=scores[cid].evidence_count if cid in scores else 0)
            for cid in tutor.load_graph(db).topological_order()]


@router.post("/{student_id}/attempts", response_model=AttemptResultOut, status_code=status.HTTP_201_CREATED)
def submit_attempt(student_id: int, body: AttemptCreate, db: Session = Depends(get_db),
                   llm: LLMProvider = Depends(get_llm)):
    result = tutor.submit_attempt(db, llm, student_id, body.problem_id, body.code)
    problem_concept = db.get(Problem, body.problem_id).concept_id
    return AttemptResultOut(
        attempt_id=result.attempt.id,
        passed=result.attempt.passed,
        findings=[f.to_dict() for f in result.findings],
        score_changes=[ScoreChangeOut(concept_id=c.concept_id, old=c.old, new=c.new) for c in result.changes],
        diagnosis=tutor.diagnosis_report(db, llm, student_id, problem_concept),
    )


@router.get("/{student_id}/diagnosis/{concept_id}", response_model=DiagnosisOut)
def get_diagnosis(student_id: int, concept_id: str, db: Session = Depends(get_db),
                  llm: LLMProvider = Depends(get_llm)):
    return tutor.diagnosis_report(db, llm, student_id, concept_id)


@router.get("/{student_id}/learning-path/{concept_id}", response_model=LearningPathOut)
def get_learning_path(student_id: int, concept_id: str, db: Session = Depends(get_db)):
    """Concepts to study before `concept_id`, prerequisites first, with an effort estimate."""
    return tutor.learning_path_report(db, student_id, concept_id)


@router.post("/{student_id}/practice", response_model=list[ExerciseOut])
def practice(student_id: int, body: PracticeRequest, db: Session = Depends(get_db),
             llm: LLMProvider = Depends(get_llm)):
    return tutor.practice_set(db, llm, student_id, body.concept_id)


@router.post("/{student_id}/exercises/{exercise_id}/answer", response_model=AnswerResultOut)
def answer(student_id: int, exercise_id: int, body: AnswerCreate, db: Session = Depends(get_db)):
    return tutor.answer_exercise(db, student_id, exercise_id, body.answer)
