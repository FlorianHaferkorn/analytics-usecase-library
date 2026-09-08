# Studio end-to-end delivery integration

**Date:** 2026-09-07  
**Status:** Implemented incremental integration; not whole-product completion.  
**Scope:** Customer-independent Nagarro consulting workbench. No customer authority was migrated or approved by this work.

## Context and decision

The product plan has always included architecture and delivery. Studio is the single operator interface; the immutable Project Package owns project content, and the Python core derives validated outputs. The previous navigation emphasized the KPI Golden Thread and library tools, making that broader purpose difficult to see.

Expose **Delivery workspace** (`/engagement`) and **Architecture** (`/architecture`) as explicit project tools. Keep the reusable Library and Golden Thread tools available without presenting their content as project evidence. Entering an explicit project surface carries project intent into subsequent Generate and assurance links.

## Workflow and implementation boundary

| Stage | Current interface and source | Current behavior | Not yet implemented |
| --- | --- | --- | --- |
| Scope and offer | Delivery workspace; opportunity and commercial modules; Automation / Cost & staffing | Recorded scope plus private, explicit-rate Decimal calculations, contingency, named-resource capacity, overload warnings and same-version scenario download/restore | Persistent commercial authority integration, guided offer authoring and commercial approval workflow; scenarios are not offers |
| Discovery | Discover; saved project draft | Source collection, extraction, explicit review and source quotes | General reliable extraction across every requirement/capability |
| Reviewed model update | Review for Project Package | Selected strategy anchors become draft objectives with before/after review; exact evidence is versioned; Package returns to Working | Verified KPI/action registry mapping and arbitrary architecture-field inference |
| Decisions and plan | Delivery workspace, Approvals and Project Package | Recorded alternatives, owners, decision gates, work, effort provenance and role requirements | Automatic workshops, scheduling, named staffing and option-to-topology derivation |
| Architecture | Architecture; Python projection of architecture_input and use_case_delivery | Recorded sources, products, transformations, explicit workspaces and native item ownership/dependencies; adaptive graph layout and filters | Semantic relationship diagrams, automatic environment cloning and approved option-to-topology derivation |
| Build and release | Generate input release, then Automation / Workflow & gates | Existing attestation required; selected deterministic architecture, workspace and native item request outputs; atomic hash-verified run records | Lakehouse and other item adapters, security/CI-CD adapters, physical-ID rebinding and complete target execution |
| Verify and operate | Automation / Deployment preflight; Health and Drift | Workspace planning and authoritative reconciliation from explicit observations; create-only Python executor with plan-bound approval, receipt and readback tests | Trusted live identity/approval runner integration, Studio apply endpoint, complete runtime acceptance and automated operations |

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

1. Integrate an authenticated, least-privileged execution identity and protected, expiring apply approvals into the Studio host. Prove create, rerun, interrupted run and readback in an explicitly authorized non-production tenant.
2. Extend execution from workspaces to fully validated item definitions, physical-ID resolution and bindings. Include Lakehouse/table provisioning, source connections, security, Git and stage promotion; every unsupported family must remain blocked.
3. Wire approved decision outcomes to explicit architecture fields through tested derivation rules. Do not turn a recommendation or an imported comment into a customer decision.
4. Connect commercial authority and staffing availability, implement dependency-aware planning and generated offer/delivery documents without leaking private rates into customer exports.
5. Prove one complete approved project from reviewed evidence through deployment, data/security tests, acceptance and drift detection before claiming end-to-end automation. Framework completeness across arbitrary tools and requirements is not established by this implementation.

References: [Product workbench plan](../../../docs/architecture/research/discovery-to-deployment-workbench.md), [Project authority](PROJECT_AUTHORITY_AND_VIEWS.md), [Discovery transfer](DISCOVERY_PACKAGE_TRANSFER.md), [Architecture compilation](PROJECT_ARCHITECTURE_COMPILATION.md), [Input release](PROJECT_INPUT_RELEASE.md).
