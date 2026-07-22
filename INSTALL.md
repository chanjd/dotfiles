# INSTALL — agent playbook

`install.sh` handles only the additive, non-conflicting artifacts (the `tools/`
helpers, the statusline wrapper, ruff). This file covers the rest: the artifacts
that can conflict with local state — `CLAUDE.md`, `settings.json`, and the
skills — plus wiring the statusline. **Run `install.sh` first**, then work
through this playbook.

This is written for a Claude Code agent to execute. Open this repo in Claude
Code and say "follow INSTALL.md". The whole point is to **reconcile, never
clobber** — a naive `cp` would destroy local edits and any settings another tool
manages. Do the steps in order; show diffs and confirm before overwriting.

Let `REPO` = this repository's directory, `DEST` = `$HOME/.claude`.

## 1. CLAUDE.md

- If `$DEST/CLAUDE.md` is absent → copy `$REPO/CLAUDE.md` to it.
- If present and byte-identical (`diff -q`) → nothing to do.
- If diverged → show the diff. The repo version is the source of truth for the
  shared rules, but local may hold machine-specific additions. Merge: take the
  repo's rule changes while preserving any local-only sections. Do not blindly
  overwrite; confirm the merged result with the user.

## 2. settings.json — merge, never overwrite

`settings.json` often carries machine-local keys (permissions, env, a statusLine
another tool set). Deep-merge repo keys in; never replace the file.

- If `$DEST/settings.json` is absent → copy `$REPO/settings.json`.
- If present → deep-merge with `jq`, putting local **last** so it wins on scalar
  conflicts (non-destructive: machine-local values and any settings another tool
  manages are preserved, while repo still contributes keys local lacks):

      jq -s '.[0] * .[1]' "$REPO/settings.json" "$DEST/settings.json" > /tmp/settings.merged.json

  In `*` the right-hand operand wins on scalar conflicts and objects merge
  recursively. With repo as `.[0]` and local as `.[1]`, **local wins**. Diff
  `/tmp/settings.merged.json` against the current file, surface any key whose
  value changed, and confirm before writing it back to `$DEST/settings.json`.
  Flip the operand order if you want a specific repo rule change to win instead.

## 3. skills — reconcile per skill, never silent-overwrite

For each `$REPO/skills/<name>/SKILL.md`:

- `$DEST/skills/<name>/` absent → create it and copy `SKILL.md`.
- present and identical → skip.
- diverged → show the diff and reconcile (take repo improvements, keep any local
  customization). Confirm before writing.

Do not delete skills that exist locally but not in the repo — they may be
installed from elsewhere.

## 4. Wire the statusline

Point Claude Code at the wrapper `install.sh` placed at `$DEST/my-statusline.sh`:

    jq '.statusLine = {"type":"command","command":"'"$HOME"'/.claude/my-statusline.sh"}' \
        "$DEST/settings.json" > /tmp/settings.sl.json
    # diff, confirm, then move into place

- The wrapper right-aligns a live context indicator and, in a git repo, shows the
  current branch (+`*` when dirty). Both derive from the statusline stdin JSON —
  no extra config.
- Optional left-hand segment: create an executable `$DEST/statusline-left.local.sh`
  (machine-local, untracked — never commit it) whose stdout becomes the left of
  the statusline (e.g. a usage bar). Absent → only the context/branch indicator
  shows.
- If another tool later resets `statusLine.command`, re-run this one jq step.

## 5. Wire the git pre-commit hook

`install.sh` placed the hook at `$DEST/hooks/pre-commit` (a report-only ruff gate
that checks each staged `.py` file's staged blob and blocks the commit on any
violation; it never runs `git add`). Wiring it means pointing git's global
`core.hooksPath` at `$DEST/hooks`.

**Warn the user first:** a global `core.hooksPath` overrides every repo's own
`.git/hooks` for all repos on the machine — repos that install hooks into
`.git/hooks` (husky, the `pre-commit` framework) have them ignored. The shipped
hook mitigates this by chaining to the repo-local `.git/hooks/pre-commit` when one
exists, but confirm the user wants a global hook before proceeding.

Read the current setting: `CUR=$(git config --global core.hooksPath || true)`.

- **unset** → set it:

      git config --global core.hooksPath "$HOME/.claude/hooks"

- **already `$HOME/.claude/hooks`** → nothing to do (idempotent).

- **set to another dir `D`** → default is to **migrate** to `$HOME/.claude/hooks`,
  because `install.sh` only refreshes `$DEST/hooks` on re-run, so a hook left in
  `D` goes stale. `core.hooksPath` is all-or-nothing (git reads hooks ONLY from
  it), so any OTHER hooks in `D` must move too or they stop firing:
  - Copy every hook in `D` not already in `$DEST/hooks` into `$DEST/hooks`. If `D`
    holds a `pre-commit` that differs from the shipped one and is not a prior
    version of it, show the diff and confirm before overwriting.
  - `git config --global core.hooksPath "$HOME/.claude/hooks"`.
  - Offer to remove the now-unused hooks from `D`.

  If the user prefers to **keep `D`** instead of migrating: copy
  `$DEST/hooks/pre-commit` into `D`, but if a *different* `pre-commit` already
  lives there, show the diff and confirm — never blind-overwrite a user hook
  (silent upgrade only when the existing file is a prior version of this one).
  Note that `install.sh` will not refresh that copy on future runs.

## 6. Sanity check

- `echo '{"cwd":"'"$REPO"'","context_window":{"total_input_tokens":1000,"context_window_size":200000}}' | SL_COLS=100 python3 "$DEST/tools/ctx_size.py"`
  should print the branch on the left and the ctx indicator on the right.
- Restart / refresh Claude Code and confirm the statusline renders.
- Hook: in a scratch repo (`git init` in a temp dir), stage a malformed Python
  file (`printf 'import os\n' > x.py; git add x.py`) and `git commit` — it should
  be blocked by ruff; a clean file should commit.
