# dotfiles

Claude Code configuration — CLAUDE.md, skills, and helper tools.

## Bootstrap

```bash
git clone https://github.com/chanjd/dotfiles.git && bash dotfiles/install.sh
```

Installs:
- `~/.claude/CLAUDE.md` — behavioral defaults and conventions
- `~/.claude/settings.json` — pre-commit ruff hook (skip this copy in environments where another tool manages settings.json)
- `~/.claude/skills/` — slash command skills
- `~/.claude/tools/` — helper scripts (statusline, token report, memory audit)
- `~/.claude/my-statusline.sh` — statusline wrapper (wire manually, see below)
- `ruff` — required for the lint skill and pre-commit hook

## Skills

- `catchup` — resume at session start: reads the RESUME handoff + memory, verifies against live state
- `summarize` — checkpoint before /clear or /compact: writes a RESUME block + durable memory (prune-on-touch)
- `memory-audit` — sweep memory for stale trails (dead links, index bloat, resolved markers); tiered auto/confirm cleanup
- `lint` — run ruff format + check on staged Python files
- `changelog-generator` — generate changelog entry from branch commits
- `test-fixing` — systematically fix failing tests by error group
- `root-cause-tracing` — trace errors back to their original trigger
- `plan-contract` — acceptance oracle + ranked decisions for a non-trivial PR
- `review-pr` — lint then subagent review of full branch diff before opening a PR
- `review-tests` — evaluate test-suite quality (coverage, mutation gaps, tautologies)
- `review-portability` — flag dev-env assumptions that break on HPC/CI/another machine

## Helper tools (`~/.claude/tools/`)

Usage-management toolset. Cost is dominated by context re-processing (~85%); these help keep it in check.
- `ctx_size.py` — statusline context indicator; reads CC statusline JSON, prints `ctx <used>/<win> (%)` colored by absolute tokens (green <300K / orange <500K / red beyond). Right-aligns via `SL_COLS`/`SL_LEFT`/`SL_MARGIN`.
- `token_report.py` — cost-weighted per-session token breakdown + per-turn cache-miss table over `~/.claude/projects/<key>/*.jsonl`.
- `memory_audit.py` — mechanical staleness detector for the memory corpus (index drift, dead `[[links]]`, unresolved markers, index bloat, age). Backs the `memory-audit` skill.

## Statusline wiring (manual, per-env)

`install.sh` does NOT edit `settings.json` for the statusline, so it never conflicts with an environment that manages that file. To enable the context indicator:

1. In `~/.claude/settings.json` set:
   ```json
   "statusLine": { "type": "command", "command": "<HOME>/.claude/my-statusline.sh", "refreshInterval": 360 }
   ```
2. If another tool already renders a statusline, disable that tool's statusline first so this one takes effect.
3. Optional left segment: drop an executable `~/.claude/statusline-left.local.sh` that prints a left-hand string (e.g. a usage bar). It's machine-local and untracked; without it, only the context indicator shows.

## Memory hygiene

Memory (`~/.claude/projects/<key>/memory/`) is machine-local and NOT in this repo (it holds private/project content; this repo is public). Keep it recoverable with a **local** git repo there (`git init`, no remote); `summarize`/`memory-audit` commit around edits so an over-prune is `git diff`/`checkout`-recoverable.

## Prerequisites

- `catchup`/`summarize` read memory from `~/.claude/projects/<repo-path-as-key>/memory/` — graceful if absent. They update an `AGENTS.md` only if one already exists (they do not create one).
- `review-pr`/`review-tests` require a remote `origin` with a fetched main/master (they scope via `git merge-base HEAD origin/main`).
- `review-tests` finds a test env via `micromamba`/`conda env list`, common conda roots (or `$CONDA_ENV_DIRS`), and falls back to the **active `python`** if it has pytest — so it works in a container/venv too, no conda required. Needs pytest + pytest-cov; source under `src/` or a top-level package; tests in `tests/`/`test/`.
