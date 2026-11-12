# Mockup Reference — Studio Rebuild

Target design for the Studio rebuild (Claude Design export, uploaded 2026-04-24): the
**visual and interaction source of truth** (see `../REBUILD_DECISIONS.md` D1). File names
match their content (`src/shell.jsx` is the shell, `src/wizard.jsx` the wizard, and so on).

Until 12.11.2026 the same files also lay in `studio/docs/design-bundle/` (export bundle) and
`studio/docs/design-reference/` (same content under swapped file names, with a name/content
map). Both were byte-identical copies of this folder (git blob hash) and were removed; the
only difference was the Tweaks default in `Studio.html` (`fontPairing: "inter"` in the
bundle, `"geist"` here). The old folders are in the git history
(ref `archiv/vor-entschlacken-2026-11-12`).
