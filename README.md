# dotfiles

Claude Code configuration — CLAUDE.md and skills.

## Bootstrap

```bash
git clone https://github.com/chanjd/dotfiles.git && bash dotfiles/install.sh
```

Installs:
- `~/.claude/CLAUDE.md` — behavioral defaults and conventions
- `~/.claude/skills/` — slash command skills

## Skills

- `catchup` — summarize project state at session start
- `summarize` — update memory files before context reset
- `lint` — run ruff format + check on staged Python files
- `changelog-generator` — generate changelog entry from branch commits
- `test-fixing` — systematically fix failing tests by error group
- `root-cause-tracing` — trace errors back to their original trigger
