# history/ISSUES.md — AAS Bridge Issues Ledger

> **Tier:** HISTORY (cold archive, but the Open section is read at session start).
> **Writer:** Executor (append/update open issues); the Reviewer subagent reports findings in
> chat and the Executor records them. Resolved issues are moved to the Resolved section at close.
> **IDs:** `ISS-XXX` are stable and never reused.
> **Language:** English entries; Spanish conversation.

## Open

| ID | Type | Severity | Origin | Summary | Status |
|---|---|---|---|---|---|
| ISS-004 | BLOCKER | MINOR | bootstrap | Docker is not installed locally; the optional Docker smoke test cannot run on this machine. | Deferred to SPEC-002 — Docker not installed; Docker smoke is `N/A` in SPEC-001. |
| ISS-010 | SPEC-AMBIGUITY | MINOR | SPEC-001 rev 2 | Rename-sweep wording defects: `aas-bridgeError` (SPEC §2 l.103, §3 l.164, CONVENTIONS §3 l.66) is not a valid identifier and must remain `AASBridgeError`; `aas-bridge_CACHE_DIR` (SPEC §1/§5, CONVENTIONS §1 l.20, DECISIONS ADR-024) conflicts with the unchanged `AASBRIDGE_CACHE_DIR`; distribution/CLI rendered `aas_bridge` in parts of the SPEC (l.6-7, 29-30, 34-35, 46-52, 97), DECISIONS ADR-024 and ROADMAP A1a; stale root/old-command references in Step 1/§5; SPEC Step 5 says `run_migration` returns `refused` while §3 says it raises `EvidenceGateError` (code keeps the raise + exit 3 and persists the report). | Open — owner: architect. Align the SPEC body, CONVENTIONS and DECISIONS/ROADMAP wording before the archive; no code change (code verified against the operative contract). |
| ISS-011 | TECH-DEBT | MINOR | SPEC-001 rev 2 reviewer | The invalid `--lang` usage message is English-only (not in the i18n catalog). | Open — owner: executor (next cycle). Exit 2 is correct; not blocking. |
| ISS-012 | TECH-DEBT | MINOR | SPEC-001 rev 2 reviewer | A refusal with an unwritable `--report` path raises `MigrationError` (exit 1) and masks the gate error; fail-closed is preserved and the adapted file is removed. | Open — owner: executor (next cycle). Harden to keep exit 3 and append the write failure. |
| ISS-013 | TECH-DEBT | MINOR | SPEC-001 rev 2 reviewer | setuptools emits a deprecation notice for `license = { file = "LICENSE" }`; migrate to PEP 639 (`license = "GPL-3.0-only"` + `license-files`) when packaging is next touched. | Open — owner: executor/architect (next packaging change). Metadata is GPL-correct today. |

## Resolved

| ID | Type | Origin | Resolution |
|---|---|---|---|
| ISS-001 | BLOCKER | bootstrap | Initial commit exists (`e2f5179`; the SPEC's `e8f5179` is a typo). Resolved 2026-11-18. |
| ISS-002 | TECH-DEBT | bootstrap | `pyproject.toml`, package skeleton, tests and build commands delivered by SPEC-001; reviewer PASS loop 2/2 (executor scope). Resolved 2026-11-18. |
| ISS-003 | TECH-DEBT | bootstrap | `pytest`, `ruff`, `mypy` and `build` declared in `[project.optional-dependencies].dev` and installed; all declared checks green. Resolved 2026-11-18. |
| ISS-006 | QA-REJECTION | SPEC-001 reviewer loop 1 | D1 (AGPL classifier) and D2 (cp1252 CLI crash) fixed; M1 documented in README; reviewer PASS loop 2/2 (executor scope). Resolved 2026-11-18. |
| ISS-007 | TECH-DEBT | SPEC-001 reviewer loop 1 | Resolved 2026-11-18 — TD-002 implemented in rev 2: the refusal report is persisted with `--report`, the adapted file is removed, `EvidenceGateError` is raised (exit 3) and the CLI prints the report path; tests cover persistence with/without `--report`, the refused schema and the CLI print. Reviewer PASS rev 2. |
| ISS-009 | BLOCKER | SPEC-001 rev 2 Step 0 | Resolved 2026-11-18 — the allowlist now reads `src/aas_bridge/**` at line 29 (reviewer verified); the explicit `src/**` allow also covers the package. No blocker. |
| ISS-005 | BLOCKER | SPEC-001 (D3) | Licence trail corrected 2026-11-18: ADR-020's original AGPL-3.0 text restored with `Status: Accepted — Superseded by ADR-023`; ADR-023 (GPL-3.0, human-approved, dated, alternatives + trade-offs) appended; ADR-022/TD-001 superseded via ADR-024/TD-002 (rename consolidation, SPEC-001 rev 2). Close unblocked; re-audit against SPEC-001 rev 2 required (rev 1 PASS invalidated by the rename). |
| ISS-008 | TECH-DEBT | SPEC-001 reviewer loop 1 | SPEC §4 Step 5 wording aligned 2026-11-18 (rev 2): `dialect_probe` reports the installed basyx version via `importlib.metadata.version("basyx-python-sdk")` (basyx has no top-level `__version__`). |

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
