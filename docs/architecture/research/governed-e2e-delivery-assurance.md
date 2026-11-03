# Governed E2E delivery assurance

Status: implemented baseline; AI-processing authorization, full-product and team acceptance pending
Scope: customer-neutral delivery framework; the first customer engagement is the first validation case, not a source of reusable customer data.

## Outcome

The delivery workflow is measured against a versioned reference model instead of being compared informally with individual products. The comparison adopts useful strengths while retaining one Project Package as the source of project intent and approval state.

The diagnostic weighted score helps prioritize improvements. It never overrides a mandatory gate. A project with 95% can still be blocked when, for example, production identities or ADR evidence are missing.

## Reference strengths adopted

| Reference | Strength adopted | Implementation in this repository |
|---|---|---|
| Backstage Software Templates | Structured intake, review before execution and reusable templates | Capability packs, adaptive questions and versioned Project Package review |
| Score and Humanitec | Environment-neutral intent resolved by target-specific implementations | Compiler input separated from Fabric and other target adapters |
| Microsoft Fabric CI/CD | Supported Git, deployment-pipeline, API, CLI and infrastructure automation paths | Explicit target delivery contracts and exception paths |
| ODCS and Data Contract CLI | Schema, quality, ownership and service-level expectations are testable | Data contracts, DQ controls, evidence requirements and negative tests |
| OpenLineage | Stable Run, Job and Dataset identities | Revision-bound observed-state and runtime evidence |
| Azure Well-Architected | Standardized workflows, observability, safe deployment and learning | Readiness gates, recovery evidence, product health and retained failure evidence |
| Fabric adoption roadmap | Ownership, least privilege and governance boundaries | Secret-free identity and access contract |
| Argo CD | Desired-versus-observed comparison, explicit self-heal and bounded retry semantics | Architecture-maintenance contract and environment-specific reconciliation policy |
| Renovate | Visible technology backlog with controlled approval rather than silent upgrades | Time-bounded authoritative-source review and explicit change policy per tool |
| Backstage Software Catalog | Owner, lifecycle and dependency metadata next to the governed asset | Accountable owners and current, target, transitional and retired lifecycle states |
| Open Policy Agent | Declarative policy evaluation over structured configuration | Closed schemas and deterministic policy checks; a dedicated OPA runtime is deferred until rule volume justifies it |

The machine-readable model is `core/reference_models/e2e_delivery_quality/model.yaml`. The deterministic evaluator is `tooling/superversion/project_package/delivery_quality.py`.

## Identity and access contract

Every project can record the following in the `identity_access` module:

- required human, service-principal, managed, workload and break-glass accounts;
- display-name pattern, purpose, accountable owner and environment scope;
- authentication method, secret-store reference and rotation interval without secret values;
- required security groups, owners and membership model;
- role assignment from a subject to an exact target and environment;
- assignment status, approver, exception decision and evidence;
- separation-of-duties rules, including independent production approval and execution.

Human access is group-based by default. A direct human assignment is accepted only as a documented exception linked to a decision. Applied or verified assignments require retained evidence. Automation uses non-personal identities.

The Fabric delivery-assurance capability pack asks for these identities, group-to-role mappings, credential lifecycle and approval separation as blocking discovery inputs. A package therefore cannot silently progress from a diagram to provisioning while those prerequisites are unknown.

## ADR and approval lifecycle

The Decision Set remains the only project decision authority. ADRs are projections of that authority, not separately edited documents.

1. A decision definition records context, options, recommendation, trade-offs, consequences, owner and due gate.
2. `Draft` and `Proposed` are not approvals.
3. A human selects an option and records the decision rationale.
4. Acceptance requires a decider, timestamp and evidence references.
5. The accepted decision is linked to affected architecture and delivery artifacts.
6. A later change creates a new revision and supersedes the earlier outcome; history is retained.

`tooling/superversion/project_package/adr.py` renders the ADR register and detailed ADRs from the Decision Set. The delivery quality gate fails when an active decision is unresolved or when an accepted ADR lacks evidence.

```powershell
python -m tooling.superversion.project_package.adr `
  --decision-set <project-package>\decisions\decision_set.yaml `
  --output <project-package>\generated\architecture-decision-register.md
```

## Readiness semantics

| Gate | Minimum interpretation |
|---|---|
| `build_ready` | Approved pinned package, resolved capability questions, machine-readable architecture and evidenced ADRs |
| `apply_ready` | Build-ready plus provisioned identities/groups, approved assignments, DQ/monitoring/recovery contracts and platform delivery contract |
| `acceptance_ready` | Apply-ready plus collected runtime evidence tied to the exact project revision and environment |

Generation, deployment and acceptance remain separate claims. A generated artifact does not prove tenant apply; a successful API call does not prove the data product; package approval does not prove runtime acceptance.

## Studio behavior

The Delivery workspace contains an **Assurance** section for the selected immutable project revision. It shows:

- the reference comparison and mandatory gate blockers;
- required accounts and groups;
- role assignments and separation rules;
- the ADR register with decider, time and evidence.
- architecture review ownership, drift policy, technology watch and current-to-target transitions.

All displayed states come from the selected Project Package or the deterministic assessment of that exact revision. The Studio does not substitute library examples for missing project evidence.

## Architecture maintenance lifecycle

Architecture is a maintained product record, not a one-time diagram. The `architecture_maintenance` module records:

- accountable owner, periodic review cadence and event-driven review triggers;
- environment-specific desired-versus-observed reconciliation, maximum observation age, remediation SLA and unmanaged-resource policy;
- authoritative product sources, last review, next review interval and change policy for each relevant technology;
- current and target bindings, rollback reference, transition state, retirement criteria and retained evidence.

The evaluator blocks apply readiness when a required environment has no current observed state, architecture review is overdue, a technology source has not been reviewed in time or the maintenance contract is inactive. A transitional path cannot be marked verified or retired without evidence.

The scheduled `Source Update Discovery` workflow runs `python -m tooling.quality.check_delivery_reference_sources`. It publishes the review status and fails when an authoritative reference passes its declared review interval, forcing a documented refresh instead of silently relying on stale tool assumptions.

This intentionally adopts the GitOps reconciliation pattern without assuming Kubernetes or installing Argo CD. The Project Package remains the desired state; platform readback remains observed state. Automatic deletion is not inferred from drift. The declared policy decides whether drift is reported, opens a controlled change or blocks release.

## Lessons converted from the first validation case

The first Fabric validation exposed gaps that are now customer-neutral blocking questions and evidence requirements:

| Reusable lesson | Enforced consequence |
|---|---|
| Workspace ownership and job, schedule or refresh ownership are different responsibilities | Every operated execution requires an explicit non-personal runtime identity and accountable owner |
| A successful job can still publish stale or invalid data | Product health combines orchestration, freshness, DQ and publication state; deliberate red-data tests exercise alerting |
| An alert configuration does not prove notification | The receiver must be supported and deliverable, and a failure-injection test must retain delivery and acknowledgement evidence |
| New platform resources may have delayed metadata visibility | Create-then-read paths use measured, bounded retries only for classified visibility delay; permanent errors stop immediately |
| A generated environment may still hide a manual seed dependency | Zero-to-running bootstrap, restart and second-apply no-op are explicit acceptance tests |
| A target architecture may coexist with compatibility writers and old bindings | Downstream rebinding, value reconciliation, negative security tests, report rendering, rollback and retirement approval are mandatory before removal |
| Tenant portal visibility is not access proof | Exact setting and security-group scope require API readback plus positive and negative identity probes |
| A Fabric schedule runs as the identity that last created or updated it, and a notebook inside a pipeline runs as the pipeline's last modifier, so one manual save moves execution back to a person | Every edit of an operated pipeline or schedule ends with an ownership readback; a controlled edit-and-correct test is part of apply readiness (`q_runtime_identity_drift`, `at_runtime_identity_drift`) |
| Ownership audits limited to production schedules miss semantic models and other stages still configured by a delivery user | The ownership audit covers schedules and semantic-model owners in every environment holding operated or tested artifacts |
| Reusing a provisioning identity as runtime identity is quick but merges two identity lanes | Reuse is allowed only as a recorded, time-bounded exception naming the replacement runtime identity (`ar_identity_lane_separation`) |
| Removing a delivery user's direct access is a separate change with lock-out risk | Group-based fallback access for the operator and a cross-environment dependency readback precede removal; the acceptance test proves runs continue afterwards (`at_personal_access_removal`) |
| Platform retention defaults are shorter than typical detection time (item recovery 3 days and workspace retention 7 days by default, Microsoft Learn, September 2026), and "backup" covers several failure classes with different recovery paths | Recovery targets per failure class, retention settings and a restore-plus-rebuild test are confirmed before handover (`q_recovery_targets_and_retention`, `at_restore_and_rebuild`) |
| A service principal without directory permissions cannot run every audit, and a check with fixed interpretation text reported an outdated state after the takeover | Checks record the executing identity, distinguish not run, not permitted and no finding, and derive their assessment from measured rows (`e_check_execution_record`, `ar_derived_assessment`) |
| One operational state change had to be carried into many customer documents and documentation pages by hand, while the package already sent to testers had to stay unchanged | Status-bearing statements are projected from the Project Package revision; delivered document sets are immutable and a changed state produces a new dated version |
| Writes to customer collaboration systems such as work-item boards and wikis may not be executable by an automated agent under the customer's or operator's controls | The delivery output for such systems is a reviewed change set with a named human executor, followed by a readback, instead of an implied automated write |
| The delivery toolchain was not complete at project start, and the final documentation home was agreed only near the end, so documentation lived in several places and had to be restructured into the wiki late | Repository, board, documentation home, deployment path and service connections are a discovery-ready prerequisite; anything missing gets a named interim location, owner and move date (`q_delivery_tooling_baseline`) |
| Work items were marked done while their child tasks were still open | Before each milestone the board is reconciled against the evidence register; done requires closed children and a linked evidence reference (`e_board_evidence_reconciliation`) |
| Branch policies and least-privilege service connections were still open when the first use case went into acceptance | Protected-branch policies and service-connection scope are proven with a positive and negative pull request before apply readiness, not added as later hardening (`q_change_governance`, `at_change_governance`) |

## Tool adoption policy

| Horizon | Recommendation | Reason |
|---|---|---|
| Now | Keep the one Project Package, architecture-maintenance module, deterministic evaluator, ADR evidence, policy checks and observed-state reconciliation | These improve control without adding another operating platform |
| Next | Add scheduled authoritative-source review and Renovate-generated dependency pull requests with manual approval for breaking toolchain changes | Keeps dependencies and platform assumptions visible and current |
| When runtime lineage exists | Emit OpenLineage-compatible run, job and dataset events from deployed workloads | Static architecture alone cannot prove runtime lineage |
| At multi-team scale | Project the package into Backstage or another catalog for discovery, ownership and lifecycle navigation | Backstage is useful as a catalog view, not as the project decision source of truth |
| Only when policy volume warrants it | Compile stable cross-project rules to OPA or Conftest | A separate policy runtime is unnecessary overhead while the current closed-schema Python checks remain small and testable |

Installing every expert product would make a one-person delivery workflow less reliable. The framework therefore adopts proven patterns first and introduces a platform dependency only when its scale benefit exceeds its operational cost.

## Completion contract: one-person and engagement-team operation

The same Studio and Project Package must serve a named solo operator **and** a Nagarro engagement team. Team operation is not a second compiler or a copy of the project in shared files. Each project retains one immutable revision history, one decision authority and one generated-output lineage. Private commercial inputs, customer evidence and tenant credentials stay in their respective access boundaries. A colleague must be able to continue work from the selected project revision without asking the original author to explain undocumented state.

The following are product acceptance gates, not estimates or a weighted maturity score. A gate is green only when its test and retained evidence exist. The diagnostic score above may help prioritize work but cannot waive a red gate.

| Gate | Required behavior | Acceptance evidence |
|---|---|---|
| Guided workflow | The project home names the current stage, owner, blocked decision, required evidence and next permitted action. Every active page has a delivery purpose; no hidden raw-YAML step is needed for supported scope. | A new colleague completes a neutral case from offer to handover using only Studio and the linked evidence; every transition can be explained from the UI. |
| Collaborative editing | Admin, editor and viewer permissions apply at every API and export boundary. Two editors cannot silently overwrite the same Package HEAD or Discovery draft. A conflict shows both revisions and a safe review path. | Concurrent-editor, stale-save, unauthorized-action and project-isolation tests at API and browser level; audit identifies the authenticated actor and exact revision. |
| Review and authority | A proposal, internal recommendation, customer decision, input release, tenant execution approval and acceptance are separate states. Team production policy requires an independently identifiable reviewer and executor; a solo exception must be explicit, scoped and auditable rather than inferred from one account. | Negative tests for self-approval under team policy, expired or changed approvals, absent evidence and role changes; signed release and execution records where applicable. |
| AI data protection | Every model-bound input has a known classification, permitted purpose, approved provider/region and allowed data form. Unknown, restricted or secret content never reaches a model; customer-confidential content requires an explicitly approved enterprise or local route. AI output remains a proposal. | Egress-denial tests for missing classification, disallowed provider/region, secrets and identifiers; retained preflight, redaction and output-scan evidence; tests that AI cannot set a decision, readiness, apply, publication or acceptance state. |
| Reproducible build | One approved revision deterministically produces architecture, ADRs, delivery plan, executable definitions and customer-facing documents. Unsupported target behavior fails closed with a named blocker. | Same-input output-hash regression on two clean machines plus official format/parser validation; no unreviewed customer-specific default appears in output. |
| Safe apply and recovery | Plans show exact project, tenant, principal, environment, changes and rollback/reconciliation path before any mutation. Apply is idempotent where the target supports it; an uncertain write is never automatically replayed. | Authorized non-production create/readback, second-run no-op, drift/conflict and interruption tests; production only after a separately approved release path. |
| Runtime acceptance | Data correctness, freshness, DQ, access denial/allowance, semantic/report results, alert delivery and ownership are proven against the deployed revision and environment. | Positive and negative probes with retained run IDs, principals, expected/actual results and an accountable acceptance record; generated files alone do not pass. |
| Visual and accessible interface | Shared typography, spacing, components and interaction rules hold across all workflow pages; charts remain readable at supported widths and keyboard/assistive-technology paths work. | Automated token, contrast, accessibility and responsive checks plus human desktop/mobile visual review of every supported state, including empty, loading, error and dense-data states. |
| Customer portability and maintenance | Scope determines questions, capability packs, outputs and gates without copying a previous customer's answers. Tool/version changes and architecture drift open a reviewed change, not a silent regeneration. | The first customer engagement as the first case **and** a second unrelated neutral case; source-watch, desired/observed diff, owner, review cadence and controlled upgrade/recovery tests. |

The implementation sequence follows the dependencies in these gates: establish a complete single-project proof, make collaboration and authority safe, complete target adapters and runtime verification, then demonstrate portability and continuous maintenance. Do not trade a red mandatory gate for a faster broad demo. Existing local checks remain labeled local; fixture simulations remain labeled simulated; tenant readback and customer approval require their own evidence.

**Shared-host topology remains UNKLAR.** Current project/org roles and SQLite records do not, by themselves, prove secure hosted multi-organization isolation or multi-host locking. A controlled single-host installation with explicit project access is a candidate for a team pilot, not an accepted customer-data hosting pattern until its isolation, backup and recovery tests pass. The protected runner now supports explicitly configured independent execution for selected environments, but existing host configurations can still allow one-person approval and execution; independent production review is not guaranteed until the team policy is configured and tested. A local one-person mode remains supported without inheriting org authority. The shared-host decision must cover backup/restore, key rotation, audit retention, cross-project leakage tests and disaster recovery before general team rollout.

## AI-processing contract: egress contained, approval workflow pending

Do not create another project authority or AI approval ledger. The ArchitectureBlueprint remains the customer-neutral platform contract; the Project Package binds customer scope and `use_case_delivery`; capability packs ask adaptive questions and supply rules; the protected runner remains the only apply boundary. The existing approved `ai_config` L0/L1/L2 layers determine model routing, provider allowlist, residency and telemetry redaction. They are necessary but insufficient for authorization to send customer content to a model.

The project Discovery chat and three projectless AI routes previously passed source text, messages, prompts or factsheet/bracket excerpts to a provider selected from those AI layers. Neither those routes nor the former `ai_config` contract established source classification, purpose limitation, provider training/logging terms, retention, permitted data form or a pre-egress secret/identifier scan. `use_case_delivery` records privacy/security controls but has no independently authorized AI-processing contract. The server now denies all five model-call branches before model resolution. Local factsheet drafting, deterministic reconciliation and a manual Wizard review path remain available. This is **containment, not completion of the AI data-protection gate**: the data-handling contract, exact-payload preflight and content-free audit evidence are implemented, while governed model use remains unavailable pending protected approval, provider/region readback, network enforcement and output control.

An optional, versioned `ai_data_handling` Project Package module now captures the proposed profile and allowed input classes per AI task, provider region and geography, credential reference, terms evidence and expiry. Its route ID must be in the referenced Decision Set instance's scope and ADR affected artifacts; an approved decision must bind the exact route-content hash, decider, date and evidence. Package validation rejects contradictory local/external boundaries and profile allowances. This is **design-time intake only**: editors can still submit complete package files, so the recorded approval is not an independently protected AI-egress authorization. An expired historical policy can remain a valid package record; current validity must be checked at request time. Capability-pack questions, protected approval, provider/region readback and output policy remain to be implemented.

The deterministic server-side preflight now scans the exact outbound candidate payload and refuses unknown/restricted/secret content or prohibited egress before model construction. It records policy version, payload digest, route, decision and findings without storing sensitive payloads in generic telemetry. Connecting this preflight to an independently protected project approval and selected provider route is still pending; until then the gate denies every model call. Customer-confidential content may use only a project-approved enterprise or local route. Output must also be scanned before it is displayed, stored or transferred. AI may draft candidates only and cannot write approval, readiness, apply, publication or acceptance states.

Model repeatable work as closed-schema operations with explicit preconditions, idempotency key, executor, evidence, readback, rollback/reconciliation and an optional AI role. Reuse the existing batch, release, runner, delivery-assurance, identity-access, ADR and architecture-maintenance contracts rather than introducing parallel status models. Customer material belongs only in private Customer Binding/Studio runtime or the customer repository; the product core and neutral fixtures remain synthetic. An operation is not automated merely because a model can describe it.

The contract is organization-neutral and must apply to both ALUCA (Nagarro) and Meridian (solo consulting) without merging their customer stores, commercial defaults or runtimes. Meridian's existing named-profile and local-residency gate is a reference for pre-adapter denial and shared negative fixtures, not a substitute for ALUCA payload authorization. Each product retains its own implementation and proves the same invariant with parity tests. Neither product may infer customer-content approval from provider availability or a residency label alone.

ALUCA now has its own `ai-data-handling-policy/1.0.0` schema and deterministic server-side evaluator. The neutral 14-case fixture is byte-identically mirrored from Meridian and SHA-256 pinned; local tests always check that pin, and a present Meridian checkout is compared for drift (`AI_CONTRACT_STRICT_PARITY=1` requires the checkout). The cases include mislabeled-local boundary attempts and profile waivers for provider training or external-cloud redaction. This evaluator is **not yet an egress permit**: project approval, provider/region readback and output control remain missing, so `requireApprovedAiEgress` still denies every model-bound Studio request.

The exact-payload gap is now closed for the currently denied routes without enabling AI egress. Immediately before model resolution, each route canonicalises and scans the complete candidate payload under `ai-egress-preflight/1.0.0`, then writes a content-free decision to the project's tamper-evident audit chain. Evidence contains the payload SHA-256, byte length, policy versions, decision, rule IDs and finding counts, never prompt text or matched values. Audit failure returns `AI_EGRESS_AUDIT_FAILED` and no provider is resolved. The nine neutral scanner cases are byte-identically mirrored and pinned against Meridian; allowlisting can suppress expected PII or identifiers but can never suppress a secret rule. Model calls remain blocked until a project-specific approved profile, provider/region readback and network egress control exist.

Intentional AUL tightening: an allowed evaluation requires an explicit complete profile policy (Meridian currently supplies conservative defaults when it is absent), and non-public external-cloud input always requires redaction even if a profile flag says otherwise. These differences do not change the shared fixture results; they are separate negative tests and must be reviewed before claiming full cross-product semantic equivalence.

The neutral evaluator can describe a customer-managed provider such as Azure OpenAI, but the current AUL model router only constructs Anthropic, Google and OpenAI adapters. Fixture allowance therefore does not imply that a matching AUL route exists or that a customer's boundary evidence has been verified.
