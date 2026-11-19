from app.services.code_analysis import ProblemSpec, analyze

SUM_SPEC = ProblemSpec("for-loops", required_construct="for", range_stop=6, single_output=True)
LIST_SPEC = ProblemSpec("list-iteration", required_construct="for", single_output=True)
WHILE_SPEC = ProblemSpec("while-loops", required_construct="while")
FUNC_SPEC = ProblemSpec("return-values", required_construct="def")


def rules(code: str, spec: ProblemSpec) -> list[str]:
    return [finding.rule for finding in analyze(code, spec)]


def concepts(code: str, spec: ProblemSpec) -> list[str]:
    return [finding.concept_id for finding in analyze(code, spec)]


def test_correct_solution_has_no_findings():
    code = "total = 0\nfor n in range(1, 6):\n    total = total + n\nprint(total)\n"
    assert analyze(code, SUM_SPEC) == []


def test_augmented_assignment_is_fine():
    code = "total = 0\nfor n in range(1, 6):\n    total += n\nprint(total)\n"
    assert analyze(code, SUM_SPEC) == []


def test_overwritten_accumulator_points_to_variable_update():
    code = "total = 0\nfor n in range(1, 6):\n    total = n\nprint(total)\n"
    findings = analyze(code, SUM_SPEC)
    assert [f.rule for f in findings] == ["overwritten-accumulator"]
    assert findings[0].concept_id == "variable-update"
    assert findings[0].line == 3


def test_tracking_a_maximum_inside_an_if_is_not_flagged():
    code = ("numbers = [4, 9, 2, 7]\nlargest = numbers[0]\nfor n in numbers:\n"
            "    if n > largest:\n        largest = n\nprint(largest)\n")
    assert analyze(code, LIST_SPEC) == []


def test_exclusive_range_stop():
    code = "total = 0\nfor n in range(1, 5):\n    total = total + n\nprint(total)\n"
    assert concepts(code, SUM_SPEC) == ["range-function"]


def test_print_inside_loop_when_one_output_is_expected():
    code = "total = 0\nfor n in range(1, 6):\n    total = total + n\n    print(total)\n"
    assert concepts(code, SUM_SPEC) == ["indentation-blocks"]


def test_missing_required_construct():
    assert rules("print(15)\n", SUM_SPEC) == ["missing-construct"]


def test_while_loop_that_never_progresses():
    code = "n = 3\nwhile n > 0:\n    print(n)\n"
    assert concepts(code, WHILE_SPEC) == ["loop-logic"]


def test_while_loop_with_break_is_not_flagged():
    code = "n = 3\nwhile True:\n    print(n)\n    break\n"
    assert analyze(code, WHILE_SPEC) == []


def test_index_past_the_end():
    code = ("numbers = [4, 9, 2, 7]\nlargest = numbers[0]\nfor i in range(len(numbers) + 1):\n"
            "    if numbers[i] > largest:\n        largest = numbers[i]\nprint(largest)\n")
    assert concepts(code, LIST_SPEC) == ["list-indexing"]


def test_return_inside_loop_without_fallback():
    code = "def evens(numbers):\n    for n in numbers:\n        if n % 2 == 0:\n            return [n]\n"
    assert concepts(code, FUNC_SPEC) == ["return-values"]


def test_early_return_with_fallback_is_fine():
    code = "def has_even(numbers):\n    for n in numbers:\n        if n % 2 == 0:\n            return True\n    return False\n"
    assert analyze(code, FUNC_SPEC) == []


def test_assignment_in_condition_is_a_comparison_problem():
    code = "for n in [1, 2]:\n    if n % 2 = 0:\n        print(n)\n"
    findings = analyze(code, LIST_SPEC)
    assert [(f.rule, f.concept_id, f.line) for f in findings] == [("assign-in-condition", "comparison-operators", 2)]


def test_indentation_error():
    code = "for n in range(3):\nprint(n)\n"
    assert concepts(code, SUM_SPEC) == ["indentation-blocks"]


def test_other_syntax_errors_are_blamed_on_the_problem_concept():
    assert rules("for n in range(1, 6)\n    print(n)\n", SUM_SPEC) == ["syntax-error"]
