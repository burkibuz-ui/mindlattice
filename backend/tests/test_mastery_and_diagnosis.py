from collections import Counter

import pytest

from app.services.diagnosis import ConceptState, diagnose
from app.services.graph import ConceptGraph
from app.services.mastery import update_score

# assignment -> update -> loop -> for ;  range -> for
GRAPH = ConceptGraph(
    ["assignment", "update", "loop", "range", "for"],
    [("update", "assignment"), ("loop", "update"), ("for", "loop"), ("for", "range")],
)


def test_update_moves_towards_outcome():
    assert update_score(0.5, 1.0, 0.3) == pytest.approx(0.65)
    assert update_score(0.5, 0.0, 0.5) == pytest.approx(0.25)
    assert update_score(0.8, 0.8, 0.3) == pytest.approx(0.8)


@pytest.mark.parametrize("outcome, rate", [(1.5, 0.3), (-0.1, 0.3), (1.0, 0.0), (1.0, 1.2)])
def test_update_rejects_invalid_input(outcome, rate):
    with pytest.raises(ValueError):
        update_score(0.5, outcome, rate)


def test_root_cause_is_the_most_fundamental_weak_concept():
    states = {
        "for": ConceptState(0.3, 3),
        "loop": ConceptState(0.35, 2),
        "update": ConceptState(0.2, 2),
        "assignment": ConceptState(0.9, 4),
        "range": ConceptState(0.8, 2),
    }
    result = diagnose(GRAPH, states, "for")
    assert result.root_cause_id == "update"
    assert result.chain == ["update", "loop", "for"]
    assert result.weak_concepts[0] == "update"  # deepest first


def test_no_weak_concepts_means_the_target_itself_and_probe_suggestions():
    result = diagnose(GRAPH, {}, "for")
    assert result.root_cause_id == "for"
    assert result.confidence < 0.45
    assert result.probe_concepts == ["loop", "range", "update"]  # closest first


def test_misconceptions_break_ties_between_independent_weak_concepts():
    states = {"update": ConceptState(0.3, 1), "range": ConceptState(0.3, 1)}
    result = diagnose(GRAPH, states, "for", Counter({"range": 2}))
    assert result.root_cause_id == "range"


def test_more_evidence_means_more_confidence():
    weak_once = diagnose(GRAPH, {"update": ConceptState(0.3, 1)}, "for")
    weak_often = diagnose(GRAPH, {"update": ConceptState(0.3, 4)}, "for")
    assert weak_often.confidence > weak_once.confidence
