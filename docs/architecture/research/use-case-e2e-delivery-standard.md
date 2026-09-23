# Use-case end-to-end delivery standard

**Status:** Implemented contract and deterministic Markdown projection  
**Version:** 2.0.0  
**Scope:** Customer-project delivery instances; not reusable business factsheets

## Decision

Every customer use case that enters technical delivery gets one project-specific `use_case_delivery` module. The module is the machine-readable source for source boundaries, data products, transformations, orchestration, controls, acceptance and unresolved gates. The customer-facing *Use Case and Data Architecture Specification* is generated from it.

This complements rather than replaces the Golden Thread:

- `Business_Factsheet.md` defines the reusable business story.
- `UseCase_Bracket.yaml` references governed KPIs, actions and UX rules.
- governed data contracts define reusable domain entities and facts.
- the project `use_case_delivery` module instantiates the physical source-to-report delivery for one customer and use case.
- generated Markdown/DOCX is a projection, never the decision authority.

## Why a separate project module

The first customer use case exposed a recurring gap: a report definition, a source inventory and an architecture diagram can all exist while the delivery chain remains incomplete. A buildable use case also needs explicit source exclusions and fallbacks, layer transformations, runtime ordering, failure behaviour, release/security/quality controls and numerical acceptance evidence.

Putting these fields into the reusable use-case bracket would mix customer-specific source names, environment choices and evidence with cross-customer business logic. Keeping them only in prose would make completeness, drift and readiness impossible to validate. The Project Package is therefore the correct lifecycle boundary.

## Required content

Each use-case entry records:

1. identity, domain, delivery state, business-scope reference and decision references;
2. reference reports, operating modes and measured metadata where available;
3. logical gateway, connection, workspace and target dependencies when the platform path is known;
4. canonical, fallback and explicitly excluded source objects, each wired to its logical connection;
5. Bronze, Silver, Gold, semantic and report products with grain, business keys, history and logical target;
6. analytical-model design with reuse boundary, a referenced PK/SK/FK contract, relationship and bridge assessments, fact-filter strategy, double-counting control and glossary references;
7. every source-to-report transformation with implementation and quality rules;
8. ordered orchestration, success conditions and failure actions;
9. delivery assurance covering measured source behavior, incremental and delete semantics, executable DQ rules, product-health signals, alert routes, classified retries, idempotency, bootstrap and rollback;
10. security, privacy, data-quality, release, operations, performance and cost controls;
11. frozen-snapshot and regression acceptance requirements with environment-qualified runtime proof references; and
12. every remaining gate with owner, due point and the lifecycle stage it blocks.

Evidence states are fixed: `confirmed`, `measured`, `derived`, `proposed`, `open`, `not_applicable`. Confirmed and measured claims require at least one evidence reference. A delivery state cannot move past an unresolved gate that blocks that state.

The platform block is optional for older packages. Once present, validation is strict: every logical ID is unique across all four resource kinds; connection-to-gateway and target-to-workspace references resolve to the correct kind; every non-excluded source and every data product is wired; and the use-case dependency list contains exactly that transitive closure. This keeps physical tenant IDs in `observed_state.resources` while the delivery contract uses stable logical IDs.

`observed_state.operational_evidence` is also optional and closed. It separates connection tests, network-path tests and use-case runtime tests. Each proof records its logical references, outcome, timestamp and evidence state. Completed connection and runtime tests also identify the tested principal. A passed or failed test must be confirmed or measured and timestamped; `not_run` cannot carry accepted evidence.

Confirmed or measured acceptance requires environment-qualified runtime proof references. Package validation resolves them against collected observed-state modules and requires passed runtime, connection and—where a gateway is declared—network evidence. The accepted runtime proofs must cover every canonical connection and every target, including corresponding observed resources. A proposed proof remains useful planning information but cannot satisfy acceptance or a `verified` delivery state.

`delivery_assurance` is the project answer to the customer-neutral
`fabric_data_delivery_assurance` capability pack. It becomes mandatory at
`design_ready`. `build_ready` additionally requires a selected incremental and delete
strategy, at least one blocking DQ rule, job/DQ/freshness/capacity signals and a
classified retry policy. Authentication, schema and DQ defects never retry blindly;
an unknown mutation outcome must be read back before another write. `verified` requires
confirmed or measured evidence for every assurance component. This prevents a diagram,
a successful job status or the presence of generated files from becoming a false-green
delivery claim.

## Standard human document

The deterministic renderer emits the same eleven-section structure for every use case:

1. Purpose and evidence rules
2. Decision and report scope
3. Source boundary
4. Target data products
5. Analytical model design
6. Transformation design
7. Orchestration and operations
8. Delivery assurance
9. Security, quality, release and operational controls
10. Acceptance and regression
11. Open gates

## Mandatory analytical-design review

The review starts during discovery; unknown answers stay `open` and become gates rather than guesses. Apply the following sequence to every relationship that could change aggregation or filtering:

1. Fix the business grain and candidate uniqueness fields before selecting tables.
2. Confirm whether the relationship is single-valued or multi-valued at that grain.
3. Confirm whether it changes over time and whether it carries a percentage, weight or other allocation attribute.
4. If it is single-valued at the fact grain, place the foreign key on the fact and do not create a bridge.
5. If it is genuinely multi-valued, retain a bridge only for navigation or membership analysis. If it must filter additive facts, define an explicit physical scope/allocation fact or governed measure logic and prove totals against double counting.
6. Record PK, dimension surrogate keys, fact-grain uniqueness and every FK in the referenced key contract. Fact surrogate keys are not required by default.
7. Test key uniqueness, nulls, referential integrity, effective-date overlap, filter propagation and totals on representative data before design approval.

Bidirectional or many-to-many semantic relationships are not a default substitute for a missing physical filter/allocation contract.

## Glossary separation

Three linked artifacts have different authority and must not redefine one another:

- the **business metric catalog** owns KPI name, purpose, definition, business formula, grain, unit, time behaviour, filters/exclusions, owner, validation and version;
- the **measure dictionary** owns the semantic implementation and references the KPI ID; and
- the **technical data dictionary/key contract** owns tables, columns, data types, grain, PK/SK/FK, nullability, lineage and quality rules.

Reusable KPIs reference `core/kpi_catalog/`. Customer-specific KPIs stay in the project package until they are sanitised and deliberately promoted. Legacy report formulas may seed a `derived` draft, but they are not business approval.

Customer branding, wording refinement and DOCX rendering may be applied after generation. They must not alter status, evidence or open-gate meaning without updating the module and its governing decision record first.

## Implementation

| Asset | Purpose |
|---|---|
| `tooling/generator/schemas/project_use_case_delivery.schema.json` | Closed JSON Schema for the module |
| `core/capabilities/fabric-data-delivery-assurance/capability.yaml` | Adaptive questions, decision options, evidence, work packages and acceptance tests for source behavior, DQ, monitoring and reliability |
| `tooling/generator/schemas/project_observed_state.schema.json` | Closed physical-resource and operational-evidence schema |
| `tooling/superversion/project_package/use_case_delivery.py` | Semantic validation and deterministic Markdown rendering |
| `core/fixtures/neutral/use-case-delivery-spec/use_case_delivery.yaml` | Customer-neutral working example |
| `core/fixtures/neutral/use-case-delivery-spec/observed_state.dev.json` | Customer-neutral connection, network and runtime proof example |
| `tooling/tests/test_use_case_delivery.py`, `tooling/tests/test_project_package.py` | Schema, renderer, reference, evidence and readiness tests |

Validate and render a project module:

```powershell
py -3 -m tooling.superversion.project_package.use_case_delivery `
  --input <project>\delivery\use_case_delivery.yaml `
  --schema tooling\generator\schemas\project_use_case_delivery.schema.json `
  --output-dir <project>\generated\use-cases
```

Validation only:

```powershell
py -3 -m tooling.superversion.project_package.use_case_delivery `
  --input <project>\delivery\use_case_delivery.yaml `
  --schema tooling\generator\schemas\project_use_case_delivery.schema.json `
  --validate-only
```

The module can be registered in `package.yaml` with `module_type: use_case_delivery`. Package validation checks its schema and hash; the compiler input carries it forward for architecture, document and test projections.

## Adoption rule

New customer use cases use this contract from the start. Existing use cases are migrated when they next enter active delivery or undergo a material architecture change. Migration must preserve evidence classification and open gates; it must not convert legacy prose into confirmed decisions without attributable proof.

That first use case is the measured reference implementation, but no customer names, source objects or values are part of the reusable fixture or framework defaults.
