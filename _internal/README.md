# Legacy Path Notice

This path is a compatibility shim.

Internal content was split into:

- `tooling/` for shared generation, validation, and automation
- `internal/` for maintainer-only CI, strategy, and archive assets

Use the new primary entry point:

- `docs/README.md`

If you maintain scripts or links that still use `_internal/`, update them to either `tooling/` or `internal/` as appropriate.
