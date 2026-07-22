#!/usr/bin/env python3
"""Live-context indicator for the Claude Code statusline.

Reads the statusline JSON payload on stdin and prints the current context size
against the model's window, ANSI-colored by absolute size (color tracks per-turn
cost, which matters well before a 1M window fills).

Primary source is the payload's `context_window` block (CC >= ~2.1); falls back
to parsing the transcript's last assistant usage if absent.

Right-alignment: if env SL_COLS (terminal width) is set, the ctx indicator is
padded to sit flush-right; SL_LEFT (an optional left-hand segment, e.g. a usage
bar, printed on the left) is measured so the padding is exact. Without SL_COLS it
prints ctx alone. Never raises — prints a dim placeholder on any error so the
statusline holds.
"""

import json
import os
import re
import subprocess
import sys

# Absolute token thresholds (not % of window): they track BOTH per-turn cost and
# quality (long context degrades attention / "context rot"), so they warn well
# before a 1M window is exhausted. green <300K, orange 300-500K, red >500K.
YELLOW_AT = 300_000
RED_AT = 500_000

# Muted 256-color triad (softer than basic ANSI): sage / orange / red.
G, Y, R, DIM, RST = "\033[38;5;108m", "\033[38;5;172m", "\033[38;5;167m", "\033[2m", "\033[0m"

ANSI = re.compile(r"\033\[[0-9;]*m")


def visible_len(s):
    return len(ANSI.sub("", s))


def from_payload(d):
    cw = d.get("context_window") or {}
    ctx = cw.get("total_input_tokens")
    if ctx is None:
        return None
    win = cw.get("context_window_size") or 200_000
    return int(ctx), int(win)


def from_transcript(path):
    if not path:
        return None
    last, win = None, 200_000
    try:
        with open(path) as f:
            for line in f:
                try:
                    o = json.loads(line)
                except Exception:
                    continue
                msg = o.get("message") or {}
                if "[1m]" in (msg.get("model") or ""):
                    win = 1_000_000
                if msg.get("usage"):
                    last = msg["usage"]
    except Exception:
        return None
    if not last:
        return None
    ctx = (
        (last.get("input_tokens") or 0)
        + (last.get("cache_read_input_tokens") or 0)
        + (last.get("cache_creation_input_tokens") or 0)
    )
    return ctx, win


def git_segment(d):
    """Branch (+`*` if dirty) for the payload's cwd; empty when not in a repo.

    Returns "" on home-centered / non-repo sessions so the segment silently
    disappears. Never raises — the statusline must always render.
    """
    cwd = d.get("cwd") or (d.get("workspace") or {}).get("current_dir")
    if not cwd:
        return ""
    # Anything under ~/.claude (the memory local-only repo, etc.) is local-only
    # plumbing, not work — don't surface its branch; it's noise.
    home_claude = os.path.join(os.path.expanduser("~"), ".claude")
    acwd = os.path.abspath(cwd)
    if acwd == home_claude or acwd.startswith(home_claude + os.sep):
        return ""
    # Run background git read-only: GIT_OPTIONAL_LOCKS=0 stops `git status` from
    # taking .git/index.lock to write back its refreshed index, which would race
    # a foreground commit/add and fail it ("index.lock: File exists").
    genv = {**os.environ, "GIT_OPTIONAL_LOCKS": "0"}
    try:
        # One call yields both: line 1 = branch, line 2 = repo toplevel.
        head = subprocess.run(
            ["git", "-C", cwd, "rev-parse", "--abbrev-ref", "HEAD", "--show-toplevel"],
            capture_output=True,
            text=True,
            timeout=0.5,
            env=genv,
        )
    except Exception:
        return ""
    if head.returncode != 0:
        return ""
    lines = head.stdout.split("\n")
    name = lines[0].strip()
    if not name:
        return ""
    repo = os.path.basename(lines[1].strip()) if len(lines) > 1 and lines[1].strip() else ""
    dirty = ""
    try:
        st = subprocess.run(
            ["git", "-C", cwd, "status", "--porcelain"],
            capture_output=True,
            text=True,
            timeout=0.5,
            env=genv,
        )
        if st.returncode == 0 and st.stdout.strip():
            dirty = "*"
    except Exception:
        pass
    label = f"{repo} {name}" if repo else name
    return f"{DIM}{label}{dirty}{RST}"


def render_ctx(d):
    got = from_payload(d) or from_transcript(d.get("transcript_path"))
    if not got:
        return f"{DIM}ctx --{RST}"
    ctx, win = got
    pct = 100 * ctx / win if win else 0
    color = R if ctx >= RED_AT else Y if ctx >= YELLOW_AT else G
    used = f"{ctx / 1000:.0f}K" if ctx < 1_000_000 else f"{ctx / 1e6:.2f}M"
    total = f"{win // 1_000_000}.0M" if win >= 1_000_000 else f"{win // 1000}K"
    return f"{color}ctx {used}/{total} ({pct:.0f}%){RST}"


def main():
    try:
        d = json.load(sys.stdin)
    except Exception:
        d = {}
    ctx_str = render_ctx(d)

    git_seg = git_segment(d)
    left = os.environ.get("SL_LEFT", "")
    if git_seg and left:
        left = f"{git_seg} {left}"
    elif git_seg:
        left = git_seg
    try:
        cols = int(os.environ.get("SL_COLS", "0"))
    except ValueError:
        cols = 0

    if cols > 0:
        # CC's statusline render area is narrower than `tput cols` (it reserves a
        # few columns), so leave a margin or the right end (the ctx %) gets
        # clipped with CC's "…". Tunable via SL_MARGIN if the fit is off.
        try:
            margin = int(os.environ.get("SL_MARGIN", "6"))
        except ValueError:
            margin = 6
        pad = cols - margin - visible_len(left) - visible_len(ctx_str)
        pad = max(1, pad)
        sys.stdout.write(f"{left}{' ' * pad}{ctx_str}")
    elif left:
        sys.stdout.write(f"{left}   {ctx_str}")
    else:
        sys.stdout.write(ctx_str)


if __name__ == "__main__":
    main()
