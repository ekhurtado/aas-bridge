# UI_SPEC.md — AAS Bridge UI Contract

> **Version:** 1.0 | **Status:** Approved | **Scope:** Normative shell/layout contract,
> navigation, primitives, data states, accessibility and bilingual content.
> **Law above:** `CONSTITUTION.md` wins on any conflict. Visual identity: `contracts/DESIGN.md`.

## 1. UI Principles

1. **Core-first:** every capability lives in the tested headless core; the GUI is a thin view
   over the same functions. No business logic in `gui/`.
2. **One job per screen:** the user drops a file, reads the diagnosis, reviews the plan and
   downloads the result. No dashboards, no settings maze.
3. **Evidence visible:** version facts, gate results and online/offline state are shown, not
   hidden. A negative diagnosis ("the version is not your problem") is a first-class result.
4. **Fail-closed UX:** an unknown version, unapproved rule or failed gate produces an
   actionable error, never a silent conversion.
5. **Bilingual by design:** every user-facing string exists in English and Spanish.

## 2. Shell / Layout Contract

- **Shell owner:** the GUI package (`src/aas_bridge/gui/`, SPEC-002). Feature views never edit
  the global
  shell or render their own chrome.
- **Layout regions:**
  - **Header:** product name, online/offline status badge, EN/ES language selector.
  - **Stepper:** `Upload → Diagnosis → Plan → Result` (the current step is visible).
  - **Main panel:** the active step's content (drop zone, diagnosis, plan decisions, result).
  - **Details/log panel:** collapsible evidence, gate output and errors.
- **Viewport/content rules:** desktop-first; content max-width 1200 px; cards and tables
  inside the main panel; no horizontal scroll at 1024 px.
- **Responsive behavior:** usable down to 1024 px; below that, stack panels vertically. Mobile
  is not a requirement in Phase 1.
- **Forbidden:** custom global chrome, multiple pages/routers, dashboards, modal-only flows,
  remote assets, desktop frameworks.

## 3. Navigation

- **Primary navigation:** one page with a stepper; no router and no browser-history
  requirement. Refresh returns to a clean Upload step.
- **Route/view ownership:** the shell owns the stepper; each step owns its panel content.
- **Selection/history behavior:** the current file and diagnosis live in session state; a
  reload discards them (the user uploads again). No hidden persistence.

## 4. Components & Primitives

- **Approved primitive source:** NiceGUI + Quasar built-ins (`q-uploader`, `q-card`, `q-table`,
  `q-badge`, `q-btn`, `q-dialog`, `q-select`, `q-expansion-item`, `q-spinner`).
- **Composition rules:** compose from the approved primitives; reuse the same status badge,
  table and error card across steps; no bespoke component library.
- **Forbidden:** literal colors/sizes, ad-hoc primitives, copied reference components,
  unapproved third-party UI kits, emoji icons.

## 5. Data States

Every data-bearing view implements four states:

1. **Loading / skeleton:** the action is in progress (upload, probe, migration, gate).
2. **Empty:** nothing to show yet, with the next action (e.g. "Drop an AASX file to start").
3. **Error:** actionable message with the cause and a retry/next step; never a raw traceback.
4. **Populated:** the data, table or result, with a clear primary action (diagnose, migrate,
   download).

Step-specific requirements:

- **Upload:** drag/drop + file picker; reject non-`.aasx`/`.xml` with a specific message.
- **Diagnosis:** detected version, source dialect, target/SMIA dialect, online/offline state,
  and a first-class "not a version problem" verdict when applicable.
- **Plan:** automatic / assisted / blocking items with counts and paths; assisted items can be
  accepted, edited or aborted.
- **Result:** gate result, before/after summary, download button, and a link to the JSON report.
- **Language selector:** switching locale re-renders all strings without losing the current
  step; both locales are complete.

## 6. Accessibility

- Visible focus, keyboard navigation and semantic labels on every control.
- Adequate hit targets (≥ 32 px), labelled upload and download controls.
- No color-only meaning: status badges include text/icons.
- Contrast: WCAG AA for normal text and interactive elements.
- Error messages are announced and associated with the field/action.
- Reduced motion respected; no autoplaying content.

## 7. Content & Language

- **Locales:** `en` and `es`; both complete for every user-facing string.
- **Default:** browser `Accept-Language` when it matches `en`/`es`; otherwise **English**.
- **Selector:** visible in the header; persists for the session; switching re-renders the
  current step.
- **Catalog:** all strings live in the GUI translation catalog (`gui/i18n/`); no hardcoded
  strings in views. Keys are stable and shared by both locales.
- **Tone:** short, specific, actionable. Empty/error messages say what happened and what to do.
- **Technical terms:** AAS terms (AASX, basyx, namespace, semanticId) stay in English; Spanish
  explanations may accompany them.
- **No placeholder** lorem ipsum or untranslated strings in a deliverable.

## 8. DoD / Stop Triggers

- [ ] The shell and stepper follow this contract; no extra global chrome.
- [ ] Only approved primitives and semantic tokens from `DESIGN.md` are used.
- [ ] Four data states exist for every data-bearing view.
- [ ] The EN/ES catalogs are complete; switching locale re-renders without losing state.
- [ ] Accessibility checks pass.
- [ ] No business logic and no AASX parsing in `gui/`; views call core functions.
- [ ] Native and Docker modes share the same code; exit button only in native mode.
- **Stop** if a visual detail, primitive, state, token or translation is not in the contract;
  ask, never invent.
- **Stop** if a UI change requires a shell change without `ui_scope: shell` and an approved
  decision.
