---
name: spec-compliance-audit
description: >
  Use when auditing an executor handoff against the active SPEC and diff (SPEC §2-§7,
  CONVENTIONS, CONSTITUTION), using verification and manual evidence to classify defects and
  produce a PASS/FAIL report. Do NOT use when only running checks (use verification-gate) or
  validating manual evidence (use manual-verification).
version: 1.0.0
consumers:
  - reviewer
---

# SPEC Compliance Audit

## Activation Criteria

- **Applies when:** a code-executor handoff must be audited against the active
  `IMPLEMENTATION_SPEC.md` and the working-tree diff, before a `PASS`/`FAIL` verdict.
- **Does NOT apply when:** only running the declared commands (`verification-gate`), validating
  the human's manual evidence (`manual-verification`) or reviewing UI-specific compliance
  (`ui-review`).

## Environment & Prerequisites

- Read `.ai/IMPLEMENTATION_SPEC.md`, the diff (`git diff`, `git status`), `.ai/CONVENTIONS.md`,
  `.ai/CONSTITUTION.md`, the relevant section of `.ai/ARCHITECTURE.md`, the Open section of
  `.ai/history/ISSUES.md` and the executor handoff.
- Read `.ai/contracts/UI_SPEC.md` + `.ai/contracts/DESIGN.md` when the diff touches UI; read
  `.ai/history/DECISIONS.md` by ID when the SPEC cites a decision.
- The `verification-gate` evidence and the human manual evidence are inputs, not assumptions.

## Technical Guidelines & Best Practices

1. **Audit the SPEC, not the code in the abstract.** Map §2 files → diff, §3 interfaces → code,
   §4 steps → changes, §5 verification → evidence, §6 DoD → results, §7 stop triggers → events.
2. **Every DoD item needs evidence.** A claim in the handoff is not evidence.
3. **Classify defects:**
   - `CRITICAL`: law/interface/data-loss/security breach, unlisted file, unverified DoD item,
     forbidden dependency, silent gate pass.
   - `MAJOR`: missing required behaviour/test, contract drift, wrong/failed verification.
   - `MINOR`: style, docs, non-blocking tech debt.
4. **No scope creep.** Do not audit unrelated pre-existing issues unless they block the SPEC.
5. **Verdict rule:** `PASS` only when every DoD item has evidence and only `MINOR` issues remain;
   otherwise `FAIL`.
6. **Cite precisely.** Every defect has a `file:line`, a rule ID and a required fix.
7. **Loop cap.** Maximum two rework loops; a third failure is an escalation, not another `FAIL`.
8. **Laws and conventions.** Check GPL-3.0, `pyproject.toml` as the dependency source, no
   secrets, Spanish chat/English artifacts, fail-closed, evidence gate, input mutation, UI
   contract/i18n.
9. **No invention.** Never fabricate a command result, hash, date or evidence source.
10. **Report in English**, summarize in Spanish if addressing the human.

## Execution Workflow

1. **Inspect:** confirm the SPEC ID, status, human approval and handoff completeness; read the
   diff and the evidence; count the review loop; identify the SPEC sections and DoD items.
2. **Execute:** walk §2-§7 and the DoD; for each item record `PASS`/`FAIL`/`N/A` with the exact
   evidence; classify each defect; check the laws/conventions/UI/dependencies; decide the verdict.
3. **Verify:** re-read the report and remove any claim without evidence; ensure every defect is
   actionable; ensure the verdict is consistent with the defect list; state the next step (close
   or rework prompt).

## Edge Cases & Resilience

- **Unlisted file:** `CRITICAL`; the executor must remove it or the SPEC must be amended by the
  architect (never by the reviewer).
- **Missing evidence:** `FAIL`; request the exact command/result.
- **Ambiguous SPEC:** stop with a blocker; do not interpret.
- **Pre-existing issue:** note it as a follow-up, not a defect of this SPEC, unless it blocks.
- **Generated/vendored files:** verify the generator/attribution, not the raw diff.
- **Dependency change:** require `dependency-review` + the ADR/TD.
- **Manual-only item:** route to `manual-verification`; do not mark it verified from code reading.

## Error Prevention & Anti-Patterns

- ⚠️ **Claim-based approval:** “the tests pass” with no output.
  ✔️ Require the command, exit code and result.
- ⚠️ **Unlisted files approved:** “it was needed”.
  ✔️ `CRITICAL`; the SPEC must be amended before the file is accepted.
- ⚠️ **Auditing unrelated code:** expanding the review beyond the SPEC.
  ✔️ Note it as a follow-up; keep the verdict scoped.
- ⚠️ **Accepting placeholders:** TODO/`pass`/fake returns in the diff.
  ✔️ `CRITICAL` or `MAJOR` depending on the path.
- ⚠️ **Self-approval:** the executor or reviewer approves its own work.
  ✔️ Human approves the close; the reviewer is independent.
