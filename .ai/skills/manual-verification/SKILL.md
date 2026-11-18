---
name: manual-verification
description: >
  Use when validating the human's manual evidence for GUI/Docker/AASX flows, or judging whether
  the SPEC's manual steps and expected results suffice. Do NOT use for automated checks (use
  verification-gate) or SPEC audit (use spec-compliance-audit).
version: 1.0.0
consumers:
  - reviewer
---

# Manual Verification

## Activation Criteria

- **Applies when:** a SPEC declares manual verification (GUI flow, Docker smoke test, AASX
  end-to-end behaviour, native launch) and the human provides evidence.
- **Does NOT apply when:** running the declared automated checks (`verification-gate`) or
  auditing the SPEC/diff (`spec-compliance-audit`).

## Environment & Prerequisites

- Read the SPEC's manual verification block (steps, environment, expected result) and the
  executor handoff.
- Read `.ai/templates/OUTCOME.md` for the record format.
- The human's evidence must include: environment (OS, Python, browser/Docker), input file(s),
  exact steps, observed result, expected result and date. Screenshots/logs are welcome.
- Never run a manual check on the human's behalf and claim it.

## Technical Guidelines & Best Practices

1. **Concrete and reproducible.** “Works” is not evidence; the steps must be repeatable by
   another person.
2. **Separate automated from manual.** Automated checks are `verification-gate`; manual evidence
   is the human's observation.
3. **Expected vs observed.** Compare explicitly; a mismatch is a defect, not a note.
4. **Both locales and both modes when declared.** EN/ES and native/Docker must be covered if the
   SPEC requires them.
5. **Check the files.** A migrated file must be downloadable, loadable by the target dialect and
   pass the evidence gate; the original must be unchanged.
6. **Record in the QA/OUTCOME.** Summarize the evidence, the result and any follow-up; the
   persistent record is `OUTCOME.md` and the session log.
7. **Do not tick the SPEC.** The executor marks the manual checkbox only after the human
   evidence is validated; the reviewer confirms it.
8. **No invention.** Never fabricate a screenshot, a command or a result.
9. **Environment transparency.** Note when the environment differs from the SPEC (e.g. no Docker,
   different browser).
10. **Stop on missing evidence.** Ask for the missing step/result; do not assume it passed.

## Execution Workflow

1. **Inspect:** list the SPEC's manual steps, expected results and required environments; check
   the human's evidence for each item.
2. **Execute:** walk each step; compare expected vs observed; check the output file, the gate
   result, both locales and both modes when required; record `PASS`/`FAIL`/`N/A` with the
   evidence source.
3. **Verify:** ensure every manual item is covered or explicitly `N/A`; ensure the evidence is
   reproducible; report the result and the next action (close or rework).

## Edge Cases & Resilience

- **Missing evidence:** `FAIL` or blocker; ask for the exact step/result.
- **Environment mismatch:** mark the limitation; do not claim parity you did not observe.
- **Screenshots only:** accept them as evidence for visual states, not for file validity; ask for
  the gate/file result.
- **Docker absent:** `N/A` with a reason; the Docker smoke test is optional.
- **Flaky manual behaviour:** ask for a second run and the exact conditions.
- **Non-expert user:** the steps must not require reading logs or code; if they do, improve the
  SPEC's manual steps.

## Error Prevention & Anti-Patterns

- ⚠️ **Accepting “works”:** no environment, input or steps.
  ✔️ Ask for the concrete evidence.
- ⚠️ **Inventing evidence:** a reviewer claiming a manual run.
  ✔️ Only the human provides manual evidence.
- ⚠️ **Marking without the human:** ticking the manual checkbox from code reading.
  ✔️ Wait for the human's observation.
- ⚠️ **Conflating automated and manual:** treating a unit test as a GUI verification.
  ✔️ Keep them separate.
- ⚠️ **Ignoring the output file:** checking only the UI message.
  ✔️ Download and load the file; run the gate.
