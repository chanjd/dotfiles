---
name: catchup
description: Summarize current project state at session start
disable-model-invocation: true
---

## Git state

- Branch: !`git rev-parse --show-toplevel 2>/dev/null | xargs -I{} git -C {} branch --show-current`
- Recent commits: !`git rev-parse --show-toplevel 2>/dev/null | xargs -I{} git -C {} log --oneline -10`
- Status: !`git rev-parse --show-toplevel 2>/dev/null | xargs -I{} git -C {} status --short`

## Agent context

!`ROOT=$(git rev-parse --show-toplevel 2>/dev/null); AGENTS=$([ -f "$ROOT/.ona/agents.md" ] && echo "$ROOT/.ona/agents.md" || echo "$ROOT/AGENTS.md"); [ -f "$AGENTS" ] && cat "$AGENTS" || echo "(no agents file found)"`

## Memory

!`MEMORY_KEY=$(git rev-parse --show-toplevel 2>/dev/null | tr '/' '-'); cat "$HOME/.claude/projects/$MEMORY_KEY/memory/MEMORY.md" 2>/dev/null || echo "(no memory file found)"`

---

Summarize the current session state concisely:
1. Which branch and what work is on it (complete vs in-progress)
2. Next actions
