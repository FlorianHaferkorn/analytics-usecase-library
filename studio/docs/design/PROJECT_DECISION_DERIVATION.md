# Reviewed decision-to-architecture and plan derivation

Status: implemented as a bounded local package workflow. No tenant execution or implicit approval.

## Purpose and design decision

Architecture and delivery planning must reflect approved choices without treating a recommendation, AI interpretation or default as approval. An optional `architecture_input.decision_rules` list records explicit, human-authored mappings. The Studio previews all consequences together and creates a new working package after review.

The rule engine replaces existing fields by stable entity identity. It is not a generic JSON Patch engine and does not infer meaning from decision prose. This reduces flexibility in exchange for a reviewable authority boundary: renaming an item, changing a capacity or selecting environment lanes cannot silently rewrite decision evidence or execute code.

## Workflow

1. Author a rule in the versioned architecture input, referencing an exact decision instance, its revision and one declared option.
2. Record the decision through the existing decision process. A rule needs `approval.state: approved`, `selection.state: confirmed`, a decider and rationale, and no custom selection value.
3. Preview the current package HEAD. The review shows the existing value, proposed value, reason, decision reference and any blocker.
4. Confirm the exact preview hash and provide a review rationale. The authenticated Studio actor is supplied by the server, not trusted from browser input.
5. Commit architecture and declared plan changes atomically in a new immutable `working` revision. Other modules, source evidence, decisions and previous snapshots remain unchanged.
6. Review and approve the resulting package through the existing process, then obtain a new input-release attestation. The old release does not authorize the new architecture.

## Example

```yaml
decision_rules:
  - id: environment_lanes
    decision_ref: decision_environment_model
    decision_revision: 1
    option_ref: three
    target:
      collection: environments
      entity_id: null
      field: recommended
    expected_value: [dev, prod]
    value: [dev, test, prod]
    rationale: Show the three explicitly approved isolation stages in the architecture.
    plan_effects:
      - target: {collection: plan_work_packages, entity_id: wp_environment, field: role_refs}
        expected_value: [fabric_engineer]
        value: [fabric_engineer, test_lead]
      - target: {collection: plan_work_packages, entity_id: wp_environment, field: effort}
        expected_value: {value: 2, unit: person_days, provenance: assumption}
        value: {value: 3, unit: person_days, provenance: assumption}
      - target: {collection: plan_tasks, entity_id: task_environment_acceptance, field: definition_of_done}
        expected_value: [DEV and PROD validated]
        value: [DEV, TEST and PROD validated]
```

This synthetic example updates the declared environment list, role demand, an explicitly authored effort assumption and a task acceptance criterion. It does not assign a person, price the work, invent TEST workspace names, capacity identifiers, native definitions, deployment bindings or access grants. Those remain separate contracts and gates. Every selected stage must already have an explicitly authored workspace for each detailed domain before this rule can be applied or the package released; this is a topology-presence check, not native deployment proof.

## Supported targets

| Collection | Stable identity | Replaceable fields |
|---|---|---|
| `environments` | `entity_id: null` | `recommended`, `accepted` |
| `domains` | Existing `id` | `capacity`, `delivery_scope` |
| `use_cases` | Existing `id` | `name`, `architecture_detail` |
| `physical_workspaces` | Existing `id` | `name`, `description`, `capacity_id`, `domain_id` |
| `physical_items` | Existing `id` | `name`, `description` |
| `plan_work_packages` | Existing `id` | `role_refs`, `effort` |
| `plan_tasks` | Existing `id` | `definition_of_done` |

The field must already exist. Plan effects must appear in the same rule's `plan_effects`, reference existing plan elements carrying the same decision reference, and acceptance tasks must belong to an impacted work package. An environment-stage rule requires explicit role demand, effort with provenance, a nonempty task acceptance criterion and authored workspaces for each selected stage in every detailed domain. A changed acceptance criterion cannot be applied to a task marked `done` or carrying old evidence; a human must review and reopen it separately. The environment mapping must reference its declared environment decision; physical-element mappings must appear in that element's `decision_refs`. A scoped decision can affect only its explicitly scoped architecture entity; root-level environment rules require a project-wide decision. Rules never change IDs, decision references, native code, compiler policy, approvals or KPI meaning.

## Review outcomes and failure behavior

| Status | Meaning |
|---|---|
| `ready` | The exact approved selection applies and the expected current value matches. |
| `pending` | Approval or confirmed selection is missing; no change is proposed. |
| `not_selected` | Another declared option was approved; this rule is not applied. |
| `unchanged` | Architecture and all declared plan effects already contain their target values; no repeated commit. |
| `blocked` | Identity, scope, option, revision, precondition or conflicting rule prevents application. |

All applicable changes are reviewed and committed together. Any blocker or invalid resulting architecture or plan schema prevents application. Changed HEAD or preview hash also prevents application. A concurrent edit is checked again during the repository's locked commit. The original snapshot is recoverable through immutable history; rollback is a newly reviewed revision, not destructive history rewriting.

Input release independently re-evaluates all recorded rules under the repository lock. Only `unchanged` and `not_selected` rules permit release. Ready but unapplied changes, pending confirmation and blocked mappings prevent both a new attestation and reuse of a previously recorded attestation. This prevents generated outputs from preserving architecture or plan fields that contradict approved decision mappings. Packages without decision rules retain their existing compiler input and release behavior. An environment-stage rule without the three required plan effects blocks release, including if an older approval record exists.

Architecture outputs contain `delivery/decision-impact-checks.json` when an applied rule has plan effects. It names the decision/revision, target fields and hashes of their selected values. The output manifest carries the rule IDs and file hash. These checks assert only the released Project Package contract; they are not tenant tests, customer acceptance, named staffing or cost approval.

Each committed review adds `architecture/derivations/<preview_sha256>.json` to the same immutable snapshot. It records before/after values, decision hashes, reviewer, time and rationale. The hash provides content integrity, not an independent digital signature against an administrator controlling the host.

## CLI integration

```text
py -3 -m tooling.superversion.project_package.decision_derivation
  --repository <trusted repository path>
  --schemas <trusted schema path>
  --mode preview|apply
```

JSON stdin for preview: `{project_ref, revision_hash}`.

JSON stdin for apply: `{project_ref, revision_hash, preview_sha256, actor, rationale, confirm_apply: true}`.

Success stdout: `{ok: true, value: ...}`. Errors return `{ok: false, error, status: 409}` and a nonzero exit code. Paths and actor must be supplied by the trusted authenticated host. The CLI does not independently authenticate a caller with local filesystem access.

Preview includes `rules`, `changes`, `blockers`, `can_apply` and `preview_sha256`. A change includes `rule_id`, `decision_ref`, `decision_revision`, `decision_sha256`, `target`, `before`, `after` and `rationale`. Apply returns the new and parent revision hashes, audit reference, `state: working`, `release_required: true` and `tenant_actions_performed: false`.

## Verification and remaining scope

`tooling/tests/test_project_decision_derivation.py` covers pure deterministic previews, exact identity lookup after array reordering, negative approval/scope/option/precondition cases, conflicts, schema validation, real immutable commits, byte-preserved decision/evidence modules, release invalidation, stale and concurrent writes, and subprocess CLI execution.

This implementation does not supply a universal decision catalog, create missing topology, author tool logic, prove native semantic validity or validate tenant behavior. It does not calculate staffing availability, duration or price. These remain explicit capability work, not implicit effects of approving a prose recommendation.
