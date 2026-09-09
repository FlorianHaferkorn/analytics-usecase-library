# Protected Studio runner host

Status: implementation and offline tests; disabled unless a host operator explicitly configures it. No tenant execution has been performed as part of this implementation.

## Decision and constraints

The Studio server is the authentication boundary. A signed OAuth session, a stable `github:<provider-account-id>` actor and project-level administrator authorization are required before it calls this private subprocess adapter. An email address, local development session or actor supplied by the browser is not sufficient.

The adapter is `tooling/superversion/project_package/runner_host.py`. It wraps the existing signed `ProtectedWorkspaceRunner` and the create-only `FabWorkspaceClient`; it does not create a competing deployment engine. A local administrator who can run the module, replace host policy or read the signing key is trusted. The CLI does not authenticate a human by itself and must not be exposed as a public command service.

## Studio access and operator workflow

In **Automation → Deployment preflight**, build and review the workspace plan, record an approval rationale, and save the signed approval. Execution requires a separate explicit confirmation. The interface displays the tenant, environment, execution principal, plan hash and expiry. A plan, project or revision change invalidates the browser confirmation.

The endpoint `/api/projects/[projectId]/runner` requires current project-admin membership and sign-in provenance from the existing GitHub OAuth provider. The actor is the stable provider account ID, not an email address. Demo Credentials sessions and legacy sessions without provenance are refused. Approval and execution require a sign-in less than 30 minutes old, a securely generated host session secret, and same-origin JSON requests. `STUDIO_RUNNER_ORIGIN` must be an exact HTTPS origin; HTTP is accepted only for explicit loopback development origins. Minimum secret checks do not establish entropy: use a cryptographically generated secret.

After approval, the URL retains only project, revision and opaque approval IDs. Reloading does not restore execution consent or retry an operation. Select the original project version and use **Retrieve saved outcome** to inspect the protected record; the ID alone grants no access. Download the receipt for handover. Neither the plan nor credentials are stored in the URL.

| Option | Benefits | Costs and limits | Decision |
|---|---|---|---|
| Ambient CLI login or a credential chain | Little host setup | Tenant and principal selection depend on machine state | Not used |
| Explicit Azure Identity credential and protected `fab` transport | Existing official SDK and CLI; exact actor, scope and one-shot intent | Host must supply a private identity, storage and operational owner | Implemented |
| Dedicated durable job service | Better long-running execution and multi-host coordination | Additional deployment, queue, identity and recovery infrastructure | Not implemented; required before distributed production execution |

## Host configuration

Only the trusted process environment may set `STUDIO_RUNNER_CONFIG` to an absolute private JSON file. No browser payload or package can select this path, credential kind, executable, state directory or signing key.

No configuration, or this minimal file, disables the runner:

```json
{"schema_version":"1.0.0","enabled":false}
```

An enabled configuration must supply every field below. This is a neutral template, not an operational authorization or a real tenant configuration:

```json
{
  "schema_version": "1.0.0",
  "enabled": true,
  "state_dir": "C:/PrivateStudio/runner-state",
  "signing_key_env": "STUDIO_RUNNER_SIGNING_KEY",
  "approvers": ["github:123456"],
  "executors": ["github:123456"],
  "scopes": [{
    "project_ref": "project_demo",
    "tenant_id": "11111111-1111-1111-1111-111111111111",
    "principal_id": "22222222-2222-2222-2222-222222222222",
    "environment": "dev",
    "identity": {
      "kind": "client_secret",
      "client_id": "33333333-3333-3333-3333-333333333333",
      "client_secret_env": "STUDIO_RUNNER_CLIENT_SECRET"
    },
    "permissions": {
      "create_workspaces": true,
      "capacity_assign_ids": ["44444444-4444-4444-4444-444444444444"],
      "domain_assign_ids": ["55555555-5555-5555-5555-555555555555"],
      "evidence_ref": "Host-verified permission evidence reference"
    }
  }]
}
```

`principal_id` is the tenant service-principal object ID, not the application/client ID. UUIDs must use canonical lower-case form. Scopes and actors are exact allowlists, with no wildcards. Separate approver and executor lists may contain the same person for a one-person operating model.

The signing reference must contain base64-encoded random key material of at least 32 bytes. The identity secret uses a different reference; neither value belongs in JSON, the package, Studio client state or an export. An operator must provide host ACLs and lifecycle management for the private file, state directory and secrets. The module checks path separation and rejects symlinks/junctions; it does not establish or certify operating-system ACLs.

For an explicit user-assigned managed identity, replace only `identity`:

```json
{"kind":"managed_identity","client_id":"33333333-3333-3333-3333-333333333333"}
```

The Azure-hosted runtime must actually have that identity assigned. No system-assigned identity fallback, `DefaultAzureCredential`, arbitrary module import, interactive sign-in or CLI login is used. `azure-identity` is an optional host prerequisite and is not installed automatically. `fab` must already be available through the trusted host installation. Only public-cloud Fabric is supported.

## Request and result contract

The trusted server invokes the fixed Python module with `--repository`, `--schemas` and one closed `--mode`. JSON is passed on stdin, never interpolated into a shell command. Repository and schema paths are selected by server configuration, not submitted by the browser.

All requests include `project_ref`, `revision_hash` and the server-derived `actor`.

| Mode | Additional input | Result and effects |
|---|---|---|
| `status` | None | Configuration metadata only; no secret value reads, credential construction, token request, filesystem writes or tenant call |
| `approve` | `plan`, `rationale`, `confirm: true` | Validates the exact current released package and persists its signed 15-minute intent; no tenant calls |
| `execute` | `approval_id`, `confirm: true` | Uses only the stored signed plan; permanently consumes this attempt before constructing a credential |
| `outcome` | `approval_id` | Reads signed evidence for the exact project/revision; does not renew or execute an approval |

Responses are `{ok:true,value:...}` or `{ok:false,error:...,status:409}`. Errors are sanitized; token, secret, subprocess output and raw filesystem diagnostics are not returned. Input size is limited and unknown fields are refused.

Status reports `configuration_checked_only: true` and `identity_verified: false`. `can_approve` and `can_execute` require enabled exact scope, the respective allowed actor, referenced environment names, Azure Identity distribution metadata, a discoverable `fab` executable and a usable configured state path. Studio additionally checks the mutation sign-in window and origin configuration. These checks do not prove that a referenced secret is valid, a tenant is reachable, the installed CLI is compatible or host ACLs are correct. A missing dependency remains a blocker rather than an implicit login fallback.

Studio now displays actionable readiness diagnostics and a six-case first-workspace acceptance procedure. See [readiness and acceptance](PROJECT_RUNNER_ACCEPTANCE.md) for the status contract, operator steps, protocol export and reproducible offline checks. Configuration and supporting evidence never automatically become customer acceptance.

Outcome state is one of:

- `approved_not_executed`: signed intent exists and has not expired or been consumed.
- `expired`: unused intent can be inspected but cannot execute.
- `consumed_requires_reconciliation`: a permanent claim exists but no final signed outcome exists. It may still be running or may have been interrupted. Do not retry.
- `completed`: the attempt produced a final signed record. **This does not mean deployment succeeded.** Inspect `result.outcome.status`, for example `workspace_verified`, `drift` or `stopped_requires_reconciliation`.

Historical evidence remains readable after a HEAD change or expiry, but current host scope and operator authorization still apply. Modified signatures, mismatched project/revision or missing consumption evidence are refused. Key rotation needs a deliberate evidence-retention strategy; a different key cannot verify old records. Evidence access does not authorize another attempt.

An emergency kill switch must not force an operator to re-enable writes to investigate. Setting `enabled: false` in a **full** host configuration stops approval and execution while retaining read-only `outcome` access through the existing exact actor/scope allowlists, private storage and signing key. The minimal disabled configuration has none of those authorities and cannot read protected evidence. Removing scope or actor access, changing the key, or requesting a foreign revision still refuses the read. No disabled-policy read constructs credentials or calls a tenant.

## Execution and recovery

After the one-shot claim is persisted, the explicit credential requests only `https://api.fabric.microsoft.com/.default`. The existing Fabric client checks token tenant, principal, audience and lifetime before sending it to `fab`; Fabric validates its actual signature and access rights. No token is stored in the runner evidence. Host permission declarations remain evidence-backed prerequisites, not grants or live authorization proof.

Fresh inventory, current release, exact desired objects and readback are checked by the existing workspace executor. Existing mismatched workspaces are conflicts, not adopted or overwritten. Uncertain creation is not retried. Created resources are preserved for reconciliation.

A Studio timeout or disconnected browser must be treated as uncertain: keep the approval ID and query `outcome`. Do not create a new approval or repeat execution to discover whether the first call succeeded. The implementation is a bounded subprocess, not a durable queue. All processes writing to a tenant must use the same protected state/lock boundary. Interrupted locks require controlled host recovery after reviewing receipts and live inventory; never automatically delete a stale lock.

## Test coverage and remaining evidence

`tooling/tests/test_project_runner_host.py` covers disabled default, read-only status without secret reads, strict host and request contracts, stable actors, unsupported credential selection, missing dependencies, no-op historical reads, tampering, foreign scope, expiry, one-shot execution, interrupted claims, startup failure sanitization, explicit SDK construction and the real subprocess JSON envelope. Fabric clients and credentials are fakes; tests never contact a tenant. Existing protected-runner and deployment-plan suites exercise the signed intent and create/readback mechanics.

Before live use, an operator must explicitly establish authenticated Studio hosting, private storage/secrets, the actual identity and permission evidence, the shared execution boundary and recovery responsibility. Then prove one authorized non-production create/readback, repeated no-op plan, interruption and reconciliation. Item definitions/bindings, security, ingestion and CI/CD still require separate adapters and acceptance tests. Workspace verification is not full delivery.

## Primary references

Checked 8 September 2026; documented interfaces are not tenant evidence:

- [Azure Identity ClientSecretCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.clientsecretcredential?view=azure-python): explicit tenant/client/secret and token request.
- [Azure Identity ManagedIdentityCredential](https://learn.microsoft.com/en-us/python/api/azure-identity/azure.identity.managedidentitycredential?view=azure-python): explicit user-assigned client ID selection.
- [Fabric service-principal token scope](https://learn.microsoft.com/en-us/fabric/data-factory/set-pipeline-owner-tutorial): public Fabric `.default` scope for acquiring an application token; endpoint permissions remain operation-specific.
