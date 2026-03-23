---
name: lint
description: Run ruff format and lint checks on staged Python files before committing. Use before every commit.
disable-model-invocation: false
---

## Staged Python files

!`git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || echo "(none)"`

## Ruff output

!`git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | xargs -r ruff format 2>&1; git diff --cached --name-only --diff-filter=ACM | grep '\.py$' | xargs -r ruff check --fix 2>&1 || echo "(no staged Python files)"`

---

Review the ruff output above.

1. **Fix any remaining ruff violations** that `--fix` could not auto-resolve.

2. **Re-stage any files you modified** (`git add <file>`) so the commit includes the fixes.

Report what was changed and confirm the files are ready to commit.
