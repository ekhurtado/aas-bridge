# templates/TEMPLATES.md — Template Index

> Blank skeletons for future entries. The live state lives in the corresponding `.ai/<file>`.
> Do not fill these templates with the current project state.

| Template | Use when | Output |
|---|---|---|
| `SPEC.md` | A new feature/change is approved for planning | Active `.ai/IMPLEMENTATION_SPEC.md`; archived `history/specs/SPEC-XXX_<slug>/SPEC.md` |
| `DECISIONS.md` | A decision changes law, architecture, interfaces, dependencies or topology | Append to `history/DECISIONS.md` |
| `ISSUES.md` | A blocker, ambiguity, defect or tech-debt item is found | Append/update `history/ISSUES.md` |
| `SESSION_LOG.md` | A cycle closes | Append to `history/SESSION_LOG.md` |
| `OUTCOME.md` | A cycle is archived | `history/specs/SPEC-XXX_<slug>/OUTCOME.md` |
| `PROMPTS.md` | The human launches an agent or closes a cycle | Chat prompt; not persisted |

Rules:

- Templates are static; agents read them, never edit them.
- Every template uses English placeholders; conversation remains Spanish.
- A closed archive (`history/specs/**`) is immutable; use a new `ISS-XXX` or a new cycle for
  corrections.
