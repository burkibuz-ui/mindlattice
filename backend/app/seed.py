from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Concept, ConceptDependency, Exercise, Problem, Student
from .seed_data import CONCEPTS, DEMO_SUBMISSIONS, EXERCISES, PROBLEMS
from .services import tutor
from .services.graph import ConceptGraph
from .services.llm import LLMProvider

# Extra practice the demo students did, so the dashboard shows different statuses.
DEMO_PRACTICE = {
    "Student D": [("range-function", "[1, 2, 3, 4]"), ("range-function", "4")],
    "Student G": [("indentation-blocks", "1")],
}


def validate_content() -> None:
    graph = ConceptGraph([c["id"] for c in CONCEPTS],
                         [(c["id"], p) for c in CONCEPTS for p in c["prerequisites"]])
    graph.topological_order()  # raises CycleError
    for item in PROBLEMS + EXERCISES:
        if item["concept_id"] not in graph:
            raise ValueError(f"Unknown concept '{item['concept_id']}'")
    for exercise in EXERCISES:
        if exercise["answer"] not in exercise["options"]:
            raise ValueError(f"Answer not among options: {exercise['question']} / {exercise['code']!r}")


def seed_content(db: Session) -> bool:
    # insert concepts, edges, problems and exercises. Returns False if already seeded
    if db.scalars(select(Concept.id).limit(1)).first() is not None:
        return False
    validate_content()
    for c in CONCEPTS:
        db.add(Concept(id=c["id"], name=c["name"], description=c["description"]))
    db.flush()
    for c in CONCEPTS:
        for prereq in c["prerequisites"]:
            db.add(ConceptDependency(concept_id=c["id"], prerequisite_id=prereq))
    for position, p in enumerate(PROBLEMS):
        db.add(Problem(position=position, **p))
    for e in EXERCISES:
        db.add(Exercise(**e))
    db.commit()
    return True


def seed_demo_class(db: Session, llm: LLMProvider) -> None:
    if db.scalars(select(Student.id).limit(1)).first() is not None:
        return
    students: dict[str, Student] = {}
    for name, problem_id, code in DEMO_SUBMISSIONS:
        if name not in students:
            students[name] = Student(name=name)
            db.add(students[name])
            db.commit()
        tutor.submit_attempt(db, llm, students[name].id, problem_id, code)

    for name, answers in DEMO_PRACTICE.items():
        for concept_id, answer in answers:
            exercise = next(e for e in db.scalars(select(Exercise).where(Exercise.concept_id == concept_id))
                            if e.answer == answer)
            tutor.answer_exercise(db, students[name].id, exercise.id, answer)
