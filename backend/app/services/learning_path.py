"""Personalised learning path: what to study, in which order, and roughly how much.

The diagnosis answers "what is the root cause?". The learning path answers
"what do I do next?": every concept the target depends on that is not yet
solid, ordered so that each prerequisite comes before what builds on it.

For each step we also estimate how many correct micro exercises it takes to
reach mastery. Because mastery is an exponential moving average, after `n`
correct answers with rate `r` the score is

    1 - (1 - s) * (1 - r) ** n

so the smallest `n` that reaches the threshold `M` is

    n = ceil( log((1 - M) / (1 - s)) / log(1 - r) )
"""

import math
from dataclasses import dataclass

from .diagnosis import ConceptState
from .graph import ConceptGraph
from .mastery import PRIOR, RATE_EXERCISE, WEAK_THRESHOLD

MASTERED_THRESHOLD = 0.7  # at or above this (with evidence) a concept needs no more work


@dataclass(frozen=True)
class PathStep:
    concept_id: str
    status: str  # "weak" | "untested" | "practicing" | "mastered" (target only)
    score: float | None
    exercises_needed: int
    is_root_cause: bool
    is_target: bool


def exercises_to_mastery(score: float, rate: float = RATE_EXERCISE,
                         threshold: float = MASTERED_THRESHOLD) -> int:
    """Correct answers needed to lift `score` to `threshold` under the EMA update."""
    if not 0.0 < rate < 1.0:
        raise ValueError("rate must be in (0, 1)")
    if score >= threshold:
        return 0
    n = math.log((1 - threshold) / (1 - score)) / math.log(1 - rate)
    return max(1, math.ceil(n - 1e-9))


def step_status(state: ConceptState | None) -> str | None:
    """Classify a concept, or return None when it is already mastered."""
    if state is None or state.evidence_count == 0:
        return "untested"
    if state.score < WEAK_THRESHOLD:
        return "weak"
    if state.score < MASTERED_THRESHOLD:
        return "practicing"
    return None


def build_learning_path(graph: ConceptGraph, states: dict[str, ConceptState],
                        target_id: str, root_cause_id: str) -> list[PathStep]:
    if target_id not in graph:
        raise KeyError(target_id)
    needed = {target_id, *graph.ancestors(target_id)}
    # Untested prerequisites far below the root cause are not worth a detour:
    # keep untested concepts only if they sit between the root cause and the target.
    between = {root_cause_id} | {c for c in needed if root_cause_id in graph.ancestors(c)}

    steps: list[PathStep] = []
    for concept_id in graph.topological_order():  # prerequisites first
        if concept_id not in needed:
            continue
        state = states.get(concept_id)
        status = step_status(state)
        if status is None and concept_id != target_id:
            continue
        if status == "untested" and concept_id not in between and concept_id != target_id:
            continue
        score = state.score if state and state.evidence_count else None
        steps.append(PathStep(
            concept_id=concept_id,
            status=status or "mastered",
            score=score,
            exercises_needed=exercises_to_mastery(score if score is not None else PRIOR),
            is_root_cause=concept_id == root_cause_id,
            is_target=concept_id == target_id,
        ))
    return steps
