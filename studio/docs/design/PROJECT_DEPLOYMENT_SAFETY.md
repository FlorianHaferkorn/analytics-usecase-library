# Project deployment safety

Status: implemented, offline tested; no tenant execution or acceptance evidence.
Date: 2026-09-07.

## Supported slice

The first executable adapter creates explicitly contracted Fabric workspaces. It
does not turn a workspace into a complete delivered solution. Item definitions,
connections, identity grants, OneLake security, semantic security, Git integration,
deployment pipeline promotion, ingestion, data quality and business acceptance
remain separate blocked capability families for this executor. Other generators
can produce files without making these families executable here.

The same approved immutable project revision supplies the diagram, workspace
contract, deployment plan and readback comparison. Planning does not grant approval.
An existing input-release attestation is mandatory and the revision must still be
HEAD. Desired workspace names, accepted environment, domain, capacity and decision
references are not inferred from inventory or library defaults.

## Operator workflow

1. Authenticate outside Studio using the intended, least-privileged tenant identity.
2. Collect every page of the principal-visible workspace inventory, then read each
   workspace by ID. Record creation and capacity/domain-assignment permission
   evidence separately. Being able to list a resource is not proof of write access.
3. Plan against a selected released revision, tenant ID and environment. The plan
   classifies each workspace as create, noop, conflict or blocked. A matching name
   with different capacity/domain, incomplete assignment, ambiguous names, missing
   permissions or stale evidence cannot be overwritten.
4. Review exact operations and IDs. A trusted authenticated operator approves only
   the create-only workspace slice for that project, revision, tenant, principal,
   environment and plan hash. The approval expires after 15 minutes.
5. A trusted runner validates the authoritative revision again, refreshes inventory,
   consumes approval once and invokes the bounded adapter. No delete/update endpoint
   exists. Each write is preceded by another inventory check.
6. Verify response ID, display name, capacity ID, domain ID and completed capacity
   assignment using Get Workspace. Save created IDs immediately. Verify the final
   inventory against those exact IDs; a replacement cannot pass as the same resource.
7. On error or an uncertain POST result, stop. Do not retry creation or remove
   resources automatically. Preserve the receipt, read back tenant state and approve
   a new plan. A stopped batch can leave successfully created workspaces behind.

No authentication, approval or apply endpoint is exposed by the read-only CLI.
The Python execution seam requires host-side authentication, protected approval
storage, protected runner state and a trusted token broker. These integrations are
not supplied by a pasted JSON approval or invented identity. Hashes detect drift;
they are **not cryptographic signatures or an authorization system**. A local
administrator can change local files. Distributed runners require shared protected
state/serialization; the local claim directory prevents replay only within that
protected runner state.

## Studio/CLI interface

`python -m tooling.superversion.project_package.deployment_plan --repository <trusted repository> --schemas <trusted schemas> --mode plan`

JSON stdin:

```json
{
  "project_ref": "project_demo",
  "revision_hash": "<current released SHA-256>",
  "tenant_id": "<tenant UUID>",
  "environment": "dev",
  "observed_state": {
    "tenant_id": "<same tenant UUID>",
    "principal_id": "<actual principal object UUID>",
    "observed_at": "2026-09-07T12:00:00Z",
    "complete": true,
    "workspaces": [],
    "permissions": {
      "create_workspaces": true,
      "capacity_assign_ids": ["<approved capacity UUID>"],
      "domain_assign_ids": ["<approved domain UUID>"],
      "evidence_ref": "<permission test record>"
    }
  }
}
```

This is a format illustration, not usable permission evidence. Input is limited
to 5 MB. Unknown fields and malformed UUIDs fail validation. Evidence older than
15 minutes fails validation. Each workspace row includes `id`, `displayName`,
`capacityId`, `domainId`, `capacityAssignmentProgress`, `type`, and optionally
`description`. Empty/null assignments are retained as missing, never guessed.

`--mode reconcile` accepts `{ "plan": <plan>, "observed_state": <fresh inventory> }`.
It checks the plan's desired objects against the released repository contract,
not merely its self-reported hash. Results report `matched`, `missing` or `drift`.
Imported evidence is user-supplied evidence, not proof this application queried a
tenant. `whole_project_apply_ready` and `whole_project_verified` remain false.

## Adapter and reuse decision

`FabWorkspaceClient` invokes the official `fab api` via argument-list subprocess
calls (`shell=False`) and a closed endpoint set. It does not interpolate a CLI
command string. It isolates `FAB_TOKEN` and `FAB_TENANT_ID` from ambient `FAB_*`
authentication variables; the broker's token must match tenant, principal,
audience and lifetime. These local claim checks do not replace signature validation
by the Fabric service. Tokens never enter generated files or receipt messages.

The existing `fabric_cli_functions.py` adapter was inspected. Its string-command
construction, optional exception-to-text behavior and automatic retries are not
appropriate for uncertain create outcomes, so this safety boundary uses the same
official CLI through a narrower transport. Public-cloud `fabric` audience only;
sovereign/private-endpoint execution requires an explicit supported adapter.

## Test evidence

Offline fake-client tests cover deterministic plans, create/noop/conflict/blocked,
stale/incomplete/foreign inventory, missing permissions, released revision gates,
approval expiry and replay, rehashed malicious desired-object substitution,
mid-run inventory changes, uncertain writes, wrong assignment readback, replaced
IDs, argument safety, identity-token mismatch, pagination, unexpected HTTP/LRO
responses and no automatic retry. These tests do not prove live tenant permission,
actual installed CLI compatibility or production readiness.

## Official references checked

- [Create Workspace](https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/create-workspace): exact request fields and 201 response; required capacity/domain permissions and documented name limits.
- [Get Workspace](https://learn.microsoft.com/en-us/rest/api/fabric/core/workspaces/get-workspace): ID, capacity/domain and assignment-progress readback.
- [Fabric CLI API](https://microsoft.github.io/fabric-cli/commands/api/): endpoint, method, JSON input and header arguments.
- [Fabric CLI environment variables](https://microsoft.github.io/fabric-cli/essentials/env_vars/): isolated token/tenant authentication and token-refresh responsibility.
