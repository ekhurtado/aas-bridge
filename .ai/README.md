# AAS Bridge — AI Workspace Context

> Read this file first. It indexes the AI-assisted engineering context of this repository.
> `CONSTITUTION.md` wins on any conflict with this file.
> Last update: 2026-11-18 (AI architecture bootstrap; see `history/SESSION_LOG.md` SES-002).

## 1. What this repository is

`AAS_bridge` is the home of **AAS Bridge**: a standalone Python tool that detects, diagnoses,
validates and migrates AASX packages across AAS metamodel versions (e.g. V3.0 ↔ V3.1), and
keeps a verified registry of the version ecosystem around the AAS standard (IDTA
specifications, basyx-python-sdk, AASX Package Explorer, SMIA).

It originates from a real production problem of SMIA: AASX files authored with a different
toolchain generation cannot be read by SMIA's pinned basyx-python-sdk, and the failure is
**silent** (empty object store, generic error, no mention of versions). The tool and the
deferred SMIA runtime layer are the two coordinated answers.

## 2. Context map / load policy

| File | Tier | Purpose | Load when |
|---|---|---|---|
| `PROJECT_BRIEF.md` | static | Vision, problem, goals, non-goals, success criteria, stack, constraints, phase | Always |
| `CONSTITUTION.md` | static | Non-negotiable laws (L0-L3) | Always; wins on conflict |
| `CONVENTIONS.md` | static | Naming, layout, interfaces, tests, git, UI standards | Before writing code or tests |
| `ARCHITECTURE.md` | static | System model, invariants, evidence gate, deployment, decision index | Any design or implementation work |
| `ECOSYSTEM_COMPATIBILITY.md` | evidence | Verified compatibility matrices, corpus evidence, sources | Whenever a version fact matters |
| `SMIA_RUNTIME_COMPAT_LAYER.md` | evidence | Saved design for the deferred SMIA layer | Only when working on Track S / the SMIA repo |
| `ROADMAP.md` | live | Phased plan with acceptance criteria | Planning and progress tracking |
| `IMPLEMENTATION_SPEC.md` | live | Active SPEC only (`Status: none` when idle) | Every implementation session |
| `contracts/UI_SPEC.md` | static | UI shell, navigation, primitives, states, accessibility, i18n | UI work (`ui_scope != none`) |
| `contracts/DESIGN.md` | static | Semantic tokens, typography, spacing, themes | UI work |
| `history/DECISIONS.md` | history | ADR/TD ledger (append-only) | Before changing a decision; by ID |
| `history/ISSUES.md` | history | Open + resolved issues (`ISS-XXX`) | At session start (open section) and at close |
| `history/SESSION_LOG.md` | history | Session index (`SES-XXX`) | At close; by ID on demand |
| `history/specs/` | history | Archived SPEC + OUTCOME per cycle | By ID on demand; never bulk-loaded |
| `templates/` | static | Blank SPEC, decision, issue, session, outcome and prompt templates | Only when creating an entry |
| `agents/` | static | Agent definitions and §7 skill interfaces | Human/harness; not runtime context |
| `skills/` | static | Skill procedures loaded on demand | According to each agent §7 trigger |

Rules:

- Never bulk-load `history/`; access entries by ID or grep.
- The evidence files (`ECOSYSTEM_COMPATIBILITY.md`, `SMIA_RUNTIME_COMPAT_LAYER.md`) are
  read-only for the executor and are never imported by source code.
- Skills are injected just-in-time; the full catalog is never loaded.

## 3. Tree

```text
.ai/
├── README.md
├── PROJECT_BRIEF.md
├── CONSTITUTION.md
├── CONVENTIONS.md
├── ARCHITECTURE.md
├── ECOSYSTEM_COMPATIBILITY.md
├── SMIA_RUNTIME_COMPAT_LAYER.md
├── ROADMAP.md
├── IMPLEMENTATION_SPEC.md
├── contracts/
│   ├── UI_SPEC.md
│   └── DESIGN.md
├── history/
│   ├── DECISIONS.md
│   ├── ISSUES.md
│   ├── SESSION_LOG.md
│   └── specs/
│       └── README.md
├── templates/
│   ├── TEMPLATES.md
│   ├── PROMPTS.md
│   ├── SPEC.md
│   ├── DECISIONS.md
│   ├── ISSUES.md
│   ├── SESSION_LOG.md
│   └── OUTCOME.md
├── agents/
│   ├── architect.md
│   ├── code-executor.md
│   └── reviewer.md
└── skills/ (13 skills; see root `AGENTS.md` and each agent's §7)
```

## 4. Agent topology

Two primary agents and one reviewer subagent:

| Agent | Mode | Path | Mission |
|---|---|---|---|
| `architect` | primary | `.ai/agents/architect.md` | Debates with the human and produces the approved `IMPLEMENTATION_SPEC.md`; owns decisions, roadmap and UI contracts |
| `code-executor` | primary | `.ai/agents/code-executor.md` | Implements the SPEC, runs the declared verification, invokes the reviewer subagent and updates the `.ai/` state |
| `reviewer` | subagent | `.ai/agents/reviewer.md` | Read-only audit of the executor handoff; returns `PASS`/`FAIL` with evidence |

Flow:

```text
Human request -> Architect (debate) -> approved SPEC -> Code Executor
  -> implementation + checks -> Reviewer subagent (PASS/FAIL)
  -> fixes or human manual verification -> close (executor prepares, human approves)
```

The human is the final gate. No agent commits, pushes, tags or publishes.

## 5. Write ownership

| File / area                                                                                           | Writer | Notes |
|-------------------------------------------------------------------------------------------------------|---|---|
| `PROJECT_BRIEF.md`, `CONSTITUTION.md`                                                                 | human (architect may edit with `ask`) | Vision/law; changes need a decision |
| `CONVENTIONS.md`, `ARCHITECTURE.md`                                                                   | architect (with `ask`) | Standards/design; changes need a decision |
| `ECOSYSTEM_COMPATIBILITY.md`, `SMIA_RUNTIME_COMPAT_LAYER.md`                                          | architect (with `ask`) | Evidence; append/supersede, never delete |
| `IMPLEMENTATION_SPEC.md`                                                                              | architect (full); executor (checkboxes + `Status` only) | Cold-start contract |
| `contracts/UI_SPEC.md`, `contracts/DESIGN.md`                                                         | architect (with `ask`) | UI contract; visual changes need a decision |
| `ROADMAP.md`                                                                                          | architect (scope); executor (progress at close) | Live plan |
| `history/DECISIONS.md`                                                                                | architect (append only) | ADR/TD ledger |
| `history/ISSUES.md`                                                                                   | executor (append/update); reviewer reports in chat | Open + resolved |
| `history/SESSION_LOG.md`, `history/specs/`                                                            | executor at close, after human approval | Append-only |
| `aas-bridge/`, `tests/`, ...  →  `src/aas_bridge/`, `tests/`, `docs/`, `pyproject.toml`, `MANIFEST.in` | executor | Only files declared in the SPEC (src layout per ADR-024) |
| `agents/`, `skills/`, `templates/`                                                                    | human (bootstrap) | Static; agents may read |

## 6. IDs, links and rotation

- IDs: `SPEC-XXX` (sequential), `SES-XXX`, `ADR-XXX`, `TD-XXX`, `ISS-XXX`; stable, never reused.
- Links: standard Markdown, repo-root-relative. No Obsidian syntax inside `.ai/`.
- Rotation: at close, archive `SPEC.md` + `OUTCOME.md` under `history/specs/SPEC-XXX_<slug>/`,
  append `SESSION_LOG.md`, update `ISSUES.md`, tick `ROADMAP.md`, and reset the live SPEC to
  `Status: none`.

## 7. Language

- Conversation with the human: **Spanish**.
- Code, commands, identifiers, technical documentation and artifacts: **English**.
- UI: **bilingual EN/ES**; every user-facing string must exist in both locales; technical AAS
  terms stay in English.

## 8. Current state

- AI architecture bootstrap: complete (2026-11-18).
- SPEC-001 rev 2 active (2026-11-18): Phase 1 headless core implemented and re-opened for
  the human-approved rename consolidation — distribution `aas_bridge`, import package
  `aas_bridge`, CLI `aas_bridge`, canonical `src/aas_bridge/` layout (ADR-024); licence
  GPL-3.0 (ADR-023). The rev 1 reviewer PASS is invalidated; full §5 re-verification and a
  reviewer re-audit are required before the close.
- Decisions: ADR-020 superseded by ADR-023; ADR-022 superseded by ADR-024; TD-001
  superseded by TD-002.
- Next: executor completes the rename (reinstall, build, §5, ISS-007), reviewer re-audits,
  human manual verification; then the close and SPEC-002 (GUI + Docker).