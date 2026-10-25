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

### Semantic UI tokens

These tokens centralize colors that were previously hardcoded in CSS rules or scoped component styles. They enable future dual-theme support without changing component code. All values below are for the current dark theme only.

| Token | Value | Use |
| --- | --- | --- |
| `--color-white-text` | `#fff` | White text on colored backgrounds (buttons, icons) |
| `--color-brand-mark-text` | `#c7c8ff` | Sidebar brand mark text |
| `--color-brand-mark-border` | `rgb(99 102 241 / 35%)` | Brand mark border |
| `--color-brand-mark-bg` | `rgb(99 102 241 / 14%)` | Brand mark background |
| `--color-nav-active-border` | `rgb(99 102 241 / 22%)` | Active navigation item border |
| `--color-nav-active-bg` | `rgb(99 102 241 / 12%)` | Active navigation item background |
| `--color-nav-active-text` | `#c7c8ff` | Active navigation item text |
| `--color-topbar-bg` | `rgb(15 17 23 / 94%)` | Topbar translucent background |
| `--color-button-secondary-hover-border` | `#555968` | Secondary button hover border |
| `--color-input-hover-border` | `#555968` | Form input hover border |
| `--color-table-row-hover` | `rgb(255 255 255 / 2%)` | Table row hover background |
| `--color-selection-bg` | `rgb(99 102 241 / 32%)` | Text selection background |
| `--color-select-arrow` | `#9296a3` | Select dropdown arrow (SVG data URI) |
| `--color-modal-overlay` | `rgb(0 0 0 / 60%)` | Modal overlay background |

#### Status pill tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-status-success-border` | `rgb(16 185 129 / 24%)` | Success pill border |
| `--color-status-success-bg` | `rgb(16 185 129 / 10%)` | Success pill background |
| `--color-status-success-text` | `#6ee7b7` | Success pill text |
| `--color-status-muted-bg` | `rgb(146 150 163 / 8%)` | Muted/neutral pill background |
| `--color-status-warning-border` | `rgb(245 158 11 / 24%)` | Warning pill border |
| `--color-status-warning-bg` | `rgb(245 158 11 / 9%)` | Warning pill background |
| `--color-status-warning-text` | `#fcd34d` | Warning pill text |

#### Movement pill tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-movement-entry-border` | `rgb(99 102 241 / 26%)` | Entry movement pill border |
| `--color-movement-entry-bg` | `rgb(99 102 241 / 10%)` | Entry movement pill background |
| `--color-movement-entry-text` | `#c7c8ff` | Entry movement pill text |
| `--color-movement-adjustment-bg` | `rgb(146 150 163 / 8%)` | Adjustment movement pill background |

#### Operation icon tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-operation-icon-entry-bg` | `rgb(16 185 129 / 12%)` | Entry operation icon background |
| `--color-operation-icon-entry-text` | `#6ee7b7` | Entry operation icon text |
| `--color-operation-icon-adjustment-bg` | `rgb(99 102 241 / 14%)` | Adjustment operation icon background |
| `--color-operation-icon-adjustment-text` | `#c7c8ff` | Adjustment operation icon text |

#### Feedback tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-feedback-error-border` | `rgb(239 68 68 / 24%)` | Error feedback border |
| `--color-feedback-error-bg` | `rgb(239 68 68 / 9%)` | Error feedback background |
| `--color-feedback-error-text` | `#fca5a5` | Error feedback text |
| `--color-feedback-success-border` | `rgb(16 185 129 / 24%)` | Success feedback border |
| `--color-feedback-success-bg` | `rgb(16 185 129 / 9%)` | Success feedback background |
| `--color-feedback-success-text` | `#6ee7b7` | Success feedback text |

#### Sale status badge tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-sale-badge-primary-bg` | `rgb(99 102 241 / 9%)` | Confirmed/Pronta badge background |
| `--color-sale-badge-primary-border` | `rgb(99 102 241 / 24%)` | Confirmed/Pronta badge border |
| `--color-sale-badge-warning-bg` | `rgb(245 158 11 / 9%)` | Em Preparação badge background |
| `--color-sale-badge-warning-border` | `rgb(245 158 11 / 24%)` | Em Preparação badge border |
| `--color-sale-badge-success-bg` | `rgb(16 185 129 / 9%)` | Entregue badge background |
| `--color-sale-badge-success-border` | `rgb(16 185 129 / 24%)` | Entregue badge border |
| `--color-sale-badge-error-bg` | `rgb(239 68 68 / 9%)` | Cancelada badge background |
| `--color-sale-badge-error-border` | `rgb(239 68 68 / 24%)` | Cancelada badge border |

#### SaleBasketCard tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-mini-badge-ok-bg` | `rgb(16 185 129 / 9%)` | Mini "ok" badge background |
| `--color-mini-badge-ok-border` | `rgb(16 185 129 / 24%)` | Mini "ok" badge border |
| `--color-inline-modal-bg` | `rgb(16 185 129 / 6%)` | Inline modal background |
| `--color-inline-modal-border` | `rgb(16 185 129 / 20%)` | Inline modal border |

#### HealthCard tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-health-card-bg` | `var(--color-surface)` | HealthCard background |
| `--color-health-card-border` | `var(--color-border)` | HealthCard border |
| `--color-health-card-hover-border` | `var(--color-border-strong)` | HealthCard hover border |
| `--color-health-card-shadow` | `0 4px 6px -1px rgb(0 0 0 / 5%), 0 2px 4px -2px rgb(0 0 0 / 5%)` | HealthCard shadow |
| `--color-health-card-hover-shadow` | `0 10px 15px -3px rgb(0 0 0 / 8%)` | HealthCard hover shadow |
| `--color-health-card-state-bg` | `var(--color-surface-elevated)` | HealthCard state panel background |
| `--color-health-card-error-bg` | `rgb(239 68 68 / 9%)` | HealthCard error state background |
| `--color-health-card-error-text` | `var(--color-error)` | HealthCard error state text |
| `--color-health-card-error-border` | `rgb(239 68 68 / 24%)` | HealthCard error state border |
| `--color-health-card-error-icon-bg` | `var(--color-error)` | HealthCard error icon background |
| `--color-health-card-error-icon-text` | `var(--color-white-text)` | HealthCard error icon text |
| `--color-health-card-details-bg` | `var(--color-surface-elevated)` | HealthCard details panel background |
| `--color-health-card-details-border` | `var(--color-border)` | HealthCard details panel border |
| `--color-health-card-label-text` | `var(--color-text-muted)` | HealthCard label text |
| `--color-health-card-value-text` | `var(--color-text-primary)` | HealthCard value text |
| `--color-health-card-status-ok` | `var(--color-success)` | HealthCard "OK" status text |
| `--color-health-card-env-bg` | `rgb(99 102 241 / 14%)` | HealthCard environment badge background |
| `--color-health-card-env-text` | `var(--color-primary)` | HealthCard environment badge text |
| `--color-health-card-btn-bg` | `var(--color-primary)` | HealthCard button background |
| `--color-health-card-btn-text` | `var(--color-white-text)` | HealthCard button text |
| `--color-health-card-btn-hover-bg` | `var(--color-primary-hover)` | HealthCard button hover background |
| `--color-health-card-spinner-border` | `var(--color-border-strong)` | HealthCard spinner border |
| `--color-health-card-spinner-top` | `var(--color-primary)` | HealthCard spinner top color |

#### StatusBadge tokens

| Token | Value | Use |
| --- | --- | --- |
| `--color-status-badge-online-bg` | `rgb(16 185 129 / 12%)` | Online badge background |
| `--color-status-badge-online-text` | `var(--color-success)` | Online badge text |
| `--color-status-badge-online-border` | `rgb(16 185 129 / 30%)` | Online badge border |
| `--color-status-badge-online-dot-shadow` | `0 0 8px rgb(16 185 129 / 60%)` | Online badge dot glow |
| `--color-status-badge-offline-bg` | `rgb(239 68 68 / 12%)` | Offline badge background |
| `--color-status-badge-offline-text` | `var(--color-error)` | Offline badge text |
| `--color-status-badge-offline-border` | `rgb(239 68 68 / 30%)` | Offline badge border |
| `--color-status-badge-loading-bg` | `rgb(245 158 11 / 12%)` | Loading badge background |
| `--color-status-badge-loading-text` | `var(--color-warning)` | Loading badge text |
| `--color-status-badge-loading-border` | `rgb(245 158 11 / 30%)` | Loading badge border |
| `--color-status-badge-idle-bg` | `rgb(146 150 163 / 15%)` | Idle badge background |
| `--color-status-badge-idle-text` | `var(--color-text-muted)` | Idle badge text |
| `--color-status-badge-idle-border` | `rgb(146 150 163 / 30%)` | Idle badge border |

**Rule:** Never introduce new hardcoded colors in CSS rules or scoped component styles. Always use or create a semantic token in `:root`. This ensures that future dual-theme support requires only adding a second set of token values, not modifying individual components.

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
| Compact button | `.btn`, `.btn.primary`, `.btn.ghost`, `.btn.small` | Compact buttons for modal detail views; smaller padding than `.button` |
| Form field | `.form-field`, `.field-hint` | Keep visible labels associated with native controls; use hints for clarification |
| Feedback | `.feedback-error`, `.feedback-success`, `.loading-state` | Pair concise text with an icon and semantic color |
| Feedback banner | `.feedback`, `.feedback-error`, `.feedback-warning` | Inline error/warning banners with semantic colors |
| Status | `.status-pill`, `.movement-pill` | Compact textual status; color reinforces the label |
| Table | `.table-card`, `.table-scroll`, `.numeric` | Horizontal separators, readable headers, aligned numeric values |
| Empty state | `.empty-state`, `.empty-panel` | Explain what is absent and the next available action when one exists |

## Modal Detail Patterns

Extracted from the SaleDetailView refactoring, these patterns define the visual identity for detail modals with tabs, sidebars, and panel-based layouts. All classes are defined in `frontend/src/style.css` under the "Modal Detail Patterns" section.

### Sale summary card

A compact header card showing the sale identity, client, status, total, and actions. Uses `.sale-summary` with grid layout.

| Class | Purpose |
| --- | --- |
| `.sale-summary` | Grid container: identity, total, actions |
| `.sale-ident` | Flex container for icon + heading + client |
| `.sale-icon` | Emoji/icon bubble with primary translucent background |
| `.sale-heading` | Title + status badge row |
| `.total` | Right-aligned total with eyebrow label |
| `.eyebrow` | Uppercase label above key values |
| `.money` | Large green currency value |
| `.actions` | Button row within the summary |

### Panels with icon bubbles

Bordered cards with optional icon bubble titles, used in sidebars and detail views.

| Class | Purpose |
| --- | --- |
| `.panel` | Bordered card container with surface background |
| `.panel-title` | Title row with icon bubble |
| `.icon-bubble` | 31px square icon container with primary translucent styling |
| `.panel-body` | Padded content area within a panel |
| `.note-text` | Secondary text within panels |

### Tab navigation

Pill-style tab buttons for switching between content sections without page reload.

| Class | Purpose |
| --- | --- |
| `.tabs` | Flex container for tab buttons |
| `.tab` | Individual tab button with surface background |
| `.tab.active` | Active tab with primary translucent highlight |
| `.tab-pane` | Content container for the active tab |

### Finance rows and progress

Breakdown of financial data with total/paid/remaining rows and a progress bar.

| Class | Purpose |
| --- | --- |
| `.finance-rows` | Grid container for finance rows |
| `.finance-row` | Label + value row with secondary/primary text |
| `.finance-row .paid` | Paid amount with primary accent color |
| `.progress` | Thin progress bar container |
| `.progress span` | Filled portion of the progress bar |

### Delivery forms

Per-basket delivery editing forms with recipient, address, date, and time fields.

| Class | Purpose |
| --- | --- |
| `.delivery-tabs-content` | Grid container for delivery form cards |
| `.delivery-form-card` | Bordered card with basket title and form |
| `.delivery-form` | Grid layout for form fields |
| `.form-row` | Two-column grid for date/time fields |
| `.field` | Form input with dark recessed background |

### Client info card

Read-only display of client data in a clean key-value layout.

| Class | Purpose |
| --- | --- |
| `.client-info-card` | Bordered card with surface background |
| `.client-field` | Key-value row with bottom border separator |
| `.client-label` | Secondary text label |
| `.client-value` | Primary text value |

### Payment list

History of payments with method, amount, and date.

| Class | Purpose |
| --- | --- |
| `.payment-list` | Vertical flex container |
| `.payment-item` | Single payment row with surface-elevated background |
| `.payment-method` | Bold method label (PIX, Cartão) |
| `.payment-amount` | Green amount with tabular numerals |
| `.payment-date` | Muted date, right-aligned |

### Compact buttons (`.btn` family)

Smaller, compact buttons for modal detail views. Distinct from the `.button` family used in forms and pages.

| Class | Purpose |
| --- | --- |
| `.btn` | Default compact button with border |
| `.btn.primary` | Primary action with indigo background |
| `.btn.ghost` | Low-emphasis button with transparent background |
| `.btn.small` | Extra-small variant for inline actions |
| `.btn.full-width` | Full-width button for panel actions |

### Responsive behavior

The modal detail patterns adapt to smaller screens:

- **≤950px:** Two-column layout becomes single column; sale-summary stacks vertically
- **≤600px:** Tabs become horizontally scrollable; sale-icon shrinks

Create a Vue component only when the same behavior-bearing visual pattern is repeated and the component provides a real consistency or maintenance benefit. CSS class reuse is sufficient for presentational patterns that do not need their own component contract.

### Two-column modal layout (`.inv-*` family)

The standard layout for detail modals that display product or entity information alongside a sidebar of related activity. First implemented in `InventoryModal.vue`, this pattern is the default for all future detail modals. Mockup reference: `docs/design/mockups/casa_afeto_modal_estoque_mockup.html`.

**Structure:** A wide modal (`width="1000px"`) with a two-column grid layout. The main column contains the entity card, metrics panels, data tables, and action forms. The sidebar (`aside`) displays recent activity in a scrollable panel.

**Header:** The modal header includes a subtitle below the title to provide context: "Acompanhe o saldo, movimentações e informações do produto."

| Class | Purpose |
| --- | --- |
| `.inv-layout` | Two-column grid: `1fr 300px`; gap between main and sidebar |
| `.inv-main` | Main column: vertical flex container for panels |
| `.inv-side` | Sidebar column: sticky position, scrollable panel |
| `.inv-side-panel` | Sidebar panel with max-height and overflow |

**Product card:** Identifies the entity at the top of the main column with a thumbnail icon, name, unit chip, and status pill.

| Class | Purpose |
| --- | --- |
| `.inv-product-card` | Flex row: thumbnail, name, status |
| `.inv-product-thumb` | 48px square icon container with surface-elevated background |
| `.inv-product-name` | Name heading with text overflow ellipsis |
| `.inv-product-meta` | Unit chip and base unit label |
| `.inv-chip` | Small bordered badge for unit display |
| `.inv-status-pill` | Active/Inactive status with colored dot |

**Metrics panel:** Displays key numerical values in a three-column grid.

| Class | Purpose |
| --- | --- |
| `.inv-metrics` | Three-column grid for metric cards |
| `.inv-metric` | Individual metric: label + large value |
| `.inv-metric-label` | Muted eyebrow label |
| `.inv-metric-value` | Large primary text with tabular numerals |

**Panel pattern:** All content sections use the `.inv-panel` base with an icon prefix in the title row.

| Class | Purpose |
| --- | --- |
| `.inv-panel` | Bordered card with surface background and padding |
| `.inv-panel-title` | Title row: icon + text + optional action button |
| `.inv-panel-icon` | 24px icon container |
| `.inv-panel-title-text` | Heading + description text block |

**Info grid:** Read-only key-value display for product reference data.

| Class | Purpose |
| --- | --- |
| `.inv-info-grid` | Two-column grid for info cards |
| `.inv-info` | Individual info card: label, value, hint |
| `.inv-info-label` | Muted label text |
| `.inv-info-value` | Bold value with tabular numerals |
| `.inv-equiv` | Full-width equivalence calculation card |

**Movements sidebar:** Recent activity list with type-colored icons and compact card layout.

| Class | Purpose |
| --- | --- |
| `.inv-movements` | Vertical flex list of movement cards |
| `.inv-move` | Single movement: icon + content |
| `.inv-move-icon` | 28px colored icon bubble (green for entry, indigo for adjustment) |
| `.inv-move-content` | Type label, quantity, description, and timestamp |
| `.inv-move-entry` | Entry-type text color (primary accent) |
| `.inv-move-adjustment` | Adjustment-type text color (muted) |

**Form inputs:** Scoped form elements for entry and adjustment operations.

| Class | Purpose |
| --- | --- |
| `.inv-entry-form` | Vertical form layout |
| `.inv-form-row` | Two-column grid for side-by-side fields |
| `.inv-form-group` | Label + input + error/hint stack |
| `.inv-form-input` | Dark recessed input with focus border |
| `.inv-field-error` | Red error message |
| `.inv-field-hint` | Muted hint text |

**Buttons:** Compact buttons consistent with the `.btn` family but scoped to the inventory modal.

| Class | Purpose |
| --- | --- |
| `.inv-btn` | Default compact button with border |
| `.inv-btn-primary` | Primary action with indigo background |
| `.inv-link-btn` | Text-only link button for secondary actions |

**Responsive behavior:**

- **≤1050px:** Two-column layout becomes single column; sidebar moves below main content
- **≤620px:** Product card wraps; metrics become single column; info grid becomes single column; form rows become single column

**Usage guidelines:**

1. Use `width="1000px"` on `BaseModal` for two-column modals.
2. Place the entity identification card at the top of the main column.
3. Use panels with icon prefixes for each logical section.
4. Keep the sidebar for related activity or history that complements the main content.
5. All CSS classes use the `inv-` prefix to avoid conflicts with global styles.
6. Styles are scoped to the component; do not leak to other modals.

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

## Light Theme — Implemented (Phases 3–4)

**Status:** Fully implemented. Light theme tokens, toggle, persistence, and OS detection are all in place.
**Implementation status:**
- Token values (`html.light-theme` selector) in `frontend/src/style.css`.
- Theme toggle button in the topbar (`App.vue`).
- `localStorage` persistence of explicit user choice.
- `prefers-color-scheme` OS detection on first visit.
- Inline script in `index.html` applies theme before render to prevent flash.
**Direction:** Cold white, discreet, sober, and professional.

The light theme is activated by adding the class `light-theme` to the `<html>` element. The toggle button in the topbar allows the user to switch between dark and light themes. The choice is saved in `localStorage`. On first visit, the system detects the OS preference via `prefers-color-scheme`. Dark theme is the fallback.

### Visual direction and principles

The light theme must feel like the same application, not a different one. The principles are:

1. **Cold white base** — the page background is a very light cool gray, not pure white, to reduce eye strain during extended operational use.
2. **White surfaces** — cards, tables, forms, and modals sit on pure white (`#ffffff`) to create clear elevation against the page background.
3. **Dark gray text** — primary text is a dark neutral gray, not pure black, for comfortable reading contrast.
4. **Subtle borders** — separators and outlines are light but perceptible, maintaining the information-dense layout without visual noise.
5. **Same accent colors** — indigo remains the primary action color; green, amber, and red retain their semantic meaning. Their translucent variants are adjusted for light surfaces.
6. **WCAG AA contrast** — all normal text must meet a minimum 4.5:1 contrast ratio. Large text (≥ 18px or ≥ 14px bold) must meet 3:1. Icons and non-textual UI elements must meet 3:1. The semantic colors `--color-success` (#059669) and `--color-warning` (#d97706) fail AA for normal text on white (3.77:1 and 3.19:1, respectively) — they are intended for UI elements (borders, icon backgrounds, translucent fills), not for text labels. Darker text variants (`#047857` and `#92400e`) are provided for text-on-white contexts.

### Core color tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-background` | `#0f1117` | `#f4f5f7` | Cool gray page background, subtle depth behind white surfaces |
| `--color-surface` | `#161822` | `#ffffff` | Pure white for sidebar, cards, panels |
| `--color-surface-elevated` | `#1a1c24` | `#ffffff` | Same as surface; elevation via border, not color |
| `--color-surface-hover` | `#20232d` | `#f9fafb` | Very light gray hover on white surfaces |
| `--color-border` | `#2b2e39` | `#e5e7eb` | Light but visible separator |
| `--color-border-strong` | `#3a3e4b` | `#d1d5db` | Emphasized border for form controls |
| `--color-text-primary` | `#f3f4f6` | `#1f2937` | Dark gray for titles and key values (contrast 14.68:1 on white) |
| `--color-text-secondary` | `#b7bac5` | `#4b5563` | Medium gray for body text (contrast 7.56:1 on white) |
| `--color-text-muted` | `#9296a3` | `#6b7280` | Muted gray for hints and captions (contrast 4.83:1 on white, 4.43:1 on page bg) |
| `--color-text-disabled` | `#666a76` | `#9ca3af` | Light gray for unavailable text (2.54:1 — intentional) |
| `--color-primary` | `#6366f1` | `#4f46e5` | Slightly darker indigo for better contrast on white (6.29:1) |
| `--color-primary-hover` | `#5558e8` | `#4338ca` | Darker indigo on hover |
| `--color-success` | `#10b981` | `#059669` | Green for UI elements; 3.77:1 on white — **FAILS** AA normal text, **PASSES** AA large text & icons (3:1). For normal text, use `#047857` (5.48:1) instead. |
| `--color-warning` | `#f59e0b` | `#d97706` | Amber for UI elements; 3.19:1 on white — **FAILS** AA normal text, **PASSES** AA large text & icons (3:1). For normal text, use `#92400e` (7.09:1) instead. |
| `--color-error` | `#ef4444` | `#dc2626` | Slightly darker red for contrast on white (4.83:1 — **PASSES** AA normal text) |

### Semantic UI tokens — proposed light values

#### General UI

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-white-text` | `#fff` | `#ffffff` | Unchanged — white text on colored buttons/icons |
| `--color-brand-mark-text` | `#c7c8ff` | `#4f46e5` | Indigo text on light surface; light lavender is illegible on white |
| `--color-brand-mark-border` | `rgb(99 102 241 / 35%)` | `rgb(79 70 229 / 30%)` | Darker indigo border for light surface |
| `--color-brand-mark-bg` | `rgb(99 102 241 / 14%)` | `rgb(79 70 229 / 8%)` | Subtle indigo tint on white |
| `--color-nav-active-border` | `rgb(99 102 241 / 22%)` | `rgb(79 70 229 / 20%)` | Active nav border |
| `--color-nav-active-bg` | `rgb(99 102 241 / 12%)` | `rgb(79 70 229 / 8%)` | Active nav background |
| `--color-nav-active-text` | `#c7c8ff` | `#4f46e5` | Indigo text for active nav item |
| `--color-topbar-bg` | `rgb(15 17 23 / 94%)` | `rgb(255 255 255 / 94%)` | White translucent topbar |
| `--color-button-secondary-hover-border` | `#555968` | `#d1d5db` | Light border on secondary button hover |
| `--color-input-hover-border` | `#555968` | `#d1d5db` | Light border on input hover |
| `--color-table-row-hover` | `rgb(255 255 255 / 2%)` | `rgb(79 70 229 / 4%)` | Subtle indigo tint on row hover |
| `--color-selection-bg` | `rgb(99 102 241 / 32%)` | `rgb(79 70 229 / 25%)` | Text selection highlight |
| `--color-select-arrow` | `#9296a3` | `#6b7280` | Darker arrow for light surface (see known issues) |
| `--color-modal-overlay` | `rgb(0 0 0 / 60%)` | `rgb(0 0 0 / 40%)` | Lighter overlay on light theme |

#### Status pill tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-status-success-border` | `rgb(16 185 129 / 24%)` | `rgb(5 150 105 / 25%)` | Green border on light surface |
| `--color-status-success-bg` | `rgb(16 185 129 / 10%)` | `rgb(5 150 105 / 8%)` | Green background on light surface |
| `--color-status-success-text` | `#6ee7b7` | `#047857` | Dark green text (contrast 5.48:1 on white — passes AA) |
| `--color-status-muted-bg` | `rgb(146 150 163 / 8%)` | `rgb(107 114 128 / 8%)` | Muted background on light surface |
| `--color-status-warning-border` | `rgb(245 158 11 / 24%)` | `rgb(217 119 6 / 25%)` | Amber border on light surface |
| `--color-status-warning-bg` | `rgb(245 158 11 / 9%)` | `rgb(217 119 6 / 8%)` | Amber background on light surface |
| `--color-status-warning-text` | `#fcd34d` | `#92400e` | Dark amber text (contrast 7.09:1 on white — passes AA) |

#### Movement pill tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-movement-entry-border` | `rgb(99 102 241 / 26%)` | `rgb(79 70 229 / 25%)` | Indigo border on light surface |
| `--color-movement-entry-bg` | `rgb(99 102 241 / 10%)` | `rgb(79 70 229 / 8%)` | Indigo background on light surface |
| `--color-movement-entry-text` | `#c7c8ff` | `#4f46e5` | Indigo text (contrast 6.29:1 on white — passes AA) |
| `--color-movement-adjustment-bg` | `rgb(146 150 163 / 8%)` | `rgb(107 114 128 / 8%)` | Muted background on light surface |

#### Operation icon tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-operation-icon-entry-bg` | `rgb(16 185 129 / 12%)` | `rgb(5 150 105 / 10%)` | Green icon background |
| `--color-operation-icon-entry-text` | `#6ee7b7` | `#047857` | Dark green icon text |
| `--color-operation-icon-adjustment-bg` | `rgb(99 102 241 / 14%)` | `rgb(79 70 229 / 10%)` | Indigo icon background |
| `--color-operation-icon-adjustment-text` | `#c7c8ff` | `#4f46e5` | Indigo icon text |

#### Feedback tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-feedback-error-border` | `rgb(239 68 68 / 24%)` | `rgb(220 38 38 / 25%)` | Red border on light surface |
| `--color-feedback-error-bg` | `rgb(239 68 68 / 9%)` | `rgb(220 38 38 / 8%)` | Red background on light surface |
| `--color-feedback-error-text` | `#fca5a5` | `#b91c1c` | Dark red text (contrast 6.47:1 on white — passes AA) |
| `--color-feedback-success-border` | `rgb(16 185 129 / 24%)` | `rgb(5 150 105 / 25%)` | Green border on light surface |
| `--color-feedback-success-bg` | `rgb(16 185 129 / 9%)` | `rgb(5 150 105 / 8%)` | Green background on light surface |
| `--color-feedback-success-text` | `#6ee7b7` | `#047857` | Dark green text |

#### Sale status badge tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-sale-badge-primary-bg` | `rgb(99 102 241 / 9%)` | `rgb(79 70 229 / 8%)` | Indigo badge background |
| `--color-sale-badge-primary-border` | `rgb(99 102 241 / 24%)` | `rgb(79 70 229 / 25%)` | Indigo badge border |
| `--color-sale-badge-warning-bg` | `rgb(245 158 11 / 9%)` | `rgb(217 119 6 / 8%)` | Amber badge background |
| `--color-sale-badge-warning-border` | `rgb(245 158 11 / 24%)` | `rgb(217 119 6 / 25%)` | Amber badge border |
| `--color-sale-badge-success-bg` | `rgb(16 185 129 / 9%)` | `rgb(5 150 105 / 8%)` | Green badge background |
| `--color-sale-badge-success-border` | `rgb(16 185 129 / 24%)` | `rgb(5 150 105 / 25%)` | Green badge border |
| `--color-sale-badge-error-bg` | `rgb(239 68 68 / 9%)` | `rgb(220 38 38 / 8%)` | Red badge background |
| `--color-sale-badge-error-border` | `rgb(239 68 68 / 24%)` | `rgb(220 38 38 / 25%)` | Red badge border |

#### SaleBasketCard tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-mini-badge-ok-bg` | `rgb(16 185 129 / 9%)` | `rgb(5 150 105 / 8%)` | Green mini badge background |
| `--color-mini-badge-ok-border` | `rgb(16 185 129 / 24%)` | `rgb(5 150 105 / 25%)` | Green mini badge border |
| `--color-inline-modal-bg` | `rgb(16 185 129 / 6%)` | `rgb(5 150 105 / 6%)` | Green inline modal background |
| `--color-inline-modal-border` | `rgb(16 185 129 / 20%)` | `rgb(5 150 105 / 20%)` | Green inline modal border |

#### HealthCard tokens

Most HealthCard tokens reference other tokens via `var()` and will inherit light values automatically. Only tokens with hardcoded values need explicit light overrides:

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-health-card-shadow` | `0 4px 6px -1px rgb(0 0 0 / 5%), 0 2px 4px -2px rgb(0 0 0 / 5%)` | `0 1px 3px rgb(0 0 0 / 6%), 0 1px 2px rgb(0 0 0 / 4%)` | Lighter shadow on light surface |
| `--color-health-card-hover-shadow` | `0 10px 15px -3px rgb(0 0 0 / 8%)` | `0 4px 6px rgb(0 0 0 / 6%), 0 2px 4px rgb(0 0 0 / 4%)` | Lighter hover shadow |
| `--color-health-card-error-bg` | `rgb(239 68 68 / 9%)` | `rgb(220 38 38 / 8%)` | Red error background |
| `--color-health-card-error-border` | `rgb(239 68 68 / 24%)` | `rgb(220 38 38 / 25%)` | Red error border |
| `--color-health-card-env-bg` | `rgb(99 102 241 / 14%)` | `rgb(79 70 229 / 8%)` | Indigo env badge background |

Tokens that inherit via `var()` and require no change: `--color-health-card-bg`, `--color-health-card-border`, `--color-health-card-hover-border`, `--color-health-card-state-bg`, `--color-health-card-error-text`, `--color-health-card-error-icon-bg`, `--color-health-card-error-icon-text`, `--color-health-card-details-bg`, `--color-health-card-details-border`, `--color-health-card-label-text`, `--color-health-card-value-text`, `--color-health-card-status-ok`, `--color-health-card-env-text`, `--color-health-card-btn-bg`, `--color-health-card-btn-text`, `--color-health-card-btn-hover-bg`, `--color-health-card-spinner-border`, `--color-health-card-spinner-top`.

#### StatusBadge tokens

| Token | Dark Value | Proposed Light Value | Rationale |
| --- | --- | --- | --- |
| `--color-status-badge-online-bg` | `rgb(16 185 129 / 12%)` | `rgb(5 150 105 / 10%)` | Green online badge background |
| `--color-status-badge-online-border` | `rgb(16 185 129 / 30%)` | `rgb(5 150 105 / 30%)` | Green online badge border |
| `--color-status-badge-online-dot-shadow` | `0 0 8px rgb(16 185 129 / 60%)` | `0 0 6px rgb(5 150 105 / 40%)` | Subtler glow on light surface |
| `--color-status-badge-offline-bg` | `rgb(239 68 68 / 12%)` | `rgb(220 38 38 / 10%)` | Red offline badge background |
| `--color-status-badge-offline-border` | `rgb(239 68 68 / 30%)` | `rgb(220 38 38 / 30%)` | Red offline badge border |
| `--color-status-badge-loading-bg` | `rgb(245 158 11 / 12%)` | `rgb(217 119 6 / 10%)` | Amber loading badge background |
| `--color-status-badge-loading-border` | `rgb(245 158 11 / 30%)` | `rgb(217 119 6 / 30%)` | Amber loading badge border |
| `--color-status-badge-idle-bg` | `rgb(146 150 163 / 15%)` | `rgb(107 114 128 / 10%)` | Muted idle badge background |
| `--color-status-badge-idle-border` | `rgb(146 150 163 / 30%)` | `rgb(107 114 128 / 25%)` | Muted idle badge border |

Tokens that inherit via `var()` and require no change: `--color-status-badge-online-text`, `--color-status-badge-offline-text`, `--color-status-badge-loading-text`, `--color-status-badge-idle-text`.

### Contrast and legibility criteria

All proposed text-on-background combinations were evaluated against WCAG 2.1 AA criteria using the relative luminance formula. Contrast ratios are exact values, not estimates.

**WCAG 2.1 AA thresholds:**
- **Normal text** (< 18px or < 14px bold): ≥ 4.5:1
- **Large text** (≥ 18px or ≥ 14px bold): ≥ 3.0:1
- **Icons and non-textual elements**: ≥ 3.1 (WCAG 2.2) / ≥ 3:1 (WCAG 2.1)

#### Text on white surface (`--color-surface`: #ffffff)

| Combination | Contrast Ratio | AA Normal Text | AA Large Text | Status |
| --- | --- | --- | --- | --- |
| `--color-text-primary` (#1f2937 on #ffffff) | 14.68:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-text-secondary` (#4b5563 on #ffffff) | 7.56:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-text-muted` (#6b7280 on #ffffff) | 4.83:1 | ✅ Pass | ✅ Pass | Approved (close to minimum) |
| `--color-text-disabled` (#9ca3af on #ffffff) | 2.54:1 | ❌ Fail | ❌ Fail | Intentional — disabled state |
| `--color-primary` (#4f46e5 on #ffffff) | 6.29:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-primary-hover` (#4338ca on #ffffff) | 7.90:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-success` (#059669 on #ffffff) | 3.77:1 | ❌ **Fail** | ✅ Pass | **See alternatives below** |
| `--color-warning` (#d97706 on #ffffff) | 3.19:1 | ❌ **Fail** | ✅ Pass | **See alternatives below** |
| `--color-error` (#dc2626 on #ffffff) | 4.83:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-white-text` on `--color-primary` (#ffffff on #4f46e5) | 6.29:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-white-text` on `--color-success` (#ffffff on #059669) | 3.77:1 | ❌ Fail | ✅ Pass | **See alternatives below** |
| `--color-white-text` on `--color-warning` (#ffffff on #d97706) | 3.19:1 | ❌ Fail | ✅ Pass | **See alternatives below** |
| `--color-white-text` on `--color-error` (#ffffff on #dc2626) | 4.83:1 | ✅ Pass | ✅ Pass | Approved |

#### Semantic text colors on white (badge and feedback text)

These are the darker variants used specifically for text labels in status pills, feedback messages, and operation icons:

| Combination | Contrast Ratio | AA Normal Text | AA Large Text | Status |
| --- | --- | --- | --- | --- |
| Status success text (#047857 on #ffffff) | 5.48:1 | ✅ Pass | ✅ Pass | Approved |
| Status warning text (#92400e on #ffffff) | 7.09:1 | ✅ Pass | ✅ Pass | Approved |
| Status error text (#b91c1c on #ffffff) | 6.47:1 | ✅ Pass | ✅ Pass | Approved |
| Movement entry text (#4f46e5 on #ffffff) | 6.29:1 | ✅ Pass | ✅ Pass | Approved |
| Brand mark text (#4f46e5 on #ffffff) | 6.29:1 | ✅ Pass | ✅ Pass | Approved |
| Nav active text (#4f46e5 on #ffffff) | 6.29:1 | ✅ Pass | ✅ Pass | Approved |
| Feedback error text (#b91c1c on #ffffff) | 6.47:1 | ✅ Pass | ✅ Pass | Approved |
| Feedback success text (#047857 on #ffffff) | 5.48:1 | ✅ Pass | ✅ Pass | Approved |
| Operation icon entry text (#047857 on #ffffff) | 5.48:1 | ✅ Pass | ✅ Pass | Approved |
| Operation icon adjustment text (#4f46e5 on #ffffff) | 6.29:1 | ✅ Pass | ✅ Pass | Approved |

#### Text on page background (`--color-background`: #f4f5f7)

| Combination | Contrast Ratio | AA Normal Text | AA Large Text | Status |
| --- | --- | --- | --- | --- |
| `--color-text-primary` (#1f2937 on #f4f5f7) | 13.46:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-text-secondary` (#4b5563 on #f4f5f7) | 6.93:1 | ✅ Pass | ✅ Pass | Approved |
| `--color-text-muted` (#6b7280 on #f4f5f7) | 4.43:1 | ❌ **Fail** | ✅ Pass | **Pending — see below** |
| `--color-text-disabled` (#9ca3af on #f4f5f7) | 2.33:1 | ❌ Fail | ❌ Fail | Intentional — disabled state |

#### Text on translucent badge backgrounds (blended on white)

Badge backgrounds are translucent; the effective background is the blend of the translucent color on white. Text contrast is evaluated against the blended result:

| Combination | Blended BG | Contrast Ratio | AA Normal Text | Status |
| --- | --- | --- | --- | --- |
| Success text (#047857) on success pill bg | #ebf6f3 | 4.96:1 | ✅ Pass | Approved |
| Warning text (#92400e) on warning pill bg | #fbf4eb | 6.50:1 | ✅ Pass | Approved |
| Error feedback text (#b91c1c) on error bg | #fceded | 5.69:1 | ✅ Pass | Approved |
| Success feedback text (#047857) on success bg | #ebf6f3 | 4.96:1 | ✅ Pass | Approved |
| Movement entry text (#4f46e5) on entry bg | #f0f0fc | 5.56:1 | ✅ Pass | Approved |
| Operation icon entry text (#047857) on bg | #e6f4f0 | 4.85:1 | ✅ Pass | Approved |
| Operation icon adj text (#4f46e5) on bg | #f0f0fc | 5.39:1 | ✅ Pass | Approved |

#### Icons and non-textual elements (≥ 3:1 threshold)

| Combination | Contrast Ratio | 3:1 | Status |
| --- | --- | --- | --- |
| `--color-success` icon (#059669 on #ffffff) | 3.77:1 | ✅ Pass | Approved as icon |
| `--color-warning` icon (#d97706 on #ffffff) | 3.19:1 | ✅ Pass | Approved as icon |
| `--color-error` icon (#dc2626 on #ffffff) | 4.83:1 | ✅ Pass | Approved as icon |
| `--color-primary` icon (#4f46e5 on #ffffff) | 6.29:1 | ✅ Pass | Approved as icon |
| `--color-border` (#e5e7eb on #ffffff) | 1.24:1 | ❌ Fail | **Not a contrast element** — borders are structural, not informational |
| `--color-border-strong` (#d1d5db on #ffffff) | 1.47:1 | ❌ Fail | **Not a contrast element** — borders are structural, not informational |

#### Failing combinations and proposed alternatives

Three combinations fail WCAG AA for normal text:

| Failing Combination | Ratio | Issue | Proposed Alternative | Alternative Ratio |
| --- | --- | --- | --- | --- |
| `--color-success` (#059669) on white | 3.77:1 | Used as button/link text would fail AA | Keep `#059669` for UI elements (icons, borders, backgrounds). For **normal text**, use `#047857` (5.48:1) — already defined as `--color-status-success-text` and `--color-feedback-success-text`. | 5.48:1 ✅ |
| `--color-warning` (#d97706) on white | 3.19:1 | Used as button/link text would fail AA | Keep `#d97706` for UI elements (icons, borders, backgrounds). For **normal text**, use `#92400e` (7.09:1) — already defined as `--color-status-warning-text`. | 7.09:1 ✅ |
| White text on `--color-success` (#ffffff on #059669) | 3.77:1 | Green button with white text fails AA | If a green button is needed with text, use `#047857` as the button background (5.48:1 with white text). Alternatively, use dark text on a light green background. | 5.48:1 ✅ |
| White text on `--color-warning` (#ffffff on #d97706) | 3.19:1 | Amber button with white text fails AA | If an amber button is needed with text, use `#b45309` as the button background (5.02:1 with white text). Alternatively, use dark text on a light amber background. | 5.02:1 ✅ |
| `--color-text-muted` (#6b7280) on page bg (#f4f5f7) | 4.43:1 | Muted text on page background fails AA | Muted text rarely appears directly on the page background — it appears on white surfaces (4.83:1, passes). If it must appear on the page background, darken to `#5b6270` (6.13:1). | 6.13:1 ✅ |

**Key insight:** The tokens `--color-success` (#059669) and `--color-warning` (#d97706) are intended for **UI elements** (borders, icon backgrounds, translucent fills), not for normal text on white. The darker text variants (`#047857` and `#92400e`) are already defined in the semantic tokens for exactly this purpose. As long as the implementation uses the correct token for each context, all normal text will meet WCAG AA.

**Important:** This table covers only the combinations documented in the proposal. Full WCAG AA compliance requires verifying every component with its actual text-and-background pairings at implementation time.

### Tokens requiring visual validation in browser

The following tokens require visual confirmation in a real browser, as contrast ratios alone don't guarantee perceptual quality:

1. **`--color-text-muted` (#6b7280)** — contrast is 4.83:1 on white (passes) but 4.43:1 on the page background #f4f5f7 (fails). Validate that muted text never appears directly on the page background in actual component layouts. If it does, consider darkening to `#5b6270`.
2. **`--color-text-disabled` (#9ca3af)** — intentionally low contrast (2.54:1) for disabled state, but must remain distinguishable from muted text.
3. **`--color-success` (#059669) and `--color-warning` (#d97706)** — these fail AA for normal text on white. Validate that the implementation never uses these tokens for normal-sized text labels. They are safe for icons, borders, and translucent backgrounds.
4. **Translucent backgrounds** — all `rgb(r g b / %)` values need visual validation to ensure they are perceptible on white without appearing washed out.
5. **`--color-table-row-hover` (rgb(79 70 229 / 4%))** — very subtle; verify it provides enough visual feedback.
6. **`--color-topbar-bg` (rgb(255 255 255 / 94%))** — translucent white; verify backdrop blur effect is appropriate.
7. **HealthCard shadows** — lighter shadows may be imperceptible on a light background.
8. **White text on green/amber buttons** — if any component uses white text on `--color-success` or `--color-warning` backgrounds, the contrast will fail AA. Validate that no such pattern exists, or use the darker alternatives (`#047857` for green, `#b45309` for amber).

### Known issues and pending items

1. **Select dropdown arrow SVG** — The `--color-select-arrow` token exists but cannot be used inside the current SVG data URI in `style.css` (line ~612). The color `%239296a3` is hardcoded in the inline SVG. Proposed light value: `#6b7280`. Resolution requires replacing the data URI with a real SVG element or using CSS `mask-image` in a future phase.
2. **HealthCard shadow tokens** — The current shadow values use `rgb(0 0 0 / %)` which works for both themes but may need different opacity levels. The proposed light values reduce opacity slightly.
3. **`color-scheme`** — Currently set to `dark` in `:root`. When the light theme is implemented, this must toggle between `dark` and `light` to affect native browser controls (scrollbars, unchecked inputs).
4. **Focus ring** — `--focus-ring: 0 0 0 3px rgb(99 102 241 / 28%)` uses the dark-theme primary color. For the light theme, it should use `rgb(79 70 229 / 28%)` to match the darker indigo.
5. **`--shadow-overlay`** — Currently `0 16px 40px rgb(0 0 0 / 18%)`. For light theme, a lighter overlay may be appropriate: `0 16px 40px rgb(0 0 0 / 10%)`.

### Implementation status

All light theme features **have been implemented**:

- `html.light-theme` selector in `frontend/src/style.css` with all token values.
- Theme toggle button in the topbar (`App.vue`) with sun/moon icons and accessible labels.
- `localStorage` persistence (`casa-afeto-theme` key: `'light'` or `'dark'`).
- `prefers-color-scheme` OS detection on first visit (no stored preference).
- Inline script in `index.html` applies the theme before Vue renders, preventing flash.
- Dark theme is the fallback when no preference is stored and the OS does not prefer light.

The dark theme remains unchanged. All Vue components consume tokens via CSS custom properties — no component-specific color changes were needed for the toggle mechanism.

---

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
