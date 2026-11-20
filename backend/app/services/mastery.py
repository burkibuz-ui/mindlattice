# mastery score per concept, 0..1
# update: new = old + rate * (outcome - old)
# rate = how much we trust the evidence (misconception > plain wrong answer)

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Mastery

PRIOR = 0.5  # what we assume before seeing any evidence
WEAK_THRESHOLD = 0.45  # below this (with evidence) a concept counts as "not mastered"

RATE_PASS = 0.3  # solved a problem for this concept
RATE_PASS_PREREQ = 0.1  # solving it is mild evidence for its direct prerequisites
RATE_FAIL_EXPLAINED = 0.15  # failed, but a misconception elsewhere explains it
RATE_FAIL = 0.3  # failed, no explanation found
RATE_MISCONCEPTION = 0.5  # the analyser pinned an error on this concept
RATE_EXERCISE = 0.35  # answered a micro exercise


@dataclass
class ScoreChange:
    concept_id: str
    old: float
    new: float


def update_score(old: float, outcome: float, rate: float) -> float:
    if not 0.0 <= outcome <= 1.0:
        raise ValueError("outcome must be between 0 and 1")
    if not 0.0 < rate <= 1.0:
        raise ValueError("rate must be in (0, 1]")
    return round(old + rate * (outcome - old), 4)


def get_scores(db: Session, student_id: int) -> dict[str, Mastery]:
    rows = db.scalars(select(Mastery).where(Mastery.student_id == student_id))
    return {row.concept_id: row for row in rows}


def apply_evidence(db: Session, student_id: int, concept_id: str, outcome: float, rate: float) -> ScoreChange:
    # update (or create) a mastery row. The caller commits
    row = db.get(Mastery, (student_id, concept_id))
    if row is None:
        row = Mastery(student_id=student_id, concept_id=concept_id, score=PRIOR, evidence_count=0)
        db.add(row)
    old = row.score
    row.score = update_score(old, outcome, rate)
    row.evidence_count += 1
    return ScoreChange(concept_id=concept_id, old=old, new=row.score)
