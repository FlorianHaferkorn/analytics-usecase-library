# Studio design-system enforcement

## Scope

The shared page primitives (`StudioPage`, header, panel, metric, toolbar, button,
field and segmented control), shared dependency canvas, Discovery components,
native dialog and application shell have an enforced source gate.
Shared data-entry controls, table primitives, badges, role chips, disclosure
controls, shortcuts and the notification action are also explicitly governed.
This is a migration boundary, not a claim that every Studio screen complies.
The command tracks older source files against `tooling/design-token-debt.json`.
Existing literal UI colors and sub-12px type remain explicit migration debt.
New findings fail CI, including another occurrence of an already known value.
Reductions pass; record the lower count in the baseline during review so removed
debt cannot be reintroduced later. Renaming or moving a file does not transfer its
debt allowance automatically. Line-number shifts do not cause false failures.

Eight exact, count-limited customer-theme preset values are excluded because they
describe editable/exported customer design data, not Studio chrome. The exclusions
name file, rule, value, allowed count and reason in the checker. Other preview and
diagram findings remain visible debt; there is no blanket preview-directory bypass.

Run from `studio/`:

```sh
npm run lint:tokens
node tooling/check_tokens.mjs --inventory
node --test tooling/check_tokens.test.mjs
npx vitest run tests/components/studio-page.test.tsx
```

The gate parses CSS and TypeScript syntax. It rejects literal colors, font sizes,
spacing and corner radii in governed CSS. Governed TSX currently enforces color
and font-size properties; it does not yet enforce all inline spacing or arbitrary
Tailwind classes. It detects circular CSS tokens across the
source tree, and prevents shell declarations from overriding inherited density.
There is no blanket quoted-string exemption or automatic baseline update option.
Do not increase baseline counts merely to make CI pass. CI runs both the rules and their
regression tests. Dynamic geometry (canvas positions, widths, transforms) is not
treated as a spacing violation.

## Token authority

`src/styles/tokens.css` owns semantic spacing, density, type roles, radius and
motion. `globals.css` supplies backward-compatible aliases. The shell consumes
tokens; it only overrides page gutters at its mobile breakpoint. The half-step
spacing token is for optical alignment and focus clearance, not body padding.

Shared captions are at least 12px before any canvas transform. This is a product
rule, not an accessibility conformance claim: contrast, zoom, focus visibility,
reflow and real content still require browser checks.

## Interaction contract

- `StudioButton` defaults to `type="button"`, accepts standard native attributes
  and supports explicitly requested form submission. All variants honor `tone`.
- `StudioField` associates its visible label with its single control, retaining
  an existing control ID. Custom field children must forward `id` and
  `aria-labelledby` to their native control or group.
- `StudioSegmentedControl` is a named button group, not a fake tablist. The chosen
  option exposes `aria-pressed`; only one option enters the tab sequence. Arrow
  keys wrap through options, Home/End jump to the first/last option, and focus
  follows selection. Actual tab navigation should use a separate tabs pattern.
- Empty, unavailable, loading and error states must retain distinct meanings.
  Zero is a data value, not a fallback for inaccessible data.
- Shared table headers expose column scope. Wide tables retain horizontal access
  rather than being clipped. Shared selection rows expose `aria-pressed` and do
  not nest interactive checkboxes inside buttons.
- Legacy helper text and labels were migrated to the 12px caption token; larger
  body text is preserved. Theme preview grids adapt their column count and grow
  with content so readable captions do not require clipping or shrinking.

## Extending coverage

1. Migrate a component to tokens and accessible interaction states.
2. Add component behavior and browser coverage with realistic content.
3. Add its exact source paths to `GOVERNED_FILES` in the checker and remove the
   migrated findings from the debt baseline.
4. Review visual changes at compact and wide desktop widths, light/dark themes,
   keyboard navigation and 200% text zoom before accepting the migration.

The current source gate does not replace screenshot review, accessibility
testing or verification of the underlying customer workflow.
