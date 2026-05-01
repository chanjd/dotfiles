# dotfiles

Claude Code configuration — CLAUDE.md and skills.

## Bootstrap

```bash
git clone https://github.com/chanjd/dotfiles.git && bash dotfiles/install.sh
```

Installs:
- `~/.claude/CLAUDE.md` — behavioral defaults and conventions
- `~/.claude/settings.json` — pre-commit ruff hook
- `~/.claude/skills/` — slash command skills
- `ruff` — required for the lint skill and pre-commit hook

## Skills

- `catchup` — summarize project state at session start
- `summarize` — update memory files before context reset
- `lint` — run ruff format + check on staged Python files
- `changelog-generator` — generate changelog entry from branch commits
- `test-fixing` — systematically fix failing tests by error group
- `root-cause-tracing` — trace errors back to their original trigger
- `review-pr` — lint then subagent review of full branch diff before opening a PR

## Prerequisites for review-pr, review-tests, catchup, summarize
-  `catchup` and `summarize` look for an agents file at `.ona/agents.md` first, then `AGENTS.md` in repo root — missing is handled gracefully. Memory is read from `~/.claude/projects/<repo-path-as-key>/memory/MEMORY.md`; also graceful if absent. `summarize` will create `AGENTS.md` on first run. 
- `review-pr` and `review-tests` both require a remote named origin with a main or master branch that has been fetched — they use git merge-base HEAD origin/main to scope the diff. Run git fetch origin if the base can't be resolved.
#### `review-tests` additionally requires:
-  A conda/micromamba environment under `$HOME/.local/share/mamba/envs/`, `$HOME/micromamba/envs/`, or `$HOME/.conda/envs/` with pytest and pytest-cov installed. The skill picks the first env it finds alphabetically, so the project's primary test env should be the only one with pytest, or the intended one should sort first.
-  Source package discoverable at `src/` (preferred) or as a top-level directory containing `__init__.py`.
-  Tests in `tests/` or `test/`.
  
