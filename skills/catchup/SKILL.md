---
name: catchup
description: Summarize current winery project state at session start
disable-model-invocation: true
---

## Git state

- Branch: !`git -C /workspaces/winery branch --show-current`
- Recent commits: !`git -C /workspaces/winery log --oneline -10`
- Status: !`git -C /workspaces/winery status --short`

## Agent context

!`cat /workspaces/winery/.ona/agents.md`

---

Summarize the current session state concisely:
1. Which branch and what work is on it (complete vs in-progress)
2. Next actions
