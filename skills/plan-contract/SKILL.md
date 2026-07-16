---
name: plan-contract
description: Use when planning a non-trivial PR or multi-PR series, before writing code. Produces a plan contract — an implementation-independent acceptance oracle plus ranked decisions and an adversarial misread check — catching intent drift at plan review, not merge.
disable-model-invocation: false
---

This skill runs during planning, before implementation. Its job is to catch **intent drift** — the gap between what the user wants and what the plan encodes — while it is still cheap to fix (rewrite prose, not code). review-pr / review-tests catch implementation drift; this is the gate at the other end.

Produce a **Plan Contract** section as part of the plan. **Do not write implementation code.** Surface the contract to the user before exiting plan mode.

## Altitude filter — what to surface, what to skip

Surface a detail only if it fails one of these three. If it passes all three it is an implementation detail — decide it silently and let code review catch it if wrong.

- Hard to reverse after merge? (semantic definitions, data representations, public contracts — yes; internal function signatures — no)
- Could a competent engineer reasonably interpret it differently?
- Does a lot depend on it?

Skip function signatures, helper names, and file-by-file mechanics when reversible and unambiguous — they add load without catching drift. **The exception is a mechanic whose wrong version still passes green** — normalization order, checkpoint/artifact identity, gene/index alignment, unit conversions, seed/split handling. These corrupt results silently, so they belong in the contract despite looking low-level. **The real filter is silent-corruption risk, not altitude.**

## Steps

Steps 1–7 are **analysis — do them all before writing the plan file**, then compose the document in one pass (see Output). An actionable finding from step 6 folds into the material of steps 2–4, so writing sections as you go means patching already-written prose — which is exactly what creates duplication, contradictions, and sections that do not flow.

1. **Verify load-bearing assumptions.** Before writing the contract, check every fact it rests on — an attribute chain, which op is last in a function, whether a code path is active, a file's shape — **against the actual source, not the spec or memory.** These are read-only checks (Read, grep, a scoped in-memory probe); plan mode allows them, so do them now, not at implementation time.

   Delegate the reading to **one read-only Haiku subagent** when it means opening whole files or several sources (those dumps are skim-and-discard — keep them out of your context); do it inline for a couple of targeted greps, where a round-trip costs more than it saves. Use more than one agent only for genuinely separate areas. **Have the agent return evidence (file:line + what is there), NOT a verdict — you draw the verified / inferred / ruled-out conclusion.**

   Record each fact in the verification block (see Output), tagged verified (with how) vs inferred. **A claim you could have checked read-only but did not is an omission, not an assumption.** Defer only genuinely mutating checks (a full test run, anything that writes) — flag those as pre-implementation steps.

2. **Acceptance oracle.** State the behaviors the finished work must show, as concrete input→output checks. **Give each a short name and refer to it by name, never by bare number** — numbers force the reader to scroll back. **At least one check must have an oracle independent of the implementation** — parity with existing behavior on real data, a hand-labeled gold set, or a user-specified criterion — and call out which one it is. "All tests pass" does not count alone: **the agent writes both tests and code, so green only proves self-consistency.**

3. **What stays unchanged.** State what is out of scope or behavior-preserving. For a refactor: **which outputs, metrics, and interfaces must be identical before and after.** This catches "I thought this was invisible but a metric moved."

4. **Ranked decisions and assumptions.** List decisions a competent engineer could have made differently, including ones already resolved. **Rank most-expensive-to-reverse first**, resolved and open together, so a high-impact resolved call still surfaces near the top for a final scan.
   - Open: the options, what is proposed, why, and cost to reverse after merge.
   - Resolved: mark `[resolved]` + a one-line statement of what was decided — nothing more; these are to sanity-scan, not re-litigate.

   **Against a tight spec most decisions are resolved and this section is short — do not pad it by restating the spec.** The value is the one or two genuinely-open calls plus any silent-corruption mechanic.

   **Ask-now bar (governs both open decisions here and input-needed adversarial findings in step 6):** raise a decision with AskUserQuestion **before** ExitPlanMode only if it blocks writing a coherent plan, or it is both expensive-to-reverse and genuinely open (no sensible default). Otherwise list it here for approval-time reaction — ExitPlanMode is that reaction point. **Never spawn a question for a decision that could simply be listed.**

5. **Silent guesses.** List anything guessed from an ambiguous request where being wrong would matter, and **for each, what changes if the opposite is true.** Omit guesses whose answer is obvious (a backward-compatible default any reader would assume) — that is filler.

6. **Adversarial misread.** Identify any interpretation or outcome that satisfies every acceptance check yet is still not what the user wants — there may be none, one, or several. **Report only the ones that genuinely hold; do not invent one to satisfy this step.** Features: a reading that passes the checks but builds the wrong thing. Experiments: the confound under which the headline looks like success but does not support the claim — leakage, domain shift, circularity, a metric moving for the wrong reason. **A plausible misread means the checks are underspecified — tighten them, or carry the confound into the writeup as a caveat.**

   Generate candidates with **a fresh subagent, NOT the plan's author** (the author is anchored to the framing that created the blind spot) — **Sonnet by default; Opus only for confound-heavy experimental plans** (leakage, circularity, confounded metrics), where the reasoning is hardest; do not default to Opus, since widened input beats model tier. Give it the intended change (an outline is enough — the doc need not be written yet), the step-2 checks, the goal, and the verification block — **but NOT your generation reasoning**, so it stays un-anchored. Prompt it to (a) find the misread/confound, ranked by impact, and (b) sanity-check the verification, re-digging only the spots whose method or evidence looks wrong — it reuses step 1 rather than re-verifying — and to return "no plausible misread" rather than manufacture one.

   **Then adjudicate yourself — do NOT paste raw candidates into the contract.** Judge each for soundness, verifying cheaply against code where checkable; a candidate that would change an acceptance check must clear a read-only check before it counts. Discard noise, merge duplicates. Then **route each surviving finding — do NOT leave a standalone critique section for the user to read.** A finding has exactly one destination:
   - **Actionable** (a fix, or a stronger check): fold it into the plan itself — the Change, the acceptance checks, or what-stays-unchanged — with a terse inline reason where it lands. The user gets the correction by reading the plan, not a critique. **Exception: a fix addressing a silent-corruption risk** (normalization order, checkpoint/artifact identity, gene/index alignment, unit conversions, seeds/splits) **must land in verified-facts or ranked-decisions with its reason — never folded into implementation mechanics (Change), which the user skims.**
   - **Needs a decision only the user can make**: handle it by the step-4 ask-now bar — AskUserQuestion **before** ExitPlanMode if it blocks the plan or is expensive-and-open, otherwise list it in ranked decisions for approval-time reaction. **Never bury an input-needed item in a section the user may skip at the approve stage**, and never spawn a question for one that could just be listed.
   - **Caveat that cannot be fixed** (it changes how a green suite or a result should be read): fold it into the oracle note, a limitations line, or — for an experiment — the writeup caveat.

   Record every candidate — folded, caveated, dismissed, or raised — with its disposition in the fenced audit trail (see Output). If nothing survived, say so there. This catches confound/underspecification drift only — it does not replace the user's review, the sole check for the plan faithfully encoding the wrong intent.

7. **Boundary examples (optional).** If behavior is subtle, give before→after examples at the boundaries (empty, single, malformed) and at the step-4 uncertain decisions — not happy-path examples, which are easy to approve and rarely where drift lives.

## Output

Write the plan file in the single pass described above, once the adversarial findings are adjudicated and routed. The document is the free-form plan followed by a `## Plan Contract` section, in this order:

- **Verified before planning** — the step-1 facts, each with how it was checked (file:line / probe) and a verified / inferred tag. This keeps the rest of the plan clean of inline tags.
- **Acceptance oracle** — the named checks, independent one called out.
- **What stays unchanged.**
- **Ranked decisions and assumptions.**
- **Silent guesses.**
- **Adversarial audit trail (skip unless auditing)** — fenced, clearly labelled; every adversarial candidate with its disposition (folded into <where> / caveat / dismissed: why / raised with the user). The user does not need to read this to get the benefit — actionable findings are already in the plan above, and anything needing input was asked before the plan was finalized. Kept only so the reasoning is auditable. Omit only if the adversarial step produced nothing at all.
- **Boundary examples** (optional).

There is deliberately no standalone "adversarial misread" section to read at approval — its findings live in the plan, in the questions already asked, or in this fenced trail.

**After composing, read the whole file once, end to end** — this is where reconciliation actually happens and where you catch duplication, contradiction, and sections that do not flow. Do not rely on incremental edits to keep the document coherent; if a later change forces edits, re-read the whole file, not just the edited span.

**Reconcile with the plan body — the contract and the free-form plan are one document; do not say the same thing twice.** Split ownership: the contract owns the verified facts, the acceptance checks, the invariants (what stays unchanged), and the decisions and their rationale; the body owns the problem statement, the implementation mechanics, the file list, and how to run it. Resolve overlap by **trimming the body to defer to the contract** — Context gives *why*, not the verified-facts list; Tests names the files and run command, not what-must-be-true; Change states what is built, not the rejected alternatives. Do NOT resolve it by cross-referencing out of the contract into the body — that reintroduces the scroll-back the named checks removed. The contract must read self-contained.

**Keep it skimmable — the acceptance oracle and the ranked decisions are the load-bearing parts.** Refer to checks by name, not number. **Prefer plain words over jargon** — a term the reader must decode is friction. Then **ask the user to confirm the acceptance oracle and the ranked decisions, and do not begin implementation until the contract is approved.**

For a multi-PR series, establish the shared verified facts and the cross-series invariants **once in a series preamble** (the parity items that stay green until the old path is deleted). Per-PR contracts build on that preamble and cover only PR-local deltas — do not re-run whole-series verification or re-derive shared facts per PR.
