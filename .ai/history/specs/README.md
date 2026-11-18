# history/specs/ — Archived Specifications

> **Tier:** HISTORY (cold archive). Immutable after close.
> **Writer:** Executor at close, after reviewer `PASS` and human approval.
> **Access:** by `SPEC-XXX` ID or grep; never bulk-loaded.

## Convention

Each completed cycle is archived in its own folder:

```text
history/specs/SPEC-XXX_<slug>/
├── SPEC.md       # exact copy of the closed IMPLEMENTATION_SPEC
└── OUTCOME.md    # verdict, evidence, files changed, manual verification, follow-ups
```

Rules:

- Folder names use the `SPEC-XXX_<slug>` pattern; the slug is lowercase kebab-case.
- The archived `SPEC.md` is an exact copy of the closed live SPEC; do not rewrite it.
- `OUTCOME.md` follows `.ai/templates/OUTCOME.md`.
- A closed folder is immutable. Corrections are recorded as a new `ISS-XXX` or a new cycle.
- The live `.ai/IMPLEMENTATION_SPEC.md` is reset to `Status: none` after the archive.
- The archive index below is append-only.

## Archive Index

| SPEC | Slug | Closed | Verdict | Outcome |
|---|---|---|---|---|
| — | — | — | — | — |
