# graph is stored as concepts (nodes) + concept_dependencies (edges: prerequisite -> concept)

from datetime import datetime, timezone

from sqlalchemy import JSON, Boolean, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Concept(Base):
    __tablename__ = "concepts"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str] = mapped_column(Text, default="")


class ConceptDependency(Base):
    # edge in the knowledge graph: `prerequisite_id` must be learned before `concept_id`

    __tablename__ = "concept_dependencies"

    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    prerequisite_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)


class Problem(Base):
    # coding task. code gets analysed, never executed

    __tablename__ = "problems"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    position: Mapped[int] = mapped_column(Integer, default=0)  # display order
    title: Mapped[str] = mapped_column(String(160))
    prompt: Mapped[str] = mapped_column(Text)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"))
    starter_code: Mapped[str] = mapped_column(Text, default="")
    expected_output: Mapped[str] = mapped_column(Text, default="")
    # hints for the analyser
    required_construct: Mapped[str | None] = mapped_column(String(16), nullable=True)  # "for" | "while" | "def"
    range_stop: Mapped[int | None] = mapped_column(Integer, nullable=True)
    single_output: Mapped[bool] = mapped_column(Boolean, default=False)


class Exercise(Base):
    # multiple choice micro exercise for one concept

    __tablename__ = "exercises"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), index=True)
    kind: Mapped[str] = mapped_column(String(32))  # "predict_output" | "spot_bug" | "concept_check"
    question: Mapped[str] = mapped_column(Text)
    code: Mapped[str] = mapped_column(Text, default="")
    options: Mapped[list[str]] = mapped_column(JSON)
    answer: Mapped[str] = mapped_column(String(200))
    explanation: Mapped[str] = mapped_column(Text)


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(120))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    mastery: Mapped[list["Mastery"]] = relationship(back_populates="student", cascade="all, delete-orphan")
    attempts: Mapped[list["Attempt"]] = relationship(back_populates="student", cascade="all, delete-orphan")


class Mastery(Base):
    # how well a student knows a concept: a score in [0, 1] plus how much evidence we have

    __tablename__ = "mastery"

    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), primary_key=True)
    concept_id: Mapped[str] = mapped_column(ForeignKey("concepts.id"), primary_key=True)
    score: Mapped[float] = mapped_column(Float)
    evidence_count: Mapped[int] = mapped_column(Integer, default=0)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    student: Mapped[Student] = relationship(back_populates="mastery")


class Attempt(Base):
    # one code submission and what the analyser found in it

    __tablename__ = "attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    problem_id: Mapped[str] = mapped_column(ForeignKey("problems.id"))
    code: Mapped[str] = mapped_column(Text)
    passed: Mapped[bool] = mapped_column(Boolean)
    findings: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    student: Mapped[Student] = relationship(back_populates="attempts")
