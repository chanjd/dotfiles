---
name: review-tests
description: Evaluate test suite quality across coverage, mutation gaps, and tautology/redundancy. Run before opening a PR on any significant new module or change.
disable-model-invocation: false
---

## Detect repo structure

!`python -m pytest --version 2>/dev/null && echo "pytest:ok" || echo "pytest:missing"`
!`cat pyproject.toml 2>/dev/null | grep -E '(tool\.pytest|tool\.coverage)' | head -20 || echo "(no pyproject coverage config)"`
!`find src/ -name "*.py" ! -name "__init__.py" ! -name "_*.py" 2>/dev/null | sort`
!`find tests/ -name "test_*.py" 2>/dev/null | sort`

## Run coverage

!`python -m pytest tests/ --cov=src --cov-branch --cov-report=term-missing --cov-report=json:.coverage.json -q 2>&1`

## Coverage summary

!`python -c "
import json
with open('.coverage.json') as f:
    data = json.load(f)
for path, info in sorted(data['files'].items()):
    pct = info['summary']['percent_covered']
    missing = info['missing_lines']
    missing_branches = info['missing_branches']
    print(f'{path}: {pct:.1f}% | missing lines: {missing} | missing branches: {missing_branches}')
" 2>&1`

---

1. If pytest is missing, stop and tell the user. Do not proceed.

2. Parse the coverage output. For each source file under src/, record:
   - Line and branch coverage percentage
   - Specific uncovered lines and branches
   - Flag files below 85% coverage

3. Build a source-to-test mapping:
   - For each file in src/, find its corresponding test file in tests/ by name convention (src/pkg/foo.py → tests/test_foo.py)
   - Files with no corresponding test file are **Untested** — record them, do not attempt to generate tests for them, flag them in the final report

4. For each source file that has a corresponding test file, spawn parallel subagents to identify mutation gaps. Select model based on file complexity:
   - Use Haiku if the file has no ML library imports and fewer than 10 functions
   - Use Sonnet otherwise

   Pass each subagent:
   - The full source file contents
   - The full contents of its corresponding test file(s)
   - The uncovered lines and missing branches for that file from the coverage report

   Instruct each subagent to identify behavioral gaps — functions or branches where existing assertions would not fail if a single mutation was applied (flipped comparison, changed boolean operator, removed a condition, swapped arithmetic operator, changed a return value). For each gap found, produce a candidate entry in this format:

       GAP: <one sentence describing the behavioral case not currently pinned>
       MUTATION THAT WOULD SURVIVE: <what change to the source would not be caught>
       DISPOSITION: new_test | strengthen_existing
         new_test: this case has no natural home in existing tests
         strengthen_existing: an existing test covers this area but its assertion is
           too weak; name the specific existing test and describe how to strengthen it
       CANDIDATE:
         <pytest code if new_test, or the strengthened assertion if strengthen_existing>

   Instruct each subagent:
   - Only assert observable outputs, raised exceptions, or side effects — not implementation details or internal state
   - Do not rewrite or duplicate existing tests
   - Do not add error handling for scenarios that cannot happen
   - Do not add type annotations, docstrings, or comments
   - If no meaningful gaps exist, return: NO GAPS FOUND

5. Spawn a single Sonnet subagent to review the full existing test suite. Pass it all test file contents combined. Ask it to identify:

   - **Tautological** — assertion cannot fail regardless of whether the code under test is correct (asserting a value the test itself computed, asserting only that no exception was raised when a return value is assertable, asserting shape or type when actual values are accessible and meaningful)
   - **Redundant** — would pass or fail for the exact same reason as another test; removing it loses no unique behavioral coverage
   - **Missing error paths** — exception or error branches visible in the source with no corresponding test

   Instruct the subagent: flag only cases where a test either cannot fail or provides zero unique coverage. Do not flag style, naming, or organizational issues.

   Output format per finding:

       [TAUTOLOGICAL | REDUNDANT | MISSING ERROR PATH] test_file.py::TestClass::test_name
       REASON: <one sentence>
       FIX: strengthen assertion | remove test | add test for: <description>

6. Present the full report to the user, structured as follows:

   **Coverage**
   - Per-file percentages, flagging anything below 85%
   - Uncovered lines and branches per file
   - Untested source files with no test file at all

   **Mutation gap candidates** (per source file)
   For each gap found, show the full candidate entry. Close this section with:
   "Review each candidate. Keep as a new test if it pins a behavioral case worth
   specifying permanently. Use strengthen_existing candidates to improve the named
   existing test rather than adding a new one. Discard candidates that are trivial
   or redundant."

   **Test suite review**
   - Tautological tests found
   - Redundant tests found
   - Missing error path tests

   **Summary**
   - Files below 85% coverage: N
   - Untested files: N
   - Mutation gap candidates: N (X new_test, Y strengthen_existing)
   - Tautological tests: N
   - Redundant tests: N
   - Missing error paths: N

7. Do not modify any files. Do not commit anything. Present findings only and wait for explicit instruction.
