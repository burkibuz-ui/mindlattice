WRONG_SUM = "total = 0\nfor n in range(1, 6):\n    total = n\nprint(total)\n"
RIGHT_SUM = "total = 0\nfor n in range(1, 6):\n    total = total + n\nprint(total)\n"


def test_health(client):
    assert client.get("/api/health").json() == {"status": "ok", "llm_provider": "mock"}


def test_graph_lists_prerequisites_before_dependents(client):
    graph = client.get("/api/graph").json()
    order = [node["id"] for node in graph["nodes"]]
    for edge in graph["edges"]:
        assert order.index(edge["from"]) < order.index(edge["to"])


def test_problems_are_listed(client):
    ids = [p["id"] for p in client.get("/api/problems").json()]
    assert ids[0] == "sum-1-to-5"  # seed order is kept


def test_wrong_attempt_is_traced_back_to_variable_update(client, student_id):
    response = client.post(f"/api/students/{student_id}/attempts",
                           json={"problem_id": "sum-1-to-5", "code": WRONG_SUM})
    assert response.status_code == 201
    body = response.json()
    assert body["passed"] is False
    assert body["findings"][0]["concept_id"] == "variable-update"
    diagnosis = body["diagnosis"]
    assert diagnosis["target"]["id"] == "for-loops"
    assert diagnosis["root_cause"]["id"] == "variable-update"
    assert [n["id"] for n in diagnosis["chain"]] == ["variable-update", "loop-logic", "for-loops"]
    assert diagnosis["evidence"]["rule"] == "overwritten-accumulator"


def test_correct_attempt_raises_mastery(client, student_id):
    body = client.post(f"/api/students/{student_id}/attempts",
                       json={"problem_id": "sum-1-to-5", "code": RIGHT_SUM}).json()
    assert body["passed"] is True
    mastery = {m["concept_id"]: m for m in client.get(f"/api/students/{student_id}/mastery").json()}
    assert mastery["for-loops"]["score"] > 0.5
    assert mastery["loop-logic"]["score"] > 0.5  # direct prerequisite got a small boost
    assert mastery["variables-assignment"]["score"] is None  # untouched


def test_practice_hides_answers_and_answering_updates_mastery(client, student_id):
    client.post(f"/api/students/{student_id}/attempts", json={"problem_id": "sum-1-to-5", "code": WRONG_SUM})
    exercises = client.post(f"/api/students/{student_id}/practice", json={"concept_id": "variable-update"}).json()
    assert len(exercises) == 3
    assert all("answer" not in e and "explanation" not in e for e in exercises)

    first = exercises[0]
    result = client.post(f"/api/students/{student_id}/exercises/{first['id']}/answer",
                         json={"answer": "20"}).json()
    assert result["correct"] is True
    assert result["new_score"] > result["old_score"]

    wrong = client.post(f"/api/students/{student_id}/exercises/{first['id']}/answer",
                        json={"answer": "10"}).json()
    assert wrong["correct"] is False
    assert wrong["new_score"] < wrong["old_score"]


def test_practice_after_fixing_root_cause_changes_diagnosis(client, student_id):
    client.post(f"/api/students/{student_id}/attempts", json={"problem_id": "sum-1-to-5", "code": WRONG_SUM})
    exercises = client.post(f"/api/students/{student_id}/practice", json={"concept_id": "variable-update"}).json()
    for exercise, answer in zip(exercises, ["20", "5", "Line 3"]):  # the seeded variable-update exercises
        result = client.post(f"/api/students/{student_id}/exercises/{exercise['id']}/answer",
                             json={"answer": answer}).json()
        assert result["correct"] is True
    diagnosis = client.get(f"/api/students/{student_id}/diagnosis/for-loops").json()
    assert diagnosis["root_cause"]["id"] != "variable-update"


def test_not_found_and_validation_errors(client, student_id):
    assert client.get("/api/students/999").status_code == 404
    assert client.get(f"/api/students/{student_id}/diagnosis/no-such-concept").status_code == 404
    assert client.post(f"/api/students/{student_id}/attempts",
                       json={"problem_id": "nope", "code": "x"}).status_code == 404
    assert client.post("/api/students", json={"name": ""}).status_code == 422


def test_teacher_overview_with_demo_class(demo_client):
    overview = demo_client.get("/api/teacher/overview").json()
    by_name = {row["name"]: row for row in overview["students"]}
    assert by_name["Student A"]["root_cause"]["id"] == "variable-update"
    assert by_name["Student A"]["status"] == "needs_help"
    assert by_name["Student C"]["status"] == "on_track"
    assert by_name["Student F"]["root_cause"]["id"] == "comparison-operators"
    counts = {c["id"]: c["count"] for c in overview["root_causes"]}
    assert sum(counts.values()) == sum(1 for row in overview["students"] if row["status"] != "on_track")
