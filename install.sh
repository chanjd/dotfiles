#!/usr/bin/env bash
set -e

DOTFILES_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

mkdir -p "$HOME/.claude/skills"
cp "$DOTFILES_DIR/CLAUDE.md" "$HOME/.claude/CLAUDE.md"
echo "Installed CLAUDE.md to ~/.claude/CLAUDE.md"

for skill_dir in "$DOTFILES_DIR/skills"/*/; do
    skill_name="$(basename "$skill_dir")"
    mkdir -p "$HOME/.claude/skills/$skill_name"
    cp "$skill_dir/SKILL.md" "$HOME/.claude/skills/$skill_name/SKILL.md"
    echo "Installed skill: $skill_name"
done
