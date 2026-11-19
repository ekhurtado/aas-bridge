# AAS Bridge — Project Brief

> **Status:** strategy and design approved on 2026-11-18; AI architecture bootstrap complete.
> Implementation has not started.
> **Companion documents:** `ARCHITECTURE.md` (how), `ROADMAP.md` (when),
> `history/DECISIONS.md` (why), `ECOSYSTEM_COMPATIBILITY.md` (verified facts),
> `SMIA_RUNTIME_COMPAT_LAYER.md` (deferred SMIA design).
> `CONSTITUTION.md` wins on any conflict with this brief.

## 1. Problem statement

The AAS standard evolves on a regular cadence (V3.0 → V3.1 → V3.2.0 [Jul 2026] → V3.3 [in
progress]), but the two tools SMIA depends on adopt each version at different times:

- **basyx-python-sdk** (SMIA's Python read path): `<=2.0.1` implements V3.0; `>=2.1.0`
  implements V3.1 and **silently returns an empty object store** for V3.0 files.
- **AASX Package Explorer** (authors `.aasx`): v2024-06-10 models V3.0; v2025-10-21 models
  V3.1 and converts V3.0 → V3.1 on load.

Production incident: V3.1 files authored by colleagues cannot be read by SMIA (pinned
`basyx-python-sdk ~= 2.0.1`); basyx logs a namespace error and returns **0 objects without
raising**, surfacing as a generic `CriticalError("The AAS model is not valid...")` that never
mentions versions. The reverse also holds: a newer basyx cannot read the V3.0 corpus.

Root causes (evidence in `ECOSYSTEM_COMPATIBILITY.md`):

1. **Rigid version coupling by XML namespace**: the payload declares its version in the xmlns IRI
   (`.../aas/3/0` vs `.../3/1`); basyx matches a single `NS_AAS` with no negotiation.
2. **Two toolchains, independent cadences**, both pinned implicitly by SMIA's dependency.
3. **Silent failure mode**: no exception, empty store, unactionable error.

## 2. Solution overview

### 2.1 SMIA runtime compatibility layer (deferred)

A thin ingestion layer inside SMIA (`aas_version_compat.py`, design in
`SMIA_RUNTIME_COMPAT_LAYER.md`): detect the declared version → load directly, re-label a
verified-additive older namespace **in memory**, or fail fast with an actionable error. basyx
remains the only validator; SMIA learns no metamodel.

### 2.2 AAS Bridge tool (this repository)

A standalone Python tool that turns version maintenance into a batch, evidence-based event:

- **Detect** the AAS version of any AASX file and validate the document.
- **Diagnose** against the ecosystem (SMIA latest, basyx dialect, PE provenance).
- **Migrate** between V3.x versions in both directions: automatic (additive), assisted
  (user decision) or blocking (no safe transformation), never silent data loss.
- **Prove correctness** with the evidence gate: baseline + target load + round-trip; a file
  that does not reproduce its baseline is not emitted.
- **Ingest** new AAS versions (official artifacts, diff, candidate rules, human review) and
  export the SMIA whitelist.

Delivery: local web GUI (NiceGUI, bilingual EN/ES) + CLI (Typer) over the same headless core,
native and Docker, zero configuration.

## 3. Goals

- **G1** — Any AASX of the V3.x line can be made loadable by the SMIA release the user runs.
- **G2** — Version mismatches are diagnosed with an explicit, actionable message; never silent.
- **G3** — Migrations are trustworthy: baseline comparison + round-trip.
- **G4** — New AAS versions cost a guided review of a generated diff, not reading PDFs.
- **G5** — Usable by a non-expert colleague in under a minute.

## 4. Non-goals (scope discipline)

- **AAS V2.0 ↔ V3.x**: structural rework; PE already converts on load. Revisit only on demand.
- **Sub-version conversions** (e.g. 3.0.1 → 3.0.2): same namespace, no operational meaning.
- **Modifying basyx-python-sdk**: never; basyx stays the only validator.
- **Generic any-version engine**: rules are per version pair, human-approved and composable.
- **Desktop GUI frameworks** (Qt/Tkinter): break the Docker requirement.
- **GUI as the product**: every feature lives in the tested headless core first.

## 5. Users

- **Primary:** SMIA developers (the owner) and the manufacturing-stack colleagues who author
  AASX files with different toolchain versions.
- **Secondary:** any AAS/SMIA user receiving `.aasx` files from third parties.

## 6. Success criteria

- **SC1** — The 6-file corpus migrates V3.0→V3.1 and back with equal baselines (automated).
- **SC2** — `doctor` on a mismatched file reproduces the exact diagnosis and fix.
- **SC3** — The next AAS version onboarding is a reviewed diff + fixture commit.
- **SC4** — SMIA never again fails silently on a version mismatch.
- **SC5** — Each cycle closes with reviewer `PASS`, human manual verification and a consistent
  `.ai/` state.

## 7. Stack

| Area | Choice |
|---|---|
| Language | Python 3.11+ (local 3.12.10) |
| Environment | `pip` + `venv`; `pytest`; `ruff`; `mypy` optional |
| AAS read path | `basyx-python-sdk` (source probe 2.0.1; target 2.2.0) |
| Validators | `aas-core3.0` / `aas-core3.1` (3.2 when stable) |
| GUI / CLI | NiceGUI (bilingual EN/ES) / Typer |
| Package I/O | `zipfile` + explicit relationships; `pyecma376-2` if needed |
| Distribution | `pip install aas-bridge` (distribution `aas-bridge`, package `aas_bridge`, src layout — ADR-024); Docker optional |
| Licence | **GPL-3.0**; vendored IDTA artifacts CC-BY-4.0 with attribution |

## 8. Absolute constraints (never violate)

1. **Fail-closed:** unknown version, unapproved rule or failed gate → refuse and explain.
2. **basyx is the only validator:** AAS Bridge learns no metamodel.
3. **Never mutate the input:** operate on a copy; write a new file.
4. **No silent data loss:** a file that does not reproduce its baseline is not emitted.
5. **No modification of basyx-python-sdk.**
6. **Offline-first:** the vendored registry is the default; online features are additive and
   visibly degraded.
7. **Licensing:** GPL-3.0; compatible dependencies; CC-BY-4.0 attribution for vendored artifacts.
8. **No secrets; the corpus (`aas_v3-0/`, `aas_v3-1/`) is read-only; the UI is a thin layer over
   the headless core and is bilingual EN/ES.**

## 9. UI identity

- Local web app, single page, stepper: **Upload → Diagnosis → Plan → Result**.
- Minimal NiceGUI/Quasar look, light theme, semantic tokens, four data states, accessibility.
- Bilingual **EN/ES** (selector, browser-locale default, English fallback, all strings in both
  locales). Contract: `contracts/UI_SPEC.md`; tokens: `contracts/DESIGN.md`.

## 10. Multi-agent topology

- `architect` (primary): debates with the human, writes the approved SPEC, decisions, roadmap and
  UI contracts. Never writes source code.
- `code-executor` (primary): implements the SPEC, runs the declared verification, invokes the
  reviewer subagent and updates the `.ai/` state.
- `reviewer` (subagent): read-only audit; returns `PASS`/`FAIL` with evidence.
- The human is the final gate and owns git. Details: `.ai/README.md` §4-5.

## 11. Current phase

- **Phase 0 — AI bootstrap:** complete (2026-11-18).
- **Phase 1 — MVP:** next; detection + upgrade V3.0→V3.1 + evidence gate + minimal bilingual GUI.
- No code, no `pyproject.toml` and no initial commit yet.

## 12. Open questions

The product questions Q1-Q6 (SMIA hot files, PE upgrade, ingestion scope, v3.0 consumers, PyPI
latency, project name) live in `history/DECISIONS.md` § Open questions. They do not block the
Phase 1 MVP unless a SPEC depends on one.
