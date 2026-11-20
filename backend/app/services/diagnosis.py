# root cause = the most basic weak concept whose own prerequisites are ok.
# ties: how weak + how often a misconception hit it + how deep it is.
# untested prerequisites come back as probe_concepts

from collections import Counter
from dataclasses import dataclass, field

from .graph import ConceptGraph
from .mastery import PRIOR, WEAK_THRESHOLD

MISCONCEPTION_WEIGHT = 0.15
DEPTH_WEIGHT = 0.02
MAX_PROBES = 3


@dataclass(frozen=True)
class ConceptState:
    score: float
    evidence_count: int


@dataclass
class Diagnosis:
    target_id: str
    root_cause_id: str
    chain: list[str]  # from the root cause up to the target
    confidence: float
    weak_concepts: list[str] = field(default_factory=list)
    probe_concepts: list[str] = field(default_factory=list)


def diagnose(graph: ConceptGraph, states: dict[str, ConceptState], target_id: str,
             misconceptions: Counter | None = None) -> Diagnosis:
    if target_id not in graph:
        raise KeyError(target_id)
    misconceptions = misconceptions or Counter()
    depth = {target_id: 0, **graph.ancestors(target_id)}

    def state(concept_id: str) -> ConceptState:
        return states.get(concept_id, ConceptState(PRIOR, 0))

    def is_weak(concept_id: str) -> bool:
        s = state(concept_id)
        return s.evidence_count > 0 and s.score < WEAK_THRESHOLD

    weak = [cid for cid in depth if is_weak(cid)]
    probes = sorted((cid for cid in depth if cid != target_id and state(cid).evidence_count == 0),
                    key=lambda cid: (depth[cid], cid))[:MAX_PROBES]

    if not weak:
        return Diagnosis(target_id, target_id, [target_id], confidence=0.2,
                         weak_concepts=[], probe_concepts=probes)

    def suspicion(concept_id: str) -> float:
        return ((WEAK_THRESHOLD - state(concept_id).score)
                + MISCONCEPTION_WEIGHT * misconceptions[concept_id]
                + DEPTH_WEIGHT * depth[concept_id])

    # Frontier: weak concepts none of whose own prerequisites are weak.
    frontier = [cid for cid in weak if not any(is_weak(a) for a in graph.ancestors(cid))]
    root = max(frontier or weak, key=lambda cid: (suspicion(cid), depth[cid], cid))

    root_state = state(root)
    confidence = min(1.0, 0.25 + 0.15 * root_state.evidence_count
                     + (WEAK_THRESHOLD - root_state.score)
                     + 0.1 * misconceptions[root])
    weak_sorted = sorted(weak, key=lambda cid: (-depth[cid], cid))
    return Diagnosis(target_id, root, graph.path(root, target_id), round(confidence, 2),
                     weak_concepts=weak_sorted, probe_concepts=probes)


def confidence_label(confidence: float) -> str:
    if confidence >= 0.7:
        return "high"
    if confidence >= 0.45:
        return "medium"
    return "low"
