# Protected workspace runner boundary

Status: host library, authenticated Studio endpoint and explicit identity adapter implemented and tested offline. Disabled by default; not configured or verified against a live tenant. See [Studio host integration](PROJECT_RUNNER_HOST.md).

## Purpose

A downloaded deployment plan is useful review evidence, not permission to modify a tenant. A caller can edit JSON and recompute its ordinary hash. The protected runner stores the exact approved plan itself and accepts only the resulting opaque approval ID for execution.

The implementation is `tooling/superversion/project_package/protected_runner.py`. It wraps the existing create-only executor in `deployment_plan.py`; it does not add another provisioning engine.

## Authority and execution sequence

1. The host authenticates the operator and verifies project-level administrative access. The actor passed to the runner comes from this session, never from a request body.
2. Host-owned policy must explicitly enable the runner and allow the exact project, tenant ID, principal ID and environment. Separate approver and executor identity allowlists are required. They may contain the same person for a one-person operating model. A versioned team policy can require a different authenticated executor for selected environments, even when both identities appear in both allowlists.
3. The runner checks the plan against the current, explicitly released package. The operator confirms the exact plan and records a meaningful rationale.
4. The host stores the plan and approval together, signed with HMAC-SHA-256. The signature binds the policy as well as project, revision, tenant, principal, environment, operations and expiry. The signing key is not stored with the record or returned to Studio. Approval expires after 15 minutes.
5. Execution takes an approval ID, authenticated actor, pinned project/revision and explicit confirmation. It does not accept a replacement plan, approval document, token, command or state path.
   In an independent-execution environment, the host compares this actor with the signer of the stored approval before constructing a client or consuming the attempt. The Studio displays the rule and blocks an obvious self-execution; only the host check is authoritative.
6. A tenant-wide lock serializes this host's workspace writes. A permanent, exclusive consumption receipt is written before the network-capable client is constructed. One approval authorizes one attempt, including an attempt that fails during startup or preflight.
7. The existing executor obtains fresh principal-visible inventory, checks the authoritative release again, creates only missing workspaces and reads back the exact workspace ID, name, capacity and domain. An uncertain create response is not retried automatically.
8. A signed outcome records the attempt. Workspace verification is not item deployment, data readiness, security verification or project acceptance.

## Host API

| Surface | Input | Result / constraint |
|---|---|---|
| `RunnerPolicy()` | No arguments | Disabled; no allowed scopes or actors |
| `AllowedScope(...)` | Exact project, canonical tenant/principal UUIDs and `dev`, `test` or `prod` | No wildcards or inferred targets |
| `ProtectedWorkspaceRunner(...)` | Trusted repository, policy, private state directory, signing key and optional client factory | Host configuration only |
| `status(project_ref)` | Selected project | Read-only capability information; no token acquisition or filesystem writes |
| `approve(plan, actor=..., rationale=..., confirm=True)` | Exact released plan and server-derived actor | Stored approval ID, expiry and `approved_not_executed` |
| `execute(approval_id, actor=..., project_ref=..., revision_hash=..., confirm=True)` | Stored intent and current explicit request | Signed outcome, or refusal before execution |

The client factory is injected host code. It can construct the existing `FabWorkspaceClient` with a trusted Fabric token provider and verified permission evidence for the allowed scope. There is no implicit login, ambient credential discovery, dynamic module loader or arbitrary-command configuration in this boundary.

The Studio endpoint now derives its actor from a verified OAuth session and current project-admin authorization. A private fixed-mode Python subprocess bridges that trusted request to this library. The subprocess is not a standalone authentication service; running it as a host administrator is a privileged operation. Browser-supplied actors and configuration are refused.

Independent execution is configured only by the trusted host, not by the browser or Project Package. It separates two authenticated operators for a single workspace-creation attempt; it does not replace customer approval, change the input-release attestation, prove that the two people reviewed the same business decision, or enforce a complete production release workflow. A team deployment must include those separate gates in its acceptance procedure.

## Storage and recovery

Use a private runner-owned directory outside the immutable package repository and outside public web roots:

```text
runner-state/
  approvals/<opaque-id>.json     Signed exact intent
  consumed/<opaque-id>.json      Signed permanent single-use claim
  outcomes/<opaque-id>.json      Signed final wrapper outcome
  tenant-locks/<tenant-id>/      Exclusive live / interrupted-run lock
  executor-receipts/...          Existing per-operation creation/readback evidence
```

Symlinks and Windows junctions are rejected. Records are exclusively created and flushed to disk; a partial or modified approval fails signature validation. The runner never overwrites evidence. The token and signing key are not recorded in these files.

Protect both storage and key access with host ACLs. HMAC detects changes by someone without the key; it does not defend against a host administrator who can replace the code, key and records. All runner instances for a tenant must share the same trusted locking/storage boundary. Independent directories do not provide cross-host serialization.

If the process stops unexpectedly, the tenant lock remains. An operator must review creation receipts, reconcile live inventory and release the interrupted lock through controlled host administration. Do not automatically remove an old lock or replay a consumed approval. Preserve created resources; produce and review a fresh plan. Host policy/key changes invalidate pending approvals. They do not cancel a request already accepted by Fabric.

## Why this boundary

| Option | Benefit | Limitation | Outcome |
|---|---|---|---|
| Execute a pasted, self-hashed approval | Simple file handoff | An edited document can impersonate approval; no authenticated issuer | Rejected |
| Add a browser execute switch using ambient CLI login | Fast visible demo | Wrong tenant/principal risk and no protected authorization boundary | Rejected |
| Persist signed intent in a host-owned runner | Exact scope, expiry, replay protection and auditable attempt | Requires private state, key management and authenticated hosting | Library and Studio adapter implemented; disabled by default |
| Durable job service with distributed recovery | Supports longer-running, multi-host execution | Needs queue, shared locking, hosting and tenant proof | Not implemented; bounded subprocess execution is not a durable service |

## Verification and remaining gates

`tooling/tests/test_project_protected_runner.py` exercises disabled default, malformed policy, exact scope, actor and confirmation checks, rehashed forged plans, persistence across a host restart, tampering, foreign project/revision, expiry, release/HEAD changes, policy/key rotation, missing broker, client failure, single use, interrupted locks and concurrent execution. A real immutable neutral package fixture covers release → signed approval → fake-client create/readback → stale-HEAD rejection. Existing deployment executor tests cover per-write checks and uncertain create responses.

Tests do not contact a tenant. Before exposing live execution:

- Configure the implemented OAuth/project-admin adapter and explicit server-side identity broker. Keep host configuration, signing key and token provider out of client input.
- Establish private host storage/ACLs and the operational recovery owner. Decide how all runner instances share tenant locks.
- Verify the implemented Studio approval, separate execution confirmation and signed-outcome recovery against the intended host configuration.
- Prove a specifically authorized non-production create, readback, repeated no-op plan, interrupted execution and reconciliation with the intended tenant identity.
- Implement and verify item/binding, security, data and CI/CD adapters separately. This runner remains workspace-create-only.
