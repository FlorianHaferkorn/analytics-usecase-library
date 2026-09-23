# Guided batch capability

Status: implemented local increment, 8 September 2026. Not Fabric execution or customer acceptance.

## Scope

`/automation/ingestion` captures one structured source-object contract and derives names, a proposed environment graph, a local processor and a delivery checklist from the same immutable Project Package revision. It remains part of the existing Studio, not a second project ledger.

The implementation executes **typed JSON rows in Python**. A CSV landing path describes the intended source but is not read. SQL Server selection explicitly blocks saving/generation. No extractor, gateway connection, CSV parser, Delta writer, CDF processing, Spark notebook, Fabric pipeline definition or production state store is supplied. Fabric-style labels describe intended targets, not deployed objects.

## Workflow and authority

1. Select a project and load its current Package. Opening the tool creates nothing. Initial form values are labelled synthetic examples.
2. Enter source, schema, columns/types, keys, load mode, environments and namespace. This increment supports one optional `batch_ingestion` module per Package, not multiple sources.
3. Review names, consequences, architecture and before/after changes. Preview is read-only; inconsistent or unsupported input blocks saving.
4. Provide a rationale and confirm the exact preview. The server supplies editor identity; Python rederives the preview hash. Expected-HEAD comparison prevents stale saves. A new **Working** version preserves other modules and adds an audit record. It does not approve a customer decision or authorize deployment.
5. Run explicit test batches against the saved contract. Studio accepts up to three batches of 1,000 rows. Each request starts fresh; batches within it run sequentially. Results are transient local evidence, not persisted customer acceptance.
6. Review/approve the Package and release its inputs separately. Only the current released version can generate the ZIP. Export never executes its contents.

## Coupling

| Contract input | Derived result | Remaining boundary |
|---|---|---|
| Namespace, domain, source | Workspace, Lakehouse and pipeline names | Generic snake_case template, not the full customer naming-policy engine |
| Schema, table and columns | Qualified name, validation and typed local state | No physical table is created |
| DEV/PROD or DEV/TEST/PROD | Environment nodes and promotion links | No binding or promotion execution |
| Load mode, keys and watermark | Update/replay behavior and explanatory content | No inferred hard deletes or CDF |
| Package revision | Same-version architecture, runtime, documentation and checklist | Existing topology is preserved, not silently rewritten |

The project Architecture view appends namespaced batch nodes with an explicit local-contract scope. Reconciling candidates into existing physical items, linking them to a business use case and compiling native definitions remain separate work. The exported `delivery-work-plan.json` contains acceptance criteria and unresolved adapter/binding tasks; it does **not** replace the Plan module, invent dates or staffing, or provide commercial estimates. Effort remains unknown.

## Data semantics and limits

Incremental mode requires a non-null integer watermark outside the business key. Inclusive boundary rows are accepted and upserted by key. Identical committed batch replay is a no-op. Changed content under the same batch ID, conflicting values at the same key/version, and older backfills fail. Absent incremental keys are retained.

Full mode explicitly replaces the local snapshot, including removing absent rows. Empty full snapshots are refused. Decimal values use exact strings. Schema drift, duplicate keys, invalid types/nulls and invalid state fail the entire batch without mutating previous caller state. Changed contracts cannot silently reuse old state.

The portable kernel limits are local safeguards, not Microsoft platform limits: 10,000 rows, 100 columns, 1,000 batch receipts and 4 MB of JSON. Studio imposes smaller request limits. A single external writer must atomically persist data, watermark and replay ledger. Concurrency and crash recovery are not proven.

## Export and trust

The ZIP contains the actual local Python kernel, schema, hash helpers, contract, architecture, provenance, README, dependency requirement and work checklist. The CLI consumes JSON rows, not CSV files. `output-manifest.json` hashes all payloads except itself; the Automation report additionally hashes that manifest. Hashes prove consistency, not signer identity or approval.

The API verifies project/revision, relative paths, uniqueness, full hash coverage and manifest content. Viewer authorization covers inspect, preview and explicit local tests/exports; saving additionally requires editor authorization. POST requires same-origin JSON and closed fields. Browser inputs cannot supply actor, arbitrary commands, host paths, credentials or prior state. The Python module and trusted paths are server-owned. The operator must configure `ALUCA_REPO_ROOT`; this work does not edit `.env` or enable a live runner.

## Reproducible checks

From the repository root:

```powershell
py -3 -m pytest tooling/tests/test_project_batch_ingestion.py tooling/tests/test_project_batch_workbench.py -q
```

From `studio`:

```powershell
npx vitest run tests/api/project-batch.test.ts tests/components/batch-ingestion-workbench.test.tsx tests/lib/project-output.test.ts tests/lib/project-batch-bridge.test.ts
npx tsc --noEmit
npm run lint:tokens
```

The opt-in browser test requires an existing development server. Its config has **no server-start or DB-reset hook**. It creates only a fresh temporary synthetic repository and connects React to the actual Python CLI through a test transport. Authentication/API enforcement is tested separately; this is not proof of the deployed HTTP bridge or tenant authentication.

```powershell
$env:STUDIO_BATCH_E2E='1'
npx playwright test --config playwright.batch.config.ts
```

Preserve immutable history. Reverting input creates another reviewed Working revision. After an uncertain save, load latest and inspect the audit before retrying. Failed local batches preserve previous state; production recovery requires the future platform adapter.

Verification on this increment: 78 core processor/export tests, 20 batch Package integration tests, 72 existing architecture/Automation/decision-derivation tests and 25 Package schema/release tests passed. Studio passed 70 API, 10 component, 13 bridge and 3 output ZIP tests. The real-processor Chromium harness passed through reviewed save, incremental update, refusal of an unapproved export, fixture-only approval/release and downloaded ZIP revision checks. TypeScript, scoped ESLint, the 40-file token gate and diff whitespace checks passed. Desktop and narrow screenshots were visually inspected. These scoped checks are not whole-product certification or tenant proof.

## Customer integration gate

A customer engagement may be used for tenant integration, but is not the source of this generic module's defaults. Before any live action, agree the exact DEV/TEST workspace or permitted creation scope, tenant/identity, capacity where required, synthetic data or an approved UC1 subset, operations, acceptance checks and cleanup owner. Read the current customer index and full Ledger before deriving customer inputs.

Recommended sequence: prove the existing create-only workspace runner under exact scope; then implement one source-to-Bronze Fabric adapter and verify extraction, reconciliation, replay, failure recovery and readback. The local processor is a reference contract, not a substitute for native runtime proof.
