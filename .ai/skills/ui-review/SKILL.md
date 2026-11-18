---
name: ui-review
description: >
  Use when the diff touches gui/ or UI files and must comply with UI_SPEC.md/DESIGN.md: four
  states, semantic tokens, EN/ES completeness, accessibility, no logic in views. Do NOT use for
  UI implementation (use nicegui-frontend) or general SPEC audit (use spec-compliance-audit).
version: 1.0.0
consumers:
  - reviewer
---

# UI Review

## Activation Criteria

- **Applies when:** the diff touches `../../../src/aas_bridge/gui/`, the i18n catalogs, the GUI token module or
  any UI-related file, and the SPEC declares `ui_scope != none`.
- **Does NOT apply when:** implementing the UI (`nicegui-frontend`) or auditing the non-UI parts
  of the SPEC (`spec-compliance-audit`).

## Environment & Prerequisites

- Read `.ai/contracts/UI_SPEC.md`, `.ai/contracts/DESIGN.md`, `.ai/CONVENTIONS.md` §8,
  `.ai/CONSTITUTION.md` L3 and the SPEC's UI steps.
- Read the diff, the GUI code and the i18n catalogs; use the human's screenshots/manual evidence
  when the app cannot be launched in the reviewer environment.
- NiceGUI/Quasar component knowledge; no visual opinion outside the contract.

## Technical Guidelines & Best Practices

1. **Contract first.** Every UI change must map to a clause in `UI_SPEC.md` or a token in
   `DESIGN.md`; a visual detail not in the contract is a stop.
2. **Four states.** Loading, empty, error and populated exist for every data-bearing view.
3. **Semantic tokens.** No literal colors, sizes, radii or shadows; grep the diff for hex values
   and magic numbers.
4. **Bilingual EN/ES.** Every user-facing string has both translations; the selector switches
   without losing the current step; no hardcoded strings in views.
5. **Accessibility.** Labels, focus, keyboard, hit targets, contrast, no color-only meaning,
   reduced motion.
6. **Thin views.** No AASX parsing, version decisions, transformation or gate logic in `gui/`.
7. **Native/Docker parity.** Same code; exit button native-only; upload/download via HTTP in
   Docker.
8. **No remote assets.** No CDN fonts/icons/images.
9. **Layout.** Usable at 1024 px; long Spanish labels do not clip the primary action.
10. **Evidence.** A screenshot or a concrete manual observation per state/locale when the app
    cannot be run by the reviewer.

## Execution Workflow

1. **Inspect:** map each UI change to the contract; list the states, strings and tokens that must
   be present; check the SPEC's `ui_scope` and `design_ref`.
2. **Execute:** inspect the code for the four states, i18n keys, token usage, accessibility and
   logic leakage; run the app (or use the human evidence) to check EN/ES and native/Docker
   behavior; record findings with file:line.
3. **Verify:** confirm every finding cites a contract clause or token; confirm no missing
   translation; confirm no logic in views; return `PASS`/`FAIL` with the defects and the next
   action.

## Edge Cases & Resilience

- **App not available in the reviewer environment:** use the human's screenshots/evidence and
  mark the unverified parts explicitly.
- **Locale switch mid-flow:** verify the current diagnosis/plan is preserved.
- **Long Spanish text:** check buttons, badges and errors at 1024 px.
- **Dark mode not declared:** do not fail the diff for a missing dark theme; it is out of scope.
- **Docker unavailable:** mark the Docker-specific checks `N/A` with a reason.
- **Missing state/translation:** `MAJOR` defect; never accept a partial UI.

## Error Prevention & Anti-Patterns

- ⚠️ **Subjective taste:** “this color looks wrong” without a contract/token reference.
  ✔️ Cite the token or clause; otherwise it is not a defect.
- ⚠️ **Hardcoded strings:** English text inside a view.
  ✔️ Require the i18n key in both locales.
- ⚠️ **Ignoring accessibility:** icon-only buttons, no labels.
  ✔️ Require labels, focus and keyboard navigation.
- ⚠️ **Logic in views:** parsing AASX or deciding compatibility in `gui/`.
  ✔️ Move it to the core; the view only renders.
- ⚠️ **Missing states:** only the happy path.
  ✔️ Require loading, empty, error and populated.
