"""Static analysis of student code with Python's `ast` module.

The code is parsed, never executed. Each rule looks for a pattern that
reveals a specific misconception and pins it on one concept of the
knowledge graph. This is the rule-based "mock LLM"; a real LLM provider can
find subtler mistakes, but must return the same `Finding` shape.
"""

import ast
import re
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class ProblemSpec:
    concept_id: str
    required_construct: str | None = None  # "for" | "while" | "def"
    range_stop: int | None = None
    single_output: bool = False


@dataclass(frozen=True)
class Finding:
    rule: str
    concept_id: str
    line: int | None
    message: str
    hint: str

    def to_dict(self) -> dict:
        return asdict(self)


_ASSIGN_IN_CONDITION = re.compile(r"^\s*(if|elif|while)\b[^=!<>]*[^=!<>]=[^=]")
_LOOPS = (ast.For, ast.While)
_CONSTRUCTS = {"for": ast.For, "while": ast.While, "def": ast.FunctionDef}


def analyze(code: str, spec: ProblemSpec) -> list[Finding]:
    try:
        tree = ast.parse(code)
    except SyntaxError as error:
        return [_syntax_finding(code, error, spec)]

    findings: list[Finding] = []
    findings += _missing_construct(tree, spec)
    findings += _overwritten_accumulator(tree)
    findings += _while_without_progress(tree)
    findings += _exclusive_range_stop(tree, spec)
    findings += _index_past_end(tree)
    findings += _print_inside_loop(tree, spec)
    findings += _return_inside_loop(tree)
    return sorted(findings, key=lambda f: (f.line or 0, f.rule))


# --- rules -----------------------------------------------------------------


def _syntax_finding(code: str, error: SyntaxError, spec: ProblemSpec) -> Finding:
    if isinstance(error, IndentationError):
        return Finding("indentation-error", "indentation-blocks", error.lineno,
                       "Python could not tell which block this line belongs to.",
                       "Lines inside a loop, an if or a function must be indented by the same amount (4 spaces).")
    for number, text in enumerate(code.splitlines(), start=1):
        if _ASSIGN_IN_CONDITION.search(text):
            return Finding("assign-in-condition", "comparison-operators", number,
                           "A condition uses `=` (assignment) instead of `==` (comparison).",
                           "Use `==` when you want to ask whether two values are equal.")
    return Finding("syntax-error", spec.concept_id, error.lineno,
                   f"Python could not read this code: {error.msg}.",
                   "Check brackets, colons at the end of if/for/while/def lines, and quotes.")


def _missing_construct(tree: ast.AST, spec: ProblemSpec) -> list[Finding]:
    node_type = _CONSTRUCTS.get(spec.required_construct or "")
    if node_type is None or any(isinstance(node, node_type) for node in ast.walk(tree)):
        return []
    word = {"def": "a function (def)"}.get(spec.required_construct, f"a {spec.required_construct} loop")
    return [Finding("missing-construct", spec.concept_id, None,
                    f"The task asks for {word}, but the code does not use one.",
                    "Re-read the task and build the solution around the requested construct.")]


def _overwritten_accumulator(tree: ast.AST) -> list[Finding]:
    """`total = n` directly inside a loop, where `total` was initialised before the loop."""
    findings = []
    for loop in (node for node in ast.walk(tree) if isinstance(node, _LOOPS)):
        initialised = _names_assigned_before(tree, loop.lineno)
        loop_vars = _names_in(loop.target) if isinstance(loop, ast.For) else set()
        for statement in loop.body:  # direct children only: `largest = n` inside an if is fine
            if not (isinstance(statement, ast.Assign) and len(statement.targets) == 1):
                continue
            target = statement.targets[0]
            if not isinstance(target, ast.Name) or target.id in loop_vars:
                continue
            if target.id in initialised and target.id not in _names_in(statement.value):
                findings.append(Finding(
                    "overwritten-accumulator", "variable-update", statement.lineno,
                    f"`{target.id}` is replaced on every iteration instead of being updated, "
                    f"so only the last value survives.",
                    f"Build on the old value: `{target.id} = {target.id} + ...` (or `{target.id} += ...`)."))
    return findings


def _while_without_progress(tree: ast.AST) -> list[Finding]:
    findings = []
    for loop in (node for node in ast.walk(tree) if isinstance(node, ast.While)):
        if any(isinstance(node, ast.Break) for node in _walk_body(loop.body)):
            continue
        condition_names = _names_in(loop.test)
        changed = set()
        for node in _walk_body(loop.body):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    changed |= _names_in(target)
            elif isinstance(node, (ast.AugAssign, ast.AnnAssign)):
                changed |= _names_in(node.target)
        if not condition_names & changed:
            names = ", ".join(f"`{name}`" for name in sorted(condition_names)) or "the condition"
            findings.append(Finding(
                "while-without-progress", "loop-logic", loop.lineno,
                f"Nothing inside the loop changes {names}, so the condition never becomes false: an infinite loop.",
                "Update the variable the condition depends on inside the loop, e.g. `n = n - 1`."))
    return findings


def _exclusive_range_stop(tree: ast.AST, spec: ProblemSpec) -> list[Finding]:
    if spec.range_stop is None:
        return []
    findings = []
    for call in _range_calls(tree):
        stop = call.args[-1] if len(call.args) >= 2 else (call.args[0] if call.args else None)
        if isinstance(stop, ast.Constant) and stop.value == spec.range_stop - 1:
            findings.append(Finding(
                "exclusive-range-stop", "range-function", call.lineno,
                f"range(..., {stop.value}) stops before {stop.value}, so the last number is skipped.",
                f"range's stop value is exclusive. To include {stop.value}, use {spec.range_stop} as the stop."))
    return findings


def _index_past_end(tree: ast.AST) -> list[Finding]:
    findings = []
    for call in _range_calls(tree):
        stop = call.args[-1] if call.args else None
        if (isinstance(stop, ast.BinOp) and isinstance(stop.op, ast.Add)
                and isinstance(stop.left, ast.Call) and getattr(stop.left.func, "id", None) == "len"
                and isinstance(stop.right, ast.Constant) and stop.right.value == 1):
            findings.append(Finding(
                "index-past-end", "list-indexing", call.lineno,
                "range(len(...) + 1) produces one index too many; the last one raises IndexError.",
                "Valid indices go from 0 to len(list) - 1, so range(len(list)) is enough."))
    return findings


def _print_inside_loop(tree: ast.AST, spec: ProblemSpec) -> list[Finding]:
    if not spec.single_output:
        return []
    for loop in (node for node in ast.walk(tree) if isinstance(node, _LOOPS)):
        for node in _walk_body(loop.body):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "print":
                return [Finding(
                    "print-inside-loop", "indentation-blocks", node.lineno,
                    "print() is indented inside the loop, so it runs on every iteration instead of once.",
                    "Un-indent the print so it sits after the loop and runs once at the end.")]
    return []


def _return_inside_loop(tree: ast.AST) -> list[Finding]:
    """A function that can only return from inside a loop stops on the first match."""
    findings = []
    for function in (node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)):
        loops = [node for node in function.body if isinstance(node, _LOOPS)]
        if not loops or any(isinstance(node, ast.Return) for node in function.body):
            continue
        for loop in loops:
            returns = [node for node in _walk_body(loop.body) if isinstance(node, ast.Return)]
            if returns:
                findings.append(Finding(
                    "return-inside-loop", "return-values", returns[0].lineno,
                    "`return` inside the loop ends the function on the first match, "
                    "and if nothing matches the function returns None.",
                    "Collect results in a list during the loop and `return` it after the loop."))
    return findings


# --- helpers ---------------------------------------------------------------


def _names_in(node: ast.AST) -> set[str]:
    return {n.id for n in ast.walk(node) if isinstance(n, ast.Name)}


def _walk_body(statements: list[ast.stmt]):
    """Walk statements without descending into nested function or class definitions."""
    stack = list(statements)
    while stack:
        node = stack.pop()
        yield node
        for child in ast.iter_child_nodes(node):
            if not isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef, ast.Lambda)):
                stack.append(child)


def _names_assigned_before(tree: ast.AST, line: int) -> set[str]:
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and node.lineno < line:
            for target in node.targets:
                names |= _names_in(target)
        elif isinstance(node, ast.FunctionDef) and node.lineno < line:
            names |= {arg.arg for arg in node.args.args}
    return names


def _range_calls(tree: ast.AST) -> list[ast.Call]:
    return [node for node in ast.walk(tree)
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "range"]
