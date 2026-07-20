#!/usr/bin/env bash
# Self-bootstrapping, concurrency-safe commit for the auto-memory dir.
#
# The memory dir is a local-only git repo (no remote — memory holds private
# content) that is the over-prune recovery net for the summarize / memory-audit
# skills. Multiple top-level Claude Code sessions on one user share ONE such
# repo, so this helper is built to be safe under concurrent callers:
#   - it git-inits the repo (with a local identity) on first use;
#   - it serializes add+commit behind an flock so racing callers queue instead
#     of colliding on .git/index.lock;
#   - it retries a lock-lost commit, then verifies HEAD actually advanced and
#     reports failure loudly (exit 1) instead of silently dropping the
#     checkpoint.
#
# Usage: memory_git.sh <memdir> "<commit message>"

set -u

memdir="${1:-}"
msg="${2:-memory checkpoint}"

if [ -z "$memdir" ] || [ ! -d "$memdir" ]; then
    echo "memory_git: dir not found: '$memdir' — skipping commit" >&2
    exit 0
fi

# Ensure the repo exists before locking inside it. `git init` is idempotent, so a
# concurrent first-run double-init is harmless. Check for $memdir's OWN .git (not
# `rev-parse --is-inside-work-tree`, which is also true when $memdir merely sits
# inside a parent repo — that would leak private memory into the parent).
if [ ! -d "$memdir/.git" ]; then
    git -C "$memdir" init -q
    git -C "$memdir" symbolic-ref HEAD refs/heads/main 2>/dev/null || true
    git -C "$memdir" config user.name "claude-memory"
    git -C "$memdir" config user.email "claude-memory@localhost"
    echo "memory_git: initialized local-only repo at $memdir" >&2
fi

commit_memory() {
    before=$(git -C "$memdir" rev-parse HEAD 2>/dev/null || echo none)

    git -C "$memdir" add -A
    if git -C "$memdir" diff --cached --quiet 2>/dev/null; then
        echo "memory_git: nothing to commit" >&2
        return 0
    fi

    n=0
    while [ "$n" -lt 5 ]; do
        git -C "$memdir" commit -q -m "$msg" && break
        n=$((n + 1))
        sleep 0.3
    done

    # Before/after check: confirm the commit actually landed. HEAD unchanged with
    # staged changes means every attempt lost the lock — surface it, don't hide it.
    after=$(git -C "$memdir" rev-parse HEAD 2>/dev/null || echo none)
    if [ "$before" = "$after" ]; then
        echo "memory_git: FAILED to commit after $n retries — checkpoint NOT saved for '$memdir'" >&2
        return 1
    fi
    echo "memory_git: committed ${after:0:9}" >&2
    return 0
}

# Serialize concurrent callers. The lock lives inside .git so `add -A` never
# stages it. flock when available; without it, the retry loop above still
# recovers from a lock race, just without queueing.
lock="$memdir/.git/mg.lock"
if command -v flock >/dev/null 2>&1; then
    exec 9>"$lock"
    flock 9
    commit_memory
    exit $?
fi
commit_memory
exit $?
