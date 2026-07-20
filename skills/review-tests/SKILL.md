---
name: review-tests
description: Evaluate test suite quality across coverage, mutation gaps, and tautology/redundancy. Run before opening a PR on any significant new module or change.
disable-model-invocation: false
---

## Detect environment and repo structure

!`
# Locate a Python with pytest. Discover env prefixes from micromamba itself
# (location-agnostic — works whether envs live under ~/scratch/conda/envs,
# ~/.local/share/mamba/envs, ~/micromamba/envs, etc.), then pick the first env
# that actually has pytest (not merely the alphabetically-first env).
ENV_PATHS=$(micromamba env list 2>/dev/null | awk '$NF ~ /\// {print $NF}')
[ -z "$ENV_PATHS" ] && ENV_PATHS=$(ls -d ${CONDA_ENV_DIRS:+$CONDA_ENV_DIRS/*/} \
  $HOME/scratch/conda/envs/*/ $HOME/.local/share/mamba/envs/*/ \
  $HOME/micromamba/envs/*/ $HOME/.conda/envs/*/ 2>/dev/null)

ENV_NAME=""; RUN=""
for prefix in $ENV_PATHS; do
  name=$(basename "$prefix")
  if micromamba run -n "$name" python -m pytest --version >/dev/null 2>&1; then
    ENV_NAME="$name"; RUN="micromamba run -n $name"; break
  fi
done

if [ -z "$ENV_NAME" ]; then
  if command -v python >/dev/null 2>&1 && python -m pytest --version >/dev/null 2>&1; then
    ENV_NAME="(system)"; RUN=""
  else
    echo "ERROR: no env with pytest found (searched micromamba envs + common roots, and bare python). Run scripts/setup/setup_envs.sh first."
    exit 1
  fi
fi

# Verify pytest is available
$RUN python -m pytest --version 2>/dev/null && echo "pytest:ok in $ENV_NAME" || echo "ERROR: pytest not found in $ENV_NAME"

# Detect source layout — supports src/ layout or flat layout (any top-level package dir)
if [ -d src ]; then
  SRC=src
else
  # Flat layout: find dirs containing __init__.py directly (depth 2 = ./pkg/__init__.py)
  SRC=$(find . -maxdepth 2 -name "__init__.py" ! -path "./.git/*" ! -path "./tests/*" ! -path "./test/*" 2>/dev/null \
        | xargs -I{} dirname {} | grep -v '^\.$' | sort -u | head -1 | sed 's|^\./||')
fi

if [ -z "$SRC" ]; then
  echo "ERROR: no source package found. Cannot proceed."
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

!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)'; true`

## Changed file diffs

!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); git diff --diff-filter=ACM $BASE..HEAD -- $(git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)')`

## Removed code + candidate dead tests (deleted files, removed defs/classes, and tests that still reference them)

!`
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null)
TESTS=$([ -d tests ] && echo tests || { [ -d test ] && echo test; })
echo "--- deleted files ---"
git diff --name-only --diff-filter=D "$BASE"..HEAD 2>/dev/null
echo "--- removed defs/classes (from deleted + modified files) ---"
REMOVED=$(git diff --diff-filter=DM "$BASE"..HEAD -- '*.py' 2>/dev/null | grep -E '^-[[:space:]]*(def|class) ' | sed -E 's/^-[[:space:]]*(def|class)[[:space:]]+([A-Za-z_][A-Za-z0-9_]*).*/\2/' | sort -u)
echo "${REMOVED:-(none)}"
echo "--- tests referencing removed symbols (CANDIDATE dead tests) ---"
if [ -n "$TESTS" ] && [ -n "$REMOVED" ]; then
  for s in $REMOVED; do
    hits=$(grep -rnw --include='*.py' "$s" "$TESTS" 2>/dev/null | head -10)
    if [ -n "$hits" ]; then echo "== $s =="; echo "$hits"; fi
  done
else
  echo "(no removed symbols, or no tests dir)"
fi
true
`

## Run coverage and summarize

!`
ENV_PATHS=$(micromamba env list 2>/dev/null | awk '$NF ~ /\// {print $NF}')
[ -z "$ENV_PATHS" ] && ENV_PATHS=$(ls -d ${CONDA_ENV_DIRS:+$CONDA_ENV_DIRS/*/} \
  $HOME/scratch/conda/envs/*/ $HOME/.local/share/mamba/envs/*/ \
  $HOME/micromamba/envs/*/ $HOME/.conda/envs/*/ 2>/dev/null)
RUN=""
for prefix in $ENV_PATHS; do
  name=$(basename "$prefix")
  if micromamba run -n "$name" python -m pytest --version >/dev/null 2>&1; then
    RUN="micromamba run -n $name"; break
  fi
done
if [ -z "$RUN" ]; then
  if command -v python >/dev/null 2>&1 && python -m pytest --version >/dev/null 2>&1; then
    RUN=""
  else
    echo "ERROR: no env with pytest found" >&2; exit 1
  fi
fi

REPO=$(git rev-parse --show-toplevel 2>/dev/null || ls -d /workspaces/*/ 2>/dev/null | head -1 | sed 's|/$||')
if [ -z "$REPO" ]; then
  echo "ERROR: cannot locate git repo" >&2; exit 1
fi

SRC=$([ -d "$REPO/src" ] && echo "$REPO/src" || (find "$REPO" -maxdepth 3 -name "__init__.py" ! -path "*/.git/*" ! -path "*/tests/*" ! -path "*/test/*" 2>/dev/null | xargs -I{} dirname {} | grep -v "^$REPO$" | sort -u | head -1))
TESTS=$([ -d "$REPO/tests" ] && echo "$REPO/tests" || ([ -d "$REPO/test" ] && echo "$REPO/test"))
BASE=$(git -C "$REPO" merge-base HEAD origin/main 2>/dev/null || git -C "$REPO" merge-base HEAD origin/master 2>/dev/null)
if [ -z "$BASE" ]; then
  echo "ERROR: cannot determine base branch (no origin/main or origin/master)" >&2; exit 1
fi

REPORT=$(mktemp /tmp/coverage_XXXXXX.json)

CHANGED_SRC=""
CHANGED_TESTS=""
for src_file in $(git -C "$REPO" diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)'); do
  CHANGED_SRC="$CHANGED_SRC $src_file"
  base=$(basename "$src_file" .py)
  # Dotted import path: strip a leading src/ or lib/ root, drop .py, / -> .
  mod=$(echo "$src_file" | sed -E 's#^.*/(src|lib)/##; s#^(src|lib)/##; s#\.py$##; s#/#.#g')
  # For __init__/__main__ the meaningful name is the package dir, not the file.
  if [ "$base" = "__init__" ] || [ "$base" = "__main__" ]; then
    stem=$(basename "$(dirname "$src_file")")
  else
    stem=$base
  fi
  # Discover candidate tests by REFERENCE, not name alone: union of
  #  (a) exact convention test_<stem>.py, (b) any test_*<stem>*.py (suffix/prefix
  #  variants like _engine), (c) any test file that imports/mentions the dotted
  #  module path or its basename. (c) is what catches feature-named tests (e.g.
  #  a batch-integration test exercising an engine module). Over-inclusion is
  #  safe here (a few extra test files run under coverage); the old basename-only
  #  match produced false "Untested" — the worse failure.
  cands=$(
    {
      find "$TESTS" -name "test_${stem}.py" 2>/dev/null
      find "$TESTS" -name "test_*${stem}*.py" 2>/dev/null
      grep -rlE "\b${mod}\b|\b${stem}\b" "$TESTS" --include='*.py' 2>/dev/null
    } | sort -u
  )
  CHANGED_TESTS="$CHANGED_TESTS $cands"
done
CHANGED_TESTS=$(echo "$CHANGED_TESTS" | tr ' ' '\n' | grep -v '^$' | sort -u | tr '\n' ' ')

# Coverage is the source of truth for "is this file exercised", not the filename
# mapping. Always run it; if no candidate tests were discovered, fall back to the
# whole suite so a changed file is confirmed uncovered rather than assumed so.
# NOTE: keep --cov at the package/dir root ($SRC). Scoping --cov to a single
# dotted submodule can trigger a second import of heavy deps (e.g. a NumPy
# reload) and corrupt the run; filter to changed files in the summary instead.
if [ -z "$CHANGED_TESTS" ]; then
  echo "No test file references found by name or import; running the full suite so coverage is authoritative."
  COV_TESTS="$TESTS"
else
  COV_TESTS="$CHANGED_TESTS"
fi
PYTHONPATH="$TESTS" $RUN python -m pytest $COV_TESTS --cov="$SRC" --cov-branch --cov-report=term-missing --cov-report=json:"$REPORT" -q 2>&1
$RUN python -c "
import json, os
repo = '$REPO'
changed_rel = [f for f in '$CHANGED_SRC'.split() if f]
with open('$REPORT') as f:
    data = json.load(f)
matched = set()
for path, info in sorted(data['files'].items()):
    rel = next((f for f in changed_rel if path == os.path.join(repo, f) or path.endswith('/' + f)), None)
    if rel is None:
        continue
    matched.add(rel)
    pct = info['summary']['percent_covered']
    missing = info['missing_lines']
    branches = ', '.join(f'{a}->{b}' for a, b in info['missing_branches'])
    print(f'{rel}: {pct:.1f}% | missing lines: {missing} | missing branches: {branches}')
for rel in changed_rel:
    if rel not in matched:
        print(f'{rel}: 0.0% | not exercised by any test in this run (Untested unless vendored/one-time/generated)')
"
rm -f "$REPORT"
`

---

1. If any ERROR lines appeared in the detect block, stop and report them to the user. Do not proceed.

2. Parse the coverage output. For each changed source file, record:
   - Line and branch coverage percentage
   - Specific uncovered lines and branches
   - Flag files below 85% coverage
   - Surface the specific uncovered lines/branches as a first-class finding per changed file, not only the 85% flag — say what is not exercised

3. Build the source-to-test mapping from the detect block's REFERENCE-based
   discovery (exact `test_<stem>.py`, `test_*<stem>*.py` variants, and any test
   file importing/mentioning the module path or basename) — NOT a bare basename
   guess. A filename convention alone silently misses suffix-named tests
   (`test_foo_engine.py`) and feature-named tests, producing false "Untested".
   Coverage, not the filename, decides whether a file is exercised:
   - **Untested = the coverage report shows the changed file at 0% or "not
     exercised by any test in this run"** — flag it, BUT provenance-calibrated:
     do not flag vendored / one-time / generated source (`vendor/`,
     `third_party/`, `generated/`, or a docstring saying "one-time"), which
     legitimately have no tests.
   - A changed file with >0% coverage IS tested; hand its discovered test
     file(s) to the mutation-gap subagents even when the filename does not match
     the source basename.
   - Unchanged source files are out of scope — do not analyze them.

4. For each changed source file that has a corresponding test file, spawn PARALLEL subagents to identify mutation gaps across multiple files at the same time. Pass each subagent:
   - The functions or classes from the source file that contain changed lines
     (extract the minimal enclosing function/class for each diff hunk — not
     the full file). Include imports and module-level constants only if needed
     to understand the changed code.
   - The branch diff for that file (to identify the specific changed lines)
   - The full contents of its corresponding test file(s)
   - The uncovered lines and missing branches for that file from the coverage report
   - The following environment variables: SRC, TESTS

   Instruct each subagent to identify behavioral gaps — functions or branches where existing assertions would not fail if a single mutation was applied (flipped comparison, changed boolean operator, removed a condition, swapped arithmetic operator, changed a return value). For each gap found, produce a candidate entry in this format:

       GAP: <one sentence describing the behavioral case not currently pinned>
       MUTATION THAT WOULD SURVIVE: <what change to the source would not be caught>
       DISPOSITION: new_test | strengthen_existing
         new_test: this case has no natural home in existing tests
         strengthen_existing: an existing test covers this area but its assertion is
           too weak; name the specific existing test and describe how to strengthen it
       CANDIDATE:
         <test code matching the style of the existing test file>

   Candidates must match the testing style of the existing test files (detect from the file: pytest-style
   plain assert functions/classes, or unittest.TestCase subclasses). Do not change the import style
   already used in the test file.

   Instruct each subagent:
   - Only analyze mutation gaps in functions or branches that overlap with the diff. Unchanged code is out of scope even if it has coverage gaps.
   - Only assert observable outputs, raised exceptions, or side effects — not implementation details or internal state
   - Do not rewrite or duplicate existing tests
   - Do not add error handling for scenarios that cannot happen
   - Do not add type annotations, docstrings, or comments
   - Patch lazy imports (imported inside a function body) at the source package, not the calling module - the calling module never binds the name
   - For each gap, describe the specific input or state that would expose the weakness
   - Report at most 5 mutation gaps per source file. If more exist, keep the 5 most likely to mask a real bug and note "plus N additional gaps omitted:" along with file:line of each omitted gap.
   - If no meaningful gaps exist, return: NO GAPS FOUND

5. Spawn a single subagent to review the test files corresponding to changed source files. Pass it those test file contents and the same scoped source context used in step 4 (the enclosing functions/classes for changed lines — same scope rules), plus the candidate-dead-test list from the **Removed code** section above. Ask it to identify:

   - **Tautological** — assertion cannot fail regardless of whether the code under test is correct (asserting a value the test itself computed, asserting a value determined entirely by mock setup rather than code logic, asserting only that no exception was raised when a return value is assertable, asserting shape or type when actual values are accessible and meaningful)
   - **Redundant** — would pass or fail for the exact same reason as another test; removing it loses no unique behavioral coverage
   - **Missing error paths** — exception or error branches visible in the source with no corresponding test
   - **Dead (removed-code)** — the test references a symbol or module removed in this diff (see the candidate-dead-test list): it now errors on import/call, or still runs but asserts nothing meaningful. Classify broken vs vacuous.
   - **Obsolete / superseded** — the test exercises behavior that no longer exists, or is fully superseded by a newer test (same coverage, no unique assertion)

   Instruct the subagent: flag only cases where a test either cannot fail or provides zero unique coverage. Do not flag style, naming, or organizational issues.

   Output format per finding:

       [TAUTOLOGICAL | REDUNDANT | MISSING ERROR PATH | DEAD | OBSOLETE] test_file.py::TestClass::test_name
       REASON: <one sentence>
       FIX: strengthen assertion | remove test | add test for: <description>

6. Review the output from step 4 and step 5 subagents yourself, do not pass the raw subagent outputs to the user. Evaluate each finding and coverage gap, discard anything you judge to be noise or not worth acting on, and present only your curated assessment:

   **Scope**: N source files changed, M with corresponding test files

   **Findings** (only include sections that have findings)

   For each finding you kept, show:
   - What the issue is (one line)
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
   - Dead tests (reference removed code) worth fixing/removing: N
   - Obsolete/superseded tests worth removing: N

7. Do not modify any files. Do not commit anything. Present findings only and wait for explicit instruction.
