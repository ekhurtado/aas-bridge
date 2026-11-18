# templates/DECISIONS.md — ADR/TD Entry Template

> Append the entry to `history/DECISIONS.md`; never edit a prior entry. If a decision is
> superseded, set `Status: Superseded by [ID]` on the old entry and append the new one.
> Adding a decision also adds its one-line row to the decision index in `ARCHITECTURE.md`.

```md
## [ADR-XXX | TD-XXX] <short title>
- **Date:** YYYY-MM-DD | **Phase:** N | **Status:** Accepted | Superseded by [ID] | Deprecated
- **Scope:** Core | Data | Interface | UI | Feature (<name>) | Process
- **Alternatives:** A, B, C
- **Decision:** X
- **Justification:** <concrete reasons; include the evidence path or decision IDs; for a
  dependency include the licence verdict and the approved alternative>
- **Accepted trade-offs:** <known costs>
- **Revisable when:** <condition that justifies re-evaluation>
```

## Checklist

- [ ] The decision changes law, architecture, a public interface, a dependency, the UI visual
      baseline or the agent topology.
- [ ] At least two alternatives are stated, including the rejected one.
- [ ] Evidence is cited (probe, corpus test, official source with date, or decision ID).
- [ ] The human approved the decision.
- [ ] The entry is appended, not inserted or rewritten.
- [ ] The decision index in `ARCHITECTURE.md` has the new row.
- [ ] The SPEC or contract that depends on it references the decision ID.
