# AAS Bridge — Architecture

> Design approved 2026-11-18. Facts backing every choice: `ECOSYSTEM_COMPATIBILITY.md`.

## 1. System context

```
   IDTA (AAS specs)        basyx-python-sdk        AASX Package Explorer
        │ (artifacts:            │ (reads AAS)          │ (authors .aasx)
        │  schemas, changelogs)   │                       │
        ▼                        ▼                       ▼
┌─────────────────────────────────────────────────────────────┐
│                       AAS BRIDGE (this repo)                  │
│  registry (knowledge) + core engine (detect/analyze/          │
│  transform/validate) + doctor + evidence gate                 │
└─────────────────────────────────────────────────────────────┘
        │                        │
        │ generated whitelist     │ migrated '-adapted.aasx'
        ▼                        ▼
   SMIA runtime layer         any AASX consumer
   (aas_version_compat.py)
```

## 2. Component design (tool)

```
src/aas_bridge/           # importable package (distribution `aas-bridge`, CLI `aas-bridge`)
├── registry/            # Layer 1: the knowledge asset (versioned, offline-first)
│   ├── artifacts/       #   official IDTA artifacts per version (vendored, hash, CC-BY-4.0)
│   ├── features/        #   feature catalog per version delta (detection + policy)
│   ├── rules/           #   transformations per version PAIR (auto / assisted / blocking)
│   │   ├── v3_0_to_v3_1/    # namespace re-label (proven, see evidence §4.3)
│   │   └── v3_1_to_v3_0/    # feature-catalog driven, plan-then-execute
│   └── ecosystem/       #   basyx↔AAS matrix (empirical probe), PE matrix (informative),
│                         #   SMIA latest (PyPI)
├── engine/              # Layer 2: headless, fully tested core
│   ├── detect.py        #   xmlns declaration peek (both forms); NOT schema inference
│   ├── analyze.py       #   document features vs target constraints → plan
│   ├── transformer.py   #   package rebuild (zipfile/rels; pyecma376-2 if needed),
│   │                    #   never mutates the input; writes <name>-adapted.aasx
│   ├── gate.py          #   EVIDENCE GATE (see §3)
│   └── _loaders/        #   basyx subprocess loaders (ADR-021; never imported in-process)
├── probes/              # ephemeral-venv basyx probe; PyPI queries; offline-degraded
├── cli/                 # Typer: check | doctor | migrate | plan | ingest | export
└── gui/                 # NiceGUI: thin views over the same core (no logic)
```

**Non-negotiable invariants:**

1. **Core-first**: every feature is implemented + tested headless in `engine/`/`registry/`;
   GUI and CLI are thin, disposable frontends over the same functions.
2. **Fail-closed**: unknown version, unapproved rule, failed gate → refuse with an
   explanation. Never transform "to see if it works". The cost asymmetry (silently
   corrupted industrial model vs one manual step) dictates everything.
3. **basyx is the only validator**: transformations happen before parsing (namespace
   declarations, attribute edits); validity is always judged by loading with the
   target-dialect basyx. AAS Bridge learns no metamodel of its own.
4. **The target dialect is imported, never hardcoded** (`NS_AAS` from the pinned basyx).
5. **Compatibility is a property of the document, not the version pair**: additive pairs
   (3.0→3.1) are auto for all documents; mixed pairs (3.1→3.2, Range) require per-document
   analysis; structural pairs (V2↔V3) are out of scope.

## 3. The evidence gate (the core asset)

For every migration, automatically:

```
original file ──load with source-dialect basyx──▶ BASELINE
   │                                              (object counts, IDs, semanticIds)
   ▼ transformation (approved rules only)
adapted file ──schema validation (target, aas-core)──┐
   │                                                 ├─▶ must equal BASELINE
   └──load with target-dialect basyx ──round-trip────┘
```

A file that does not reproduce its baseline is **not emitted**. This is what
differentiates AAS Bridge from "PE converts and you trust it": conversions come with
proof, batch-capable, on any OS.

## 4. Doctor (diagnosis UX)

- Input: a `.aasx` + (if online) ecosystem state.
- Chain: detected file dialect → SMIA latest (PyPI `requires_dist` → basyx pin) →
  dialect via probe/cache → verdict. First-class negative result: "the version is NOT
  your problem — look at config/XMPP/path".
- Online features are additive; the tool works fully offline with the vendored registry
  and shows its online/offline state.

## 5. Runtime + tool relationship

The SMIA runtime layer (deferred; design in `SMIA_RUNTIME_COMPAT_LAYER.md`) handles
**verified-additive upgrades transparently in memory** for files SMIA receives at
runtime. AAS Bridge handles everything else: downgrades, non-additive transitions,
batch conversion, new-version onboarding — and **generates the runtime whitelist**
(`export --target smia-whitelist`) so the two never duplicate knowledge. The registry
is the single source of truth for compatibility; SMIA consumes a generated artifact.

## 6. Deployment

- **Local**: `aas-bridge` → NiceGUI/Uvicorn on 127.0.0.1 (dynamic port) →
  `webbrowser.open()`. Feels like a native app; exit button terminates the process.
- **Docker**: `docker run -p 8080:8080 ekhurtado/aas-bridge` — same code; exit button
  disabled; files via HTTP upload/download (no volume mounts, no UID/GID issues).
- **UI contract**: the GUI implements `contracts/UI_SPEC.md` and `contracts/DESIGN.md`; it is
  bilingual EN/ES (language selector, browser-locale default with English fallback), light
  theme, four data states, and no business logic in views.
- Packaging: `pip install aas-bridge` first (src layout; ADR-024); PyInstaller binaries
  deferred (Phase 5). Probe-capable image (`aas-bridge-full`) optional; default image ships
  cached matrix.

## 7. Technology choices (rationale in `history/DECISIONS.md`)

| Choice | What | Why |
|---|---|---|
| Language | Python 3.11+ | same ecosystem as SMIA/basyx; aas-core SDKs; team knowledge |
| Validators | `aas-core3.0`/`aas-core3.1` (+3.2 when stable) | per-version verification + de/serialization |
| GUI | NiceGUI (web local) | works identically native and in Docker; Python-only; tree/table/dialog built-ins |
| CLI | Typer | thin, testable, CI-friendly |
| Package I/O | zipfile + explicit rels handling (pyecma376-2 if needed) | preserve supplementary parts, BOMs, thumbnails byte-for-byte |
| Specs | vendored artifacts + hash, never runtime downloads | reproducibility, offline, licensing control |
| Ecosystem facts | empirical probes > release notes | evidence beats documentation |

## 8. Decision index

One line per decision; full rationale, alternatives and trade-offs live in
`history/DECISIONS.md`.

| ID | Decision | Status |
|---|---|---|
| ADR-001 | SMIA upgrades to `basyx-python-sdk ~= 2.2` | Accepted |
| ADR-002 | Runtime normalization direction is upgrade-only | Accepted |
| ADR-003 | SMIA gets a thin ingestion layer | Accepted |
| ADR-004 | Whitelist opt-in, coupled to basyx upgrades | Accepted |
| ADR-005 | AAS Bridge is a standalone project | Accepted |
| ADR-006 | Version knowledge centralized in the registry | Accepted |
| ADR-007 | Every migration must pass the evidence gate | Accepted |
| ADR-008 | Ecosystem facts via empirical probes | Accepted |
| ADR-009 | Scope discipline: V3.x bidirectional | Accepted |
| ADR-010 | Compatibility is judged per document | Accepted |
| ADR-011 | GUI is a thin web-local frontend over a headless core | Accepted |
| ADR-012 | New AAS versions onboarded via ingest + human review | Accepted |
| ADR-013 | SMIA work deferred to a dedicated session | Accepted |
| ADR-014 | Two primary agents plus a reviewer subagent | Accepted |
| ADR-015 | Simplified context layout | Accepted |
| ADR-016 | UI is in scope and bilingual | Accepted |
| ADR-017 | Skill catalog of 13 skills | Accepted |
| ADR-018 | Permissions baseline | Accepted |
| ADR-019 | Adopt the existing `.ai/` with controlled migration | Accepted |
| ADR-020 | Python and licence baseline | Accepted — Superseded by ADR-023 |
| ADR-021 | Evidence gate dialect mechanism: same-venv pip swap in subprocesses | Accepted |
| ADR-022 | Dependency baseline for SPEC-001 | Accepted — Superseded by ADR-024 |
| ADR-023 | Project licence is GPL-3.0 | Accepted |
| ADR-024 | Naming, layout and packaging: `aas-bridge` / `aas_bridge` / `src` layout | Accepted |
| TD-001 | CLI contract, JSON detect-only scope, and the no-migration result | Accepted — Superseded by TD-002 |
| TD-002 | CLI contract v2: command `aas-bridge`; refusal-report persistence | Accepted |

