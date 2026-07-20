#!/bin/sh
# Claude Code statusline: an optional left segment + a right-aligned live context
# indicator. Portable — no environment-specific tooling.
#
# Left segment (optional): if an executable machine-local provider exists at
# ~/.claude/statusline-left.local.sh, its stdout is shown on the left (e.g. a
# usage bar). Absent (e.g. gitpod/ona) → only the context indicator is shown.
# The provider is machine-local and NOT tracked in dotfiles.
#
# Wiring: point settings.json statusLine.command at this file.

CTX="$HOME/.claude/tools/ctx_size.py"
LEFT_PROVIDER="$HOME/.claude/statusline-left.local.sh"

input=$(cat)

left=""
[ -x "$LEFT_PROVIDER" ] && left=$("$LEFT_PROVIDER" 2>/dev/null)

# Terminal width for right-alignment (tput preferred; COLUMNS fallback).
cols=$(tput cols 2>/dev/null)
[ -n "$cols" ] || cols="${COLUMNS:-0}"

printf '%s' "$input" | SL_LEFT="$left" SL_COLS="$cols" python3 "$CTX" 2>/dev/null
