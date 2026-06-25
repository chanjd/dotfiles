## Behavioral Defaults

### Plan Mode
- Enter plan mode for any non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, stop and re-plan — do not keep pushing
- Write detailed specs upfront to reduce ambiguity
- Use plan mode for verification steps, not just building

### Subagent Strategy
- Two axes, decided per sub-task:
  - Delegate vs inline by context hygiene — offload bulky read/run/iterate work; keep the judgment spine (intent, design, contracts, done-call) inline.
  - Model by task difficulty, not by "it's a subagent":
    - Haiku — describe/lookup/format (verify its specifics — it guesses at gaps)
    - Sonnet — understand; default for coding, research, integration
    - Opus — audit: contract-break/completeness, subtle debugging, hard reasoning; reserve it
- Widen a subagent's INPUT before upgrading its model: point to files it reads itself (don't paste), give it the blast radius + goal. A well-scoped Sonnet beats a narrow-scope Opus.
- Each delegated result returns its conclusion + the cheapest way to verify it (trace for a bug, conformance+deviations for code, file:line cites for exploration); the subagent self-verifies the executable part first.
- One task per subagent. `isolation: "worktree"` only for subagents making conflicting code changes; skip for read-only.

### Memory and Lessons
- CLAUDE.md is for instructions and rules (written by the user)
- Auto memory (`MEMORY.md` + topic files) is for learnings Claude accumulates from corrections and project context
- After any correction: update memory files — do not create separate lessons files
- Review memory files at session start when catching up on a project

### Task Tracking
- Use TaskCreate/TaskUpdate tools for in-session multi-step tracking
- Do not maintain parallel todo.md files — single source of truth is the task tool
- Mark tasks in_progress before starting, completed only when fully done
- Check in before starting implementation on non-trivial plans

### Verification Before Done
- Never mark a task complete without proving it works
- Run tests, check logs, demonstrate correctness
- Ask: "Would a staff engineer approve this?"

### Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky, implement the clean solution instead
- Skip this for simple, obvious fixes — do not over-engineer

### Autonomous Bug Fixing
- When given a bug report: fix it without asking for hand-holding
- Use logs, errors, and failing tests to find root cause
- Fix failing CI without being told how

---

## Universal Conventions

- No emojis or decorative symbols — not in code, not in docs, not in responses
- No Co-Authored-By or author trailer lines in commit messages
- Bullet points over tables in markdown
- No docstrings, comments, or type annotations added to code that was not changed
- Do not add error handling or validation for scenarios that cannot happen
- Do not create helpers or abstractions for one-time operations
- Simplicity first: minimum complexity needed for the current task
- Find root causes — no temporary fixes, no backwards-compatibility hacks for dead code
