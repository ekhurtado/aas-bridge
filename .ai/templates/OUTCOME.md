# templates/OUTCOME.md — Archived Cycle Outcome Template

> Output: `history/specs/SPEC-XXX_<slug>/OUTCOME.md`. Write it at close, after reviewer `PASS`
> and human approval. The archived `SPEC.md` is an exact copy of the closed live SPEC.

```md
# OUTCOME — SPEC-XXX <feature title>

> Closed: YYYY-MM-DD | Verdict: PASS | Phase: N
> Session: [SES-XXX](../../SESSION_LOG.md) | Reviewer: PASS (loop N)

## 1. What shipped

<One paragraph: the capability delivered and the user-visible result.>

## 2. Files changed

| File | Action | Notes |
|---|---|---|
| `<path>` | create / modify / delete | <one line> |

## 3. Verification evidence

- Build: `<command>` → <result>
- Tests: `<command>` → <result>
- Lint: `<command>` → <result>
- Typecheck: `<command>` → <result/N/A>
- Contract/grep: `<command>` → <result>
- UI: <four states, EN/ES, tokens, accessibility>
- Manual verification: <environment, inputs, steps, observed result>
- Reviewer: `QA-REPORT` verdict + loop number

## 4. DoD

- [ ] All SPEC steps verified.
- [ ] No changes outside the SPEC file list.
- [ ] Reviewer `PASS`.
- [ ] Manual verification recorded.
- [ ] `.ai/` state updated.

## 5. Follow-ups

| ID | Type | Severity | Summary | Owner |
|---|---|---|---|---|
| ISS-XXX | BUG / TECH-DEBT | CRITICAL / MAJOR / MINOR | <summary> | <owner> |

## 6. Commit

- **Message:** `<type>(<scope>): <summary>`
- **Hash:** `pending human commit` (never invent a hash)
```

## Checklist

- [ ] SPEC and OUTCOME are archived together.
- [ ] Every verification item cites a real result.
- [ ] Follow-ups are recorded in `history/ISSUES.md`.
- [ ] The live SPEC is reset to `Status: none`.
- [ ] No secrets or personal data are recorded.
