"""LLM provider interface.

Everything "intelligent" goes through `LLMProvider`, so the rest of the app
does not care whether answers come from a real model or from rules.

`MockLLM` needs no API key: it uses the static analyser for code and picks
exercises from the curated bank. To add a real provider, implement the same
three methods and register it in `get_llm()`.
"""

from typing import Protocol

from .code_analysis import Finding, ProblemSpec, analyze


class ExerciseLike(Protocol):
    id: int
    concept_id: str


class LLMProvider(Protocol):
    name: str

    def analyze_code(self, code: str, spec: ProblemSpec) -> list[Finding]:
        """Find misconceptions in student code, each pinned on one concept."""

    def select_exercises(self, concept_id: str, bank: list[ExerciseLike], limit: int) -> list[ExerciseLike]:
        """Choose (or generate) micro exercises that target `concept_id`."""

    def explain_diagnosis(self, target_name: str, root_name: str, chain_names: list[str],
                          finding: Finding | None) -> str:
        """A short, student-facing explanation of the diagnosis."""


class MockLLM:
    name = "mock"

    def analyze_code(self, code: str, spec: ProblemSpec) -> list[Finding]:
        return analyze(code, spec)

    def select_exercises(self, concept_id: str, bank: list[ExerciseLike], limit: int) -> list[ExerciseLike]:
        matching = [exercise for exercise in bank if exercise.concept_id == concept_id]
        return sorted(matching, key=lambda exercise: exercise.id)[:limit]

    def explain_diagnosis(self, target_name: str, root_name: str, chain_names: list[str],
                          finding: Finding | None) -> str:
        if root_name == target_name:
            text = f"Your difficulty seems to be with {target_name} itself; its prerequisites look solid."
        else:
            text = (f"You are struggling with {target_name}, but the root cause looks like {root_name}. "
                    f"{target_name} builds on it through: {' -> '.join(chain_names)}.")
        if finding is not None:
            text += f" In your last attempt: {finding.message}"
        return text


def get_llm(provider: str = "mock") -> LLMProvider:
    if provider == "mock":
        return MockLLM()
    raise ValueError(f"Unknown LLM provider '{provider}'. Available: mock")
