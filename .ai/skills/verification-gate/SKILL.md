---
name: verification-gate
description: >
  Use when closing a SPEC step or preparing a review handoff requires running the declared
  build/test/lint/typecheck/grep checks and recording PASS/FAIL/N/A with exact evidence. Do NOT
  use for test design (use python-testing), manual evidence (use manual-verification) or the
  final verdict (use spec-compliance-audit).
version: 1.0.0
consumers:
  - code-executor
  - reviewer
---

# Verification Gate

## Activation Criteria

- **Applies when:** a SPEC step is closed, a review handoff is prepared, or the reviewer must
  reproduce the declared checks for a verdict.
- **Does NOT apply when:** designing tests (`python-testing`), validating the human's manual
  evidence (`manual-verification`) or deciding the final `PASS`/`FAIL`
  (`spec-compliance-audit`).

## Environment & Prerequisites

- Read the SPEC §5 verification block and the SPEC §4 step verifications. The SPEC is the only
  source of the commands; do not invent additional checks.
- `pyproject.toml`, the package, the tests and the fixtures must exist (SPEC-001 creates them).
- Local environment: Python 3.12.10, `pytest` 9.1.1, `ruff`/`mypy` as dev dependencies,
  Docker optional (may be absent).
- No network unless the SPEC declares a network check.

## Technical Guidelines & Best Practices

1. **Run exactly what the SPEC declares.** No extra commands, no skipped commands.
2. **Record the command, exit code and a short result** for each check.
3. **Use `PASS`/`FAIL`/`N/A`:** `N/A` requires a reason (e.g. Docker not installed, packaging not
   changed).
4. **Do not tick a checkbox without a result.** A failed check keeps the step open.
5. **Build:** `python -m build` when packaging changes.
6. **Tests:** `python -m pytest`; focused tests when the SPEC declares them; integration/network
   tests only when declared.
7. **Lint/format:** `ruff check .`, `ruff format --check .`.
8. **Typecheck:** `mypy aasbridge` when the SPEC declares it (optional).
9. **Contract/grep checks:** exact patterns and expected output; include the command.
10. **UI checks:** four states, EN/ES catalogs, no literal tokens, accessibility, native/Docker
    behavior; record manual evidence separately.
11. **No hidden failures:** a red check is reported, not retried until green or omitted.
12. **Evidence format:** a markdown table or list with `Check | Command | Result | Evidence`.

## Execution Workflow

1. **Inspect:** list the declared checks from SPEC §5 and §4; confirm the working directory and
   that the required tools are available; mark obvious `N/A` items with a reason.
2. **Execute:** run each check in order; capture the exit code and the relevant output; do not
   modify the code to make a check pass (that is a new implementation step).
3. **Verify:** confirm every check has a result; confirm the evidence is reproducible; report the
   table to the executor/reviewer; leave failed checks open and describe the next action.

## Edge Cases & Resilience

- **Command not installed:** report `FAIL` or `N/A` with the reason; do not silently skip.
- **Timeout / memory:** report the failure and the environment; do not retry indefinitely.
- **Environment mismatch:** record the Python/OS/tool versions; the reviewer must be able to
  reproduce.
- **Docker absent:** `N/A` with a reason; the Docker smoke test is optional.
- **Flaky test:** mark it and report; do not hide it with a retry loop.
- **Partial run:** report the checks that ran and the ones that did not; no overall `PASS`.

## Error Prevention & Anti-Patterns

- ⚠️ **Skipping checks:** “not needed”.
  ✔️ Run it or mark `N/A` with a reason.
- ⚠️ **Ticking without evidence:** a checkbox with no command/result.
  ✔️ Record the exact evidence.
- ⚠️ **Running undeclared commands:** inventing a new lint/test suite.
  ✔️ The SPEC defines the checks; propose an amendment if a gap exists.
- ⚠️ **Hiding a failure:** re-running until it passes or omitting the red line.
  ✔️ Report the failure and keep the step open.
- ⚠️ **Comparing against claims:** trusting the handoff without running the check.
  ✔️ Reproduce it.
