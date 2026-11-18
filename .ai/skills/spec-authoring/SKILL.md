---
name: spec-authoring
description: >
  Use when turning an approved request into IMPLEMENTATION_SPEC.md or revising a SPEC before
  implementation. Do NOT use for ADR/TD entries (use adr-writing) or UI contracts (use
  ui-contract-authoring).
version: 1.0.0
consumers:
  - architect
---

# Spec Authoring

## Activation Criteria

- **Applies when:** a new feature, phase, bug fix or decision needs an implementation contract;
  an existing SPEC needs revision before implementation; an oversized SPEC must be split.
- **Does NOT apply when:** the task is recording a decision (`adr-writing`), creating/revising
  the UI contract (`ui-contract-authoring`), or implementing code (`code-executor`).

## Environment & Prerequisites

- Read `.ai/README.md` (context map and write ownership), `.ai/PROJECT_BRIEF.md`,
  `.ai/CONSTITUTION.md`, `.ai/CONVENTIONS.md`, `.ai/ARCHITECTURE.md`, `.ai/ROADMAP.md`,
  `.ai/IMPLEMENTATION_SPEC.md`, the Open section of `.ai/history/ISSUES.md` and
  `.ai/templates/SPEC.md`.
- Read `.ai/ECOSYSTEM_COMPATIBILITY.md` when the request depends on a version fact; read
  `.ai/contracts/UI_SPEC.md` + `.ai/contracts/DESIGN.md` when `ui_scope != none`.
- Read `.ai/history/DECISIONS.md` by ID for decisions the SPEC references.
- No tools required beyond read/grep; the architect writes the SPEC after human approval.

## Technical Guidelines & Best Practices

1. **Write for a cold-start executor.** The SPEC is the only contract that survives the
   architect session; no requirement may live only in chat.
2. **Scope first.** State what is in and explicitly out. If the request spans two independent
   outcomes, split it into two SPECs.
3. **Exhaustive file list.** Every file the executor will touch must appear in §2 with an action
   (`create`/`modify`/`delete`) and a layer. Include tests, docs, packaging and `.ai/` state files.
4. **Interfaces before steps.** Declare public functions, dataclasses, CLI commands, JSON keys,
   error types and what must not change. Link the relevant decision IDs.
5. **Ordered, verifiable steps.** Each step names its target files, instructions, required tests
   and an observable verification. Order bottom-up: registry/engine → probes → CLI → GUI →
   tests/docs, unless a dependency forces another order.
6. **Verification is executable.** Use exact commands (`python -m pytest`, `ruff check .`,
   `python -m build`, `mypy aasbridge` when applicable) and explicit manual steps for GUI/Docker.
7. **DoD is testable.** No “works well” items; every checkbox must map to evidence.
8. **UI gates.** `ui_scope: none|ui|shell`; `ui: ui` requires `design_ref` and a contract update;
   `ui: shell` additionally requires a decision. Cover the four data states and EN/ES.
9. **Dependencies and decisions.** A new/changed dependency needs an approved ADR/TD and a
   `dependency-review` verdict; link both in §3/§8.
10. **No placeholders.** Replace every angle-bracket field with real content; no unresolved placeholder at approval.

## Execution Workflow

1. **Inspect:** confirm the request and preconditions; read the context; debate 3-4 rounds with
   the human (why it matters, 2-4 options, one recommendation); map the request to files,
   interfaces, data, dependencies, UI scope and verification.
2. **Execute:** draft the SPEC from `.ai/templates/SPEC.md`; fill §1-§8; set the gates; link the
   decisions/evidence; define the exact verification commands and manual steps; keep the file
   list inside the write scope.
3. **Verify:** run this checklist before asking for `APROBADO`:
   - [ ] Scope and out-of-scope are explicit.
   - [ ] Every step has target files, tests and an observable verification.
   - [ ] Every file is inside the declared write scope.
   - [ ] Dependency/interface/UI changes link to accepted decisions/contracts.
   - [ ] UI gates are coherent; four states and EN/ES are covered when applicable.
   - [ ] No unresolved angle-bracket or template placeholder remains.
   - [ ] The human approved the scope; after approval, write the SPEC with `Status: active`.

## Edge Cases & Resilience

- **Missing or contradictory information:** stop and ask; never invent a path, schema or version.
- **Oversized request:** split into sequential SPECs with explicit dependencies.
- **UI change without a contract:** stop; run `ui-contract-authoring` first.
- **Dependency without a decision:** stop; run `dependency-review` + `adr-writing` first.
- **Public interface change:** require an ADR/TD and a migration/verification plan.
- **Pre-existing unrelated defects:** list them as follow-ups; do not expand the SPEC.

## Error Prevention & Anti-Patterns

- ⚠️ **Vague step:** “implement detection” with no files or verification.
  ✔️ Name `aasbridge/engine/detect.py`, the detection cases and the exact test command.
- ⚠️ **Chat-only requirement:** a detail agreed in conversation but absent from the SPEC.
  ✔️ Write it in §1/§3/§4 before approval.
- ⚠️ **Unbounded file list:** “touch whatever is needed”.
  ✔️ Enumerate every file; an unlisted file is a stop for the executor.
- ⚠️ **UI by intuition:** no `design_ref`, no tokens, no states.
  ✔️ Update the UI contract first and reference it in the SPEC.
- ⚠️ **Self-approval:** the architect marks the SPEC approved.
  ✔️ The human approves; the reviewer audits the implementation.
