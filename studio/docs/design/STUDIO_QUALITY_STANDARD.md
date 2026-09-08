# Studio quality standard

## Purpose

The Studio is a professional consulting workbench, not a collection of dashboards. Every page must make the current project state, the next decision and the resulting delivery action understandable without reconstructing context from other tools.

## Visual system

- Use the 4 px spacing grid: 4, 8, 12, 16, 20, 24, 32 and 48 px.
- Use semantic spacing tokens. Page gutters, section gaps, panel padding and control height are separate concerns.
- The default workbench density is `balanced`. `airy` is an optional presentation preference, not the product baseline.
- Default content width is 1,280 px. Wide data workspaces may use 1,600 px. Graph canvases may use the full available width.
- Body copy is 14 px with a readable line height. Metadata is at least 12 px. Text below 11 px is prohibited.
- Use one primary action per decision region. Secondary actions must not compete with it.
- Use `plain`, `outlined` and `elevated` surfaces intentionally. Shadows are reserved for overlays and genuinely elevated content.
- Status colours communicate status only. Domain colours identify domains. Neither is decorative.

## Page contract

The primary work surface is the page. The canvas, table, editor or conversation receives the largest share of the initial viewport. At desktop widths, page identity stays compact: short descriptions align with the title, page actions share the in-page navigation row when their scope is clear, and secondary metrics move into the work-surface header. Do not stack separate rows that repeat context, metrics, filters and actions, or add a second horizontal gutter inside the shared page gutter.

Every primary workflow page should answer these questions in order:

1. Where am I in the engagement?
2. What is the current state?
3. What requires my attention or decision next?
4. What evidence supports that step?
5. What will change when I continue?

Pages should use progressive disclosure for details. Long collections use filtering, pagination or natural page scrolling; nested scroll containers are an exception that require a documented reason.

## Interaction and accessibility

- All controls have visible hover, focus, active and disabled states.
- Keyboard focus is never removed without a visible replacement.
- Interactive targets are at least 32 px in the desktop workbench and 44 px in touch layouts.
- Colour is never the only status cue.
- Layouts must remain usable at 1,440 px, 1,024 px and 768 px without horizontal overflow.
- Reduced-motion preferences disable non-essential transitions.

## Quality gate

The Playwright Studio quality baseline covers every primary navigation route at three reference widths. It blocks unexpected console errors, failed resources, horizontal overflow and visible text below 11 px. Explicit permission-denied states are accepted only when the page explains the required role in the interface. Scaled report previews are exempt from the text-size measurement because they intentionally represent a complete canvas at reduced scale. Optical snapshots are updated only after an intentional design review.

## Migration rule

New pages must use shared tokens and primitives. Existing pages are migrated in this order: shell and navigation, page primitives, Overview, Discovery, Blueprint, Generate, then secondary registry and administration screens. Inline styles are removed during migration; a page is not complete merely because it renders.
