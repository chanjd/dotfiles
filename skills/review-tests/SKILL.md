---
name: review-tests
description: Evaluate test suite quality across coverage, mutation gaps, and tautology/redundancy. Run before opening a PR on any significant new module or change.
disable-model-invocation: false
---

## Detect environment and repo structure

!`
# Locate a managed Python env (micromamba or conda).
# Deliberately skips system python — bare python may not be the project env.
# If multiple envs exist, picks the first alphabetically; adjust if needed.
PYTHON=$(ls $HOME/micromamba/envs/*/bin/python 2>/dev/null | head -1 || ls $HOME/.conda/envs/*/bin/python 2>/dev/null | head -1)
if [ -z "$PYTHON" ]; then
  echo "ERROR: no managed python env found under micromamba or conda. Cannot proceed."
  exit 1
fi
ENV_NAME=$(basename $(dirname $(dirname $PYTHON)))
RUN="micromamba run -n $ENV_NAME"

# Verify pytest is available in the env
$RUN python -m pytest --version 2>/dev/null && echo "pytest:ok" || echo "ERROR: pytest not found in env $ENV_NAME"

# Detect src layout — expects src/ or fails explicitly
SRC=$([ -d src ] && echo src || echo "")
if [ -z "$SRC" ]; then
  echo "ERROR: no src/ directory found. Skill expects src layout."
  exit 1
fi

# Detect test directory
TESTS=$([ -d tests ] && echo tests || ([ -d test ] && echo test) || echo "")
if [ -z "$TESTS" ]; then
  echo "ERROR: no tests/ or test/ directory found."
  exit 1
fi
echo "ENV=$ENV_NAME"
echo "RUN=$RUN"
echo "SRC=$SRC"
echo "TESTS=$TESTS"

# List source and test files for mapping
echo "--- source files ---"
find $SRC/ -name "*.py" ! -name "__init__.py" ! -name "_*.py" | sort
echo "--- test files ---"
find $TESTS/ -name "test_*.py" | sort
`

## Changed source files
!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)'`

## Changed file diffs
!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); git diff --diff-filter=ACM $BASE..HEAD -- $(git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)')`

## Run coverage on changed file tests
!`
PYTHON=$(ls $HOME/micromamba/envs/*/bin/python 2>/dev/null | head -1 || ls $HOME/.conda/envs/*/bin/python 2>/dev/null | head -1)
ENV_NAME=$(basename $(dirname $(dirname $PYTHON)))
RUN="micromamba run -n $ENV_NAME"
SRC=$([ -d src ] && echo src)
TESTS=$([ -d tests ] && echo tests || ([ -d test ] && echo test))
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null)

CHANGED_TESTS=""
for src_file in $(git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)'); do
  base=$(basename "$src_file" .py)
  test_file=$(find $TESTS -name "test_${base}.py" 2>/dev/null)
  [ -n "$test_file" ] && CHANGED_TESTS="$CHANGED_TESTS $test_file"
done

if [ -z "$CHANGED_TESTS" ]; then
  echo "No test files found for changed source files."
else
  $RUN python -m pytest $CHANGED_TESTS --cov=$SRC --cov-branch --cov-report=term-missing --cov-report=json:.coverage.json -q 2>&1
fi
`

## Coverage summary

!`
PYTHON=$(ls $HOME/micromamba/envs/*/bin/python 2>/dev/null | head -1 || ls $HOME/.conda/envs/*/bin/python 2>/dev/null | head -1)
ENV_NAME=$(basename $(dirname $(dirname $PYTHON)))

micromamba run -n $ENV_NAME python -c "
import json
with open('.coverage.json') as f:
    data = json.load(f)
for path, info in sorted(data['files'].items()):
    pct = info['summary']['percent_covered']
    missing = info['missing_lines']
    branches = ', '.join(f'{a}->{b}' for a, b in info['missing_branches'])
    print(f'{path}: {pct:.1f}% | missing lines: {missing} | missing branches: {branches}')
" 2>&1
`

---

1. If any ERROR lines appeared in the detect block, stop and report them to the user. Do not proceed.

2. Parse the coverage output. For each changed source file, record:
   - Line and branch coverage percentage
   - Specific uncovered lines and branches
   - Flag files below 85% coverage

3. Build a source-to-test mapping using only the changed source files from the branch diff:
   - Match $SRC/pkg/foo.py → $TESTS/test_foo.py by filename convention
   - Changed files with no corresponding test file are **Untested** — flag in report
   - Unchanged source files are out of scope - do not analyze them

4. For each changed source file that has a corresponding test file, spawn PARALLEL subagents to identify mutation gaps across multiple files at the same time. Pass each subagent:
   - The full source file contents (for context)
   - The branch diff for that file (to identify changed regions)
   - The full contents of its corresponding test file(s)
   - The uncovered lines and missing branches for that file from the coverage report
   - The following environment variables: SRC, TESTS

   Instruct each subagent:
   - Identify behavioral gaps — functions or branches where existing assertions would not fail if a single mutation was applied (flipped comparison, changed boolean operator, removed a condition, swapped arithmetic operator, changed a return value). For each gap found, produce a candidate entry in this format:
       GAP: <one sentence describing the behavioral case not currently pinned>
       MUTATION THAT WOULD SURVIVE: <what change to the source would not be caught>
       DISPOSITION: new_test | strengthen_existing
         new_test: this case has no natural home in existing tests
         strengthen_existing: an existing test covers this area but its assertion is too weak; name the specific existing test and describe how to strengthen it
       CANDIDATE: <pytest code if new_test, or the strengthened assertion if strengthen_existing>

   - Only analyze mutation gaps in functions or branches that overlap with the diff. Unchanged code is out of scope even if it has coverage gaps.
   - Only assert observable outputs, raised exceptions, or side effects - not implementation details or internal state
   - Do not rewrite or duplicate existing tests
   - Do not add error handling for scenarios that cannot happen
   - Do not add type annotations, docstrings, or comments
   - Patch lazy imports (imported inside a function body) at the source package, not the calling module - the calling module never binds the name
   - For each gap, describe the specific input or state that would expose the weakness
   - Report at most 5 mutation gaps per source file. If more exist, keep the 5 most likely to mask a real bug and note "plus N additional gaps omitted:" along with file:line of each omitted gap.
   - If no meaningful gaps exist, return: NO GAPS FOUND

5. Spawn a single subagent to review the test files corresponding to changed source files. Pass it only those test file contents. Ask it to identify:

   - **Tautological** — assertion cannot fail regardless of whether the code under test is correct (asserting a value the test itself computed, asserting only that no exception was raised when a return value is assertable, asserting shape or type when actual values are accessible and meaningful)
   - **Redundant** — would pass or fail for the exact same reason as another test; removing it loses no unique behavioral coverage
   - **Missing error paths** — exception or error branches visible in the source with no corresponding test

   Instruct the subagent: flag only cases where a test either cannot fail or provides zero unique coverage. Do not flag style, naming, or organizational issues.

   Output format per finding:

       [TAUTOLOGICAL | REDUNDANT | MISSING ERROR PATH] test_file.py::TestClass::test_name
       REASON: <one sentence>
       FIX: strengthen assertion | remove test | add test for: <description>

6. Review the output from step 4 and step 5 subagents yourself, do not pass the raw subagent outputs to the user. Evaluate each finding and coverage gap, discard anything you judge to be noise or not worth acting on, and present only your curated assessment:

  **Scope**: N source files changed, M with corresponding test files

  **Findings** (only include sections that have findings)

  For each finding you kept, show:
  - what the issue is (one line)
  - Why it matters (one line)
  - What to do about it (one line)

  Group by source file. Do not include CANDIDATE code blocks in the output. If a source file has no findings worth reporting, omit it entirely.

   **Summary**
   - Coverage: flag any source files below 85% test coverage
   - Untested files: N
   - Mutation gaps worth fixing: N
   - Tautological/redundant tests worth fixing: N
   - Tautological/redundant tests that should be removed: N
   - Missing error paths worth adding: N

7. Do not modify any files. Do not commit anything. Present findings only and wait for explicit instruction.
