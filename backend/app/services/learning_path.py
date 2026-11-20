# Learning path = what to study next, in order, and roughly how many exercises each step takes.

import math
from dataclasses import dataclass

from .diagnosis import ConceptState
from .graph import ConceptGraph
from .mastery import PRIOR, RATE_EXERCISE, WEAK_THRESHOLD

MASTERED_THRESHOLD = 0.7


@dataclass(frozen=True)
class PathStep:
    concept_id: str
    status: str  # weak / untested / practicing / mastered
    score: float | None
    exercises_needed: int
    is_root_cause: bool
    is_target: bool


def exercises_to_mastery(score, rate=RATE_EXERCISE, threshold=MASTERED_THRESHOLD):
    # after n correct answers: score_n = 1 - (1 - score) * (1 - rate)^n
    # solve score_n >= threshold for n
    if not 0 < rate < 1:
        raise ValueError("rate must be between 0 and 1")
    if score >= threshold:
        return 0
    n = math.log((1 - threshold) / (1 - score)) / math.log(1 - rate)
    return max(1, math.ceil(n - 1e-9))  # 1e-9: float error can push 3.0 to 3.0000001


def step_status(state):
    if state is None or state.evidence_count == 0:
        return "untested"
    if state.score < WEAK_THRESHOLD:
        return "weak"
    if state.score < MASTERED_THRESHOLD:
        return "practicing"
    return None  # mastered


def build_learning_path(graph: ConceptGraph, states: dict[str, ConceptState],
                        target_id: str, root_cause_id: str) -> list[PathStep]:
    if target_id not in graph:
        raise KeyError(target_id)

    needed = {target_id, *graph.ancestors(target_id)}
    # only keep untested concepts that sit between root cause and target,
    # otherwise the path gets long with stuff that is probably fine
    between = {root_cause_id}
    for c in needed:
        if root_cause_id in graph.ancestors(c):
            between.add(c)

    steps = []
    for cid in graph.topological_order():
        if cid not in needed:
            continue
        state = states.get(cid)
        status = step_status(state)
        is_target = cid == target_id

        if status is None and not is_target:
            continue
        if status == "untested" and cid not in between and not is_target:
            continue

        score = state.score if state and state.evidence_count else None
        steps.append(PathStep(
            concept_id=cid,
            status=status or "mastered",
            score=score,
            exercises_needed=exercises_to_mastery(PRIOR if score is None else score),
            is_root_cause=cid == root_cause_id,
            is_target=is_target,
        ))
    return steps
