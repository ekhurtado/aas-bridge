---
name: nicegui-frontend
description: >
  Use when implementing gui/ views over the headless core: upload → diagnosis → plan → download,
  four states, EN/ES, native/Docker behavior, no business logic. Do NOT use for UI contracts
  (use ui-contract-authoring) or UI review (use ui-review).
version: 1.0.0
consumers:
  - code-executor
---

# NiceGUI Frontend

## Activation Criteria

- **Applies when:** implementing or changing `../../../src/aas_bridge/gui/`: the shell, the stepper, upload,
  diagnosis, plan decisions, result/download, the language selector or the details panel.
- **Does NOT apply when:** writing or revising the UI contract (`ui-contract-authoring`),
  reviewing a UI diff (`ui-review`) or implementing core logic (`aasx-core`,
  `basyx-evidence-gate`).

## Environment & Prerequisites

- Read `.ai/contracts/UI_SPEC.md`, `.ai/contracts/DESIGN.md`, `.ai/ARCHITECTURE.md` §6,
  `.ai/CONVENTIONS.md` §8, `.ai/CONSTITUTION.md` L3 and the SPEC's UI steps.
- Read the core API the view will call (detection, diagnosis, plan, migration, export). For
  NiceGUI API details, fetch the current documentation with context7.
- NiceGUI/Quasar built-ins only; no extra UI libraries.
- The GUI must run natively (`aas_bridge` opens the browser) and in Docker (port 8080, HTTP
  upload/download, no exit button).

## Technical Guidelines & Best Practices

1. **Thin views.** Call core functions; do not parse AASX, decide compatibility, transform files
   or duplicate business rules in `gui/`.
2. **One page, four steps.** Header + stepper (`Upload → Diagnosis → Plan → Result`) + main panel
   + details/log panel. No router, no dashboard.
3. **Four data states per view.** Loading (skeleton/spinner), empty (next action), error
   (actionable, retry when possible), populated.
4. **Bilingual EN/ES.** All strings come from the i18n catalog; the language selector is in the
   header; default from the browser locale with English fallback; switching re-renders without
   losing the current step.
5. **Semantic tokens.** Use the GUI token module derived from `DESIGN.md`; no literal colors,
   sizes, radii or shadows.
6. **Accessibility.** Labels on controls, visible focus, keyboard navigation, adequate hit
   targets, status badges with text/icons, no color-only meaning.
7. **No remote assets.** No CDN fonts, icons or images; the app must work offline.
8. **No blocking.** Long operations (probe, migration, gate) run off the UI thread and show a
   loading state; errors are actionable.
9. **Native/Docker parity.** The exit button is native-only; Docker uses HTTP upload/download and
   no volume mounts.
10. **No persistence.** A reload returns to a clean Upload step; do not hide state in local
    storage unless the SPEC declares it.

## Execution Workflow

1. **Inspect:** read the contract and the core API; map each step to a core function; list the
   states, strings and tokens to implement; confirm the SPEC's `ui_scope` and `design_ref`.
2. **Execute:** build the shell, then the steps; wire the core calls; add the four states, the
   i18n catalogs and the token module; implement accessibility labels; keep the view logic thin.
3. **Verify:** run the app natively; exercise upload → diagnosis → plan → result; switch EN/ES at
   every step; check loading/empty/error/populated; check long Spanish text at 1024 px; check
   `no literal colors` by grep; record manual evidence for the SPEC.

## Edge Cases & Resilience

- **Invalid file:** specific error state; do not crash or show a traceback.
- **Large file:** show progress/loading; avoid blocking the event loop.
- **Offline:** show the online/offline badge; disable online-only actions with an explanation.
- **Port conflict:** fail with an actionable message and a configurable port.
- **Docker:** no browser auto-open; exit button hidden; upload/download via HTTP.
- **Locale switch mid-flow:** re-render the current step without losing the diagnosis/plan.
- **Long Spanish labels:** wrap or ellipsize with a tooltip; never clip the primary action.

## Error Prevention & Anti-Patterns

- ⚠️ **Business logic in views:** parsing AASX or deciding a migration in `gui/`.
  ✔️ Call the core function; the view only renders.
- ⚠️ **Hardcoded strings:** English text in the view.
  ✔️ Use the i18n catalog with `en` and `es`.
- ⚠️ **Literal styles:** `color="#1976D2"` or `width="320px"`.
  ✔️ Use the semantic tokens from `DESIGN.md`.
- ⚠️ **Blocking call:** a long probe on the UI thread.
  ✔️ Run it asynchronously and show a loading state.
- ⚠️ **Remote assets:** CDN fonts/icons.
  ✔️ Use the local/system stack and Quasar icons.
- ⚠️ **Missing state:** only the happy path.
  ✔️ Implement loading, empty, error and populated.
