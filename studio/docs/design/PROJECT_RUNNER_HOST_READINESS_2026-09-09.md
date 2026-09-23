# Protected runner host readiness — measured 9 September 2026

Status: host diagnostics only. No tenant API was called, no workspace was created and no credential was read or created. The runner remains disabled.

## Measured, not asserted

The diagnostic was executed rather than described. `runner_host.py --mode status` ran on this host against an empty repository with actor `github:101591047`; the full result is held outside this repository as `runner-host-status-2026-09-09.json`, SHA-256 `DB215570…`. It reports `enabled: false`, `can_approve: false`, `can_execute: false` and, across its twelve checks, **7 missing, 2 configured, 3 not verified**.

| Check | State | Measured on this host |
|---|---|---|
| `identity_sdk` | configured | `azure-identity` 1.25.3 in Python 3.13, also the default `python` |
| `fabric_cli` | configured | `fab` 1.6.1 at `…\Python313\Scripts\fab.exe` |
| `host_policy` | missing | no host configuration exists; `STUDIO_RUNNER_CONFIG` is not set |
| `project_scope` | missing | no allowed tenant/principal/project/environment scope |
| `approver` / `executor` | missing | the actor is on no allowlist |
| `signing_reference` | missing | no signing key reference |
| `identity_reference` | missing | no client identity or managed identity |
| `state_storage` | missing | no private state directory |
| `identity_permissions`, `host_recovery`, `tenant_acceptance` | not verified | by design: configuration presence proves none of these |

The two dependencies that usually cost the most time are already satisfied. Everything still missing is configuration and authorisation, not tooling.

## Values that are now known

| Value | Measured | Source |
|---|---|---|
| Stable operator actor | `github:101591047` (`FlorianHaferkorn`) | `gh api user` on this host |
| Tenant of the existing `_Test` workspace | `<customer-tenant-id>` | `tid` claim of the Fabric access token |
| Identity home tenant | `<nagarro-tenant-id>` (Nagarro) | `idp` claim of the same token |

The two tenant IDs differ, which confirms that the identity used for the UC1 runs is a **guest** in the workspace's tenant. The `_Test` workspace therefore sits in the customer tenant, not in a Nagarro tenant.

## The decision that blocks Gate 1

The runner's only capability is `fabric_workspaces_create_only`: it creates a workspace and reads it back. It cannot operate inside an existing workspace, so a Gate 1 proof cannot run inside `_Test`. Combined with the tenant measurement above, a Gate 1 proof as things stand would **create a new workspace in the customer tenant**. That is a wider authorisation than the one recorded for the UC1 runs, which covers a single existing disposable workspace with synthetic data.

Two ways forward, both requiring a decision that this document does not make:

1. Provide a separate non-production tenant. Clean boundary, no customer exposure, but it has to exist.
2. Explicitly authorise exactly one additional, clearly named and disposable workspace in the customer tenant, and record who authorised it.

## What a customer-tenant Gate 1 actually requires — corrected against the project ledger

An earlier revision of this document assumed the customer tenant would first have to switch on two Fabric developer settings. **That assumption is wrong and is corrected here**, measured against the project ledger rather than against generic documentation.

Ledger K-68 records a full export of all 170 tenant settings on 03.09.2026 (`tenant-settings-export-20260903.json`, SHA-256 `1AD8BA25…`). Both switches the runner needs are **already enabled**: `ServicePrincipalAccessGlobalAPIs`, which governs workspaces, connections and deployment pipelines, and `ServicePrincipalAccessPermissionAPIs` for the Fabric public APIs. Admin APIs are deliberately off for the principal.

The real constraints are narrower and sharper:

| Constraint | Source | Effect on Gate 1 |
|---|---|---|
| Both settings are scoped to exactly one group, `sg-fabric-sp-provisioning` (`<group-id>`) | K-68 | Only a principal inside that group can create a workspace at all |
| The only principal there is the central bootstrap application `svc-fabric-provisioning-<tenant>`, App ID `<app-id>` | K-114, ADR-0004 identity lanes | Its purpose is central platform bootstrap, recovery and governed Blueprint upgrades |
| That principal must not be shared across purposes | K-121 | Sharing it would share credentials, permissions, failure scope and audit attribution. A Studio product gate is none of its three permitted purposes |
| The domain principals `svc_fabric_provisioning_<domain>` and `svc_fabric_cicd_{domain}` are prepared but created only after the final Blueprint approval | K-121, K-115, ADR-0004 | They do not exist yet and are gated behind O-73 |
| Permanent automation uses customer-owned workload identity federation and **no client secret is distributed to Nagarro**; a guest cannot impersonate the application | K-118 action B02 | There is no secret to configure, by design |

The last row is the hard technical blocker, and it is a property of this runner, not of the customer. `_credential` in `runner_host.py` constructs exactly two credential types, `ClientSecretCredential` and `ManagedIdentityCredential`. **Workload identity federation is not implemented.** Even with every permission in place, the runner cannot authenticate the way this customer requires.

Three ways forward, and only one of them is available today:

1. **A separate non-production tenant.** The gate runs entirely inside our own boundary, where a client secret or a user-assigned managed identity is ours to create. No customer decision, no exception to K-121, no product change.
2. **Add federated credentials to the runner.** The right answer for the target architecture, because the customer's stated model is federation. This is product development, not a Gate 1 run, and it needs its own decision.
3. **Ask the customer for an exception.** Either a secret for the central principal, which contradicts K-118 directly, or early creation of `svc_fabric_provisioning_<domain>` ahead of O-73, which contradicts K-121. Both trade governance for a product gate.

## Remaining steps once that decision exists

1. **Execution identity.** A dedicated client identity (`client_secret`) or an explicit user-assigned managed identity, with a canonical UUID client ID. The ambient `az login` session is deliberately unusable: `_credential` refuses `DefaultAzureCredential` and CLI fallbacks. Creating this identity and its secret is a host or customer administrator action.
2. **Signing key.** At least 32 bytes, cryptographically generated, base64-encoded, exposed through its own environment reference. It must differ from the identity secret reference; the loader rejects a shared reference.
3. **Private state directory.** An absolute path outside the project package repository, with restricted host ACLs. The loader rejects a state path inside or containing the repository root.
4. **Host configuration file.** The template in [`PROJECT_RUNNER_HOST.md`](PROJECT_RUNNER_HOST.md) filled with the values from 1 to 3 plus the actor and tenant above, stored at a private absolute path and referenced by `STUDIO_RUNNER_CONFIG`. It carries the trusted permission evidence reference for `create_workspaces`.

Re-run the status command afterwards; every `missing` above must read `configured` before an approval is attempted.

## Boundaries

- Configuration presence is not permission. `identity_verified`, `tenant_actions_performed` and `whole_project_apply_ready` stay false until the separately authorised acceptance procedure runs.
- Gate 1 covers workspace creation, a repeated no-op plan, an interruption and a readback. Items, lakehouses, security, data loading, Git and CI/CD are separate, unimplemented adapters.
- The UC1 tenant evidence recorded under the customer project does not substitute for this gate. That work ran through purpose-built Python and REST scripts, not through the Studio generator, so it proves Fabric feasibility, not that Studio produces executable artefacts.
