# templates/ISSUES.md — Issue Entry Template

> Append to the Open section of `history/ISSUES.md`; move to Resolved only after the fix is
> verified. `ISS-XXX` IDs are stable and never reused.

```md
## [ISS-XXX] <short title>
- **Type:** SPEC-AMBIGUITY | BLOCKER | QA-REJECTION | BUG | TECH-DEBT
- **Severity:** CRITICAL | MAJOR | MINOR
- **Origin spec:** [SPEC-XXX](history/specs/SPEC-XXX_<slug>/SPEC.md) | bootstrap | none
- **Opened:** YYYY-MM-DD | **Owner:** human | architect | code-executor | reviewer
- **Status:** Open | In progress | Resolved | Accepted risk
- **Summary:** <what happened and why it matters>
- **Evidence:** <file:line, command output, SPEC quote or human evidence>
- **Next action:** <what unblocks it>
```

## Resolution entry

```md
- **Resolved in:** [SES-XXX](history/SESSION_LOG.md) (YYYY-MM-DD)
- **Root cause:** <why it happened>
- **Resolution:** <exact fix, file:line, commit>
- **Rule:** <CONSTITUTION/CONVENTIONS rule involved, if any>
```

## Checklist

- [ ] The issue is real, reproducible or explicitly an accepted risk.
- [ ] Severity matches the impact (`CRITICAL` blocks the cycle; `MAJOR` must be fixed before
      close; `MINOR` can be accepted with a record).
- [ ] The origin SPEC or session is linked.
- [ ] The resolution cites evidence, not a claim.
- [ ] A resolved issue is moved, not duplicated.
