---
name: review-pr
description: Lint all Python files changed on the branch, then review the full branch diff via subagent before opening a PR.
disable-model-invocation: false
---

## Lint

!`BASE=$(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master); git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | xargs -r ruff format 2>&1; git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -E '\.py$' | xargs -r ruff check --fix 2>&1`

## Branch diff

!`git diff $(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master)..HEAD -- $(git diff --name-only --diff-filter=ACM $(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master)..HEAD | grep -Ev '\.(yml|yaml|md|cfg|txt|ipynb|toml|rst|json)$')`

## Conventions

!`cat ~/.claude/CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md found)"`

---

1. If ruff made any changes to files, commit them before proceeding.

2. Spawn a Sonnet subagent to review the diff. Pass it the full diff and conventions. Ask it to identify:
   - Bugs or logic errors
   - Violations of the conventions
   - Missing error handling at system boundaries

   Instruct the subagent: do not flag style issues enforced by ruff, do not suggest removing working intentional code, do not suggest deprecation cleanups or stylistic rewrites — only flag bugs and clear convention violations.

3. Review the subagent's report critically. For each finding, categorize it as:
   - **Bug** — incorrect behavior
   - **Convention violation** — clear rule broken per CLAUDE.md
   - **Opinion** — stylistic preference or debatable change

4. Present the categorized summary to the user. Do not make any changes until the user explicitly instructs you to.
