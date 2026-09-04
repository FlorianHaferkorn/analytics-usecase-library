# Discovery-to-Deployment Workbench

> **Status:** Proposed product extension, not an accepted architecture decision.
> **Date:** 2026-09-01.
> **Scope:** Customer-independent operating model for converting a selected consulting
> scope into governed decisions, architecture, deliverables, deployment plans and
> post-deployment evidence.
>
> This plan extends the existing Studio, Superversion and ArchitectureBlueprint path.
> It does not create a second compiler, question ledger, approval workflow or source of
> truth.

## 1. Outcome

Build one reusable workbench that turns customer input into a verified delivery chain:

```text
Scope profile
  -> required discovery and evidence
  -> decision-ready workshops
  -> approved project model
  -> interactive architecture and documents
  -> deterministic deployment manifest
  -> plan, approval, apply and verification
  -> tenant readback, drift report and reusable learning
```

The same approved model must drive every representation. An answer entered in the
Studio may propose a change; it may not silently mutate architecture, generated files
or a target tenant.

## 2. Product boundary and authoritative path

The Studio is the guided editor and visual projection. It is not an independent source
of truth and it must not reimplement derivation logic in TypeScript.

The authoritative path is:

```text
Studio input
  -> versioned project package
  -> governed Python core / Superversion
  -> ArchitectureBlueprint and canonical model
  -> target adapters, documents, gates and deployment manifests
```

Existing assets to extend rather than duplicate:

| Need | Existing authority to reuse |
|---|---|
| Missing inputs and answer paths | `tooling/superversion/open_questions.py` |
| Customer-facing approvals | Studio approval lifecycle and audit trail |
| Stack-neutral target model | `tooling/generator/schemas/architecture_blueprint.schema.json` |
| Architecture derivation | `tooling/superversion/architecture_blueprint.py` |
| Data-governance strategy | `tooling/superversion/governance_concepts.py` |
| Data contracts | `tooling/superversion/odcs.py` and `core/data_contracts/` |
| Gov/eng/arch checks | `tooling/superversion/layer_tools/engines/` |
| Tool-specific checks | `tooling/superversion/layer_tools/packs/` |
| Target generation | Superversion target registries and adapters |
| Studio-to-core seam | `tooling/superversion/bridge.py` |

The workbench adds a project-scoping and decision layer around these components. It
does not change their Golden Thread ownership.

### Organization boundary

This repository implements the workbench as a **Nagarro consulting product**. The
Studio is its only operator interface and supports named roles, staffing assignments,
commercial hand-off and several delivery streams through an explicit resource plan.
Nagarro rates and margins are project-specific commercial inputs; they are not
framework defaults and must not be copied into customer packages.

Freelancing is a separate one-person consulting product. It may implement the same
versioned `consulting-operating-profile/1.0.0` exchange semantics, but it does not share
this runtime, brand, price book or customer fixtures. This avoids both hidden product
coupling and leakage of Nagarro customer context.

HTF is the first governed Nagarro customer case. Its Ledger remains authoritative for
customer decisions, and HTF-specific facts stay in the customer repository or a
reviewed sanitized showcase fixture. They never become generic ALUCA defaults.

## 3. Scope profile: select only what the engagement needs

Every engagement begins with a versioned scope profile. Each capability can be set to
`not_in_scope`, `assess`, `design`, `implement` or `operate`. The selected level drives
the required inputs, workshops, decisions, deliverables, implementation tasks and
acceptance gates.

| Capability | Typical discovery | Deterministic outputs when selected |
|---|---|---|
| Strategy and value | objectives, sponsors, decisions, KPI ownership | strategy anchors, use-case pack, value hypothesis, outcome measures |
| Data governance | ownership, glossary, classification, contracts, quality, lineage, retention, access policies | governance profile, RACI, terms, ODCS contracts, DQ and policy controls |
| Data architecture | domains, products, layers, sharing, topology, non-functional requirements | ArchitectureBlueprint, domain and environment topology, decision records |
| Data engineering | sources, connectivity, volume, latency, change capture, transformation and recovery | ingestion and transformation plan, contracts, orchestration and test plan |
| Semantic and analytics | grains, measures, relationships, security, user journeys and reports | canonical model, semantic targets, reports, security and acceptance tests |
| Delivery and CI/CD | repositories, environments, approvals, identities, bindings and rollback | release manifest, environment bindings, pipelines and rollback plan |
| Operations | ownership, SLOs, monitoring, incident response, cost and capacity | observability controls, runbook, evidence plan and operating model |
| AI and grounding | approved products, retrieval boundary, safety and evaluation | governed grounding manifest, access restrictions and evaluation gates |

### Data-governance profiles

Data governance is a selectable capability, not a mandatory full-suite programme. The
existing governance concepts remain composable:

| Profile | Use when | Minimum outputs |
|---|---|---|
| Contract-first | Delivery needs explicit producer/consumer interfaces | ODCS contract, owner, quality rules, change policy |
| Data-product / Purview | Products, discoverability, lineage and stewardship are primary | product registration, glossary links, classification and ownership |
| Glossary-first | Terms and KPI meaning are inconsistent across teams | approved terms, owners, mappings and semantic references |
| DQ-first | Trust and operational data defects block adoption | critical data elements, DQ rules, thresholds, exception and remediation flow |
| Composed | Several governance outcomes are required | combined profile with conflicts surfaced for human decision |

Selecting `assess` produces findings and a roadmap. Selecting `design` additionally
produces approved policies and contracts. `implement` adds platform-specific controls
and verification. `operate` also requires ownership, cadence, SLOs and response
evidence.

## 4. Guided discovery and decision model

Discovery is driven by dependencies and evidence, not by a fixed questionnaire. A
question is shown only when the scope profile and prior answers make it applicable.

Each decision record needs at least:

```yaml
id: environment_topology
status: ready_for_decision
question: Which lifecycle must the delivery support?
dependencies: [release_owner, test_data_route]
decider_role: platform_owner
due_date: 2026-10-01
options: [dev_prod, dev_test_prod]
recommendation: dev_test_prod
selected_option: null
rationale: null
evidence_refs: []
impact_dimensions: [cost, delivery, operations, architecture]
architecture_refs: []
document_refs: []
revision: 1
```

Decision lifecycle:

```text
Draft answer
  -> Proposed
  -> Evidence complete
  -> Ready for decision
  -> Approved
  -> Recorded in the project source of truth
  -> Compiled
  -> Applied
  -> Verified
  -> Superseded
```

Answers, recommendations and defaults are not approvals. A decision is only buildable
after the named decider has approved it and required evidence is attached.

## 5. Workshop and evidence orchestration

The workbench groups unresolved decisions by dependency and decider. It generates only
the workshops needed for the selected scope.

| Workshop module | Expected decisions | Typical participants |
|---|---|---|
| Objectives and operating model | outcomes, sponsor, domain and ownership boundary | sponsor, domain lead, programme lead |
| Governance and accountability | product ownership, stewardship, contracts, quality and policy | data owner, steward, governance lead, security |
| Platform and architecture | topology, environments, capacities, sharing and non-functional requirements | architect, platform owner, security, operations |
| Sources and engineering | source contracts, connectivity, incremental strategy, transformation and recovery | source owner, data engineer, network/platform owner |
| Security and self-service | identities, role boundaries, data security and delegation | security, domain owner, platform owner |
| Semantic and consumption | model boundary, KPIs, reports, audience and acceptance | business owner, BI lead, report consumers |
| Delivery and operations | Git, promotion, bindings, monitoring, support and rollback | DevOps, operations, platform owner |
| Final readiness | residual risks, manifest approval and release decision | sponsor, accountable owners, delivery lead |

For each workshop the workbench generates an agenda, pre-read, required evidence,
decision owners, options with trade-offs, architecture before/after and follow-up tasks.
Status is explicit: `complete`, `ready`, `needs_input`, `blocked` or `deferred`.

## 6. Customer experience in Studio

Three views expose the same state:

| View | Primary content |
|---|---|
| Sponsor | what must be decided, recommendation, benefits, risks, effort and later-change cost |
| Workshop | one active question, evidence, options, live impact and progress |
| Technical | artifacts, names, contracts, identities, bindings, controls, limitations and tests |

The workshop view should use a split layout: decision on the left, affected architecture
on the right. Selecting an option highlights only the changed nodes, edges, roles,
contracts and documents. The user can compare the proposal with both the confirmed
baseline and the session start state.

Required product components:

- session bar with scope, baseline version and decision-set hash;
- adaptive agenda rail;
- decision card with recommendation, alternatives and evidence;
- architecture impact canvas with before/after diff;
- evidence drawer and conflict warnings;
- confirmation tray with named decider;
- export centre with a manifest of generated outputs.

The first implementation can store and import a project package locally. Shared
customer operation requires authenticated, auditable server-side state; browser local
storage is insufficient as the authoritative store.

## 7. Canonical project package

The implementation should converge on a schema-versioned package, not one monolithic
unvalidated JSON file:

```text
project/
  package.yaml
  scope/profile.yaml
  context/context.yaml
  discovery/questions.yaml
  discovery/decisions.yaml
  discovery/requirements.yaml
  evidence/index.yaml
  architecture/model.yaml
  architecture/policies.yaml
  architecture/contracts/
  environments/dev.yaml
  environments/test.yaml
  environments/prod.yaml
  observed/dev.json
  observed/test.json
  observed/prod.json
  runs/
  generated/
```

Stable keys identify logical resources. Display and physical names are derived fields,
not identifiers. The same naming-policy change can therefore regenerate names without
breaking relationships or decision references.

Secrets never enter the package or customer-side HTML. Store references to an approved
secret provider and bind the secret only in the target environment.

## 8. Deterministic compiler and projections

One approved package revision compiles into:

- interactive architecture;
- sponsor decision pack;
- technical architecture and handover documentation;
- naming workbook and data contracts;
- roles and permissions matrix;
- ArchitectureBlueprint and stack-specific plans;
- environment-specific deployment manifests;
- tests, acceptance criteria and evidence requirements.

Every output records the package version, decision-set hash, compiler version and
generation timestamp. Generated outputs are read-only projections and must never become
decision authorities.

LLMs may extract candidate facts, propose follow-up questions and explain trade-offs.
They must not sit on the deterministic compile, approval, apply or verification path.

## 9. Readiness gates and delivery loop

The compiler calculates gates; users cannot manually set them green.

| Gate | Minimum condition |
|---|---|
| Discovery ready | required inputs identified; source and owner known |
| Decision ready | applicable options, evidence and named decider present |
| Visual ready | no unresolved references; architecture projection renders |
| Build ready | required decisions approved; contracts and identities complete |
| Apply ready | environment bindings, tool support, plan, rollback and approval complete |
| Acceptance ready | expected tests, owners and evidence capture defined |
| Verified | target readback and tests match the approved desired state |

Execution path:

```text
collect -> decide -> compile -> plan -> approve
  -> apply DEV -> verify -> promote TEST -> accept
  -> promote PROD -> verify -> read back -> report drift
```

An apply is blocked by unresolved placeholders, missing identities or bindings, raw
secrets, unsupported provider actions, absent rollback, destructive actions without
approval or missing positive and negative security tests.

## 10. Deployment provider boundary

The compiler produces an ordered desired-state manifest. Providers implement only the
resource types and operations they can prove.

| Concern | Preferred execution path |
|---|---|
| Cloud/platform infrastructure | platform IaC provider or official cloud CLI |
| Workspace and supported item control plane | official platform CLI/API adapter |
| Versioned definitions | Git-connected development workspace and promotion pipeline |
| Environment-specific connections, roles and schedules | explicit binding adapter or documented controlled step |
| Schemas, tables, transformations and data-quality controls | SQL, orchestrated jobs and notebooks as appropriate |
| Verification | official read APIs, runtime tests and normalized desired-vs-observed diff |

Preview or partially supported providers may assist discovery or generate a plan, but
they may not be represented as a proven deployment path. The provider capability matrix
must be versioned and tested.

## 11. One-day tenant implementation: the honest prerequisite

One-day implementation is a deployment objective, not a discovery shortcut. It is
credible only when the project passed `apply_ready` before the delivery day.

Target run:

| Time | Activity |
|---|---|
| 08:00 | preflight, tenant readback and reviewed manifest diff |
| 09:00 | approval and platform apply |
| 11:00 | development definitions, bindings and identities |
| 12:30 | representative end-to-end and security tests |
| 14:00 | test promotion and acceptance |
| 16:00 | production promotion and smoke tests |
| 17:00 | readback, drift scan, evidence bundle and rollback checkpoint |

Unresolved source access, contracts, security decisions or target limitations make this
a no-go. The workbench must state that explicitly rather than compressing those tasks
into the deployment day.

## 12. Consolidation and productization loop

After each engagement:

1. collect only dated evidence, accepted decisions, delivery metrics, defects and
   verified tenant behavior;
2. separate reusable patterns from customer-specific facts and names;
3. compare findings with existing questions, rules, schemas, adapters and tests;
4. propose changes through review; never teach the framework from an unverified note;
5. add or revise reference profiles, impact rules, provider capabilities and test
   fixtures;
6. replay at least one previous project package and prove that intentional changes are
   explainable;
7. release a versioned framework increment with migration notes.

The resulting learning may extend Data Governance, Data Architecture, Data Engineering,
semantic/analytics or operations independently. It must not force every future customer
to buy or execute the full scope.

## 13. Build increments

### Increment 0: engagement retrospective and contract freeze

- consolidate verified findings from the next completed engagement;
- inventory current Studio, Blueprint, open-question, governance and deployment paths;
- define package ownership, stable IDs, state machine and evidence semantics;
- remove or mark stale duplicate inputs and generators.

**Done when:** one documented authority exists for every field and no generated output is
treated as a decision source.

### Increment 1: guided scope and discovery

- scope-profile editor with Data Governance as a selectable capability;
- adaptive question and dependency engine;
- sponsor, workshop and technical views;
- decision/evidence lifecycle and live architecture diff.

**Done when:** a facilitator can derive only the required workshops, inputs and decisions
for two materially different scope profiles.

### Increment 2: project package and deterministic exports

- schemas and migrations for the canonical package;
- deterministic compiler into Blueprint, architecture, PDF, workbook and decision pack;
- visual, build and apply readiness reports;
- output manifest and package/decision hashes.

**Done when:** identical approved input produces byte-stable normalized output and one
decision change affects only traced projections.

### Increment 3: provider adapters and verified delivery

- provider capability registry;
- dry-run, idempotency, rollback and environment binding contracts;
- DEV/TEST/PROD apply orchestration;
- target readback, normalized drift and evidence bundle.

**Done when:** first apply creates the expected resources, second apply is a no-op and
negative security tests are retained as evidence.

### Increment 4: reusable engagement profiles

- package reusable discovery, governance and delivery profiles;
- generate agendas, pre-reads, RACI, decisions, plans and acceptance packs;
- measure lead time, rework, decision latency, gate failures and automation coverage.

**Done when:** a new engagement can be initialized from a profile without copying a
previous customer's data, decisions or names.

## 14. Definition of Done

The workbench is product-ready only when:

- one approved input changes the canonical package once and all projections follow;
- scope selection deterministically controls questions, meetings, artifacts and gates;
- Data Governance can be independently assessed, designed, implemented or operated;
- recommendations expose evidence, alternatives, limitations and impact;
- all generated artifacts trace to decisions and package revision;
- apply is dry-runnable, approved, idempotent and reversible;
- desired state is compared with observed tenant state;
- security includes positive and negative tests;
- no customer names, secrets or unsupported claims enter reusable framework defaults;
- a second team can execute the documented flow without the original builder.
