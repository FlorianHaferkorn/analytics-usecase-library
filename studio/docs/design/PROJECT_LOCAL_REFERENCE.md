# Local reference lab

Date: 2026-09-08  
Status: Implemented bounded local reference; no tenant acceptance.  
Scope: Neutral synthetic fixture in analytics-usecase-library. Not a customer project change.

## Purpose and use

Use **Automation → Open local reference lab**, or `/automation/reference`, when no test tenant is available. Studio is the operator interface; it delegates to the existing Python package and compiler code. There is no second decision engine or architecture renderer.

1. Sign in to the local Studio. The development demo session is sufficient for this synthetic endpoint; it cannot authorize protected tenant execution.
2. Choose DEV/TEST/PROD or DEV/PROD and confirm the synthetic-only scope.
3. Select **Run local reference**. A fresh temporary repository runs locally; allow roughly a minute, depending on the host. The server process accepts only one reference run at a time.
4. Inspect **Input to delivery**, **Architecture**, **Checks & limitations**, and **Generated files**. The input panel collapses after success; reopen it to change the decision and rerun. A changed selection discards the old displayed outputs and requires a fresh confirmation.
5. Download the ZIP to retain the evidence and generated files. Reloading the page neither replays the operation nor restores its results.

The selected customer project is not read or changed by the lab. The surrounding Studio shell can still read ordinary session and project-selection metadata. A reserved `local_reference` namespace and a visibly synthetic scope prevent the example from being mistaken for the selected customer.

## What is executed, simulated or still absent

| Step | Actual local implementation | Evidence boundary |
| --- | --- | --- |
| Input | Versioned synthetic brief and three invented sales rows | Fixed fixture, not arbitrary document discovery or customer evidence |
| Decision | Explicit environment option, real before/after derivation and a new immutable Working revision | Targets are declared in the fixture for each option; no general topology inference or automatic environment cloning |
| Fixture release | Local fixture approval followed by the existing release machinery | Tests approval mechanics; not a customer approval, tenant permission or reusable host authorization |
| Architecture and plan | Existing architecture, workspace and native-item compilers, all pinned to the same final revision | Existing graph projection, not a new alternative diagram model |
| Documentation | Existing generated delivery documents plus source, derivation evidence, file hashes and test records | Describes this synthetic package, not an implementation-complete Fabric deployment |
| Data assertion | Python Decimal arithmetic: hardware 30.00 + services 7.50 = 37.50 | Does not execute Spark, SQL, DAX, Direct Lake or the generated Notebook/Pipeline |
| Workspace adapter | Existing planner and create-only executor called with an in-memory client | Create, exact repeat/no-op, conflict, interrupted outcome and readback recovery are simulations |
| Item adapter | Existing item compiler plus fake IDs and exact JSON-pointer binding contracts | No API call; Notebook/Pipeline definitions are transport examples, not a runnable data platform |
| Real platform acceptance | Not run | Credentials, Fabric compatibility, data/security/refresh behavior, promotion and performance remain unverified |

The logical source-to-serving graph and the native item transport examples are deliberately not described as an executable end-to-end data pipeline. Semantic/report definitions, Lakehouse storage and complete capability adapters remain separate implementation work.

## Evidence labels

- **Locally checked:** a bounded local assertion such as derivation, schema, file hash or deterministic generation.
- **Simulated:** behavior against fake targets. Passing this status never grants a tenant badge.
- **Tenant verified:** only the protected runner's matching verified workspace readback result; explicitly scoped to workspaces, not the whole project. The local-reference API rejects this evidence kind.
- **Not verified:** no qualifying evidence, including every tenant test in this lab.

A generated-file status is not a release approval. A release is not permission to deploy. A workspace readback is not complete project acceptance.

## Safety and isolation

- The endpoint requires a signed Studio session, same-origin JSON and explicit confirmation. It accepts only the two fixed variant identifiers; it rejects customer/project, actor, path, command, credential and policy fields.
- The bridge launches a fixed local module using the trusted repository/schema paths. It does not invoke the protected runner or a credential broker. The Python reference has no network, subprocess or Fabric SDK path.
- Every run receives a fresh OS temporary directory. Only that exact newly created directory is eligible for automatic cleanup. No selected Project Package root or existing database is a reference target. A timeout/file lock can leave temporary files; cleanup never expands to a broader path.
- The protected live runner refuses `local_reference` and `local_reference_*` scopes even if someone attempts to configure them in an allowlist. Local fixture approvals are not exported as live authority.
- The bridge validates synthetic provenance, forbids tenant evidence and verifies every UTF-8 SHA-256. Archive paths must be safe relative paths without case-insensitive duplicates.
- ZIP files contain `SYNTHETIC_ONLY.json`, the generated outputs and a summary report. Realistic request shapes are compiler test outputs, never a recommendation to submit them to Fabric.
- The HTTP process lock and bounded subprocess are local-development safeguards, not a distributed job queue or durable operations service. A dropped browser connection may leave the bounded local process finishing; it cannot call a tenant. Do not add an automatic retry loop.

## Reproduction

Run from the repository root:

```powershell
py -3 -m pytest tooling/tests/test_project_local_reference.py tooling/tests/test_project_item_simulation.py tooling/tests/test_project_protected_runner.py tooling/tests/test_project_runner_host.py -q
```

For an isolated CLI run, use a new empty absolute directory:

```powershell
$referenceRoot = Join-Path ([IO.Path]::GetTempPath()) ('studio-reference-' + [guid]::NewGuid().ToString('N'))
py -3 -m tooling.superversion.project_package.local_reference --root $referenceRoot --schemas tooling/generator/schemas --variant dev_test_prod
```

The standalone CLI retains its evidence in that directory. The Studio bridge instead returns the report and cleans its own temporary directory; use the ZIP for retention.

From `studio`, with an existing local development server:

```powershell
npx vitest run tests/api/local-reference.test.ts tests/lib/local-reference.test.ts tests/components/local-reference-lab.test.tsx tests/lib/project-scope.test.ts tests/components/project-runner.test.tsx
$env:STUDIO_LOCAL_REFERENCE_E2E='1'
npx playwright test --config=playwright.local-reference.config.ts --reporter=list
npx tsc --noEmit
node tooling/check_tokens.mjs
```

The dedicated browser configuration never starts a server or invokes a database reset. Do not replace it with the standard E2E server-start hook for a user workspace. The opt-in browser test uses real local session authentication and the real Python endpoint, verifies both decision variants and every downloaded file hash, checks customer-content/live-runner requests are absent, and tests reload behavior. It does not test Fabric.

## Verification record

- 168 Python tests passed together across the real local reference, item simulation, protected runner and host. After independent review, the namespace guard was made case-insensitive; all 34 protected-runner tests passed again, including two added mixed-case cases.
- 68 focused Studio tests passed across the lab API/bridge/UI, project scope and protected-runner UI. TypeScript, scoped ESLint, `git diff --check` and the design-token gate passed (38 governed files).
- The opt-in Chromium workflow passed with real local authentication and both actual compiler runs. It verified every exported file/hash, different variant revisions, no customer-content or live-runner requests, retained selection metadata, reload behavior and a 768px no-overflow assertion. Desktop and narrow screenshots were inspected. This is not full-product accessibility or design certification.
- The initial standard browser harness started its dedicated `.e2e` database reset hook because no server was running. No customer database was targeted; the later passing run used the new dedicated no-start/no-reset configuration. The dedicated test database is disposable, not an authoritative project store.

## Design and extension decision

The shared Studio panels, controls, typography and spacing tokens are retained. The reference uses the existing React Flow canvas, Dagre layout, accessible list alternative and ZIP implementation. After a run, inputs collapse so the outputs are the primary working area. The new components are included in the scoped token gate. No new dependency is required.

An unrelated simulator would be quick to demo but would not exercise the actual compiler/release boundary. Connecting to a customer tenant without a dedicated test scope would add risk and would not satisfy the requested tenant-free workflow. The chosen reference reuses production-path components while clearly limiting the evidence each can provide locally.

Next increments should replace one explicitly scoped placeholder at a time with a tested capability implementation, retain negative cases, and add real platform acceptance only after a separate authorized non-production target exists. Do not generalize this fixture into a promise of automatic delivery for every requirement.

Rollback is code-only: remove the lab page/link and its fixed endpoint/bridge selectively. No customer package migration, schema change, tenant cleanup or database rollback is required. Retain the reserved-namespace live guard and existing audit evidence.
