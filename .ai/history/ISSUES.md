# history/ISSUES.md — AAS Bridge Issues Ledger

> **Tier:** HISTORY (cold archive, but the Open section is read at session start).
> **Writer:** Executor (append/update open issues); the Reviewer subagent reports findings in
> chat and the Executor records them. Resolved issues are moved to the Resolved section at close.
> **IDs:** `ISS-XXX` are stable and never reused.
> **Language:** English entries; Spanish conversation.

## Open

| ID | Type | Severity | Origin | Summary | Status |
|---|---|---|---|---|---|
| ISS-001 | BLOCKER | MAJOR | bootstrap | Repository has no initial commit; `git diff` has no baseline for the reviewer. | Open — owner: human. Run `git add .` + initial commit before SPEC-001. |
| ISS-002 | TECH-DEBT | MAJOR | bootstrap | No `pyproject.toml`, package skeleton or tests exist; build/test commands are not runnable yet. | Open — owner: executor. Resolve in SPEC-001. |
| ISS-003 | TECH-DEBT | MINOR | bootstrap | `ruff` and `mypy` are not installed in the local environment. | Open — owner: executor. Add as dev dependencies in SPEC-001; `mypy` optional. |
| ISS-004 | BLOCKER | MINOR | bootstrap | Docker is not installed locally; the optional Docker smoke test cannot run on this machine. | Open — owner: human. Accept `N/A` until Docker is available. |

## Resolved

*(none yet)*

## Entry Format

```md
## [ISS-XXX] <short title>
- **Type:** SPEC-AMBIGUITY | BLOCKER | QA-REJECTION | BUG | TECH-DEBT
- **Severity:** CRITICAL | MAJOR | MINOR
- **Origin spec:** [SPEC-XXX](history/specs/SPEC-XXX_<slug>/SPEC.md)
- **Opened:** YYYY-MM-DD | **Resolved in:** [SES-XXX](history/SESSION_LOG.md) (YYYY-MM-DD)
- **Root cause:** <why it happened>
- **Resolution:** <exact fix, file:line, commit>
- **Rule:** <CONSTITUTION/CONVENTIONS rule involved, if any>
```

> Archive convention: when an issue is resolved and verified, move its entry to the Resolved
> section (or to `history/specs/SPEC-XXX_<slug>/OUTCOME.md` when it belongs to a closed cycle)
> and keep the `ISS-XXX` ID.
