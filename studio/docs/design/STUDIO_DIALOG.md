# StudioDialog

Use this component for a short, blocking task such as pasting source notes or choosing a saved use case. Keep ongoing work and long-form editors on the page.

## Contract

| Property | Purpose |
| --- | --- |
| `open` | Controls the native modal state. |
| `title` | Required visible title and accessible dialog name. |
| `description` | Optional context, connected through `aria-describedby`. |
| `onClose` | Parent closes the dialog and handles draft cancellation. Called by Close or Escape. |
| `children` | Task controls and actions. Add `data-autofocus` to the intended starting control. |

The native `dialog.showModal()` puts the dialog in the browser top layer and makes the background inert. Tab and Shift+Tab wrap within available controls. Escape closes the dialog. Closing restores focus to its connected opening control. All form controls still require labels. Do not add another focus trap around this component.

The dialog uses shared text, spacing, border, surface and elevation tokens. Width is capped at 36rem and adapts to narrow viewports. The dialog itself scrolls if its content exceeds the available viewport; do not add fixed-height inner lists.

## Discovery usage

- Paste notes: initial focus on Source text; Add Source stays disabled for whitespace-only content.
- Use-case picker: loading, empty, error, retry and adding states are distinct. It closes only after a valid definition was loaded and added. Authorization failures are explained, not converted into empty results.
- Source upload: TXT, MD, CSV, YAML and YML, with a 10 MB per-file client-side limit. Empty and null-byte binary contents are rejected. Valid files in a mixed drop are retained and rejected files are named in the error. These checks are intake safeguards, not evidence that source claims are trusted or approved.

## Verification

`e2e/discovery-interactions.spec.ts` checks keyboard traversal, Escape, focus restoration, paste submission, mixed-file drag/drop, removal, request error recovery and a successful use-case load in Chromium. API responses are fixture-controlled for the picker test; this does not prove customer authorization or live source availability.

The same spec checks equal panel height and top alignment at 1600 × 900 and readable loaded chat text. The chat fixture follows `/api/ai/chat`'s plain-text streaming response. `tests/components/discovery-chat.test.tsx` additionally splits a response at every byte to verify partial lines and multi-byte UTF-8 characters. No live AI provider is invoked by these tests. Structured tool-result delivery is not provided by the current text-only endpoint and is not covered as a working end-to-end feature.
