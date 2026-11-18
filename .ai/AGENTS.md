# AAS Bridge — Agent Instructions

> Read `README.md` first. `CONSTITUTION.md` wins on any conflict with this file.
> This file is a harness entry point, not project law. Do not duplicate law here.

## Language

- Converse with the human in **Spanish**.
- Keep code, commands, identifiers, technical docs and artifacts in **English**.
- The GUI is **bilingual EN/ES**; every user-facing string must exist in both locales.

## Available Agents

| Agent | Mode | Path | Purpose |
|---|---|---|---|
| `architect` | primary | `agents/architect.md` | Debates with the human, writes the approved `IMPLEMENTATION_SPEC.md`, decisions, roadmap and UI contracts. Never writes source code. |
| `code-executor` | primary | `agents/code-executor.md` | Implements the SPEC, runs the declared verification, invokes the `reviewer` subagent and updates the `` state. |
| `reviewer` | subagent | `agents/reviewer.md` | Read-only audit of the executor handoff against the SPEC and diff; returns `PASS`/`FAIL` with evidence. |

## Available Skills

| Skill | Consumers | Activation (short) |
|---|---|---|
| `spec-authoring` | architect | Turning an approved request into `IMPLEMENTATION_SPEC.md` or revising a SPEC. |
| `aas-version-research` | architect | A plan depends on AAS/basyx/PE/SMIA version facts or new releases. |
| `adr-writing` | architect | A decision changes law, architecture, interfaces, dependencies or topology. |
| `ui-contract-authoring` | architect | A SPEC declares `ui_scope != none` and the UI contract must be created or revised. |
| `aasx-core` | code-executor | Implementing AASX package I/O or AAS version detection. |
| `basyx-evidence-gate` | code-executor | Implementing basyx probes or the evidence gate. |
| `nicegui-frontend` | code-executor | Implementing `gui/` views over the headless core. |
| `python-testing` | code-executor | Adding or changing tests, fixtures, corpus regression or golden reports. |
| `spec-compliance-audit` | reviewer | Auditing an executor handoff against the SPEC and diff. |
| `verification-gate` | code-executor, reviewer | Running the declared checks and recording PASS/FAIL/N/A evidence. |
| `ui-review` | reviewer | The diff touches `gui/` or UI files. |
| `manual-verification` | reviewer | Validating the human's manual evidence for GUI/Docker/AASX flows. |
| `dependency-review` | architect, reviewer | A feature or diff adds, changes or removes a dependency. |

## Auto-invoke: Action → Skill

| Action | Skill |
|---|---|
| Write or revise the implementation plan | `spec-authoring` |
| Verify an AAS/basyx/PE version fact | `aas-version-research` |
| Record a decision with alternatives and trade-offs | `adr-writing` |
| Create or revise `UI_SPEC.md` / `DESIGN.md` | `ui-contract-authoring` |
| Implement AASX detection or package I/O | `aasx-core` |
| Implement or change the basyx probe or evidence gate | `basyx-evidence-gate` |
| Implement the NiceGUI frontend | `nicegui-frontend` |
| Write tests, fixtures or golden reports | `python-testing` |
| Audit the diff against the SPEC | `spec-compliance-audit` |
| Run the declared build/test/lint/grep checks | `verification-gate` |
| Review UI changes against the contract | `ui-review` |
| Validate the human's manual runtime evidence | `manual-verification` |
| Review a new or changed dependency and its licence | `dependency-review` |

## Workflow

1. The human launches `architect` with a request. The architect debates, proposes a SPEC and waits for `APROBADO`.
2. The human launches `code-executor` with the active SPEC. The executor implements, runs the declared checks and invokes the `reviewer` subagent.
3. The reviewer returns `PASS` or `FAIL` with evidence. The executor fixes `FAIL` defects, up to two loops.
4. On `PASS`, the executor updates the SPEC, issues, session log and roadmap and prepares the close. The human approves the close and commits.
5. The human performs manual verification when the SPEC declares it.

## Boundaries

- Agents never commit, push, tag, publish or open pull requests. The human owns git and releases.
- `external_directory: * deny` is the baseline for every agent.
- The executor writes only the SPEC file list plus the declared `` state files. The architect never writes source code.
- Never write credentials, tokens, private keys or personal data. `service.json` and `cli.json` are local harness files and must never be committed.
`- Scope: src/aas_bridge/ (when created), ...`  →  `- Scope: src/aas_bridge/, tests/, docs/, pyproject.toml, MANIFEST.in, .ai/. The corpus folders aas_v3-0/ and aas_v3-1/ are read-only.`
