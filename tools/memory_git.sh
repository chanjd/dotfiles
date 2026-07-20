#!/usr/bin/env bash
# Self-bootstrapping commit for the auto-memory dir.
#
# The memory dir is a local-only git repo (no remote — memory holds private
# content) that acts as the over-prune recovery net for the summarize /
# memory-audit skills. On a fresh machine that repo was never initialized, so a
# bare `git commit` silently does nothing and the net doesn't exist. This helper
# initializes the repo (with a local identity, so it works with no global git
# config) the first time, then commits — idempotent on every later call.
#
# Usage: memory_git.sh <memdir> "<commit message>"

set -u

memdir="${1:-}"
msg="${2:-memory checkpoint}"

if [ -z "$memdir" ] || [ ! -d "$memdir" ]; then
    echo "memory_git: dir not found: '$memdir' — skipping commit" >&2
    exit 0
fi

# Check for $memdir's OWN .git, not `rev-parse --is-inside-work-tree`: the latter
# is true when $memdir merely sits inside a parent repo, which would make the
# commit below land in that parent (leaking private memory into e.g. a home repo).
if [ ! -d "$memdir/.git" ]; then
    git -C "$memdir" init -q
    git -C "$memdir" config user.name "claude-memory"
    git -C "$memdir" config user.email "claude-memory@localhost"
    echo "memory_git: initialized local-only repo at $memdir" >&2
fi

git -C "$memdir" add -A
git -C "$memdir" commit -q -m "$msg" || true
