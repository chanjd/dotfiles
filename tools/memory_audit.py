#!/usr/bin/env python3
"""Mechanical staleness detector for the auto-memory corpus.

Emits signals a cleanup pass should act on; it does NOT edit anything (the agent
decides what to prune). Signals:
  1. index <-> files sync   (files missing from MEMORY.md; index links to no file)
  2. dead [[wikilinks]]     (a [[slug]] with no file whose frontmatter name: matches)
  3. unresolved markers     (OPEN/DEFERRED/PAUSED/SHELVED/TODO/NEXT — verify still true)
  4. least-recently-touched (age candidates to re-check for currency)

Usage: memory_audit.py [MEMORY_DIR]   (defaults to the home-key memory dir)
"""

import os
import re
import sys
import time

WIKILINK = re.compile(r"\[\[([^\]]+)\]\]")
NAME = re.compile(r"^name:\s*(.+?)\s*$", re.M)
INDEX_LINK = re.compile(r"\]\(([^)]+\.md)\)")
MARKERS = re.compile(r"\b(OPEN|DEFERRED|PAUSED|SHELVED|TODO|NEXT =|in progress|in-progress)\b")


def default_dir():
    home = os.path.expanduser("~")
    key = home.replace("/", "-")
    return os.path.join(home, ".claude", "projects", key, "memory")


def main():
    d = sys.argv[1] if len(sys.argv) > 1 else default_dir()
    if not os.path.isdir(d):
        print(f"(no memory dir at {d})")
        return
    files = sorted(f for f in os.listdir(d) if f.endswith(".md") and f != "MEMORY.md")
    texts = {}
    slugs = {}
    for f in files:
        try:
            t = open(os.path.join(d, f)).read()
        except Exception:
            continue
        texts[f] = t
        m = NAME.search(t)
        if m:
            slugs[m.group(1)] = f

    # 1. index <-> files
    idx_path = os.path.join(d, "MEMORY.md")
    idx = ""
    try:
        idx = open(idx_path).read()
    except Exception:
        pass
    linked = set(INDEX_LINK.findall(idx))
    missing_from_index = [f for f in files if f not in linked]
    dangling_links = sorted(p for p in linked if not os.path.exists(os.path.join(d, p)))
    print("== index <-> files ==")
    print(f"  files not in MEMORY.md ({len(missing_from_index)}): {', '.join(missing_from_index) or '-'}")
    print(f"  index links to missing files ({len(dangling_links)}): {', '.join(dangling_links) or '-'}")

    # 2. dead wikilinks
    dead = {}
    for f, t in texts.items():
        for target in set(WIKILINK.findall(t)):
            if target not in slugs:
                dead.setdefault(target, []).append(f)
    print("\n== dead [[wikilinks]] (slug -> files referencing it) ==")
    if dead:
        for target, refs in sorted(dead.items()):
            print(f"  [[{target}]]  <- {', '.join(refs)}")
    else:
        print("  - none")

    # 3. unresolved markers
    print("\n== unresolved markers (verify each is still true; drop if resolved) ==")
    hits = 0
    for f in files:
        for i, line in enumerate(texts.get(f, "").splitlines(), 1):
            if MARKERS.search(line):
                hits += 1
                if hits <= 60:
                    print(f"  {f}:{i}: {line.strip()[:110]}")
    if hits == 0:
        print("  - none")
    elif hits > 60:
        print(f"  ... (+{hits - 60} more)")

    # 4. index bloat (MEMORY.md is loaded EVERY session — keep lines terse)
    print("\n== MEMORY.md index bloat (loaded every session; condense to pointer, move detail to the file) ==")
    LIMIT = 200
    bloated = []
    for i, line in enumerate(idx.splitlines(), 1):
        if line.lstrip().startswith("- [") and len(line) > LIMIT:
            bloated.append((len(line), i, line))
    if bloated:
        for n, i, line in sorted(bloated, reverse=True):
            print(f"  L{i}: {n} chars — {line[:80]}...")
        print(f"  ({len(bloated)} lines over {LIMIT} chars; convention is ~150)")
    else:
        print(f"  - none over {LIMIT} chars")

    # 5. age
    print("\n== least-recently-touched (re-check currency) ==")
    now = time.time()
    ages = sorted(((os.path.getmtime(os.path.join(d, f)), f) for f in files))
    for mt, f in ages[:8]:
        print(f"  {int((now - mt) / 86400):>4}d  {f}")


if __name__ == "__main__":
    main()
