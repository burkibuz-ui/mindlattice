import json

import httpx
import pytest

from app.services.code_analysis import Finding, ProblemSpec
from app.services.llm import ANTHROPIC_URL, ClaudeLLM, MockLLM, get_llm

FINDING = Finding(rule="overwritten-accumulator", concept_id="variable-update", line=3,
                  message="`total = n` replaces the running total instead of adding to it.",
                  hint="Use total = total + n.")
ARGS = ("For loops", "Updating a variable", ["Updating a variable", "Loop logic", "For loops"], FINDING)


def claude_with(handler) -> tuple[ClaudeLLM, list[httpx.Request]]:
    seen: list[httpx.Request] = []

    def record(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return handler(request)

    client = httpx.Client(transport=httpx.MockTransport(record))
    return ClaudeLLM(api_key="test-key", model="test-model", client=client), seen


def test_explanation_comes_from_the_messages_api():
    llm, seen = claude_with(lambda _: httpx.Response(200, json={
        "content": [{"type": "text", "text": "  You keep overwriting total.  "}]}))
    assert llm.explain_diagnosis(*ARGS) == "You keep overwriting total."

    request = seen[0]
    assert str(request.url) == ANTHROPIC_URL
    assert request.headers["x-api-key"] == "test-key"
    body = json.loads(request.content)
    assert body["model"] == "test-model"
    prompt = body["messages"][0]["content"]
    assert "Updating a variable -> Loop logic -> For loops" in prompt
    assert "line 3" in prompt


@pytest.mark.parametrize("response", [
    httpx.Response(500, json={"error": "overloaded"}),
    httpx.Response(200, json={"unexpected": True}),
    httpx.Response(200, json={"content": []}),
])
def test_falls_back_to_the_offline_explanation(response):
    llm, _ = claude_with(lambda _: response)
    assert llm.explain_diagnosis(*ARGS) == MockLLM().explain_diagnosis(*ARGS)


def test_network_error_falls_back():
    def boom(request):
        raise httpx.ConnectError("no network", request=request)

    llm, _ = claude_with(boom)
    assert "root cause looks like Updating a variable" in llm.explain_diagnosis(*ARGS)


def test_code_analysis_stays_deterministic_and_offline():
    llm, seen = claude_with(lambda _: httpx.Response(500))
    mock = MockLLM()
    spec = ProblemSpec(concept_id="for-loops", required_construct="for", range_stop=6)
    code = "total = 0\nfor n in range(1, 6):\n    total = n\nprint(total)\n"
    assert llm.analyze_code(code, spec) == mock.analyze_code(code, spec)
    assert seen == []


def test_get_llm():
    assert get_llm("mock").name == "mock"
    assert get_llm("claude", api_key="k").name == "claude"
    with pytest.raises(ValueError):
        get_llm("claude")  # no key
    with pytest.raises(ValueError):
        get_llm("gpt-9000")
