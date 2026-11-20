# everything "smart" goes through LLMProvider, so mock and real models are swappable

import logging
from typing import Protocol

import httpx

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


logger = logging.getLogger(__name__)

ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_CLAUDE_MODEL = "claude-sonnet-5-5"
MAX_EXPLANATION_CHARS = 800

EXPLAIN_PROMPT = (
    "You are a tutor for Python beginners. Explain this diagnosis to the student in 2-3 short "
    "sentences: what the real gap is and why it blocks their topic. Only use the info given. "
    "Talk to the student directly. Plain text, no lists or code."
)


# Claude only writes the explanation text. Code analysis stays rule based because
# diagnosis needs every finding mapped to exactly one concept id.
# If the API call fails for any reason we fall back to the mock text.
class ClaudeLLM:
    name = "claude"

    def __init__(self, api_key: str, model: str = DEFAULT_CLAUDE_MODEL,
                 client: httpx.Client | None = None, timeout: float = 10.0):
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY is not set")
        self.model = model
        self._fallback = MockLLM()
        self._client = client or httpx.Client(timeout=timeout)
        self._headers = {"x-api-key": api_key, "anthropic-version": ANTHROPIC_VERSION,
                         "content-type": "application/json"}

    def analyze_code(self, code: str, spec: ProblemSpec) -> list[Finding]:
        return self._fallback.analyze_code(code, spec)

    def select_exercises(self, concept_id: str, bank: list[ExerciseLike], limit: int) -> list[ExerciseLike]:
        return self._fallback.select_exercises(concept_id, bank, limit)

    def explain_diagnosis(self, target_name: str, root_name: str, chain_names: list[str],
                          finding: Finding | None) -> str:
        lines = [
            f"Topic: {target_name}",
            f"Root cause: {root_name}",
            f"Chain: {' -> '.join(chain_names)}",
        ]
        if finding:
            lines.append(f"Last attempt, line {finding.line}: {finding.message}")
        try:
            text = self._complete(EXPLAIN_PROMPT, "\n".join(lines), max_tokens=200)
        except (httpx.HTTPError, KeyError, IndexError, TypeError, ValueError) as e:
            logger.warning("claude call failed: %s", e)
            text = ""
        if not text:
            return self._fallback.explain_diagnosis(target_name, root_name, chain_names, finding)
        return text[:MAX_EXPLANATION_CHARS]

    def _complete(self, system: str, prompt: str, max_tokens: int) -> str:
        response = self._client.post(ANTHROPIC_URL, headers=self._headers, json={
            "model": self.model,
            "max_tokens": max_tokens,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        })
        response.raise_for_status()
        blocks = response.json()["content"]
        return " ".join(b["text"] for b in blocks if b.get("type") == "text").strip()


def get_llm(provider: str = "mock", *, api_key: str = "", model: str = DEFAULT_CLAUDE_MODEL) -> LLMProvider:
    if provider == "mock":
        return MockLLM()
    if provider == "claude":
        return ClaudeLLM(api_key=api_key, model=model)
    raise ValueError(f"Unknown LLM provider '{provider}'. Available: mock, claude")
