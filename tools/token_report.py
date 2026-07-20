#!/usr/bin/env python3
"""Token-usage analyzer for Claude Code session transcripts.

Reads the per-session JSONL logs under ~/.claude/projects/<cwd-key>/ and reports
where tokens (and cost) actually go. Cost is reported in "input-token equivalents"
using the stable Anthropic price ratios (input=1.0):

    cache_read   ~= 0.10   (re-reading a warm cached prefix)
    input        ~= 1.00   (fresh/uncached prompt tokens)
    cache_write  ~= 1.25   (writing new content into the cache)
    output       ~= 5.00   (generation)

The cache TTL is 5 min: a gap > 5 min between turns invalidates the prefix, so the
next turn re-pays full price (as input + cache_write) instead of cache_read. The
per-turn table exposes exactly that.

Usage:
    token_report.py [PROJECT_DIR_or_GLOB] [--turns N] [--session FILE]
"""

import glob
import json
import os
import sys
from datetime import datetime

W = {"cache_read": 0.10, "input": 1.00, "cache_write": 1.25, "output": 5.00}


def parse_ts(s):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def iter_usages(path):
    """Yield (timestamp, usage_dict) for every assistant message with usage."""
    for line in open(path):
        try:
            o = json.loads(line)
        except Exception:
            continue
        u = (o.get("message") or {}).get("usage")
        if not u:
            continue
        yield parse_ts(o.get("timestamp")), u


def cats(u):
    return {
        "cache_read": u.get("cache_read_input_tokens", 0) or 0,
        "input": u.get("input_tokens", 0) or 0,
        "cache_write": u.get("cache_creation_input_tokens", 0) or 0,
        "output": u.get("output_tokens", 0) or 0,
    }


def cost_equiv(c):
    return sum(c[k] * W[k] for k in c)


def fmt(n):
    return f"{n / 1e6:.2f}M" if n >= 1e6 else f"{n / 1e3:.1f}K" if n >= 1e3 else str(int(n))


def report_session(path, show_turns=0):
    tot = {k: 0 for k in W}
    turns = []
    prev_ts = None
    for ts, u in iter_usages(path):
        c = cats(u)
        for k in c:
            tot[k] += c[k]
        gap = (ts - prev_ts).total_seconds() if (ts and prev_ts) else None
        turns.append((ts, gap, c))
        prev_ts = ts
    ce = cost_equiv(tot)
    name = os.path.basename(path)[:12]
    print(f"\n=== session {name}  ({len(turns)} model turns) ===")
    print(f"{'category':<12}{'tokens':>10}{'cost-equiv':>12}{'%cost':>8}")
    for k in ("cache_read", "input", "cache_write", "output"):
        ck = tot[k] * W[k]
        pct = 100 * ck / ce if ce else 0
        print(f"{k:<12}{fmt(tot[k]):>10}{fmt(ck):>12}{pct:>7.1f}%")
    print(f"{'TOTAL':<12}{'':>10}{fmt(ce):>12}{'100.0%':>8}")
    warm = tot["cache_read"]
    cold = tot["input"] + tot["cache_write"]
    print(f"cache-hit ratio (read / (read+fresh)): {100 * warm / (warm + cold):.1f}%" if (warm + cold) else "no input")

    if show_turns:
        print(f"\n  last {show_turns} turns (gap = seconds since previous turn):")
        print(f"  {'gap(s)':>8}{'cache_read':>12}{'fresh_in':>10}{'cache_wr':>10}{'output':>9}  miss?")
        for ts, gap, c in turns[-show_turns:]:
            miss = "COLD>5m" if (gap is not None and gap > 300 and c["cache_write"] > 2000) else ""
            g = f"{gap:.0f}" if gap is not None else "-"
            print(
                f"  {g:>8}{fmt(c['cache_read']):>12}{fmt(c['input']):>10}"
                f"{fmt(c['cache_write']):>10}{fmt(c['output']):>9}  {miss}"
            )
    return tot, ce, len(turns)


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show_turns = 0
    one = None
    for a in sys.argv[1:]:
        if a.startswith("--turns"):
            show_turns = int(a.split("=")[1]) if "=" in a else int(sys.argv[sys.argv.index(a) + 1])
        if a.startswith("--session"):
            one = a.split("=")[1] if "=" in a else sys.argv[sys.argv.index(a) + 1]

    if one:
        report_session(one, show_turns)
        return

    base = args[0] if args else os.path.expanduser("~/.claude/projects/*")
    files = sorted(
        glob.glob(os.path.join(base, "*.jsonl"))
        if os.path.isdir(base)
        else glob.glob(base) or glob.glob(os.path.join(base, "*.jsonl")),
        key=os.path.getmtime,
        reverse=True,
    )
    if not files:
        print(f"no transcripts under {base}")
        return

    grand = {k: 0 for k in W}
    rows = []
    for f in files:
        tot, ce, n = report_session(f, show_turns if len(files) == 1 else 0)
        for k in grand:
            grand[k] += tot[k]
        rows.append((os.path.basename(f)[:12], ce, n, tot))

    gce = cost_equiv(grand)
    print("\n" + "=" * 60)
    print(f"GRAND TOTAL across {len(files)} sessions")
    for k in ("cache_read", "input", "cache_write", "output"):
        ck = grand[k] * W[k]
        print(f"{k:<12}{fmt(grand[k]):>10}{fmt(ck):>12}{100 * ck / gce:>7.1f}%")
    print(f"{'TOTAL':<12}{'':>10}{fmt(gce):>12}")
    print("\ntop sessions by cost-equiv:")
    for name, ce, n, _ in sorted(rows, key=lambda r: r[1], reverse=True)[:10]:
        print(f"  {name}  {fmt(ce):>8} cost-equiv  {n:>4} turns  {fmt(ce / n) if n else 0:>7}/turn")


if __name__ == "__main__":
    main()
