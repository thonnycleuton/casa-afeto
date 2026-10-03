# Casa Afeto Design System

**Status:** Active for M1
**Scope:** Existing Products & Inventory web application

## Purpose and visual concept

Casa Afeto uses a dark, modern administrative interface: calm, compact, professional, and readable for frequent operational work. The design is intentionally information-dense without relying on decoration. Hierarchy comes from typography, spacing, restrained indigo accents, subtle borders, and distinct surface levels.

The canonical page background is `#0F1117`. Surfaces are neutral charcoal; indigo is reserved for primary actions and selected navigation. Green, amber, and red communicate business or operation states, not decoration. Do not add dashboard concepts, modules, or functionality to fill unused space.

## Design tokens

The tokens live in `frontend/src/style.css` as CSS custom properties. Reuse them in application styles; do not scatter new raw values through Vue components.

### Colors

| Token | Value | Use |
| --- | --- | --- |
| `--color-background` | `#0F1117` | Main page background and recessed input surfaces |
| `--color-surface` | `#161822` | Sidebar, cards, and primary panels |
| `--color-surface-elevated` | `#1A1C24` | Table headers and elevated controls |
| `--color-surface-hover` | `#20232D` | Hovered neutral surfaces |
| `--color-border` | `#2B2E39` | Default separators and outlines |
| `--color-border-strong` | `#3A3E4B` | Form controls and emphasized outlines |
| `--color-text-primary` | `#F3F4F6` | Titles and key values |
| `--color-text-secondary` | `#B7BAC5` | Body text and supporting labels |
| `--color-text-muted` | `#9296A3` | Hints, captions, and secondary metadata |
| `--color-text-disabled` | `#666A76` | Unavailable text and placeholders |
| `--color-primary` | `#6366F1` | Primary action, focus, and selected navigation |
| `--color-primary-hover` | `#5558E8` | Hovered primary action |
| `--color-success` | `#10B981` | Successful operations and active/available states |
| `--color-warning` | `#F59E0B` | Attention or low inventory when that state is explicitly represented |
| `--color-error` | `#EF4444` | Failed operations and validation errors |

Use semantic colors with a restrained translucent background and readable text, icon, or label. Never communicate status by color alone. Use semantic colors only when the underlying state is known; do not infer new business states for visual effect.

### Spacing

Use the compact spacing scale below. The existing tokens are `--space-1` through `--space-10`.

| Token | Value |
| --- | ---: |
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |

Prefer these values for gaps, padding, and section rhythm. Do not add a new spacing value unless the existing scale cannot express the layout clearly.

### Typography

Use the existing Plus Jakarta Sans font loaded by `frontend/index.html`, with the system sans-serif fallback from the root stylesheet. Do not add another font package or a second competing type family.

| Token | Size | Typical use |
| --- | ---: | --- |
| `--font-size-xs` | 12px | Eyebrows, hints, compact badges |
| `--font-size-sm` | 13px | Table headers, buttons, secondary copy |
| `--font-size-base` | 14px | Body copy and form values |
| `--font-size-md` | 16px | Brand name and emphasized body copy |
| `--font-size-lg` | 18px | Card and section headings |
| `--font-size-xl` | 24px | Compact page headings and key metrics |
| `--font-size-display` | 28px | Standard page heading |

Use medium-to-semibold weights for headings and controls. Keep body and table copy at a comfortable compact size. Use tabular numerals for quantities and balances.

### Radius, borders, and elevation

Use `--radius-sm` (8px) for buttons and controls, `--radius-md` (10px) for compact marks, `--radius-lg` (12px) for cards, and `--radius-pill` for status chips. Do not apply pill rounding to large panels.

Use `--color-border` for low-emphasis boundaries and `--color-border-strong` for form fields. Tables use horizontal row separators rather than vertical grid lines. Avoid heavy shadows; elevation is mainly communicated through surface contrast. `--shadow-overlay` is reserved for a future overlay that is actually required.

## Iconography

Use small, consistent line icons only when they clarify navigation or an action. The current frontend has no icon library, so its few required navigation/search icons are inline SVGs with `currentColor` strokes. Continue that lightweight approach for isolated icons. Do not add another icon library for a handful of symbols.

Decorative icons must be hidden from assistive technology. Icon-only buttons must have an accessible name via visible text, `aria-label`, or an associated label. Do not add icon-only controls when a text label is clearer.

## Layout and responsive behavior

The M1 shell has a fixed-width desktop sidebar, a compact top bar, and a centered, width-constrained content area. Navigation exposes only the existing Products and Inventory sections. The selected section is visually distinct and programmatically marked. Do not add placeholder destinations for future milestones.

Page content begins with a concise heading, context line, and (when appropriate) one primary action. Related controls belong together in a card or toolbar. Keep the main content fluid and prevent the document from overflowing horizontally.

At narrower widths, the sidebar becomes a compact horizontal navigation row. Page actions and form grids stack, while wide tables remain usable inside a local horizontal scroll area. Do not hide product or movement data solely to fit a narrow viewport.

## Shared component patterns

Keep the reusable vocabulary small and use the existing frontend architecture. Shared styling patterns are defined in `frontend/src/style.css`; apply their classes consistently rather than adding page-specific variants.

| Pattern | Current classes | Guidance |
| --- | --- | --- |
| Application shell | `.app-shell`, `.sidebar`, `.topbar`, `.page-content` | Preserve the Products/Inventory navigation and responsive hierarchy |
| Page heading | `.page-heading`, `.page-eyebrow`, `.page-description` | One clear title and concise context per section |
| Card | `.card`, `.card-heading` | Group related controls and information; use surface and border tokens |
| Button | `.button.primary`, `.button.secondary`, `.button.ghost` | One main action; use secondary/ghost for supporting actions |
| Form field | `.form-field`, `.field-hint` | Keep visible labels associated with native controls; use hints for clarification |
| Feedback | `.feedback-error`, `.feedback-success`, `.loading-state` | Pair concise text with an icon and semantic color |
| Status | `.status-pill`, `.movement-pill` | Compact textual status; color reinforces the label |
| Table | `.table-card`, `.table-scroll`, `.numeric` | Horizontal separators, readable headers, aligned numeric values |
| Empty state | `.empty-state`, `.empty-panel` | Explain what is absent and the next available action when one exists |

Create a Vue component only when the same behavior-bearing visual pattern is repeated and the component provides a real consistency or maintenance benefit. CSS class reuse is sufficient for presentational patterns that do not need their own component contract.

## Tables

Use a slightly elevated header surface, subtle horizontal dividers, and a restrained row hover. Avoid vertical separators and spreadsheet-like borders. Align quantities and other numeric values to the right and use tabular numerals. Keep operational actions together and make their text labels clear. Place a wide table in `.table-scroll` so small viewports can reach every column.

## Forms

Use visible labels associated with their input, select, or number control. Controls share a 42px minimum height, 8px radius, dark recessed background, and consistent border treatment. Focus uses the primary border and `--focus-ring`. Hints and errors remain readable and adjacent to the relevant control or form feedback.

Keep native form constraints and the existing field vocabulary intact. Visual work must not change required fields, accepted values, input steps, quantity handling, or validation semantics.

## Buttons and interaction

Use `.button.primary` for the main page/form action, `.button.secondary` for supporting actions, and `.button.ghost` for low-emphasis row actions. Use consistent dimensions and keep labels action-oriented. Disabled controls must remain visibly unavailable. If an existing operation is loading, show a subtle status without changing the operation or its availability rules.

All interactive controls need a visible keyboard focus state. Hover is an enhancement, not the only indication of interactivity. Respect `prefers-reduced-motion`; transitions should be brief and nonessential.

## Badges, alerts, and states

Status pills are compact labels, not decoration. Use success for active or successful states, warning for attention, and error for an operation failure. Neutral inactive states should remain neutral unless an approved business rule assigns another meaning.

Movement-type pills distinguish Entry from Adjustment as record types; their styling does not indicate a warning or a different operation outcome.

Feedback includes concise explanatory text, an icon or other non-color cue, and a semantic color. Loading states should be quiet and informative. Empty states should distinguish a valid empty result from an application error. Error states retain the existing error message and do not disguise a failed operation as success.

Do not introduce a confirmation dialog for ordinary operations. Use a dialog only where the existing product behavior requires an explicit confirmation.

## Accessibility

Preserve semantic headings, landmarks, native controls, and form-label associations. Navigation communicates the current section programmatically. Maintain visible focus, readable contrast, keyboard access, and text labels for status and errors. Decorative SVGs and marks are hidden from assistive technology; icon-only controls require accessible names.

Do not remove content or rely exclusively on color, hover, placeholder text, or an icon to convey important information. Preserve reduced-motion preferences.

## M1 application and functional boundary

This Design System is applied to the existing M1 Products & Inventory screen: product search/listing, create/edit controls, activation state, inventory selection and balance, entry/adjustment forms, movement history, and existing loading, empty, success, and error feedback.

Visual refactoring does not authorize changes to API contracts, endpoints, database models, inventory calculations, business rules, validation semantics, quantity rules, product lifecycle, or transaction/concurrency behavior. It must not add future modules, dashboard charts, or any other M1 capability. If a requested visual treatment appears to require a behavior change, stop and request a product-owner decision.

## Rules for AI-assisted frontend development

1. Reuse existing Design System patterns and tokens before creating new ones.
2. Do not scatter arbitrary colors, spacing, radius, or typography values through components.
3. Do not create page-specific versions of shared patterns without a concrete justification.
4. Do not introduce a second icon library, frontend framework, or styling system unnecessarily.
5. Create a reusable component only to solve an actual repeated need.
6. Never introduce business functionality through a visual refactoring task.
7. If a visual request conflicts with business behavior, stop and ask the product owner rather than choosing a behavior.
8. Keep new screens visually consistent with the existing M1 shell and shared patterns.
9. Preserve labels, validation, keyboard behavior, loading/error semantics, and API use unless an explicitly approved requirement says otherwise.
10. Avoid dashboard, chart, or future-module work unless separately specified and authorized.
