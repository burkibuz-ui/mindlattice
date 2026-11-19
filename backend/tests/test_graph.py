import pytest

from app.seed import validate_content
from app.services.graph import ConceptGraph, CycleError

# a -> b -> d, a -> c -> d   (edges are (concept, prerequisite))
DIAMOND = ConceptGraph(["a", "b", "c", "d"], [("b", "a"), ("c", "a"), ("d", "b"), ("d", "c")])


def test_ancestors_with_depth():
    assert DIAMOND.ancestors("d") == {"b": 1, "c": 1, "a": 2}
    assert DIAMOND.ancestors("a") == {}


def test_path_goes_from_prerequisite_up_to_target():
    assert DIAMOND.path("a", "d") in (["a", "b", "d"], ["a", "c", "d"])
    assert DIAMOND.path("d", "a") == []
    assert DIAMOND.path("b", "b") == ["b"]


def test_topological_order_puts_prerequisites_first():
    order = DIAMOND.topological_order()
    assert order.index("a") < order.index("b") < order.index("d")


def test_cycle_is_detected():
    graph = ConceptGraph(["x", "y"], [("x", "y"), ("y", "x")])
    with pytest.raises(CycleError):
        graph.topological_order()


def test_unknown_concept_in_edge_is_rejected():
    with pytest.raises(KeyError):
        ConceptGraph(["x"], [("x", "missing")])


def test_seed_content_is_consistent():
    validate_content()  # acyclic, known concepts, every answer is one of the options
