#!/usr/bin/env bash
# Slim, additive install. Only handles artifacts that cannot meaningfully
# conflict with local state: the helper tools, the statusline wrapper, and ruff.
#
# The conflict-prone artifacts (CLAUDE.md, settings.json, and the skills) are
# NOT touched here — a blind copy would clobber local edits or settings another
# tool manages. Reconcile those with an agent using INSTALL.md.
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Helper tools: statusline ctx indicator, token-cost report, memory-staleness
# audit, and the memory-git bootstrap. These are owned by dotfiles — safe to
# overwrite (additive: they are new files, not local config).
mkdir -p "$HOME/.claude/tools"
cp "$DOTFILES_DIR/tools/"*.py "$HOME/.claude/tools/"
cp "$DOTFILES_DIR/tools/"*.sh "$HOME/.claude/tools/"
chmod +x "$HOME/.claude/tools/"*.py "$HOME/.claude/tools/"*.sh
echo "Installed tools to ~/.claude/tools/"

# Statusline wrapper. Does NOT auto-wire settings.json (that is a reconcile step
# in INSTALL.md). An optional ~/.claude/statusline-left.local.sh (machine-local,
# untracked) can supply a left-hand segment; without it, only the context (and,
# in a git repo, the branch) indicator shows.
cp "$DOTFILES_DIR/my-statusline.sh" "$HOME/.claude/my-statusline.sh"
chmod +x "$HOME/.claude/my-statusline.sh"
echo "Installed my-statusline.sh"

# Git pre-commit hook (dotfiles-owned, additive). Placing the file is safe; it is
# NOT wired here — pointing core.hooksPath at it is a reconcile step in INSTALL.md
# (it overrides every repo's own .git/hooks, so it must be set diff-and-confirm).
mkdir -p "$HOME/.claude/hooks"
cp "$DOTFILES_DIR/hooks/pre-commit" "$HOME/.claude/hooks/pre-commit"
chmod +x "$HOME/.claude/hooks/pre-commit"
echo "Installed hooks/pre-commit to ~/.claude/hooks/"

# Install ruff, which the lint skill and the pre-commit hook both use.
if ! command -v ruff &>/dev/null; then
    pip install ruff -q
    echo "Installed ruff"
else
    echo "ruff already installed: $(ruff --version)"
fi

echo
echo "Next: reconcile CLAUDE.md, settings.json, and skills, and wire the"
echo "statusline and the git pre-commit hook, by following INSTALL.md (an agent"
echo "playbook — open this repo in Claude Code and ask it to run INSTALL.md)."
echo "These are not wired here because doing so would clobber local edits or"
echo "override every repo's own git hooks."
