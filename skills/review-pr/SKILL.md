---
name: review-pr
description: Review the full branch diff via subagent before opening a PR. Ruff linting is handled automatically by hooks on commit.
disable-model-invocation: false
---

## Fetch latest remote

!`git fetch origin 2>&1`

## Branch diff

!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); git diff $BASE..HEAD -- $(git diff --name-only --diff-filter=ACM $BASE..HEAD | grep -Ev '\.(yml|yaml|md|cfg|txt|ipynb|toml|rst|json)$')`

## Conventions

!`cat ~/.claude/CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md found)"`

---

1. Spawn a Sonnet subagent to review the diff. Pass it the full diff and conventions. Ask it to identify:
   - Bugs or logic errors
   - Violations of the conventions
   - Missing error handling at system boundaries
   - Abstractions or helpers introduced in this diff with only one caller
   - Derived state stored as a variable or field when it could be computed from existing state
   - Functions or methods whose signature or return shape changed, where callers outside this diff are not updated

   Instruct the subagent: do not flag style issues enforced by ruff, do not suggest removing working intentional code, do not suggest deprecation cleanups or stylistic rewrites — only flag bugs and clear convention violations.

2. Review the subagent's report. Categorize each finding as:
   - **Bug** — incorrect behavior or likely runtime error
   - **Convention violation** — explicit rule broken per CLAUDE.md
   - **Opinion** — anything else; discard these silently

3. Present only Bugs and Convention violations to the user. Do not make any changes until the user explicitly instructs you to.
