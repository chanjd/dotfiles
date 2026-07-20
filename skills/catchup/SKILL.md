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

1. **If the user named a task/project in their invocation** (this skill is
   usually invoked as `/catchup <what I want to work on this session>`), let that
   steer everything: focus on that project's topic file and its RESUME block. The
   newest-file RESUME block shown above is the default thread if they named none —
   confirm it matches what they asked for before leaning on it.
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
