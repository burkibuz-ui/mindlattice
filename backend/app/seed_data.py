"""Static content: the Python-basics knowledge graph, coding problems and micro exercises.

Each concept lists its *direct* prerequisites. The graph must be acyclic
(validated in tests and at seed time).
"""

CONCEPTS: list[dict] = [
    {"id": "variables-assignment", "name": "Variables & assignment", "prerequisites": [],
     "description": "Storing a value under a name with `=`; the name points to the latest value."},
    {"id": "data-types", "name": "Data types", "prerequisites": [],
     "description": "int, float, str and bool, and what each one can do."},
    {"id": "arithmetic-operators", "name": "Arithmetic operators", "prerequisites": ["data-types"],
     "description": "+, -, *, /, // and %."},
    {"id": "variable-update", "name": "Updating a variable", "prerequisites": ["variables-assignment", "arithmetic-operators"],
     "description": "Computing a new value from the old one: `x = x + 1` or `x += 1`."},
    {"id": "comparison-operators", "name": "Comparison operators", "prerequisites": ["data-types"],
     "description": "==, !=, <, >, <=, >= and the difference between `=` and `==`."},
    {"id": "boolean-logic", "name": "Boolean logic", "prerequisites": ["comparison-operators"],
     "description": "Combining conditions with and, or, not."},
    {"id": "indentation-blocks", "name": "Indentation & code blocks", "prerequisites": [],
     "description": "Indentation decides which lines belong to an if, a loop or a function."},
    {"id": "conditionals", "name": "Conditionals", "prerequisites": ["boolean-logic", "indentation-blocks"],
     "description": "if / elif / else."},
    {"id": "loop-logic", "name": "Loop logic", "prerequisites": ["variable-update", "indentation-blocks"],
     "description": "Repeating a block; what changes on every iteration and when the loop stops."},
    {"id": "range-function", "name": "The range() function", "prerequisites": ["arithmetic-operators"],
     "description": "range(start, stop, step); `stop` is exclusive."},
    {"id": "for-loops", "name": "For loops", "prerequisites": ["loop-logic", "range-function"],
     "description": "Iterating over a sequence with `for item in sequence`."},
    {"id": "while-loops", "name": "While loops", "prerequisites": ["loop-logic", "boolean-logic"],
     "description": "Repeating while a condition is true; something must change so it can stop."},
    {"id": "accumulator-pattern", "name": "Accumulator pattern", "prerequisites": ["for-loops", "conditionals"],
     "description": "Building up a total or a count across loop iterations."},
    {"id": "lists", "name": "Lists", "prerequisites": ["data-types"],
     "description": "Ordered collections: creating them, len(), appending."},
    {"id": "list-indexing", "name": "List indexing", "prerequisites": ["lists", "arithmetic-operators"],
     "description": "Indices start at 0; the last valid index is len(list) - 1."},
    {"id": "list-iteration", "name": "Iterating over lists", "prerequisites": ["for-loops", "list-indexing"],
     "description": "Visiting every element of a list with a for loop."},
    {"id": "functions", "name": "Functions", "prerequisites": ["indentation-blocks", "variables-assignment"],
     "description": "Defining a function with def and calling it."},
    {"id": "return-values", "name": "Return values", "prerequisites": ["functions"],
     "description": "`return` sends a value back and ends the function immediately."},
]


PROBLEMS: list[dict] = [
    {
        "id": "sum-1-to-5",
        "title": "Sum from 1 to 5",
        "prompt": "Use a for loop to add up the numbers from 1 to 5 and print the result once.",
        "concept_id": "for-loops",
        "starter_code": "total = 0\n",
        "expected_output": "15",
        "required_construct": "for",
        "range_stop": 6,
        "single_output": True,
    },
    {
        "id": "count-evens",
        "title": "Count the even numbers",
        "prompt": "Count how many even numbers are in [3, 8, 10, 7, 4] and print the count once.",
        "concept_id": "accumulator-pattern",
        "starter_code": "numbers = [3, 8, 10, 7, 4]\ncount = 0\n",
        "expected_output": "3",
        "required_construct": "for",
        "range_stop": None,
        "single_output": True,
    },
    {
        "id": "countdown",
        "title": "Countdown with while",
        "prompt": "Use a while loop to print 3, 2, 1 (one number per line).",
        "concept_id": "while-loops",
        "starter_code": "n = 3\n",
        "expected_output": "3\n2\n1",
        "required_construct": "while",
        "range_stop": None,
        "single_output": False,
    },
    {
        "id": "largest-number",
        "title": "Largest number without max()",
        "prompt": "Find the largest number in [4, 9, 2, 7] with a loop (no max()) and print it once.",
        "concept_id": "list-iteration",
        "starter_code": "numbers = [4, 9, 2, 7]\n",
        "expected_output": "9",
        "required_construct": "for",
        "range_stop": None,
        "single_output": True,
    },
    {
        "id": "evens-function",
        "title": "Function that returns the even numbers",
        "prompt": "Write a function evens(numbers) that returns a new list with only the even numbers.",
        "concept_id": "return-values",
        "starter_code": "def evens(numbers):\n    ",
        "expected_output": "evens([1, 2, 3, 4]) -> [2, 4]",
        "required_construct": "def",
        "range_stop": None,
        "single_output": False,
    },
]


EXERCISES: list[dict] = [
    # variables-assignment
    {"concept_id": "variables-assignment", "kind": "predict_output", "question": "What does this print?",
     "code": "a = 4\nb = a\na = 7\nprint(b)", "options": ["4", "7", "11", "Error"], "answer": "4",
     "explanation": "`b = a` copies the value 4 into b. Changing a afterwards does not change b."},
    {"concept_id": "variables-assignment", "kind": "predict_output", "question": "What does this print?",
     "code": "name = \"Ada\"\nname = \"Bob\"\nprint(name)", "options": ["Ada", "Bob", "AdaBob", "Error"], "answer": "Bob",
     "explanation": "A new assignment replaces the old value. The name now points to \"Bob\"."},
    # data-types
    {"concept_id": "data-types", "kind": "predict_output", "question": "What does this print?",
     "code": "print(type(3.0).__name__)", "options": ["float", "int", "str", "number"], "answer": "float",
     "explanation": "A number with a decimal point is a float, even when the decimal part is 0."},
    # arithmetic-operators
    {"concept_id": "arithmetic-operators", "kind": "predict_output", "question": "What does this print?",
     "code": "print(7 // 2)", "options": ["3", "3.5", "4", "1"], "answer": "3",
     "explanation": "`//` is floor division: it drops the fractional part."},
    {"concept_id": "arithmetic-operators", "kind": "predict_output", "question": "What does this print?",
     "code": "print(7 % 3)", "options": ["1", "2", "2.33", "0"], "answer": "1",
     "explanation": "`%` gives the remainder: 7 = 2 * 3 + 1."},
    # variable-update
    {"concept_id": "variable-update", "kind": "predict_output", "question": "What does this print?",
     "code": "score = 10\nscore = score + 5\nscore = score + 5\nprint(score)", "options": ["10", "15", "20", "5"], "answer": "20",
     "explanation": "Each line takes the OLD value of score and adds 5 to it: 10 -> 15 -> 20."},
    {"concept_id": "variable-update", "kind": "predict_output", "question": "What does this print?",
     "code": "x = 3\nx = x * 2\nx = x - 1\nprint(x)", "options": ["5", "6", "3", "2"], "answer": "5",
     "explanation": "x becomes 3 * 2 = 6, then 6 - 1 = 5. The right side is computed first, then stored."},
    {"concept_id": "variable-update", "kind": "spot_bug", "question": "This should count the names. Which line is wrong?",
     "code": "count = 0\nfor name in names:\n    count = 1\nprint(count)", "options": ["Line 1", "Line 2", "Line 3", "Line 4"], "answer": "Line 3",
     "explanation": "`count = 1` overwrites the counter on every iteration. It should be `count = count + 1`."},
    # comparison-operators
    {"concept_id": "comparison-operators", "kind": "predict_output", "question": "What does this print?",
     "code": "x = 5\nprint(x == 5)", "options": ["True", "False", "5", "Error"], "answer": "True",
     "explanation": "`==` compares and gives a bool. `=` would assign instead."},
    {"concept_id": "comparison-operators", "kind": "concept_check", "question": "Which of these is a comparison?",
     "code": "", "options": ["x = 5", "x == 5", "x += 5", "x * 5"], "answer": "x == 5",
     "explanation": "Only `==` asks a question (is x equal to 5?). `=` and `+=` change x."},
    # boolean-logic
    {"concept_id": "boolean-logic", "kind": "predict_output", "question": "What does this print?",
     "code": "print(True and not False)", "options": ["True", "False", "None", "Error"], "answer": "True",
     "explanation": "`not False` is True, and `True and True` is True."},
    # indentation-blocks
    {"concept_id": "indentation-blocks", "kind": "predict_output", "question": "How many times is \"done\" printed?",
     "code": "for i in range(3):\n    pass\nprint(\"done\")", "options": ["0", "1", "3", "4"], "answer": "1",
     "explanation": "The print is not indented, so it is outside the loop and runs once after it."},
    # conditionals
    {"concept_id": "conditionals", "kind": "predict_output", "question": "What does this print?",
     "code": "n = 7\nif n > 10:\n    print(\"big\")\nelif n > 5:\n    print(\"medium\")\nelse:\n    print(\"small\")",
     "options": ["big", "medium", "small", "medium small"], "answer": "medium",
     "explanation": "Python checks the branches in order and runs only the first one that is true."},
    # loop-logic
    {"concept_id": "loop-logic", "kind": "predict_output", "question": "What does this print?",
     "code": "i = 0\nwhile i < 3:\n    i = i + 1\nprint(i)", "options": ["3", "2", "0", "It never stops"], "answer": "3",
     "explanation": "i grows by 1 each time. When i reaches 3 the condition is false and the loop ends."},
    # range-function
    {"concept_id": "range-function", "kind": "predict_output", "question": "What does this print?",
     "code": "print(list(range(1, 5)))", "options": ["[1, 2, 3, 4]", "[1, 2, 3, 4, 5]", "[0, 1, 2, 3, 4]", "[2, 3, 4]"],
     "answer": "[1, 2, 3, 4]",
     "explanation": "range's stop value is exclusive: range(1, 5) stops before 5."},
    {"concept_id": "range-function", "kind": "predict_output", "question": "How many times does the loop body run?",
     "code": "for i in range(2, 6):\n    print(i)", "options": ["3", "4", "5", "6"], "answer": "4",
     "explanation": "range(2, 6) gives 2, 3, 4, 5: that is 6 - 2 = 4 values."},
    # for-loops
    {"concept_id": "for-loops", "kind": "predict_output", "question": "What does this print?",
     "code": "total = 0\nfor n in [2, 4, 6]:\n    total = total + n\nprint(total)", "options": ["12", "6", "2", "0"], "answer": "12",
     "explanation": "The loop visits 2, 4 and 6 and adds each to total: 0 + 2 + 4 + 6 = 12."},
    {"concept_id": "for-loops", "kind": "predict_output", "question": "What does this print?",
     "code": "for c in \"abc\":\n    print(c, end=\"\")", "options": ["abc", "a b c", "c", "Error"], "answer": "abc",
     "explanation": "A for loop can walk over a string one character at a time."},
    # while-loops
    {"concept_id": "while-loops", "kind": "predict_output", "question": "What does this print?",
     "code": "n = 3\nwhile n > 0:\n    n = n - 1\nprint(n)", "options": ["0", "1", "-1", "It never stops"], "answer": "0",
     "explanation": "n goes 3 -> 2 -> 1 -> 0. At 0 the condition `n > 0` is false, so the loop stops."},
    # accumulator-pattern
    {"concept_id": "accumulator-pattern", "kind": "predict_output", "question": "What does this print?",
     "code": "total = 0\nfor n in range(1, 4):\n    total = n\nprint(total)", "options": ["3", "6", "1", "0"], "answer": "3",
     "explanation": "`total = n` replaces total each time, so only the last value (3) survives. To sum, write `total = total + n`."},
    {"concept_id": "accumulator-pattern", "kind": "predict_output", "question": "What does this print?",
     "code": "count = 0\nfor n in [1, 2, 3, 4]:\n    if n % 2 == 0:\n        count = count + 1\nprint(count)",
     "options": ["2", "4", "1", "0"], "answer": "2",
     "explanation": "Only 2 and 4 are even, so count is increased twice."},
    # lists
    {"concept_id": "lists", "kind": "predict_output", "question": "What does this print?",
     "code": "nums = [3, 1, 2]\nprint(len(nums))", "options": ["3", "2", "6", "[3, 1, 2]"], "answer": "3",
     "explanation": "len() returns the number of elements."},
    # list-indexing
    {"concept_id": "list-indexing", "kind": "predict_output", "question": "What does this print?",
     "code": "nums = [10, 20, 30]\nprint(nums[1])", "options": ["20", "10", "30", "Error"], "answer": "20",
     "explanation": "Indices start at 0, so index 1 is the second element."},
    {"concept_id": "list-indexing", "kind": "predict_output", "question": "What happens?",
     "code": "nums = [10, 20, 30]\nprint(nums[3])", "options": ["IndexError", "30", "None", "0"], "answer": "IndexError",
     "explanation": "The last valid index is len(nums) - 1 = 2."},
    # list-iteration
    {"concept_id": "list-iteration", "kind": "predict_output", "question": "What does this print?",
     "code": "for x in [1, 2, 3]:\n    print(x * 2, end=\" \")", "options": ["2 4 6", "1 2 3", "6", "2"], "answer": "2 4 6",
     "explanation": "The loop takes each element in order and prints it doubled."},
    # functions
    {"concept_id": "functions", "kind": "concept_check", "question": "A file only contains this. What is printed?",
     "code": "def greet():\n    print(\"hi\")", "options": ["Nothing", "hi", "greet", "Error"], "answer": "Nothing",
     "explanation": "`def` only defines the function. It runs when you call it: greet()."},
    # return-values
    {"concept_id": "return-values", "kind": "predict_output", "question": "What does this print?",
     "code": "def first():\n    for n in [1, 2, 3]:\n        return n\nprint(first())", "options": ["1", "3", "[1, 2, 3]", "None"], "answer": "1",
     "explanation": "`return` ends the function immediately, on the first iteration."},
]


# Demo class used to populate the teacher dashboard on first start.
# Each student submits real code through the normal analysis pipeline.
DEMO_SUBMISSIONS: list[tuple[str, str, str]] = [
    ("Student A", "sum-1-to-5", "total = 0\nfor n in range(1, 6):\n    total = n\nprint(total)\n"),
    ("Student B", "countdown", "n = 3\nwhile n > 0:\n    print(n)\n"),
    ("Student C", "count-evens", "numbers = [3, 8, 10, 7, 4]\ncount = 0\nfor n in numbers:\n    if n % 2 == 0:\n        count = count + 1\nprint(count)\n"),
    ("Student D", "sum-1-to-5", "total = 0\nfor n in range(1, 5):\n    total = total + n\nprint(total)\n"),
    ("Student E", "largest-number", "numbers = [4, 9, 2, 7]\nlargest = numbers[0]\nfor i in range(len(numbers) + 1):\n    if numbers[i] > largest:\n        largest = numbers[i]\nprint(largest)\n"),
    ("Student F", "count-evens", "numbers = [3, 8, 10, 7, 4]\ncount = 0\nfor n in numbers:\n    if n % 2 = 0:\n        count = count + 1\nprint(count)\n"),
    ("Student G", "sum-1-to-5", "total = 0\nfor n in range(1, 6):\n    total = total + n\n    print(total)\n"),
    ("Student H", "evens-function", "def evens(numbers):\n    for n in numbers:\n        if n % 2 == 0:\n            return [n]\n"),
]
