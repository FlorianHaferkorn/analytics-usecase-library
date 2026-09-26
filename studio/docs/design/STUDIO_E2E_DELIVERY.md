# Studio end-to-end delivery integration

**Date:** 2026-09-08
**Status:** Implemented incremental integration; not whole-product completion.  
**Scope:** Customer-independent Nagarro consulting workbench. No customer authority was migrated or approved by this work.

## Current increment: tenant-free reference lab

`/automation/reference` exercises a fixed synthetic brief, explicit environment decision, immutable revision, existing compilers and generated documentation through Studio. Both DEV/TEST/PROD and DEV/PROD variants are supported. Fake workspace and item targets cover creation, no-op, conflict and uncertain-operation behavior; file hashes and same-version output provenance are checked locally. The customer selection is preserved and its package is not used.

Evidence labels now distinguish locally checked, simulated and narrowly scoped tenant-verified results. The lab cannot produce tenant verification or live approval; the protected runner rejects its reserved namespace. This reference does **not** supply the missing executable data, security, semantic/report or CI/CD adapters and does not replace live acceptance.

Implementation boundaries, tests and operator steps: [Local reference lab](PROJECT_LOCAL_REFERENCE.md).

## Context and decision

The product plan has always included architecture and delivery. Studio is the single operator interface; the immutable Project Package owns project content, and the Python core derives validated outputs. The previous navigation emphasized the KPI Golden Thread and library tools, making that broader purpose difficult to see.

Expose **Delivery workspace** (`/engagement`) and **Architecture** (`/architecture`) as explicit project tools. Keep the reusable Library and Golden Thread tools available without presenting their content as project evidence. Entering an explicit project surface carries project intent into subsequent Generate and assurance links.

## Workflow and implementation boundary

| Stage | Current interface and source | Current behavior | Not yet implemented |
| --- | --- | --- | --- |
| Scope and offer | Delivery workspace; opportunity and commercial modules; Automation / Cost & staffing | Recorded scope plus private, explicit-rate Decimal calculations, contingency, named-resource capacity, overload warnings and same-version scenario download/restore | Persistent commercial authority integration, guided offer authoring and commercial approval workflow; scenarios are not offers |
| Discovery | Discover; saved project draft | Source collection, extraction, explicit review and source quotes | General reliable extraction across every requirement/capability |
| Reviewed model update | Review for Project Package | Selected strategy anchors become draft objectives with before/after review; exact evidence is versioned; Package returns to Working | Verified KPI/action registry mapping and arbitrary architecture-field inference |
| Decisions and plan | Delivery workspace, Approvals and Project Package | Recorded alternatives, owners, decision gates, work, effort provenance and role requirements; explicit approved option-to-field rules with reviewed before/after changes | Automatic workshops, scheduling, named staffing and a governed reusable decision-rule catalog |
| Architecture | Architecture; Python projection of architecture_input and use_case_delivery | Recorded sources, products, transformations, explicit workspaces and native item ownership/dependencies; adaptive graph layout and filters; reviewed decision effects create a new Working version and update the selected graph | Semantic relationship diagrams, automatic environment cloning and derivation of missing topology or native tool logic |
| Build and release | Generate input release, then Automation / Workflow & gates | Existing attestation required; selected deterministic architecture, workspace and native item request outputs; atomic hash-verified run records | Lakehouse and other item adapters, security/CI-CD adapters, physical-ID rebinding and complete target execution |
| Verify and operate | Automation / Deployment preflight; Health and Drift | Workspace planning and reconciliation; create-only executor; authenticated Studio approval/execution adapter and explicit host identity broker with signed single-use intent, exact scope and outcome recovery | Operational host configuration, live tenant proof, durable distributed jobs, complete runtime acceptance and automated operations |

Module presence is displayed as **recorded**, never as an approval or completion percentage. Roles in the current plan are requirements, not named assignments. Commercial figures retain their stated provenance; no rate or margin is supplied by the UI.

## Options and trade-offs

1. **Feed project data into the existing library Blueprint/Fabric emitters.** Less new code, but these emitters currently introduce workspace naming, ingestion, serving and CI/CD defaults. Rejected for project compilation until those choices are explicit inputs.
2. **Build an independent Studio compiler.** Fast local UI changes, but duplicates validation and decision authority in TypeScript. Rejected.
3. **Extend the Python Project Package boundary with a strict projection and bounded adapters.** Selected. Reuses package validation, hashing, release records and the existing detailed delivery-document renderer. Adds a small projection because the legacy derivation defaults are unsafe for this use. Unsupported inputs remain blocked.

The architecture schema's optional `physical_workspaces` field is backwards compatible. It contains exact names, environments, domain/capacity UUIDs and decision references. Nothing infers those values from a domain label. Native workspace request files are inputs to the documented API, not an executor, reconciliation loop or full-project deployment.

## Safety, testing and rollback

- No tenant operations, new dependency, customer role grant, customer approval or repository commit.
- Discovery checks saved draft revision and expected Package HEAD. Exact-quote-backed objectives are draft-only; existing decision records are not silently overwritten.
- Architecture views and downloads bind project identity and revision; a change in revision invalidates the browser's generation confirmation. A valid existing release attestation is required server-side.
- TypeScript and the token gate passed; 24 targeted Studio unit/route tests and seven browser workflows passed in the final focused runs. The architecture agent also ran 19 Python tests covering schemas, actual immutable revisions, release gates and generated outputs. Discovery adds seven actual repository tests. Browser customer/project data and AI behavior use fixtures, not live customer acceptance.
- Desktop and narrow architecture screenshots were inspected. Graph, filter, expandable contracts, output confirmation, navigation, project switch and Discovery transfer were exercised.
- Preserve and back up the existing Package and SQLite data roots. Roll back code selectively; the checkout contains unrelated user changes. Older schema consumers can reject packages using the optional extension, so keep compiler/schema versions aligned when sharing them.

## Automation implementation increment

The `/automation` route is an explicit project surface. It keeps workflow gates, private estimation, workspace preflight and run evidence in the same interface. Studio delegates authoritative calculations and release decisions to Python. The status view never equates recorded modules with acceptance, and no progress percentage implies full delivery readiness.

Generation consumes the current released revision and an explicit list of outputs. It rejects the whole selected run if any selected target is blocked. Repeated identical requests reuse the same hash-checked record; concurrent writes and a changing Package HEAD cannot publish a partial successful run. The saved record includes the authenticated Studio actor, exact input/release hashes, output hashes and the scope of the run. Customer content is not persisted in browser storage.

The optional `physical_items` contract supplies exact Notebook, DataPipeline, SemanticModel and Report definition parts. Local checks cover envelope integrity, supported format families, JSON syntax, approved decision references and declared dependencies. This does not prove business logic, credentials, embedded physical IDs, model security or runtime behavior. Definitions and diagram nodes derive from the same contract, but declared build dependencies are labeled separately from data lineage.

Workspace preflight can classify create/noop/conflict/blocked and compare imported readback with the authoritative released contract. The `fab` create-only execution adapter is implemented and fake-client tested, but is not exposed to a browser as an unauthenticated apply endpoint. Live execution requires a trusted token broker, protected approval/state storage, exact target authorization and tenant evidence. No tenant was contacted or changed by this increment.

Commercial schema policy forbids embedded private prices. Consequently, the calculator intentionally remains a private scenario: rates, people and availability are explicit; save/restore is a private downloaded file scoped to the same project and revision. It is neither persistent offer approval nor dependency-aware scheduling.

Implementation details: [Native item generation](PROJECT_NATIVE_ITEM_GENERATION.md), [Workspace execution safety](PROJECT_DEPLOYMENT_SAFETY.md), [Private estimation](PROJECT_ESTIMATION.md).

### Validation of this increment

- 121 focused Python tests passed together: generation orchestration, native item transport, architecture projection, workspace planning/execution seams, estimation, input release and reviewed Discovery transfer. Fixtures use temporary repositories and fake tenant clients.
- 54 focused Studio unit/API/component tests passed. TypeScript and scoped ESLint passed. The design gate reports 29 governed files with no tracked token debt; this is not whole-product accessibility or design certification.
- Eight Chromium workflow tests passed across Discovery, project isolation, architecture, automation and the shell. The extended automation case was rerun after ZIP persistence/download and narrow-header changes; it also opens the actual downloaded ZIP and checks its files and run identity.
- Desktop and narrow screenshots were inspected. Input bounds, project/revision confirmation reset, target selection, tab-state retention, output retrieval after reload and header search visibility were checked. No new dependency or tenant action was required.

These are implementation tests, not customer acceptance, actual tenant permission evidence, a full repository regression run or a production release. The architecture and testing skills shaped the approval/reconciliation boundaries; the design-system skill kept new views on shared controls and tokens.

## Remaining completion gates

1. Configure and prove the implemented authenticated Studio/runner integration with a least-privileged identity, private storage and recovery ownership. Prove create, repeated no-op planning, interrupted execution and readback in an explicitly authorized non-production tenant. Implementation and fixture tests are not live operational acceptance.
2. Extend execution from workspaces to fully validated item definitions, physical-ID resolution and bindings. Include Lakehouse/table provisioning, source connections, security, Git and stage promotion; every unsupported family must remain blocked.
3. Expand the implemented explicit option-to-field mappings into a governed reusable rule catalog and separately tested topology/native-definition adapters. Current rules replace a limited set of existing fields; they do not create TEST workspaces or infer tool logic. Do not turn a recommendation or an imported comment into a customer decision.
4. Connect commercial authority and staffing availability, implement dependency-aware planning and generated offer/delivery documents without leaking private rates into customer exports.
5. Prove one complete approved project from reviewed evidence through deployment, data/security tests, acceptance and drift detection before claiming end-to-end automation. Framework completeness across arbitrary tools and requirements is not established by this implementation.

### Decision-to-plan impact increment

An approved environment-stage mapping now requires explicit effects on plan role demand, effort with provenance, and a task Definition of Done. Studio previews architecture and plan changes together; a reviewer commits both in one Working revision. Input release rejects missing, stale or unapplied effects, including when an old release attestation exists. Generated architecture outputs include a revision-bound, hash-checked static decision-impact record. This prevents a three-stage architecture choice from silently retaining a two-stage delivery plan.

This is one bounded WB-008 slice, not WB-008 completion. It does not create missing TEST workspaces/items, assign available people, calculate private rates or duration, execute deployment, or verify tenant tests. The neutral fixture demonstrates the contract; no customer baseline was edited. Remaining WB-008 acceptance requires a released synthetic, customer-neutral reference fixture and explicit topology, manifest, and execution-test obligations across the selected tools. WB-008 is closed without a customer tenant and without customer data; Fabric runtime behavior is proven separately in an isolated test tenant with synthetic data and its own identities.

References: [Product workbench plan](../../../docs/architecture/research/discovery-to-deployment-workbench.md), [Project authority](PROJECT_AUTHORITY_AND_VIEWS.md), [Discovery transfer](DISCOVERY_PACKAGE_TRANSFER.md), [Architecture compilation](PROJECT_ARCHITECTURE_COMPILATION.md), [Input release](PROJECT_INPUT_RELEASE.md).

### Alternative impact increment

A draft alternative can now be compared against the released baseline without changing it. The engine evaluates the authored decision rules with the alternative selected, reports architecture, plan, role demand, effort, topology, manifest and test deltas plus the obligations before a release, and verifies that repository history, HEAD and release records are byte-identical afterwards. The reference is a synthetic, customer-neutral manufacturer package (sales and finance, SAP S/4HANA declared as source by table label only) with an accepted DEV / TEST / PROD baseline and a DEV / PROD alternative.

This closes the WB-008 proof at engine level. The Studio comparison view is not built yet; named staffing and commercials remain WB-009; tenant behavior remains a separate, isolated test-tenant proof. Details: [Alternative impact](PROJECT_ALTERNATIVE_IMPACT.md).

## Reviewed decisions and protected execution increment — 8 September

**Definition of done for this increment:** an explicit approved decision can be reviewed as a deterministic before/after change, transferred to an auditable Working revision, displayed in the selected architecture and prevented from bypassing a fresh release. Execution intent can be stored and consumed safely by a protected host library without enabling a live tenant connection.

Architecture now includes **Decision effects**. A viewer can inspect the pinned preview; an editor can confirm the exact preview hash and provide a rationale. Python reads all values and existing approvals from the immutable Package. The API does not accept an actor, rule payload, replacement value or decision approval from the browser. Updates reset the generation confirmation, and the graph loads the returned new revision. Both the callback and the shared Package loader reject responses for a no-longer-selected project or revision.

The release boundary checks declared rules before reading or writing an attestation. Pending, conflicting or still-unapplied effects block release even when the package says Approved or an older attestation exists. Already-applied and nonselected-option rules do not create repeated revisions. The engine preserves decisions and source evidence and adds a versioned review record. Fields outside the bounded rule contract remain unsupported.

The protected workspace runner stores HMAC-signed plan/approval records under opaque IDs, checks exact tenant/principal/environment/project and actor policies, expires approvals, consumes each intent once and serializes workspace writes within its host storage. It wraps the existing create-only executor. Its default policy is disabled; no key, token, tenant scope or live endpoint has been configured by this work.

**Verification strategy:** pure rule and policy tests; actual temporary immutable repositories, release records and CLI integration; authenticated route boundary tests; component tests for confirmation and stale responses; Chromium review → updated graph → release-blocked output flow at desktop and narrow widths. Tenant operations use fake clients only. This is not production approval or proof of arbitrary capability automation.

**Recovery:** preserve immutable Package history and protected runner receipts. A failed update response can be uncertain after a commit; reload HEAD before retrying. Do not automatically replay a consumed execution or delete created workspaces. No customer ledger, handbook, tenant or private commercial authority was changed.

Details: [Reviewed decision derivation](PROJECT_DECISION_DERIVATION.md), [Protected runner boundary](PROJECT_PROTECTED_RUNNER.md).

### Validation result for 8 September

- 186 focused Python tests passed together across decision derivation, protected runner, generation, item/architecture compilation, deployment planning, estimation, release and Discovery transfer. These include 37 decision-derivation cases and 28 protected-runner cases.
- 72 focused Studio tests passed in 14 API, component and library files. TypeScript, scoped ESLint and `git diff --check` passed. The token gate covers 31 governed files with no tracked token debt; this remains a scoped check, not whole-product certification.
- Five Chromium workflows passed: delivery navigation, architecture contracts/outputs, automation and ZIP export, decision review through updated graph/release invalidation, and project isolation. The 1440px and 768px decision-review screenshots were inspected after the compact-layout refinement. The scenario uses fixtures; no customer package was changed.
- The local Studio was started without resetting its database. No new dependency, repository commit, customer decision or tenant operation was required. The full repository suite and live acceptance tests were not run.

## Authenticated workspace execution integration — 8 September

The protected runner is now connected to **Automation → Deployment preflight** through a server-only bridge and fixed Python host adapter. The existing create-only executor remains the execution engine. This supersedes the earlier library-only integration status above; it does not establish live tenant readiness.

The Studio guard requires a current project-admin role, verified GitHub OAuth provenance and a stable provider actor. Demo and legacy sessions are refused. Mutations require a fresh sign-in, a securely generated host session secret and exact-origin JSON requests, with HTTPS outside loopback. The browser cannot choose credentials, commands, host paths, actor identity or policy. Host-owned exact allowlists select the tenant, service principal and environment. Explicit Azure Identity credentials replace ambient login discovery.

The operator reviews the exact plan, records a rationale and saves its signed, expiring approval. A second confirmation starts its single allowed execution attempt. After a timeout or reload, the operator can retrieve the signed outcome using project/revision/approval IDs retained in the URL; no plan or credential is retained there. Recovery never retries execution. A full disabled host configuration can retain read-only evidence access without re-enabling writes. Interrupted claims and tenant locks require controlled reconciliation.

**Verified in this increment:**

- 111 Python tests passed together across the host adapter, protected runner and workspace deployment executor. Credentials and Fabric clients are fakes; subprocess envelopes and persisted evidence use actual local test files.
- 70 Studio tests passed across runner routes/components, authorization, OAuth provenance and session behavior. TypeScript and scoped ESLint passed.
- Two Chromium workflows passed: existing automation/generation/private scenario/export behavior, and separate workspace approval/execution with an uncertain response followed by reload and signed-outcome retrieval. Browser APIs use fixtures, not live authentication or tenant writes.
- Desktop (1440px) and narrow (768px) screenshots were inspected. The token gate covers 32 governed files with no tracked token debt; this is not whole-product visual or accessibility certification. `git diff --check` passed.

The design-system skill kept the added surface on shared panels, buttons and tokens. No dependency was installed, no database was reset, and no customer artifact, tenant or permission was changed. Host configuration remains an explicit operational prerequisite. The bounded subprocess is not a durable distributed job service. Item definitions, physical-ID bindings, security, data loading and CI/CD execution remain separate completion gates.

Operational configuration, recovery and limitations: [Protected Studio runner host](PROJECT_RUNNER_HOST.md).

## Readiness and first-workspace acceptance increment — 8 September

Automation / Deployment preflight now starts with read-only readiness diagnostics. The authenticated status combines four Studio access/origin checks and twelve host configuration/evidence checks. Missing prerequisites have specific next actions. A refused access check does not invoke the host; an unavailable host produces a sanitized remediation. Configured references remain distinct from operational proof. Approval and execution maintain independent role eligibility.

The first-workspace acceptance procedure is available in the same page with a project/version-scoped JSON export. It covers explicit non-production authorization, host review, creation/readback, repeat no-op planning, recovery and final reconciliation. It recommends one initial create only and never runs a tenant operation merely by opening or downloading it. A matching runner result is evidence to review, not acceptance. Formal acceptance recording and aggregation of historical evidence are not implemented by this review protocol.

Independent review found and resolved split-role gating and planning-input remount/focus loss. Regression tests cover separate approvers/executors, plan-change consent invalidation, late response rejection and retained input focus. Shared design-system panels, controls and tokens were reused; configured details and the full procedure are expandable.

Details and reproducible checks: [Workspace readiness and acceptance](PROJECT_RUNNER_ACCEPTANCE.md). No host activation, credential provisioning, tenant operation, database reset or customer decision was performed. The next gate remains explicitly authorized operational configuration and live non-production proof, not another claim of full delivery readiness.

Validation: 129 Python tests passed across host diagnostics, protected runner and deployment; 113 Studio tests passed across access/session guards, runner API/UI, acceptance derivation and existing automation. Two Chromium workflows passed, including remediation/recheck, protocol JSON content, focus preservation, separate consent, uncertain response and reload recovery. These are fixture-based implementation tests, not actual tenant evidence.

TypeScript, scoped ESLint and `git diff --check` passed. The token gate covers 35 governed files with no tracked token debt. Readiness and expanded-procedure screenshots were inspected at desktop and narrow widths; the runner workflow was rerun after the final screenshot assertions. These scoped checks do not constitute full-product design/accessibility certification or a production release.

## Guided batch capability increment — 8 September

Studio now captures a versioned batch contract through Inputs, Review changes, Local test and Outputs. Names, environment graph, runtime and delivery checklist derive from that contract. Reviewed saves create Working revisions and preserve other modules; release remains separate. The processor runs actual typed JSON rows and checks full/incremental loading, repeated batches and schema/type failures. It does not read CSV files, extract SQL Server data, write Delta, process CDF or execute Fabric items.

The existing Architecture view includes scoped batch candidates; Automation can export the released local runtime package. These are bounded additions, not full topology reconciliation, automatic commercial planning or end-to-end customer delivery. A first customer engagement is the possible next integration case, with exact tenant scope and data authorization still required. No tenant, customer Package, handbook or project ledger was changed by this increment.

Detailed scope, operator workflow, tests and recovery: [Guided batch capability](PROJECT_BATCH_INGESTION.md).
