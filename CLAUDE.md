## Behavioral Defaults

### Plan Mode
- Enter plan mode for any non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, stop and re-plan — do not keep pushing
- Write detailed specs upfront to reduce ambiguity
- Use plan mode for verification steps, not just building

### Subagent Strategy
- Use subagents to keep the main context window clean
- Offload research, exploration, and parallel analysis to subagents
- One task per subagent for focused execution
- Model selection:
  - Sonnet — default for most subagents (coding, research, moderate reasoning)
  - Opus — hard reasoning only (architecture, complex planning, subtle debugging)
  - Haiku — simple or parallelizable tasks (lookups, classification, formatting)
- Use `isolation: "worktree"` only when the subagent will make code changes that could conflict with the main working tree; skip it for read-only subagents

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
