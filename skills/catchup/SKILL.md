---
name: catchup
description: Resume at session start — read the RESUME handoff + relevant memory, verify against live state
disable-model-invocation: true
---

## Memory key

This environment is not necessarily a git repo. Anchor memory on the home
directory key, not the git root.

!`echo "Memory dir: $HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"`

## RESUME handoff (from the most-recently-checkpointed topic file)

!`MEMDIR="$HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"; NEWEST=$(ls -1t "$MEMDIR"/*.md 2>/dev/null | grep -v '/MEMORY.md$' | head -1); if [ -n "$NEWEST" ]; then if grep -q '^## RESUME' "$NEWEST"; then echo "(from $(basename "$NEWEST"))"; awk '/^## RESUME/{f=1;print;next} f&&/^## /{exit} f{print}' "$NEWEST" | head -40; else echo "(newest topic file $(basename "$NEWEST") has no RESUME block — fall back to the index + topic files below)"; fi; else echo "(no topic files)"; fi`

## MEMORY.md index

!`MEMDIR="$HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"; cat "$MEMDIR/MEMORY.md" 2>/dev/null || echo "(no MEMORY.md found)"`

## Memory topic files (newest first)

!`MEMDIR="$HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"; ls -1t "$MEMDIR" 2>/dev/null | grep -v '^MEMORY.md$' || echo "(none)"`

## Optional git state (only if cwd is a repo)

!`git rev-parse --show-toplevel >/dev/null 2>&1 && { echo "Branch: $(git branch --show-current)"; echo "Recent: $(git log --oneline -10 | tr '\n' '; ')"; echo "Status:"; git status --short; } || echo "(not a git repo — skip)"`

## Optional agents file (only if present in cwd repo)

!`ROOT=$(git rev-parse --show-toplevel 2>/dev/null); AGENTS="$ROOT/AGENTS.md"; [ -f "$AGENTS" ] && cat "$AGENTS" || echo "(no agents file — auto-memory is the source of truth here)"`

---

Resume work. The auto-memory above (RESUME handoff + MEMORY.md + topic files) is
the primary source of truth here, not git/agents files. This is the read half of
the `catchup` / `summarize` pair; `summarize` writes the RESUME block.

1. **Scope the session to one project** (this matters under concurrent
   terminals — all top-level sessions on this user share ONE memory dir):
   - **If the user named a task/project** (usual form
     `/catchup <what I want to work on this session>`), that is the session
     scope: focus on that project's topic file and its RESUME block.
   - **If they named nothing**, the newest-file RESUME block above is only a
     *heuristic* pick — with concurrent sessions the most-recently-modified file
     may belong to a DIFFERENT terminal's project, not yours. Do not assume it.
     Say which project it points to, confirm it is the one the user wants, and if
     that is unclear, ask before leaning on it.
   - Until the scope is a single, confirmed project, treat this session as
     **unscoped**: its eventual `summarize` must run **additive-only** (write the
     RESUME block + add new facts, prune nothing), so it cannot destructively
     edit a project another terminal is actively working on. See `summarize`
     step 2's scope gate.
   - **If the chosen project's RESUME has multiple `### <thread>` sub-blocks**
     (parallel features/experiments), scope further to the thread being picked
     up: focus on that thread's sub-block and read the siblings only for context.
     If no thread was named and several exist, list them and ask which. `summarize`
     will then update ONLY that thread's sub-block and leave the siblings verbatim,
     so resuming one thread never clears the others.
2. Read the relevant topic files in full (not just the index) for the target
   project — the RESUME block is the live thread; the topic file body is the
   durable detail behind it.
3. **Memory is point-in-time and may lag the code.** Before relying on any
   load-bearing fact (a file path, function/flag name, data statistic, or a
   "next action" from the RESUME block), verify it against current file/repo
   state. Treat RESUME-block and recalled facts as unverified until checked.
   Flag any conflict between memory and what you observe now.
4. Summarize concisely: where the project stands (done vs in-progress), the
   concrete next action, and any conflicts you found. If cwd is a git repo, fold
   in branch/status. Then proceed with the task the user named.
