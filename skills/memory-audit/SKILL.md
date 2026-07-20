---
name: memory-audit
description: Sweep the auto-memory corpus for stale trails and clean them up — dead links, index drift, resolved-but-open markers, superseded facts. Run periodically or when memory feels cluttered.
disable-model-invocation: true
---

## Memory key

!`echo "Memory dir: $HOME/.claude/projects/$(echo "$HOME" | tr '/' '-')/memory"`

## Mechanical staleness signals

!`python3 "$HOME/.claude/tools/memory_audit.py" 2>/dev/null || echo "(memory_audit.py missing)"`

---

Clean up the memory corpus using the signals above. Memory accrues stale trails
because sessions append faster than they prune; this sweep is the counterweight
to the per-session prune-on-touch that `summarize` does. Goal: every file reads
as **current state**, not an archaeological record. Keep the main context clean
by delegating the heavy reading.

**Run this solo.** It rewrites the whole corpus and acts on a snapshot; if other
top-level terminals are checkpointing into the same memory dir concurrently, it
will act on stale state and its commit may sweep in their in-flight edits. Run it
when the other sessions are idle or closed.

**First, snapshot** so the whole sweep is recoverable (the memory dir is a
local-only git repo; the helper initializes it on first use):

    ~/.claude/tools/memory_git.sh "<memdir>" "memory: pre-audit snapshot"

**Delegate the reading — keep this context clean.** The detector only *names* the
flagged files; do not read their bodies here. Fan out one proposer per flagged
file (in parallel), routed by task difficulty, each returning proposals only (no
edits — the orchestrator applies):

- **Haiku — straight read / summarize / format (no fact reconciliation):** write
  a one-line index entry (<~150 chars) for a file missing from `MEMORY.md`;
  condense a bloated index line (flagged >~200 chars) to a title + one-line hook,
  first confirming that detail already lives in the topic body (a lookup) and
  flagging it to migrate if the index is its only home; propose dead
  `[[wikilink]]` / index-link repoints (or de-bracket a skill/external target).
- **Sonnet — fact reconciliation against live state (Haiku is not enough here):**
  resolve the OPEN/DEFERRED/PAUSED/SHELVED/TODO/NEXT markers by checking the
  referenced repos/paths/git, returning per marker still-true / resolved /
  superseded + concrete evidence; and judge any changelog-stack collapse or
  Tier-C candidate where information could be lost.

One task per subagent; give each the file(s) to read itself, not pasted text.
Then apply by tier — the dividing line is *information loss*, not effort:

- **Tier A — auto, nothing lost:** apply the Haiku proposals (missing index
  entries, dangling-link removals, `[[wikilink]]` repoints, condensations). If a
  bloated line's detail is not already in the body, migrate it in before trimming;
  leave a `[[link]]` as a forward ref only if you will create that memory now.
  These fix pointers/bloat, not knowledge — just do them.
- **Tier B — auto only WITH proof:** drop a marker or fact ONLY on the Sonnet
  verifier's positive evidence it is resolved/superseded (e.g. git shows the
  DEFERRED PR merged). Collapse a changelog stack (old fact + its correction) into
  the single current line and update the matching index line. No evidence → it
  becomes Tier C; do not guess.
- **Tier C — confirm with the user first (destructive or unprovable):** deleting
  an entire memory file; removing any fact/marker you could NOT verify as
  resolved; any collapse where information might be lost. List these with your
  reasoning and ask before touching them.

**Finally:** commit the cleaned state (`~/.claude/tools/memory_git.sh "<memdir>" "memory: audit cleanup"`)
and report concisely — what you auto-fixed (A), what you pruned with evidence (B),
and what you are asking about (C). If anything looks wrong afterward,
`git -C <memdir> diff HEAD~1` shows exactly what changed.

Tip: for hands-off hygiene, schedule a weekly cron running this in report-only
mode (Tiers surfaced, nothing applied) — but keep any deletion attended.
