---
name: review-pr
description: Review the full branch diff via subagent before opening a PR. Ruff linting is handled automatically by hooks on commit.
disable-model-invocation: false
---

## Fetch latest remote
!`git fetch origin 2>&1`

## Branch diff
!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); git diff $BASE..HEAD -- $(git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -Ev '\.(yml|yaml|md|cfg|txt|ipynb|toml|rst|json|tsv|csv)$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)')`

## Full changed files
!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); for f in $(git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -Ev '\.(yml|yaml|md|cfg|txt|ipynb|toml|rst|json|tsv|csv)$' | grep -Ev '(^tests/|^test/|/tests/|/test/|test_.*\.py$|_test\.py$|conftest\.py$)'); do echo "=== $f ==="; git show HEAD: "$f"; done

## Conventions
!`cat ~/.claude/CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md found)"`

## Project context
Search for project-level design docs, architecture notes, or specs relevant to the files changed in this diff/feature branch. 
1. Check memory files for references to relevant documentation.
2. If memory doesn't point to anything, check in files like AGENTS.md, CLAUDE.md, plans dir, and any markdown files in the repo root or docs/ directory. Pass whatever you find that is relevant to Agent 2.
If nothing relevant exists or if you judge the feature branch to be very simple, skip Agent 2 and run Agent 1 only.

---

1. Spawn Agent 1 (Sonnet subagent) - correctness review. Pass it the branch diff and conventions only. Ask it to identify:
   - Bugs or logic errors
   - Violations of the conventions
   - Missing error handling at system boundaries
   - Abstractions or helpers introduced in this diff with only one caller
   - Derived state stored as a variable or field when it could be computed from existing state

   Instruct Agent 1:
   - Do not flag style issues enforced by ruff
   - Do not suggest removing working intentional code
   - Do not suggest deprecation cleanups or stylistic rewrites
   - Before reporting a bug, use grep or read to trace callers and verify the bug actually manifests - do not report based on pattern matching alone
   - Output format per finding (strict):
     [BUG|VIOLATION] file:line - description
     Trace: caller() -> callee() - one-line explanation of how the bug manifests
   - If no bugs or violations found, output: "No issues found."

2. Spawn Agent 2 (Sonnet subagent) - architectural review. Pass it the full changed files and project context. Ask it to identify:
   - Functions or methods whose signature or return shape changed, where callers outside this diff are not updated
   - Implementation that contradicts the design intent described in project context
   - Integration issues: changed contracts, missing updates to related modules, broken assumptions in code that imports from changed files

   Instruct Agent 2:
   - Use grep to find callers of changed functions outside the diff before reporting a contract break
   - Do not duplicate correctness findings - assume Agent 1 handles line-level bugs
   - Output format per finding (strict):
     [CONTRACT_BREAK|DESIGN_MISMATCH] file:line - description
     Evidence: file:line where the broken caller/consumer lives
   - If implementation matches design and no contract breaks found, output: "No issues found."

3. Merge both agents' outputs:
   - If agents disagree (Agent 1 says bug, Agent 2 says intentional per design), prefer Agent 2
   - Present the merged list to the user, grouped by catagory
   - Do not make any changes until the user explicitly instructs you to
