---
name: review-portability
description: Analyze a codebase for portability issues — assumptions that hold in the dev environment (Gitpod, local container) but break on HPC, CI, or a colleague's machine. Trigger when the user asks about portability, hardcoded paths, env assumptions, "will this work on HPC", or before a handoff or release. Also trigger proactively if you notice hardcoded paths, bare open() calls, or os.environ[] without guards during any code review.
---

# Portability Review

Surface assumptions baked into the codebase that are true in the dev environment but will crash or silently misbehave elsewhere (HPC, CI, another laptop, another user). Not a style review — only flag things that will actually break.

---

## Step 1: Collect files and grep

```bash
SRC=$([ -d src ] && echo src || echo ".")

echo "--- python files ---"
find $SRC -name "*.py" ! -name "__init__.py" | sort

echo "--- all other text files ---"
find . -not -path "./.git/*" -not -path "./node_modules/*" \
  \( -name "*.sh" -o -name "*.yaml" -o -name "*.yml" -o -name "*.toml" \
     -o -name "*.cfg" -o -name "*.ini" -o -name ".env*" -o -name "Dockerfile*" \
     -o -name "Makefile" -o -name "*.mk" -o -name "*.txt" -o -name "*.md" \
     -o -name "*.conf" -o -name "*.json" \) | sort
```

```bash
SRC=$([ -d src ] && echo src || echo ".")

echo "=== bare open() ==="
grep -rn "open(" $SRC --include="*.py" | grep -v "#"

echo "=== path construction ==="
grep -rn "os\.path\.\|Path(" $SRC --include="*.py"

echo "=== cwd usage ==="
grep -rn "os\.getcwd\|Path(\"\.\"\)\|Path('\.')\|os\.chdir\|glob\.glob(" $SRC --include="*.py"

echo "=== hardcoded machine paths (py) ==="
grep -rn '"/home/\|"/Users/\|"/root/\|"/workspace/\|"/mnt/\|"C:\\' $SRC --include="*.py"
grep -rn "'/home/\|'/Users/\|'/root/\|'/workspace/\|'/mnt/" $SRC --include="*.py"

echo "=== env var access ==="
grep -rn "os\.environ\[\|os\.environ\.get\|os\.getenv" $SRC --include="*.py"

echo "=== subprocess / shell ==="
grep -rn "subprocess\.\|os\.system\|os\.popen\|shell=True" $SRC --include="*.py"

echo "=== resource / device ==="
grep -rn "\.cuda()\|torch\.cuda\|cpu_count\|/tmp/" $SRC --include="*.py"

echo "=== config loading ==="
grep -rn "open.*\.\(yaml\|toml\|cfg\|ini\|json\)\|load_dotenv\|dotenv" $SRC --include="*.py"

echo "=== hardcoded paths (all text files) ==="
grep -rn \
  '/home/[a-zA-Z]\|/Users/[a-zA-Z]\|/root/\|/workspace/\|C:\\Users\|~/[a-zA-Z]' \
  --include="*.sh" --include="*.yaml" --include="*.yml" --include="*.toml" \
  --include="*.cfg" --include="*.ini" --include="*.env" --include="Dockerfile*" \
  --include="Makefile" --include="*.conf" --include="*.json" . 2>/dev/null

echo "=== assumed env vars (all text files) ==="
grep -rn '\$[A-Z_]\{2,\}' \
  --include="*.sh" --include="*.yaml" --include="*.yml" \
  --include="Makefile" --include="*.mk" --include="Dockerfile*" . 2>/dev/null | head -60

echo "=== tool assumptions (all text files) ==="
grep -rn 'micromamba\|conda\|mamba\|pip install' \
  --include="*.sh" --include="Dockerfile*" --include="Makefile" . 2>/dev/null
```

---

## Step 2: Subagent deep-dive — Python files only

For each Python file, spawn a **parallel subagent**. Pass: full file contents, grep hits for that file from Step 1.

For each issue found, output:

```
ISSUE: <one line>
SEVERITY: SEVERE | MODERATE | WARNING
  SEVERE   = will crash or corrupt output in another env
  MODERATE = fragile — likely breaks under specific but common conditions
  WARNING  = assumption worth documenting; low breakage risk
LOCATION: file.py:line
CATEGORY: PATH_FRAGILITY | CWD_ASSUMPTION | HARDCODED_PATH | ENV_ASSUMPTION | EXISTENCE_ASSUMPTION | CONFIG_GAP | RESOURCE_ASSUMPTION | SHELL_DEPENDENCY
DETAIL: <what assumption is made and when it breaks>
FIX: <how to make the assumption explicit or validated — prefer failing loudly over silent fallback>
```

### Checks

**PATH_FRAGILITY**
- `open(s)` or `Path(s)` where `s` is not traceable to `__file__`, `Path(__file__).parent`, `os.path.abspath()`, or a config value already made absolute.
- `__file__` used without `.resolve()` or `.parent` — can be relative depending on invocation.
- Paths constructed with string concat rather than `Path` / `os.path.join`.

**CWD_ASSUMPTION**
- `os.getcwd()` used as a meaningful anchor (not just logging).
- `open("filename")` with no path component.
- `Path(".")` used to locate or write real files.
- `subprocess` calls without explicit `cwd=` where the subprocess is directory-sensitive.
- `glob.glob("relative/pattern")` used to find real files.

**HARDCODED_PATH**
- Any literal beginning with `/home/`, `/Users/`, `/root/`, `/workspace/`, `/mnt/`, `C:\`, or a specific conda/mamba env path.
- `/tmp/` used as a durable store (fine for scratch, not for artifacts expected to persist).

**ENV_ASSUMPTION**
- `os.environ["VAR"]` — only acceptable if there is a documented startup check that fails loudly; flag if absent.
- `os.getenv("VAR")` where `None` causes a downstream error (e.g. passed to `Path()`).
- Env vars relied on but not documented (no `.env.example`, no startup check, no README mention).
- Assumptions about `$HOME`, `$USER`, `$TMPDIR`, `$PYTHONPATH` being set or having a specific value.

**EXISTENCE_ASSUMPTION**
- `open(path, "r")` on a path not guaranteed by the package itself, with no prior existence check.
- Writing to a directory without `mkdir(parents=True, exist_ok=True)`.
- References to files/dirs (e.g. `data/`, `results/`, `logs/`) not in the repo and not documented as user-provided.

**CONFIG_GAP**
- Config loaded from a relative path.
- Required keys with no validation — error surfaces far from the config load.
- Default values that are machine-specific (paths, usernames).
- No documented schema for required vs optional keys.

**RESOURCE_ASSUMPTION**
- `.cuda()` or any CUDA/GPU call with no device check — crashes on CPU-only machines.
- Hardcoded thread/worker counts ignoring available CPUs.
- Scratch paths assumed writable (HPC `/tmp` is often per-node and small).

**SHELL_DEPENDENCY**
- `subprocess` invoking a tool that may not be on `PATH` (e.g. `rsync`, `conda`, `mamba`) without a `shutil.which()` guard.
- `shell=True` with environment-dependent commands.
- OS-specific shell syntax that won't work outside bash.

If no issues, return: `NO ISSUES FOUND`

---

## Step 3: Triage non-Python grep hits

Review the "all text files" grep output from Step 1 directly — no subagents. For each hit:
- Hardcoded machine path in a config or Dockerfile → SEVERE if it's a default value, MODERATE if it's a comment or example
- Undocumented env var in a shell script or Makefile with no guard → MODERATE
- Tool assumption (e.g. `micromamba` assumed present in a Makefile with no availability check) → MODERATE

Discard hits that are clearly documentation examples or already guarded.

---

## Step 4: Curate and present

Review all subagent outputs and Step 3 findings. Discard false positives (e.g. `Path(".")` in a test fixture, `/tmp/` as genuine scratch, `os.environ["PATH"]`). Consolidate duplicate root causes across files into one finding with all locations listed.

---

**Scope**: N Python files, M other text files analyzed

**SEVERE** *(omit section if none)*

```
[CATEGORY] file:line — description
Breaks when: <specific env>
Fix: <one line>
```

**MODERATE** *(omit section if none)*

Same format.

**WARNING** *(omit section if none; summarize as a pattern, not per-file)*

**Summary**

- SEVERE: N
- MODERATE: N
- WARNING: N
- Files with no issues: N

**Top recommendation**: highest-leverage fix if this codebase is going to HPC or shared with others.

---

Do not modify any files. Present findings only and wait for explicit instruction.
