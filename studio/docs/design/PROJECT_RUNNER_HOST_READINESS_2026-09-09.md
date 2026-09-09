# Protected runner host readiness — measured 9 September 2026

Status: host diagnostics only. No tenant API was called, no workspace was created and no credential was read or created. The runner remains disabled.

## What was measured on this host

| Precondition | Measured state | Source |
|---|---|---|
| `fab` executable on PATH | present, version 1.6.1 at `C:\Users\florianhaferkorn\AppData\Local\Programs\Python\Python313\Scripts\fab.exe` | `fab --version`, `Get-Command fab` |
| `azure-identity` in the runner Python runtime | present, 1.25.3 in Python 3.13 (also the default `python`) | `importlib.metadata.version` |
| `STUDIO_RUNNER_CONFIG` | not set | process environment |
| `ALUCA_REPO_ROOT` | not set | process environment |
| Signing key environment reference | not configured (no host configuration exists) | derived from the two above |
| Private state directory | not configured | derived |
| Azure CLI session | signed in as `florian.haferkorn@nagarro.com` | `az account show` |

Consequence: `runner_host.status` would report `enabled: false`, `can_approve: false` and `can_execute: false`. The two dependencies that usually cost the most time — the Fabric CLI and the identity SDK — are already satisfied on this machine. Everything still missing is configuration and authorisation, not tooling.

## What is still missing, in the order it has to be decided

1. **Target tenant and workspace decision.** The runner's only capability is `fabric_workspaces_create_only`: it creates a workspace and reads it back. It cannot operate inside an existing workspace. A Gate 1 proof therefore creates a *new* workspace; it cannot be run inside the customer `_Test` workspace that the UC1 vertical slice uses. Either a separate non-production tenant is provided, or creating one additional, clearly named and disposable workspace in the customer tenant is explicitly authorised. This decision is not made by this document.
2. **Execution identity.** A dedicated client identity (`client_secret`) or an explicit user-assigned managed identity, with a canonical UUID client ID. The ambient `az login` session is deliberately not usable: `_credential` refuses `DefaultAzureCredential` and CLI fallbacks. Creating this identity and its secret is a customer or host administrator action.
3. **Signing key.** A cryptographically generated key of at least 32 bytes, base64-encoded, exposed through its own environment reference. It must differ from the identity secret reference; the configuration loader rejects a shared reference.
4. **Private state directory.** An absolute path outside the project package repository, with restricted host ACLs. The loader rejects a state path inside or containing the repository root.
5. **Stable operator identity.** The `github:<provider-account-id>` actor for the approver and executor allowlists. An email address or local development session is refused.
6. **Host configuration file.** The template in `PROJECT_RUNNER_HOST.md` filled with the values from 1 to 5, stored at a private absolute path and referenced by `STUDIO_RUNNER_CONFIG`. It carries the trusted permission evidence reference for `create_workspaces`.

## Boundaries

- Configuration presence is not permission. `identity_verified`, `tenant_actions_performed` and `whole_project_apply_ready` stay false until the separately authorised acceptance procedure runs.
- Gate 1 covers workspace creation, a repeated no-op plan, an interruption and a readback. Items, lakehouses, security, data loading, Git and CI/CD are separate, unimplemented adapters.
- The UC1 tenant evidence recorded under the customer project does not substitute for this gate. That work ran through purpose-built Python and REST scripts, not through the Studio generator, so it proves Fabric feasibility, not that Studio produces executable artefacts.
