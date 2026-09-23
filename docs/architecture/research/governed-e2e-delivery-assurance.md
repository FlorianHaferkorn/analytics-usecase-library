# Governed E2E delivery assurance

Status: implemented baseline  
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

## Tool adoption policy

| Horizon | Recommendation | Reason |
|---|---|---|
| Now | Keep the one Project Package, architecture-maintenance module, deterministic evaluator, ADR evidence, policy checks and observed-state reconciliation | These improve control without adding another operating platform |
| Next | Add scheduled authoritative-source review and Renovate-generated dependency pull requests with manual approval for breaking toolchain changes | Keeps dependencies and platform assumptions visible and current |
| When runtime lineage exists | Emit OpenLineage-compatible run, job and dataset events from deployed workloads | Static architecture alone cannot prove runtime lineage |
| At multi-team scale | Project the package into Backstage or another catalog for discovery, ownership and lifecycle navigation | Backstage is useful as a catalog view, not as the project decision source of truth |
| Only when policy volume warrants it | Compile stable cross-project rules to OPA or Conftest | A separate policy runtime is unnecessary overhead while the current closed-schema Python checks remain small and testable |

Installing every expert product would make a one-person delivery workflow less reliable. The framework therefore adopts proven patterns first and introduces a platform dependency only when its scale benefit exceeds its operational cost.
