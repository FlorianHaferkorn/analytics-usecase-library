# Reviewed decision-to-architecture derivation

Status: implemented as a bounded local package workflow. No tenant execution or implicit approval.

## Purpose and design decision

Architecture must reflect approved choices without treating a recommendation, AI interpretation or default as approval. An optional `architecture_input.decision_rules` list records explicit, human-authored mappings. The Studio can preview their consequences and create a new working package after review.

The rule engine replaces existing fields by stable entity identity. It is not a generic JSON Patch engine and does not infer meaning from decision prose. This reduces flexibility in exchange for a reviewable authority boundary: renaming an item, changing a capacity or selecting environment lanes cannot silently rewrite decision evidence or execute code.

## Workflow

1. Author a rule in the versioned architecture input, referencing an exact decision instance, its revision and one declared option.
2. Record the decision through the existing decision process. A rule needs `approval.state: approved`, `selection.state: confirmed`, a decider and rationale, and no custom selection value.
3. Preview the current package HEAD. The review shows the existing value, proposed value, reason, decision reference and any blocker.
4. Confirm the exact preview hash and provide a review rationale. The authenticated Studio actor is supplied by the server, not trusted from browser input.
5. Commit a new immutable revision in `working` state. Other modules, source evidence, decisions and previous snapshots remain unchanged.
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
```

This changes the declared environment list only. It does not invent TEST workspace names, capacity identifiers, native definitions, deployment bindings or access grants. Those must be explicitly authored before their generation and execution gates can pass.

## Supported targets

| Collection | Stable identity | Replaceable fields |
|---|---|---|
| `environments` | `entity_id: null` | `recommended`, `accepted` |
| `domains` | Existing `id` | `capacity`, `delivery_scope` |
| `use_cases` | Existing `id` | `name`, `architecture_detail` |
| `physical_workspaces` | Existing `id` | `name`, `description`, `capacity_id`, `domain_id` |
| `physical_items` | Existing `id` | `name`, `description` |

The field must already exist. The environment mapping must reference its declared environment decision; physical-element mappings must appear in that element's `decision_refs`. A scoped decision can affect only its explicitly scoped entity; root-level environment rules require a project-wide decision. Rules never change IDs, decision references, native code, compiler policy, approvals or KPI meaning.

## Review outcomes and failure behavior

| Status | Meaning |
|---|---|
| `ready` | The exact approved selection applies and the expected current value matches. |
| `pending` | Approval or confirmed selection is missing; no change is proposed. |
| `not_selected` | Another declared option was approved; this rule is not applied. |
| `unchanged` | The architecture already contains the rule's target value; no repeated commit. |
| `blocked` | Identity, scope, option, revision, precondition or conflicting rule prevents application. |

All applicable changes are reviewed and committed together. Any blocker or invalid resulting architecture schema prevents application. Changed HEAD or preview hash also prevents application. A concurrent edit is checked again during the repository's locked commit. The original snapshot is recoverable through immutable history; rollback is a newly reviewed revision, not destructive history rewriting.

Input release independently re-evaluates all recorded rules under the repository lock. Only `unchanged` and `not_selected` rules permit release. Ready but unapplied changes, pending confirmation and blocked mappings prevent both a new attestation and reuse of a previously recorded attestation. This prevents generated outputs from preserving architecture that contradicts its approved decision mappings. Packages without decision rules retain their existing compiler input and release behavior.

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

This implementation does not supply a universal decision catalog, create missing topology, author tool logic, prove native semantic validity or validate tenant behavior. These remain explicit capability work, not implicit effects of approving a prose recommendation.
