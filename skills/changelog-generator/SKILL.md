---
name: changelog-generator
description: Generate a user-facing changelog entry from git commits. Invoke when a feature branch is about to be merged.
---

# Changelog Generator

Generate a clear, user-facing changelog entry from git commit history on the current branch.

## Steps

1. Identify commits on this branch since diverging from the base branch:

!`git log $(git merge-base HEAD main 2>/dev/null || git merge-base HEAD master)..HEAD --oneline`

2. Categorize commits into:
   - New features
   - Improvements
   - Bug fixes
   - Breaking changes (if any)

3. Rewrite each commit as a plain-English user-facing line — no internal jargon, no commit SHAs.

4. Format as a markdown section using today's date and the branch/feature name.

5. Append the entry to `CHANGELOG.md` at the repo root, below the header and above any previous entries.

## Output format

```markdown
## [unreleased] — YYYY-MM-DD — <feature name>

### New Features
- ...

### Improvements
- ...

### Bug Fixes
- ...
```

Omit sections with no entries. For tagged releases, entries can be manually condensed and the `[unreleased]` label replaced with the version number.
