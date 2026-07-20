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

# Install ruff for the lint skill and pre-commit hook.
if ! command -v ruff &>/dev/null; then
    pip install ruff -q
    echo "Installed ruff"
else
    echo "ruff already installed: $(ruff --version)"
fi

echo
echo "Next: reconcile CLAUDE.md, settings.json, and skills, and wire the"
echo "statusline, by following INSTALL.md (an agent playbook — open this repo"
echo "in Claude Code and ask it to run INSTALL.md). These are not copied here"
echo "because a blind overwrite would clobber local edits."
