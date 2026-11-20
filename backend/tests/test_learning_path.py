import pytest

from app.services.diagnosis import ConceptState
from app.services.graph import ConceptGraph
from app.services.learning_path import MASTERED_THRESHOLD, build_learning_path, exercises_to_mastery
from app.services.mastery import RATE_EXERCISE, update_score

# assignment -> update -> loop -> for ;  range -> for
GRAPH = ConceptGraph(
    ["assignment", "update", "loop", "range", "for"],
    [("update", "assignment"), ("loop", "update"), ("for", "loop"), ("for", "range")],
)


@pytest.mark.parametrize("score", [0.0, 0.2, 0.45, 0.5, 0.69])
def test_exercise_estimate_matches_the_mastery_update(score):
    n = exercises_to_mastery(score)
    after_n = after_fewer = score
    for i in range(n):
        after_n = update_score(after_n, 1.0, RATE_EXERCISE)
        if i < n - 1:
            after_fewer = after_n
    assert after_n >= MASTERED_THRESHOLD - 1e-3
    assert n == 1 or after_fewer < MASTERED_THRESHOLD  # n is the smallest such number


def test_mastered_concept_needs_no_exercises():
    assert exercises_to_mastery(0.9) == 0


def test_path_puts_prerequisites_first_and_skips_mastered_concepts():
    states = {
        "assignment": ConceptState(0.9, 4),  # mastered: skipped
        "update": ConceptState(0.2, 2),  # root cause
        "loop": ConceptState(0.55, 1),  # practicing
        "for": ConceptState(0.3, 3),  # target
        # "range" untested, but it is not between the root cause and the target
    }
    steps = build_learning_path(GRAPH, states, "for", "update")
    assert [s.concept_id for s in steps] == ["update", "loop", "for"]
    assert [s.status for s in steps] == ["weak", "practicing", "weak"]
    assert steps[0].is_root_cause and steps[-1].is_target
    assert steps[0].exercises_needed > steps[1].exercises_needed


def test_untested_concepts_between_root_cause_and_target_are_included():
    states = {"update": ConceptState(0.2, 2), "for": ConceptState(0.3, 3)}
    steps = build_learning_path(GRAPH, states, "for", "update")
    assert [s.concept_id for s in steps] == ["update", "loop", "for"]
    assert steps[1].status == "untested" and steps[1].score is None


def test_mastered_target_is_reported_as_done():
    steps = build_learning_path(GRAPH, {"for": ConceptState(0.95, 5)}, "for", "for")
    assert [(s.concept_id, s.status, s.exercises_needed) for s in steps] == [("for", "mastered", 0)]


def test_learning_path_endpoint(client, student_id):
    wrong = "total = 0\nfor n in range(1, 6):\n    total = n\nprint(total)\n"
    client.post(f"/api/students/{student_id}/attempts", json={"problem_id": "sum-1-to-5", "code": wrong})
    body = client.get(f"/api/students/{student_id}/learning-path/for-loops").json()
    ids = [s["concept_id"] for s in body["steps"]]
    assert body["root_cause"]["id"] == "variable-update"
    assert ids[0] == "variable-update" and ids[-1] == "for-loops"
    assert ids.index("variable-update") < ids.index("loop-logic") < ids.index("for-loops")
    assert body["total_exercises"] == sum(s["exercises_needed"] for s in body["steps"])


def test_learning_path_unknown_concept_is_404(client, student_id):
    assert client.get(f"/api/students/{student_id}/learning-path/nope").status_code == 404
