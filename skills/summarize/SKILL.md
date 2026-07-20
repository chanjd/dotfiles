---
name: summarize
description: Checkpoint the session into auto-memory (a RESUME handoff block + durable updates) so it can be resumed after /clear or /compact. Invoke ONLY when the user explicitly asks to checkpoint/summarize/save state, or says they are about to /clear or /compact. Do NOT invoke proactively mid-task.
---

## Memory key

This environment is not necessarily a git repo. Anchor memory on the home
directory key, not the git root.

!`echo "Memory dir: $HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"`

## Current MEMORY.md

!`MEMDIR="$HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"; cat "$MEMDIR/MEMORY.md" 2>/dev/null || echo "(no MEMORY.md found)"`

## Memory topic files (newest first — the top one is likely the active thread)

!`MEMDIR="$HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"; ls -1t "$MEMDIR" 2>/dev/null | grep -v '^MEMORY.md$' || echo "(none)"`

## Optional git state (only if cwd is a repo)

!`git rev-parse --show-toplevel >/dev/null 2>&1 && { echo "Branch: $(git branch --show-current)"; echo "Recent: $(git log --oneline -5 | tr '\n' '; ')"; echo "Status:"; git status --short; } || echo "(not a git repo — skip)"`

---

Checkpoint this session so a future session can resume it losslessly after a
`/clear` (or so a `/compact` can drop the transcript without losing the thread).
The conversation history is the source of truth — do not speculate. This is the
write half of the `catchup` / `summarize` pair; `catchup` reads what you write.

Do two things, in order.

### 1. Write the RESUME handoff (the part that makes `/clear` safe)

Memory topic files record durable *conclusions*; they do NOT capture the live
reasoning thread of the task in flight — which is exactly what is lost on a
`/clear`. Capture it now.

Identify the active project (what this session actually worked on — use cwd, git,
and the topic file that matches). At the **top of that project's topic file**,
maintain a `## RESUME` block (create it if absent, **overwrite it if present** —
it is a live pointer, not accumulating history):

```
## RESUME (updated <YYYY-MM-DD>)
- State: what is done this session; what is in progress right now.
- Next: the single most concrete next action (command/file/decision), then others.
- Decisions this session + WHY: the reasoning a fresh session could not re-derive.
- Open questions / in flight: anything unresolved or waiting (jobs, reviews).
- Gotchas: commands, paths, flags that worked or bit us this session.
```

Keep it tight and load-bearing. Prefer **pointers to re-verifiable ground truth**
(file paths, function names, artifact/run locations, commit SHAs) over prose
restatements of facts — a pointer survives paraphrase; a restated fact can drift.
Writing this block also makes that topic file the most-recently-modified, so
`catchup` finds it first.

### 2. Update durable memory for anything that changed

For each memory type that changed this session (user, project, feedback,
reference), update the relevant topic file, or create one with proper frontmatter
(`name`, `description`, `metadata.type`). For feedback/project entries lead with
the rule/fact, then **Why:** and **How to apply:** lines. Link related memories
with `[[name]]`.

- Keep `MEMORY.md` a terse pointer index — one line per entry, no frontmatter,
  title + one-line hook, under ~150 chars. It is loaded EVERY session, so detail
  belongs in the topic file, NOT the index. Add pointers for new topic files; fix
  stale lines; do not let an index line grow into a paragraph.
- **Prune on touch — but only with positive evidence, never on suspicion.**
  In files you edit this session, replace/remove a line ONLY when THIS session
  produced something that supersedes or disproves it. Age or vague "looks stale"
  is NOT sufficient — when unsure, leave it. A topic file should read as current
  state, not a changelog, but a wrong deletion loses more than a stale line costs.
  Two tiers:
  - Volatile content (the `## RESUME` block, "current status" lines, OPEN/NEXT
    markers) — overwrite freely; it is meant to be replaced.
  - Durable facts (findings, data stats, decisions, gotchas) — prefer UPDATE in
    place over delete; delete only what this session proved wrong.
  Update the matching `MEMORY.md` index line so it still summarizes the file.
- **Report the prune.** In your closing message, list what you removed or
  replaced (file: what/why) so the user can catch an over-prune immediately.
- Do NOT save what is derivable from current file state, git history, or
  CLAUDE.md. Only record what is non-obvious and useful for future sessions.
- If cwd is a git repo AND an `AGENTS.md` exists, update its "Current Branch" /
  "Next" sections. If it does not exist, skip — do not create one.

After writing, commit the snapshot so every checkpoint is a recoverable restore
point (the memory dir is a local-only git repo — an over-prune is always
`git -C <memdir> diff`/`checkout`-recoverable):

    git -C <memdir> add -A && git -C <memdir> commit -q -m "checkpoint: <active project>, <date>" || true

Then tell the user it is safe to `/clear` (or `/compact`), name the topic file
holding the RESUME block, and report what you pruned.
