# External delivery handoff bridge

The Studio Project Package can retain a content-addressed metadata snapshot of an external use-case handoff. The external source remains authoritative for its contracts and decisions. The bridge imports no source payload, secret, workbook, report definition or executable artifact into the generic library.

## Operator flow

1. Read the source project's index, decision authority and handoff instructions before interpreting its results.
2. From the library root, run `python -m tooling.superversion.project_package.external_handoff --source-root <source-root> --descriptor <root-relative-descriptor.json> --repository <studio-project-package-repository> --schemas tooling/generator/schemas`.
3. Open Studio > Project Package for the matching project. The External delivery handoff panel reports source integrity, open gates and the proof boundary. A changed source creates a new immutable package revision; an unchanged snapshot is idempotent.
4. Re-run after each authoritative source or manifest change. The CLI exits `0` only when all listed hashes match and exits `2` when the snapshot has drift. It still records the `needs_attention` snapshot, so an older green status cannot silently remain current.

For an intentionally updated inventory manifest, use `--refresh-manifest` only after reviewing the changed source rows. Pin the old manifest hash with `--expected-manifest-sha256` and enumerate each reviewed changed key with `--allow-drift-key`. The tool refuses changed required contracts, executable-package drift and an incomplete or broader allowlist. It refreshes inventory hashes, not decisions or acceptance. Run the normal bridge again afterward. Do not rebaseline while another editor is changing the source authority.

## Authority and proof boundary

| Item | Meaning |
|---|---|
| `hashes_match` | Source bytes matched their stated manifests at import time only. |
| `needs_attention` | At least one source or executable-package file is missing or changed. Inspect `drift`; do not use old manifests as current evidence. |
| `static_handoff_inventory` | File and contract provenance, not execution or semantic correctness. |
| `apply_ready: false` | No target-system mutation is authorized by this bridge. |
| `runtime_proven: false` | Parser and unit checks do not prove execution, bindings, values, rendering or security. |
| `customer_accepted: false` | Acceptance requires dated, attributable evidence under the source project's approval process. |

The source descriptor, manifests, ledger references, counts and use-case mapping stay in the source project. The generic bridge recognizes versioned handoff and executable-package manifest formats by their schema suffixes and validates their required structure and hashes. It does not create a parallel release route or decision source.

## Review gate for a mapped use case

1. Freeze one source snapshot: required contracts, referenced directories and every executable-package entry pass the bridge. Preserve the prior manifest and reconciliation diff when rebaselining.
2. Run bridge tests, Project Package repository read-back, Studio typecheck and UI tests. In a signed-in Studio session, verify the panel displays the same revision, gate count and integrity state without overflow or console errors. An unauthenticated response is not a UI pass.
3. Review the proposed `use_case_delivery` mapping against the authoritative contracts. Keep `delivery_state` at `contract_pending` until runtime and acceptance evidence closes the relevant gates.
4. Only then test decision-to-architecture propagation and release readiness. A green hash inventory or approved Project Package revision does not imply Apply authorization.
