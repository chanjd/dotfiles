## Behavioral Defaults

### Plan Mode
- Enter plan mode for any non-trivial task (3+ steps or architectural decisions)
- If something goes sideways, stop and re-plan — do not keep pushing
- Write detailed specs upfront to reduce ambiguity
- Use plan mode for verification steps, not just building

### Subagent Strategy
- Delegate vs inline by context hygiene — default to delegating any step whose OUTPUT you'd skim, not keep (whole-file or multi-file reads, wide greps, long logs, exploration) to a subagent that returns only the conclusion. Keep the judgment spine (intent, design, contracts, done-call) inline; don't delegate small/quick lookups (overhead > savings) or detail you need for ongoing judgment.
- Sonnet is the default; set the model explicitly (subagents inherit the session model otherwise) and adjust by difficulty — Haiku for trivial retrieval/format, Opus only for the hardest reasoning/audit.
- Explore agents especially: they default to the current session model (Opus here), so always pass an explicit model — usually Sonnet; Opus only when you must distrust stated info (messy repo, stale or contradictory notes).
- Give a subagent good input: point it at files it reads itself (don't paste); state the blast radius + goal. A well-scoped Sonnet beats a narrow-scope Opus.
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
- Smoke-test the real entrypoint end-to-end, not a hand-built proxy of its parts
- Ask: "Would a staff engineer approve this?"

### Demand Elegance (Balanced)
- For non-trivial changes: pause and ask "is there a more elegant way?"
- If a fix feels hacky, implement the clean solution instead
- Skip this for simple, obvious fixes — do not over-engineer

### Autonomous Bug Fixing
- When given a bug report: fix it without asking for hand-holding
- Use logs, errors, and failing tests to find root cause
- Fix failing CI without being told how

### Reasoning & Communication
- Verify before asserting — for load-bearing facts, including when answering questions about project state or recalling something, check the actual file/data/live state, not memory or an adjacent function. Tag claims as verified vs inferred.
- Push back with reasoning; don't just execute. Lead with a recommendation + the main tradeoff; name category errors or wrong premises.
- Hypothesize the mechanism before running a significance test — a mechanism verified cheaply in code usually beats a CI.
- Clarifying questions: popups are fine when they allow free-text ("Other"); use prose for open or underspecified decisions.
- Long or slow work goes to the scheduler/background, not a foreground poll; rely on a watcher/notification.
- Structured + versioned over one-offs: edit the reproducible harness, commit to a topic branch with decision records, lock inputs as files.
- Reports/decks: every number traces to a committed artifact at the same protocol; one concept per slide; plain words over jargon.

---

## Universal Conventions

- No emojis or decorative symbols — not in code, not in docs, not in responses
- Be concise: answer what's asked; no tangential "also worth noting" pile-ons; no reflexive compliments or affirmations ("Great question", "You're absolutely right", "Good catch")
- No Co-Authored-By or author trailer lines in commit messages
- Bullet points over tables in markdown
- No docstrings, comments, or type annotations added to code that was not changed
- Do not add error handling or validation for scenarios that cannot happen
- Do not create helpers or abstractions for one-time operations
- Simplicity first: minimum complexity needed for the current task
- Find root causes — no temporary fixes, no backwards-compatibility hacks for dead code
