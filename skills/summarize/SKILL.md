---
name: summarize
description: Update catchup files with current session state before context reset
disable-model-invocation: true
---

## Current agent context

!`ROOT=$(git rev-parse --show-toplevel 2>/dev/null); AGENTS=$([ -f "$ROOT/.ona/agents.md" ] && echo "$ROOT/.ona/agents.md" || echo "$ROOT/AGENTS.md"); [ -f "$AGENTS" ] && cat "$AGENTS" || echo "(no agents file found)"`

## Current MEMORY.md

!`MEMORY_KEY=$(git rev-parse --show-toplevel 2>/dev/null | tr '/' '-'); cat "$HOME/.claude/projects/$MEMORY_KEY/memory/MEMORY.md" 2>/dev/null || echo "(no memory file found)"`

## Git state

- Branch: !`git rev-parse --show-toplevel 2>/dev/null | xargs -I{} git -C {} branch --show-current`
- Recent commits: !`git rev-parse --show-toplevel 2>/dev/null | xargs -I{} git -C {} log --oneline -5`
- Status: !`git rev-parse --show-toplevel 2>/dev/null | xargs -I{} git -C {} status --short`

---

Update the two catchup files to reflect what actually happened this session. Use the conversation history as the source of truth — do not speculate.

1. Rewrite the agents file:
   - Update "Current Branch" section: what is complete, what is in-progress
   - Update "Next" section: concrete next actions based on this session
   - Update any other sections that changed this session

2. Update MEMORY.md if any of the following changed:
   - Key architectural decisions or patterns
   - Bugs discovered or confirmed
   - Corrections to existing memory entries

Be concise. Do not add entries for things that did not happen this session. Do not duplicate what is already accurate in the files.
