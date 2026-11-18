# CONSTITUTION.md — AAS Bridge Non-Negotiable Laws

> **Version:** 1.0 | **Status:** Approved | **Scope:** Invariants enforced by all agents (L0-L3).
> Violations are build-blockers. `CONVENTIONS.md` details style; this file defines law.
> **Law above:** None. This file wins on any conflict.
> **Change control:** any change to L0-L3 requires an ADR/TD entry in `history/DECISIONS.md` and
> explicit human approval before implementation.

## L0. Core Laws

1. **SOURCE OF TRUTH:** Each fact lives in one file. `PROJECT_BRIEF.md` owns vision,
   `ARCHITECTURE.md` the system model, `CONVENTIONS.md` the working standards,
   `contracts/UI_SPEC.md` + `contracts/DESIGN.md` the UI contract and `README.md` the context
   map. Other files point, never restate.

2. **SINGLE WRITER:** Non-owner agents are read-only on static and live files. The write matrix
   is in `README.md` §5: the architect owns SPEC, decisions, roadmap and UI contracts; the
   executor owns the working tree and `.ai/` state; the reviewer is read-only.

3. **LANGUAGE:** Agents converse in **Spanish** and keep code, commands, identifiers, technical
   docs and artifacts in **English**. The GUI is bilingual **EN/ES**; every user-facing string
   exists in both locales.

4. **QUALITY GATE:** A cycle closes only when the active SPEC is verified, the declared automated
   checks are green, the reviewer subagent returned `PASS` (when invoked) and the human completed
   manual verification. No self-approval.

5. **CHANGE CONTROL:** A change to law, architecture, public interfaces, dependencies, UI visual
   baseline or agent topology requires an ADR/TD entry in `history/DECISIONS.md` and human
   approval before implementation.

6. **NO SECRETS:** Context, prompts and committed artifacts never contain credentials, tokens,
   private keys or personal data. `.ai/service.json` and `.ai/cli.json` are local harness files
   and are never committed.

7. **NO INVENTED CONTEXT:** If a required input is missing or ambiguous, stop and ask. Never
   invent schemas, interfaces, paths, version facts or requirements.

8. **FAIL-CLOSED:** Unknown version, unapproved rule, missing UI contract or failed evidence gate
   → refuse and explain. Never transform "to see if it works".

## L1. Product Constraints

9. **BASYX IS THE ONLY VALIDATOR:** AAS Bridge learns no metamodel. Transformations happen
   before parsing; validity is judged by loading with the target-dialect basyx.

10. **EVIDENCE OVER DOCUMENTATION:** Every compatibility claim traces to a probe, a corpus test
    or an official source with a date. Release notes are informative; empirical probes win.

11. **NEVER MUTATE THE INPUT:** Migrations write a new `<name>-adapted.aasx`; the original is
    untouched.

12. **NO SILENT DATA LOSS:** Every migration reproduces its baseline (object counts, IDs,
    semanticIds) and passes a round-trip. A file that fails is not emitted.

13. **V3.x SCOPE:** Only AAS V3.x. V2.0 ↔ V3.x, sub-version conversions and a generic
    any-version engine are out of scope. "Any version" = "any ingested version with approved
    rules".

14. **OFFLINE-FIRST:** The vendored registry is the default. Online features are additive and
    must show their online/offline state; the tool works fully offline.

## L2. Engineering Laws

15. **LICENSING:** The project is **GPL-3.0**. Dependencies must be licence-compatible; vendored
    IDTA artifacts keep **CC-BY-4.0** attribution; a dependency change requires
    `dependency-review` and an approved decision.

16. **ERROR HANDLING:** Errors are actionable: what failed, why and what to do next. No silent
    failure, swallowed exceptions, placeholder returns or versionless `CriticalError`.

17. **TESTING:** Every feature is tested headless before the GUI or CLI. The 6-file corpus is the
    regression baseline. Unit tests are offline; integration tests are marked. The evidence gate
    is tested in both directions.

18. **INTERFACES:** AAS model semantics, AASX package layout, CLI contracts and JSON report
    schemas are public interfaces. A change requires an approved decision and reviewer audit.

19. **DEPENDENCIES:** `pyproject.toml` is the single source. No unapproved dependency; no
    modification of `basyx-python-sdk`; the target dialect is imported from basyx (`NS_AAS`),
    never hardcoded.

20. **VERSIONING:** Semantic Versioning. `pyproject.toml` and the package `__version__` stay in
    sync. The human cuts releases.

## L3. UI Laws

21. **UI SOURCE OF TRUTH:** `contracts/UI_SPEC.md` defines shell, navigation, primitives, states
    and accessibility; `contracts/DESIGN.md` defines semantic tokens. Literal colors, sizes,
    radii or shadows in source code are forbidden.

22. **CORE-FIRST:** Every feature is implemented and tested headless before any UI. GUI views
    call core functions; they never contain business logic or become the only home of a
    capability.

23. **FOUR DATA STATES:** Every data-bearing view implements loading (skeleton), empty, error
    (actionable, retry when possible) and populated.

24. **BILINGUAL EN/ES:** Every user-facing string exists in both locales through the i18n
    catalog; no hardcoded UI strings. A missing translation is a build-blocker. AAS terms may
    stay in English with a Spanish explanation.

25. **ACCESSIBILITY & PARITY:** Visible focus, keyboard navigation, semantic labels, adequate hit
    targets, no color-only meaning, reduced motion. Native and Docker share the code; remote
    assets are forbidden unless a decision approves them.

## Enforcement

- The **reviewer** owns the quality gate. Any L0-L3 violation fails review, with a maximum of two
  fix loops before escalation to the architect or human.
- The **executor** on ambiguity appends a `[SPEC-AMBIGUITY]` or `BLOCKER` entry to
  `history/ISSUES.md` and stops. It never invents schema or interface signatures.
- A law change requires a human-approved ADR/TD entry and a version bump of this file.
- The **human** is the final gate for manual verification and git operations.
