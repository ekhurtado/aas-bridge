---
name: adr-writing
description: >
  Use when a decision changes law, architecture, interfaces, dependencies or agent topology and
  an ADR/TD entry plus decision index row must be written. Do NOT use for the implementation SPEC
  (use spec-authoring) or licence verification (use dependency-review).
version: 1.0.0
consumers:
  - architect
---

# ADR / TD Writing

## Activation Criteria

- **Applies when:** a change affects `CONSTITUTION.md`, `ARCHITECTURE.md`, a public interface, a
  dependency, the UI visual baseline, the agent topology or a process invariant.
- **Does NOT apply when:** the task is writing the implementation SPEC (`spec-authoring`),
  creating the UI contract (`ui-contract-authoring`) or auditing a dependency licence
  (`dependency-review`).

## Environment & Prerequisites

- Read `.ai/history/DECISIONS.md` (existing entries and IDs), the decision index in
  `.ai/ARCHITECTURE.md` §8, `.ai/CONSTITUTION.md`, `.ai/CONVENTIONS.md` and
  `.ai/templates/DECISIONS.md`.
- Gather the alternatives, the evidence (probe, corpus test, official source with date or a
  prior decision ID) and the human's approval.
- For a dependency decision, obtain the `dependency-review` verdict first.

## Technical Guidelines & Best Practices

1. **One decision per entry.** Do not bundle unrelated choices; split them.
2. **At least two alternatives**, including the rejected one and why.
3. **Decision + justification + trade-offs + revisable when.** A decision without trade-offs is
   incomplete.
4. **Stable IDs.** Use `ADR-XXX` for architecture/process and `TD-XXX` for technical debt; never
   reuse or renumber.
5. **Append-only.** Never edit a prior entry; set `Status: Superseded by [ID]` and append the new
   one.
6. **Evidence.** Cite the probe/source/date or the decision ID that supports the choice.
7. **Index row.** Every entry adds one line to `ARCHITECTURE.md` §8.
8. **Human approval.** A decision is not accepted until the human approves it.
9. **Licence/AGPL.** A dependency decision records the licence verdict and the approved
   alternative.
10. **UI baseline.** A token or shell change records the version bump and the affected contract.

## Execution Workflow

1. **Inspect:** confirm a decision is actually required (not a convention or a SPEC detail);
   list the alternatives and the evidence; check whether an existing decision already covers it
   (then reference it instead of duplicating).
2. **Execute:** draft the entry from `.ai/templates/DECISIONS.md`; review it with the human;
   append it to `.ai/history/DECISIONS.md`; add the index row; link the decision from the SPEC,
   contract or code comment that depends on it.
3. **Verify:** the ID is unique; no prior entry was edited; the index row exists; the SPEC/contract
   references the ID; the evidence is cited; the human approved.

## Edge Cases & Resilience

- **No decision needed:** record why in the SPEC or a code comment; do not create noise.
- **Superseding:** keep the old entry, set its status and append the new one.
- **Conflicting decisions:** cite both, explain the resolution and supersede explicitly.
- **Missing evidence:** stop; do not record a decision on a guess.
- **Dependency change:** require `dependency-review` + the AGPL-3.0 verdict.
- **UI baseline change:** bump the contract version and reference the decision.

## Error Prevention & Anti-Patterns

- ⚠️ **Editing history:** rewriting an old decision.
  ✔️ Supersede with a new entry.
- ⚠️ **No alternatives:** “we chose X” with no rejected option.
  ✔️ State at least one alternative and why it lost.
- ⚠️ **Post-hoc decision:** writing the ADR after implementation to justify it.
  ✔️ Decide before the SPEC/implementation.
- ⚠️ **No trade-offs:** pretending the choice is free.
  ✔️ Record the known cost.
- ⚠️ **Missing index:** an ADR that cannot be found from `ARCHITECTURE.md`.
  ✔️ Add the one-line row.
