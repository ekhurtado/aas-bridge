# CONVENTIONS.md — AAS Bridge Working Standards

> **Version:** 1.0 | **Status:** Approved | **Purpose:** Operational handbook for naming,
> layout, interfaces, tests, git and UI. Read by the architect, executor and reviewer.
> **Law above:** `CONSTITUTION.md` wins on any conflict with this file.

## 1. Naming & File Layout

| Layer | Element | Case / pattern | Example |
|---|---|---|---|
| Python | Packages / modules | `snake_case` | `aasx_reader.py`, `evidence_gate.py` |
| Python | Classes | `PascalCase` | `AASXPackage`, `MigrationPlan` |
| Python | Functions / methods | `snake_case` | `detect_version()` |
| Python | Constants | `UPPER_SNAKE_CASE` | `DEFAULT_TIMEOUT` |
| Python | Private helpers | leading underscore | `_iter_xml_parts()` |
| Files / folders | Source tree | `snake_case` | `tests/fixtures/golden/` |
| Skills | Skill IDs | `kebab-case` | `basyx-evidence-gate` |
| CLI | Commands / flags | `kebab-case` | `aasbridge doctor --file` |
| JSON | Report keys | `snake_case`, stable | `detected_version` |
| Environment | Variables | `AASBRIDGE_*` | `AASBRIDGE_CACHE_DIR` |
| AAS | Model identifiers | preserve the standard spelling | `AssetKind`, `idShort` |

Layout (created by SPEC-001, not by the bootstrap):

```text
aasbridge/
├── registry/            # Layer 1: knowledge asset (artifacts, features, rules, ecosystem)
├── engine/              # Layer 2: headless core (detect, analyze, transformer, gate)
├── probes/              # ephemeral-venv basyx probe; PyPI queries; offline-degraded
├── cli/                 # Typer commands
└── gui/                 # NiceGUI views over the same core
tests/
├── unit/
├── integration/
└── fixtures/            # expected baselines, golden JSON reports
aas_v3-0/                # READ-ONLY corpus (3 AAS V3.0 files)
aas_v3-1/                # READ-ONLY corpus (3 AAS V3.1 files)
pyproject.toml
MANIFEST.in
```

Rules:

- No source file outside the package tree; no ad-hoc scripts in the repo root.
- `registry/artifacts/` stores vendored official artifacts with hash + CC-BY-4.0 attribution.
- The corpus folders are fixtures: never edit, move or overwrite them.
- `.ai/` is context, not a source tree; agents write only the files declared in the SPEC plus
  the `.ai/` state files allowed by `README.md` §5.

## 2. Interfaces & Data Formats

- Public Python API: pure functions and dataclasses; no side effects on import.
- Version identifiers keep the AAS/IETF spelling (`https://admin-shell.io/aas/3/0`).
- Detection handles both XML declaration forms: default `xmlns="..."` and prefixed
  `xmlns:aas="..."`. Versioned external IRIs are **not** declarations.
- JSON reports: UTF-8, stable `snake_case` keys, a `schema_version` field, ISO 8601 dates,
  no `NaN`/`Infinity`, deterministic ordering.
- CLI exit codes: `0` success, `1` user/input error, `2` usage error, `3` evidence-gate failure,
  `4` internal error.
- Output files: `<name>-adapted.aasx`; never overwrite the input; never emit on gate failure.
- IDs (`SPEC-XXX`, `SES-XXX`, `ADR-XXX`, `TD-XXX`, `ISS-XXX`) are stable and never reused.

## 3. Error Handling & Edge Cases

- Custom exception hierarchy rooted at `AASBridgeError`:
  `DetectionError`, `MigrationError`, `EvidenceGateError`, `ProbeError`, `IngestError`.
- User-facing messages state **what failed**, **why**, and **what to do next**, naming both
  versions when relevant.
- No bare `except`; no swallowed exceptions; no placeholder returns; no silent fallback to a
  "best guess" conversion.
- Log with the standard `logging` module; library code never uses `print`.
- Fail-closed: if the target dialect, rule or gate is unknown, stop and explain.
- CLI maps exceptions to exit codes; the GUI renders the error state with a retry action when
  possible.

## 4. Testing & Verification

- **Framework:** `pytest`; test files `test_*.py`; test functions `test_*`.
- **Unit:** fast, no network, no Docker, no real subprocess; use `tmp_path` and small fixtures.
- **Integration:** marked `@pytest.mark.integration`; may use an ephemeral venv or subprocess.
  Network tests are separately marked `@pytest.mark.network` and are never part of the default
  suite.
- **Corpus:** the 6 AASX files in `aas_v3-0/` and `aas_v3-1/` are the regression baseline;
  expected object counts/IDs live in tests, not in the corpus.
- **Golden reports:** deterministic JSON reports under `tests/fixtures/golden/`.
- **Evidence gate:** tested for baseline equality, round-trip, and non-emission on failure.
- **Commands** (available after `pyproject.toml` exists in SPEC-001):

  ```bash
  python -m pytest
  python -m pytest -m "not integration"
  ruff check .
  ruff format --check .
  python -m build
  mypy aasbridge        # optional
  ```

- A step is done only when the declared checks pass; otherwise it stays open.

## 5. Git & Commits

- Format: `<type>(<scope>): <concise summary in lowercase>`.
- Types: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`, `perf`, `build`, `ci`.
- Scopes: `engine`, `registry`, `probes`, `cli`, `gui`, `docs`, `packaging`, `ai`.
- The **human** executes commits; agents draft the message only.
- Never commit: `.ai/service.json`, `.ai/cli.json`, secrets, `.venv/`, caches, build artifacts,
  generated `-adapted.aasx` outputs.

## 6. Documentation & Language

- Conversation with the human: Spanish.
- Code, docstrings, comments, commands, identifiers, technical docs and artifacts: English.
- Markdown links inside `.ai/` are repo-root-relative; no Obsidian wikilinks, anchors or tags.
- Every new public behaviour gets a docstring; user-facing behaviour gets a README/docs note.
- Keep the SPEC, CONVENTIONS, CONSTITUTION and README consistent through pointers, not
  duplicated text.

## 7. Stack-Specific Standards

### Python

- Python **>=3.11**; the local environment is 3.12.10.
- Type hints on public functions and methods; `from __future__ import annotations` optional.
- Prefer the standard library; use `dataclasses` for data, `pathlib` for paths.
- No mutable default arguments; no wildcard imports; no `print` in library code.
- Imports ordered: standard library, third-party, local.
- Ruff: line length 100, rules `E,F,I,UP,B,SIM`; format with `ruff format`.
- Mypy is optional but public interfaces should type-check.

### AASX / AAS

- AASX is an OPC/ZIP package. Preserve `[Content_Types].xml`, `_rels`, supplementary parts,
  thumbnails, BOMs and the compression of untouched parts **byte-for-byte**.
- Detect namespace **declarations** only; never rewrite versioned external IRIs or semanticId
  values that contain the same URI in a value position.
- Support both `xmlns="..."` and `xmlns:aas="..."` forms.
- Never hardcode `NS_AAS`; import it from the pinned basyx so a dependency upgrade moves the
  target dialect automatically.
- Transformations happen before parsing; basyx is the validator.
- Never mutate the input; write a new `<name>-adapted.aasx`.
- Evidence gate: load the original with the source dialect → baseline; transform; load with the
  target dialect; compare object counts, IDs and semanticIds; round-trip; emit only on pass.

### Dependencies

- `pyproject.toml` is the single source of dependency declarations.
- Pin meaningful ranges; dev dependencies under `[project.optional-dependencies].dev`.
- A new or changed dependency requires `dependency-review` and an ADR/TD decision.
- Never modify `basyx-python-sdk`; `aas-core` is a validator, not the runtime reader.

## 8. UI Standards

- NiceGUI/Quasar built-in components; no custom design system, no desktop frameworks.
- Single-page shell: header (title, online/offline status, EN/ES selector), stepper
  (Upload → Diagnosis → Plan → Result), details/log panel.
- Views are thin: they call core functions; no business logic, no direct AASX parsing in `gui/`.
- Four data states per view: loading (skeleton), empty, error (actionable, retry when possible),
  populated.
- **i18n:** every user-facing string lives in a translation catalog with `en` and `es`; keys are
  stable; both locales are updated together; default locale follows the browser, fallback `en`;
  no hardcoded strings in views. Technical AAS terms may stay in English.
- Use semantic tokens from `contracts/DESIGN.md`; no literal colors, sizes, radii or shadows.
- Accessibility: labelled controls, visible focus, keyboard navigation, adequate hit targets,
  contrast, no color-only meaning, reduced motion respected.
- Native/Docker parity: same code; the exit button exists only in native mode; Docker uses HTTP
  upload/download and no volume mounts.
- Manual verification covers both locales and, when declared, both native and Docker modes.

## 9. Definition of Done (per SPEC)

- [ ] Only the SPEC file list was changed.
- [ ] Declared build/test/lint/typecheck checks are green.
- [ ] Reviewer subagent returned `PASS`.
- [ ] Human manual verification is recorded when the SPEC declares it.
- [ ] `.ai/` state is updated: SPEC checkboxes/status, issues, session log, roadmap progress.
- [ ] No secrets, no unapproved dependencies, no UI contract drift.
