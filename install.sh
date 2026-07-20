#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOME/.claude/skills"
cp "$DOTFILES_DIR/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
echo "Installed CLAUDE.md to ~/.claude/CLAUDE.md"

cp "$DOTFILES_DIR/settings.json" "$HOME/.claude/settings.json"
echo "Installed settings.json to ~/.claude/settings.json"

for skill_dir in "$DOTFILES_DIR/skills"/*/; do
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$HOME/.claude/skills/$skill_name"
    cp "$skill_dir/SKILL.md" "$HOME/.claude/skills/$skill_name/SKILL.md"
    echo "Installed skill: $skill_name"
done

# Helper tools (statusline ctx indicator, token-cost report, memory-staleness audit)
mkdir -p "$HOME/.claude/tools"
cp "$DOTFILES_DIR/tools/"*.py "$HOME/.claude/tools/"
chmod +x "$HOME/.claude/tools/"*.py
echo "Installed tools to ~/.claude/tools/"

# Statusline wrapper. Does NOT auto-wire settings.json (it may be managed by
# another tool in some environments). To enable, point statusLine.command at it.
# An optional ~/.claude/statusline-left.local.sh (machine-local, untracked) can
# supply a left-hand segment; without it, only the context indicator shows.
cp "$DOTFILES_DIR/my-statusline.sh" "$HOME/.claude/my-statusline.sh"
chmod +x "$HOME/.claude/my-statusline.sh"
echo "Installed my-statusline.sh (wire it in settings.json — see README)"

# Install ruff for the lint skill and pre-commit hook
if ! command -v ruff &>/dev/null; then
    pip install ruff -q
    echo "Installed ruff"
else
    echo "ruff already installed: $(ruff --version)"
fi
