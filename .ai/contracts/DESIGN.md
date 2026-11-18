# DESIGN.md — AAS Bridge Visual Identity

> **Version:** 1.0 | **Status:** Approved | **Scope:** Semantic tokens, typography, spacing,
> density, themes and asset policy for the minimal NiceGUI interface.
> **Law above:** `CONSTITUTION.md` wins on any conflict. Shell/layout: `contracts/UI_SPEC.md`.

## 1. Identity

- **Brand / tone:** technical, calm, evidence-first. A working tool for engineers, not a
  marketing site. No logo, no illustration, no custom brand system.
- **Design references:** NiceGUI/Quasar default look; the AASX Package Explorer is a functional
  reference only, not a visual one.
- **Principles:** clarity over decoration; one primary action per step; evidence visible;
  consistent status language; bilingual layouts that do not break with longer Spanish text.

## 2. Design Tokens

### 2.1 Color (light theme only)

| Token | Value | Usage |
|---|---|---|
| `color.primary` | `#47AADF` | Primary actions, active step |
| `color.primary-contrast` | `#FFFFFF` | Text on primary |
| `color.positive` | `#21BA45` | Gate passed, compatible |
| `color.warning` | `#F2C037` | Assisted decision, degraded/offline |
| `color.negative` | `#C10015` | Gate failed, blocking, error |
| `color.info` | `#31CCEC` | Informational badges, hints |
| `color.surface` | `#FFFFFF` | Cards, panels |
| `color.background` | `#F5F7FA` | Page background |
| `color.text` | `#1F2937` | Primary text |
| `color.text-muted` | `#6B7280` | Secondary text, metadata |
| `color.border` | `#E5E7EB` | Dividers, card borders |

Rules:

- Use semantic token names in code, not raw hex values.
- Status colors are always paired with text or an icon; never color-only.
- No gradients, glass effects or decorative shadows.

### 2.2 Typography

| Token | Family | Size / line-height | Weight | Usage |
|---|---|---|---|---|
| `text.display` | system/Roboto | 24 / 1.3 | 600 | Page title |
| `text.heading` | system/Roboto | 20 / 1.35 | 600 | Section title |
| `text.subheading` | system/Roboto | 16 / 1.4 | 500 | Card/step title |
| `text.body` | system/Roboto | 14 / 1.5 | 400 | Body, tables |
| `text.caption` | system/Roboto | 12 / 1.4 | 400 | Metadata, hints |
| `text.mono` | system monospace | 13 / 1.5 | 400 | Versions, JSON, paths |

- No custom or remote fonts; use the system/Roboto stack.
- Spanish accents, `ñ`, `¿`, `¡` and long compound words must render without clipping.
- Do not use more than three weights on one view.

### 2.3 Spacing, radius, elevation, motion

| Token | Value | Usage |
|---|---|---|
| `space.1` | 4 px | Base unit |
| `space.2` | 8 px | Tight gaps |
| `space.3` | 12 px | Control spacing |
| `space.4` | 16 px | Card padding |
| `space.6` | 24 px | Section spacing |
| `space.8` | 32 px | Page sections |
| `radius.sm` | 4 px | Inputs, badges |
| `radius.md` | 8 px | Cards, dialogs |
| `elevation.0` | none | Default |
| `elevation.1` | subtle shadow | Dialogs, sticky header |
| `motion.fast` | 150 ms ease-out | Hover/focus transitions |

- Spacing base is 4 px; use tokens, never arbitrary pixel values.
- No elevation stacking; at most one raised surface at a time.

## 3. Themes

- **Modes:** light only in Phase 1.
- **Parity rule:** if a dark theme is added later, every color token must exist in both themes;
  a one-theme token is a build-blocker.
- **Generated file:** no generated theme file in Phase 1; tokens are consumed directly from this
  document through the GUI token module. If a generated theme is introduced, hand edits are
  forbidden.
- **Contrast:** WCAG AA for normal text and interactive elements.

## 4. Layout & Density

- **Spacing base:** 4 px.
- **Density:** comfortable; card padding 16 px, section spacing 24 px; tables use 12 px row
  padding.
- **Radii scale:** 4 px (controls), 8 px (cards/dialogs).
- **Elevation/shadow policy:** flat by default; one subtle elevation for dialogs and the sticky
  header.
- **Content width:** max 1200 px; centered; no horizontal scroll at 1024 px.

## 5. Components

- **Approved primitives:** NiceGUI/Quasar built-ins listed in `UI_SPEC.md` §4.
- **Variants:** primary, secondary (outline), flat, danger; status badge variants
  positive/warning/negative/info.
- **States:** default, hover, focus, active, disabled, loading, error.
- **Forbidden:** literal values, palette classes, gradients, glass, emoji icons, unapproved
  icon sets, custom component libraries.

## 6. Assets

- **Fonts:** system/Roboto stack only; no remote fonts.
- **Icons:** Quasar/Material Icons only; no emoji, no custom SVGs unless a decision approves
  them.
- **Images/illustrations:** none in Phase 1.
- **Remote assets:** forbidden; the app must work offline.

## 7. Governance

- This file is the token source of truth for the GUI.
- A token change requires a version bump and an ADR/TD entry when it changes the visual baseline.
- The GUI code must not contain raw hex values, magic sizes or ad-hoc styles; use the token
  module derived from this document.
- A missing token for a new pattern is a stop: the architect updates this contract first.
