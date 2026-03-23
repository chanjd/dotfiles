#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOME/.claude"
cp "$DOTFILES_DIR/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
echo "Installed CLAUDE.md to ~/.claude/CLAUDE.md"
