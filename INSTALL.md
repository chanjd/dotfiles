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
- If present → merge with `jq`, local as the base so local wins on scalar
  conflicts, then eyeball the result:

      jq -s '.[0] * .[1]' "$DEST/settings.json" "$REPO/settings.json" > /tmp/settings.merged.json

  `*` recursively merges objects; arrays and scalars from the second file
  override. Because local is `.[0]` and repo is `.[1]`, **repo values win on
  scalars** — flip the order (`"$REPO"` then `"$DEST"`) if you instead want
  local to win. Diff `/tmp/settings.merged.json` against the current file, show
  any key whose value changed, and confirm before writing it back to
  `$DEST/settings.json`.

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

## 5. Sanity check

- `echo '{"cwd":"'"$REPO"'","context_window":{"total_input_tokens":1000,"context_window_size":200000}}' | SL_COLS=100 python3 "$DEST/tools/ctx_size.py"`
  should print the branch on the left and the ctx indicator on the right.
- Restart / refresh Claude Code and confirm the statusline renders.
