# edges go prerequisite -> concept, e.g. variable-update -> loop-logic -> for-loops

from collections import deque
from collections.abc import Iterable


class CycleError(ValueError):
    pass


class ConceptGraph:
    def __init__(self, concept_ids: Iterable[str], edges: Iterable[tuple[str, str]]):
        # `edges` are (concept_id, prerequisite_id) pairs
        self.concept_ids: list[str] = list(concept_ids)
        known = set(self.concept_ids)
        self._prereqs: dict[str, list[str]] = {cid: [] for cid in self.concept_ids}
        self._dependents: dict[str, list[str]] = {cid: [] for cid in self.concept_ids}
        for concept_id, prereq_id in edges:
            if concept_id not in known or prereq_id not in known:
                raise KeyError(f"Edge {prereq_id} -> {concept_id} references an unknown concept")
            self._prereqs[concept_id].append(prereq_id)
            self._dependents[prereq_id].append(concept_id)

    def __contains__(self, concept_id: str) -> bool:
        return concept_id in self._prereqs

    def prerequisites(self, concept_id: str) -> list[str]:
        return list(self._prereqs[concept_id])

    def dependents(self, concept_id: str) -> list[str]:
        return list(self._dependents[concept_id])

    def ancestors(self, concept_id: str) -> dict[str, int]:
        # every prerequisite (direct or not) -> distance from concept_id
        depth: dict[str, int] = {}
        queue = deque([(concept_id, 0)])
        while queue:
            current, d = queue.popleft()
            for prereq in self._prereqs[current]:
                if prereq not in depth:
                    depth[prereq] = d + 1
                    queue.append((prereq, d + 1))
        return depth

    def path(self, start: str, goal: str) -> list[str]:
        # shortest chain start -> ... -> goal, [] if there is none
        if start == goal:
            return [start]
        previous: dict[str, str] = {}
        queue = deque([start])
        seen = {start}
        while queue:
            current = queue.popleft()
            for nxt in self._dependents[current]:
                if nxt in seen:
                    continue
                seen.add(nxt)
                previous[nxt] = current
                if nxt == goal:
                    chain = [goal]
                    while chain[-1] != start:
                        chain.append(previous[chain[-1]])
                    return list(reversed(chain))
                queue.append(nxt)
        return []

    def topological_order(self) -> list[str]:
        # prerequisites first, raises CycleError if there is a cycle
        indegree = {cid: len(self._prereqs[cid]) for cid in self.concept_ids}
        queue = deque(cid for cid in self.concept_ids if indegree[cid] == 0)
        order: list[str] = []
        while queue:
            current = queue.popleft()
            order.append(current)
            for nxt in self._dependents[current]:
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)
        if len(order) != len(self.concept_ids):
            raise CycleError("The concept graph contains a cycle")
        return order
