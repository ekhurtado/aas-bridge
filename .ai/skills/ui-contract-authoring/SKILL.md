---
name: ui-contract-authoring
description: >
  Use when a SPEC declares ui_scope != none and contracts/UI_SPEC.md or contracts/DESIGN.md must
  be created or revised. Do NOT use for NiceGUI implementation (use nicegui-frontend) or UI
  review (use ui-review).
version: 1.0.0
consumers:
  - architect
---

# UI Contract Authoring

## Activation Criteria

- **Applies when:** a new UI feature, shell change, visual pattern, token, locale, state or
  accessibility requirement must be added to `contracts/UI_SPEC.md` or `contracts/DESIGN.md`.
- **Does NOT apply when:** implementing the GUI (`nicegui-frontend`) or reviewing a UI diff
  (`ui-review`).

## Environment & Prerequisites

- Read `.ai/contracts/UI_SPEC.md`, `.ai/contracts/DESIGN.md`, `.ai/ARCHITECTURE.md` §6,
  `.ai/ROADMAP.md` Phase 1, `.ai/CONVENTIONS.md` §8 and `.ai/CONSTITUTION.md` L3.
- Read the relevant SPEC (`ui_scope`, `design_ref`, `design_delta`) and the NiceGUI/Quasar
  built-in component set.
- The human approves visual/UX changes; the architect writes the contract.

## Technical Guidelines & Best Practices

1. **Minimal by default.** NiceGUI/Quasar built-ins, one page, a stepper and a details panel. No
   custom design system, no desktop framework.
2. **Core-first.** The UI is a thin view over the headless core; no business logic in `gui/`.
3. **Shell contract.** Header (title, online/offline, EN/ES selector), stepper
   (Upload → Diagnosis → Plan → Result), main panel, details/log panel.
4. **Four data states.** Loading, empty, error (actionable, retry when possible), populated.
5. **Bilingual EN/ES.** Every user-facing string in both locales; keys in a catalog; default from
   the browser locale with English fallback; a visible selector.
6. **Semantic tokens.** Use `DESIGN.md` tokens; no literal colors, sizes, radii or shadows.
7. **Accessibility.** Visible focus, keyboard navigation, labelled controls, adequate hit targets,
   contrast, no color-only meaning, reduced motion.
8. **Assets.** No remote fonts, icons or images; Material Icons via Quasar only.
9. **Change control.** A visual baseline or shell change needs a version bump and an ADR/TD.
10. **No placeholders.** Every state, string and token is concrete; a missing one is a stop.

## Execution Workflow

1. **Inspect:** read the current contract and the SPEC's UI scope; list the new views, states,
   strings, tokens and accessibility requirements; decide whether it is `ui_scope: ui` or `shell`.
2. **Execute:** update `UI_SPEC.md` (shell, navigation, primitives, states, a11y, i18n) and
   `DESIGN.md` (tokens, typography, spacing, theme); keep both consistent; add the decision if the
   baseline changes; reference the contract from the SPEC.
3. **Verify:** check every state, locale and token is covered; verify Spanish accents/ñ and long
   strings fit; check contrast; confirm no remote asset; confirm the SPEC's `design_ref` points to
   the contracts; ask for human approval.

## Edge Cases & Resilience

- **Dark mode requested:** add a full token set for both themes; a one-theme token is a blocker.
- **New locale:** add the catalog and the selector entry; both locales ship together.
- **Long Spanish text:** test labels, buttons and errors at 1024 px; no clipping.
- **Docker/native difference:** document the exit button and upload/download behavior.
- **New visual pattern:** require a decision and a contract version bump.
- **Missing token/state:** stop; never let the executor invent it.

## Error Prevention & Anti-Patterns

- ⚠️ **Literal styles:** `color="#1976D2"` in the view.
  ✔️ Use the semantic token from `DESIGN.md`.
- ⚠️ **Hardcoded strings:** English text inside the view.
  ✔️ Use the i18n catalog with `en` and `es`.
- ⚠️ **Custom UI kit:** adding a third-party component library.
  ✔️ Compose from NiceGUI/Quasar built-ins.
- ⚠️ **Logic in views:** parsing AASX or deciding compatibility in `gui/`.
  ✔️ Call the core function; the view only renders.
- ⚠️ **Inaccessible control:** icon-only button without a label.
  ✔️ Add an accessible label and a tooltip.
- ⚠️ **Missing translation:** shipping only English.
  ✔️ Complete both locales before the SPEC is approved.
