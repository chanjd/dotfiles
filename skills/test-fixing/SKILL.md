---
name: test-fixing
description: Systematically fix all failing tests using smart error grouping. Use when tests are failing or CI is broken.
---

# Test Fixing

Systematically identify and fix all failing tests.

## Steps

### 1. Run the full test suite

Use the project's test command (`pytest`, `tox`, etc.) and identify all failures.

### 2. Group failures by root cause

- Import/module errors
- API or signature changes
- Logic bugs and assertion failures

Fix in that order — infrastructure failures often cause cascading failures that mask the real count.

### 3. Fix each group

For each group:
- Read the relevant code and recent changes (`git diff`)
- Make minimal, focused changes
- Run only the affected tests to verify the group passes before moving on

### 4. Final verification

Run the full suite. Verify no regressions and coverage is intact.

## Guidelines

- One group at a time — do not batch across groups
- Use TaskCreate/TaskUpdate to track groups if there are many
- Keep changes minimal — fix the failure, do not refactor surrounding code
- If a fix requires changing test expectations, confirm the behaviour change is intentional
