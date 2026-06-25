---
name: review-pr
description: Review the branch diff before opening a PR via two Sonnet subagents — Agent 1 (local code correctness) and Agent 2 (completeness / contract / provenance, given the change's blast radius + intent). Classifies changed files by modality so data/config/docs get the right lens instead of being silently dropped. Ruff linting is handled by commit hooks.
disable-model-invocation: false
---

## Fetch latest remote
!`git fetch origin 2>&1 | tail -3`

## Base + ALL changed files (classification happens below — nothing is pre-excluded here)
!`BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master 2>/dev/null); echo "BASE=$BASE"; git diff --name-status --diff-filter=ACMR $BASE..HEAD 2>&1`

## Conventions
!`cat ~/.claude/CLAUDE.md 2>/dev/null || echo "(no CLAUDE.md found)"`

---

You are orchestrating a pre-PR review. The lesson this skill encodes: a diff-only review checks whether the change is *correct*, not whether it is *complete*; omissions are invisible to a diff. So Agent 2 gets the change's blast radius and intent, and every changed file is routed to a lens by modality rather than dropped by extension. Do the steps in order.

### Step 0 — Establish intent + provenance context (the yardstick)
- Determine what the branch is SUPPOSED to do, from the PR/MR description if present, the commit messages (`git log <BASE>..HEAD`), and any design doc the changes point at (check memory and `docs/`). Write a short intent summary — Agent 2 measures completeness against it. If intent is genuinely unclear, ask the user ONE question instead of guessing.
- Capture any provenance / per-run context the user gives (e.g. "these config paths are per-run", "`vendor/` is upstream"). If none, you will infer it in Step 1.

### Step 1 — Classify every changed file (route, never silently exclude)
Bucket each changed file on two axes and REPORT the routing so nothing vanishes unannounced:
- **Modality**: code (`.py .nf .groovy .sh .R .js .ts .go ...`) / config (`.yaml .toml .cfg .ini .config`) / data (`.tsv .csv .parquet .npy`, large `.json`) / docs (`.md .rst .txt`) / notebook (`.ipynb`) / binary. **Path overrides beat extension**: `*/data/* */sample_metadata/* */fixtures/*` → data; `vendor/ third_party/ generated/ *_pb2*` → vendored/generated.
- **Provenance**: contract-built (ours) / one-time-or-historical (e.g. a docstring saying "one-time") / vendored / generated / data. Infer from directory conventions, file headers/`@generated`, git history (single bulk-add vs incremental), manifests, and any provenance docs. Treat any marker as a cue to verify against git/structure, not as gospel.
- **Lens + input projection per modality**:
  - code → full diff + full current contents (to both agents)
  - config → full diff (semantic / key / cross-reference review)
  - data → header + a few sample rows + row count ONLY — never line-review a data file
  - docs → list; check claim-accuracy only if they describe changed behavior
  - notebook → review code cells as code; ignore output cells
  - binary / generated / vendored → skip content; note provenance

### Step 2 — Compute the blast radius (Agent 2's key input)
Find the change's reverse dependencies: changed/removed symbols (`def`/`class`/`function` names), renamed config keys, and produced OUTPUTS — then grep the repo for consumers OUTSIDE the changed files. Starting point:
```
BASE=$(git merge-base HEAD origin/main 2>/dev/null || git merge-base HEAD origin/master)
CHANGED=$(git diff --name-only $BASE..HEAD)
SYMS=$(git diff $BASE..HEAD -- '*.py' '*.nf' '*.sh' | grep -E '^[-+].*\b(def|class|function|func)\b' \
       | sed -E 's/.*\b(def|class|function|func)\s+([A-Za-z_][A-Za-z0-9_]*).*/\2/' | sort -u)
for s in $SYMS; do echo "== $s =="; git grep -nI -w "$s" | grep -vF -f <(printf '%s\n' $CHANGED) | head -20; done
```
Also grep for any renamed config keys / changed output identifiers by hand. Hand the consumer list to Agent 2.
**KNOWN LIMIT — tell Agent 2 explicitly:** symbol-grep finds callers/users but NOT output-format consumers or decoupled duplicates (no shared symbol). Agent 2 must reason about those separately; they are otherwise covered by tests, not review.

### Step 3 — Spawn Agent 1 (Sonnet) — LOCAL code correctness
Pass it the CODE files only (diff + contents) and the conventions. It stays local — it is NOT responsible for distant consumers (Agent 2 owns that). Ask it to find:
- Bugs / logic errors
- Missing error handling at system boundaries (file/IO, external-data shape assumptions, CLI args)
- Abstractions/helpers introduced with only one caller
- Derived state stored when it could be computed from existing state
- Convention violations — **provenance-calibrated**: do not flag vendored / one-time / generated code for conventions it was never built to.

Instruct Agent 1:
- Skip ruff-enforced style; don't suggest removing working intentional code; don't suggest deprecation/stylistic rewrites.
- Trace the data/call path to confirm a bug actually manifests before reporting — no pattern-matching.
- Output per finding (strict):
  `[BUG|BOUNDARY|ABSTRACTION|DERIVED-STATE|VIOLATION] file:line - description`
  `Manifest: how/when it actually goes wrong`
- If nothing: `No issues found.`

### Step 4 — Spawn Agent 2 (Sonnet) — completeness / contract / provenance / data
Pass it: the full diff, the **blast-radius consumer list**, the **intent summary** (yardstick), the **provenance / per-run context**, and the **data previews**. Ask for these sections:
1. **COMPLETENESS / PROPAGATION** — from the blast radius, list consumers NOT updated that are now stale/broken; classify each *live-break* vs *historical/one-time* (provenance-exempt). Include consumers of the change's OUTPUTS, and **explicitly consider OUT-OF-REPO / alternate-reader consumers of any written artifact** (e.g. a file later read with `anndata` vs raw `h5py`), not just in-repo symbol callers.
2. **CONTRACT INTEGRITY** — signature / return / config-key / data-schema changed where a consumer wasn't updated; implementation contradicting the stated intent. Watch for a **sibling that should have changed in lockstep** (e.g. a validator paired with a formatter).
3. **DATA-LENS** — for data files, referential integrity ONLY: do keys/IDs match what code/config expect; is the schema consistent with sibling data files. NOT line review.
4. **PROVENANCE NOTES** — per file/consumer, its class and how it shaped the judgment. **Distinguish PER-RUN config** (paths/params edited each run → NOT a finding) **from STRUCTURAL config gaps** (e.g. a key-map missing a new entry → a finding).
5. **VERDICT** — given intent, did the change propagate completely? Separate genuine omissions from intentional / per-run / historical non-changes.

Instruct Agent 2:
- Read actual code, trace before asserting, cite real `file:line`. A diff-only inference (e.g. "this lost its `raise`, so X is now silent") MUST be checked against the caller before reporting — that exact error has happened.
- Output per finding (strict):
  `[STALE-CONSUMER|CONTRACT-BREAK|DESIGN-MISMATCH|DATA-INTEGRITY] file:line - description`
  `Evidence: file:line of the consumer/mismatch | classification: live-break | historical | per-run`
- If nothing: `No issues found.`

### Step 5 — Merge and present
- On disagreement (Agent 1 says bug, Agent 2 says intentional-per-design), prefer Agent 2.
- Curate yourself — drop noise, keep findings worth acting on. Verify any flipped-conclusion finding cheaply before relaying it. Present grouped by concern, each as: what / why it matters / suggested fix.
- Do NOT make any changes until the user explicitly instructs you to.

### When to escalate to Opus (high-stakes only)
Both agents are Sonnet by default — the leverage is the widened input (blast radius + intent + classified lenses), not the model tier; on a real trial, Sonnet-with-blast-radius outperformed narrow-scope Opus and avoided a diff-only false positive Opus made. Escalate **Agent 2 to Opus** only for high-stakes changes (security-sensitive, irreversible data migrations, broad refactors): Opus is the tier that catches latent out-of-repo / alternate-reader consequences a Sonnet pass can miss. That escalation is worth running as a Workflow (per-agent effort control); the default 2-Sonnet path does not need one.
