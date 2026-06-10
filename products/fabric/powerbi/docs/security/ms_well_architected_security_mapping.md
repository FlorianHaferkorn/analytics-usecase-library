# MS Well-Architected Security Mapping (Fabric)

This document maps the Microsoft Well-Architected Framework security guidance for Microsoft Fabric to the “what we enforce in this repo” layer.

Primary references:
- Microsoft Fabric security controls: https://learn.microsoft.com/de-de/azure/well-architected/microsoft-fabric/security
- Microsoft Fabric architecture patterns (context): https://learn.microsoft.com/de-de/azure/well-architected/microsoft-fabric/overview#architecture-pattern

## How to use this document

Use it when:
- defining a new environment (dev/test/prod),
- onboarding a new domain/workspace,
- reviewing a security regression or a compliance gap,
- deciding which security checks should be “Definition of Done” for PRs.

## Repo “control plane” vs “data plane” (important boundary)

This repo primarily controls:
- governance structure (workspace separation),
- least-privilege patterns (roles, RLS/OLS),
- code-driven deployment, validation gates, and drift prevention.

Microsoft Fabric primarily controls:
- platform-managed network/security primitives (managed VNets / private endpoints),
- baseline encryption and TLS enforcement,
- the underlying service resilience.

Therefore this mapping focuses on: *how we operationalize Microsoft guidance with repo standards and checks*.

## Control mapping (MS -> Repo -> Action)

### 1) Baseline & guardrails

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Security baseline | Define a baseline (“blueprint”) and use it as an input to risk and governance policy | Strong governance conventions and CI gates (“SSOT + strict integrity”) | Missing explicit “Fabric security baseline” doc for workspace-level settings | Add environment security baseline checklist (see “Definition of Done” below) |

Evidence in repo:
- `products/fabric/powerbi/docs/fabric_architecture_best_practices.md` (governance and security section)
- `core/strategy_operating_model/operating_model/data_governance.md` (security is intentional, least privilege, lineage/traceability)
- Stage 1 + registry strict gates (repo continuous integrity)

### 2) Isolation boundaries (workspaces, capacity)

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Workspace as first defense line | Create separate workspaces by team/project/environment and enforce element-level permissions | `fabric_architecture_best_practices.md` defines DE_/DM_/BI_/Shared workspace strategy, plus DTAP patterns and roles | Workspace sprawl / ad-hoc “shared workspaces” without clear ownership | Add a “workspace naming + ownership + permission” Definition of Done for new workspaces |
| Capacity as isolation tool | Use capacities to isolate settings, administrative responsibilities, and performance | Repo recommends Pattern 2/3 (single capacity vs separate capacities) | Lack of an explicit rule for when to split capacities (SLO/criticality thresholds) | Add a “capacity split criteria” doc (can start simple: criticality + performance + governance boundaries) |

### 3) Identity and Zero Trust (Entra ID, PIM, least privilege)

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Entra ID as the authentication backbone | All access flows through Entra ID; enforce least privilege | Repo role model + least privilege pattern and RLS/OLS are clearly established | Admin elevation workflow not documented end-to-end | Add a “who can do what” runbook that includes a “PIM required for admin” note |
| Privileged Identity Management | Admin roles should require PIM; elevated permissions only when needed | Repo documents least privilege; deployment automation emphasizes restricting who can deploy | No explicit PIM integration or policy statement in repo docs | Add environment onboarding note: “admin rights require PIM” and ensure deploy identities are separated |

Evidence in repo:
- `products/fabric/powerbi/docs/fabric_architecture_best_practices.md` (workspace roles + least privilege)
- `products/fabric/powerbi/docs/fabric_powerbi.md` (RLS/OLS patterns, least privilege roles)

### 4) Secure networking (managed VNets, private endpoints, IP allowlists)

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Managed VNets / private endpoints | Use managed VNets and private endpoints so the service runs in isolated network segments | Repo focuses on governance and data/model security; network primitives are not documented as a repo “standard” | Teams may treat “workspace identity + RLS” as sufficient, without network controls | Add a “network standard” section to environment baseline (even if partly org-managed) |
| Workspace IP firewall rules | Optionally restrict client IPs at workspace level | Not explicitly covered as a repo standard | Missing “how to set it” and “how to test it” | Add “network controls test” checklist item (connectivity test + negative test) |

### 5) Encryption (at rest, in transit, CMK)

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Default encryption | Encrypt data at rest and in transit (TLS 1.2+) | Not a repo-config item; we rely on Fabric baseline | None (platform-managed) | Document “platform baseline relies on Microsoft” |
| Customer-Managed Keys (CMK) | For stricter requirements, use CMK and separate supported/unsupported artifacts | Repo doesn’t specify per-artifact CMK adoption rules | If CMK is desired, we need explicit “what supports CMK” and “how we validate” | Add CMK decision tree + operational dependency note |

Evidence in repo:
- Repo contains general “secure config” guidance (Key Vault and secrets). Example: `products/fabric/powerbi/docs/references/fabric-api-core.md` (secrets guidance)
- `internal/continuity/runbook.md` emphasizes secure operational practices, including exporting backups

### 6) Hardening and “secure defaults”

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Disable unnecessary features | Disable external sharing, avoid “anyone with link”, standardize confidentiality labels | Repo emphasizes governance and least privilege but does not list “Fabric feature hardening toggles” | Missing “Fabric setting hardening checklist” | Add environment hardening checklist (public link/external sharing, confidentiality labels, datasource auth defaults) |

### 7) Secret management (Key Vault)

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| No secrets in notebooks/scripts | Use Key Vault with runtime retrieval | Repo explicitly avoids committing secrets and uses secure config patterns | Some automation may still log secrets if not sanitized | Add “logging sanitization” requirement for deployment scripts |

Evidence in repo:
- `products/fabric/powerbi/docs/references/fabric-api-core.md` (secrets guidance)
- `studio/src/lib/secrets/*` (Azure Key Vault integration patterns)
- `internal/continuity/runbook.md` (store secrets in secure config)

### 8) Monitoring, Security observability, SIEM, DLP

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Centralized monitoring (SIEM) | Export Fabric audit + Entra ID sign-in logs; correlate events; configure alerts including RBAC changes and exports/downloads | Repo has deployment observability (structured logging) and health checks | No explicit security-event-to-alert mapping | Add a “Security Observability Standard” mapping to: Fabric audit events + Entra sign-ins + DLP violations + SIEM alerts |
| DLP testing | Test DLP policies and verify enforcement and warnings | Not explicitly documented as a standard test type | DLP regressions could go unnoticed | Add DLP test procedure to environment security test plan |

### 9) Security tests

| MS guidance area | What Microsoft expects | What we already have in this repo | Typical gap to check | Repo action |
|---|---|---|---|---|
| Access control tests | Validate only intended users can access workspaces/artifacts | RLS/OLS patterns exist; integration tests are more “model correctness” than “access security tests” | Missing negative access tests (viewer vs attacker scenario) | Add Definition of Done: “access matrix validation” for new sensitive artifacts |

## Definition of Done (Environment baseline checklist)

For every environment (at minimum dev/test, and prod with stricter rules), consider the following “minimum baseline” items:

1. Workspace isolation
   - Workspaces are created with clear purpose boundaries (no mixed environments in one workspace).
   - Roles are assigned per RACI; production editing is restricted.

2. Identity & least privilege
   - Admin/deploy identities are separated from viewer/consumer identities.
   - Least privilege applies to workspace interactions and to data/model access (RLS/OLS).

3. Secrets handling
   - No credentials or secrets are committed to the repo.
   - Deployment logs are sanitized (no secrets in structured logging).

4. Network controls (org-dependent, but testable)
   - If private connectivity is required, document the expected network path.
   - Execute at least one positive and one negative connectivity test per environment.

5. Encryption posture
   - Document whether CMK is used or explicitly not used.
   - If CMK is used: plan for rotation and revocation testing.

6. Security monitoring & alerting
   - Document what event sources are exported (Fabric audit + Entra sign-ins).
   - Define alert ownership and response for at least: RBAC changes, suspicious sign-ins, and large exports.

## Suggested next improvement (PR-packaged)

If you want this mapping to become operational in CI:
- Add a “security baseline lint” script that checks repo metadata (workspace roles expected to exist, RLS/OLS presence in sensitive models, no secrets committed).
- Add a “security test checklist artifact” for each new sensitive use case (stored alongside use case factsheets or deployment manifests).

---

Last reviewed: 2026-06-04
