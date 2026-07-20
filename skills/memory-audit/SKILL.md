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

**First, snapshot** so the whole sweep is recoverable (the memory dir is a
local-only git repo):

    git -C <memdir> add -A && git -C <memdir> commit -q -m "memory: pre-audit snapshot" || true

Then act by tier — the dividing line is *information loss*, not effort:

- **Tier A — auto, no confirmation (consistency fixes, nothing is lost):**
  - Files not in `MEMORY.md` → add a one-line index entry (<~150 chars, accurate).
  - Index link → a file that no longer exists → remove the dangling pointer.
  - Dead `[[wikilinks]]` → repoint to the right slug, or de-bracket if the target
    is a skill/external thing (not a memory). Leave as a forward ref only if you
    will create that memory now.
  - **Bloated `MEMORY.md` index lines** (flagged over ~200 chars; convention is
    ~150). `MEMORY.md` is loaded EVERY session, so it must be a terse pointer
    index — title + one-line hook — with detail in the topic file. Condense each
    over-long line to a pointer, but FIRST confirm the detail it carries already
    lives in the topic file body; if the index is the only place that detail
    exists, migrate it into the file before trimming (that migration step is the
    only reason this isn't purely mechanical — done right, nothing is lost).
  These fix pointers/bloat; they do not delete knowledge, so just do them.

- **Tier B — auto only WITH proof, then report (evidence-gated):**
  - The OPEN/DEFERRED/PAUSED/SHELVED/TODO/NEXT markers were true when written but
    may be resolved. Spawn ONE **Sonnet** subagent to read the flagged files and
    check the referenced repos/paths/git, returning per marker:
    still-true / resolved / superseded, each with concrete evidence.
  - Drop a marker or fact ONLY when the subagent gives positive evidence it is
    resolved/superseded (e.g. git shows the DEFERRED PR merged). Collapse a
    changelog stack (old fact + its correction) into the single current line.
    Update the matching index line. No evidence → it becomes Tier C, do not guess.

- **Tier C — confirm with the user first (destructive or unprovable):**
  - Deleting an entire memory file.
  - Removing any fact/marker you could NOT verify as resolved.
  - Any collapse where information might be lost.
  List these with your reasoning and ask before touching them.

**Finally:** commit the cleaned state (`git -C <memdir> commit -am "memory: audit cleanup"`)
and report concisely — what you auto-fixed (A), what you pruned with evidence (B),
and what you are asking about (C). If anything looks wrong afterward,
`git -C <memdir> diff HEAD~1` shows exactly what changed.

Tip: for hands-off hygiene, schedule a weekly cron running this in report-only
mode (Tiers surfaced, nothing applied) — but keep any deletion attended.
