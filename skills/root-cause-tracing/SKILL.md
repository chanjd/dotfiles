---
name: root-cause-tracing
description: Trace errors back to their original trigger rather than fixing at the symptom site. Use when an error occurs deep in execution or the call chain is unclear.
---

# Root Cause Tracing

Fix at the source, not the symptom.

## Process

### 1. Observe the symptom

Note exactly where and how the error manifests.

### 2. Find the immediate cause

What line of code directly produces the error?

### 3. Trace backward

What called that code? What value was passed? Keep asking "where did this value come from?" up the call chain until you reach the original trigger.

### 4. Add instrumentation if needed

When manual tracing is unclear, add temporary logging before the failing operation:

```python
import logging
logging.debug("DEBUG value=%r, caller context: ...", value)
```

Log the value, its type, and any relevant context. Remove instrumentation after the fix.

### 5. Fix at the source

Fix where the bad value or condition originates, not where it eventually causes a crash.

### 6. Add defense-in-depth

After fixing the root cause, add validation at intermediate layers where the bad value passed through unchecked. This catches regressions and similar future bugs.

## Key principle

Never fix just where the error appears. A crash deep in the stack is a symptom — the bug is wherever the invalid data was first created or allowed.
