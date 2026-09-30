"""provision_terraform — emit a Terraform (microsoft/fabric) platform-skeleton from a blueprint.

Backend adapter (ADR-0015 follow-up) that renders the *declarative* platform skeleton the
Fabric-automation research (2026-07-15 landscape doc §1/§5) recommends for infra: the
`microsoft/fabric` Terraform provider, with plan/apply + drift detection — complementary to
the imperative `fab` scripts (provision_fabric). Both come from the same IR.

Emits HCL for the objects the provider manages declaratively:
- `fabric_workspace` (one per de-duplicated workspace; capacity via `fabric_capacity` data
  sources — the provider does NOT create capacity, that is an Azure ARM resource). Since D-596
  (30.09.2026) production and non-production workspaces reference **separate** capacities
  (one per stage group, consolidated within); the assignment comes from
  `kapazitaet_stufen.zuordnung` (workspace stage + `platform.capacities[].stages`),
- `fabric_domain` (+ workspace assignment) per mesh domain — domain resources are GA,
- `fabric_workspace_role_assignment` (principals from a local governance map / variables),
- `fabric_workspace_git` (optional, from a git config).

Honest by construction: resource shapes are grounded in the provider docs; the provider is
beta overall (some resources lack service-principal support, `fabric_domain` needs a Fabric
admin user context) and the exact domain-workspace-assignment resource is annotated with a
VERIFY pointer to the registry rather than guessed silently.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import re

from core.dataarch_engine.blueprint.governance_strategy import LAKEHOUSE_ROLES

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _tf_name(name: str) -> str:
    """A valid HCL local resource name (letters/digits/underscore, not leading digit)."""
    s = _NONWORD_RE.sub("_", (name or "").lower()).strip("_")
    return f"w_{s}" if s[:1].isdigit() else s


def _unique_workspaces(bp: dict) -> list[tuple[str, str]]:
    seen: dict[str, str] = {}
    for d in sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        for ws in d.get("workspaces", []):
            seen.setdefault(ws["name"], ws.get("role", ""))
    return sorted(seen.items())


def _backend_tf() -> str:
    """Remote-State im Azure-Speicher (I-21 W5.4 c). Der CI/CD-Leitfaden verlangt den State
    verschlüsselt in geschütztem Cloud-Speicher (Learn `fundamentals/understand-best-practices-
    fabric-cicd`, Checkliste „Project setup“). Teilkonfiguration: Werte kommen per
    `-backend-config`, damit kein Speicherkonto im Repo steht."""
    return (
        "# Remote state (Azure Storage, encrypted at rest). Partial configuration — values come from\n"
        "# `terraform init -backend-config=backend.hcl` (copy backend.hcl.example, do not commit it).\n"
        "# Local try-out without remote state: `terraform init -backend=false`.\n"
        "terraform {\n"
        "  backend \"azurerm\" {}\n"
        "}\n"
    )


def _backend_hcl_example() -> str:
    return (
        "# Copy to backend.hcl (gitignored) and fill in. Use Entra auth, not an access key.\n"
        "resource_group_name  = \"<rg-terraform-state>\"\n"
        "storage_account_name = \"<sttfstate>\"\n"
        "container_name       = \"tfstate\"\n"
        "key                  = \"fabric-platform.tfstate\"\n"
        "use_azuread_auth     = true\n"
    )


def _providers_tf() -> str:
    return (
        "# Terraform providers — Fabric platform skeleton (ADR-0015; research 2026-07-15 §1).\n"
        "terraform {\n"
        "  required_version = \">= 1.8\"\n"
        "  required_providers {\n"
        "    fabric = {\n"
        "      source  = \"microsoft/fabric\"\n"
        "      version = \"~> 1.0\"   # provider is beta; pin + re-validate on upgrade\n"
        "    }\n"
        "  }\n"
        "}\n\n"
        "provider \"fabric\" {\n"
        "  # Auth via Azure CLI / service principal / managed identity (env or blocks).\n"
        "  # fabric_domain: a service principal IS supported — the caller must be a Fabric\n"
        "  # ADMINISTRATOR, whichever identity is used. One extra condition that is easy to miss:\n"
        "  # the Azure application must NOT have any Fabric permissions configured in the Azure\n"
        "  # portal that require admin consent. Verified 2026-07-31 against the provider docs\n"
        "  # (microsoft/terraform-provider-fabric docs/resources/domain.md) and the REST reference\n"
        "  # (learn.microsoft.com/rest/api/fabric/admin/domains/create-domain) — two independent\n"
        "  # sources. An earlier note here said 'SP not supported'; that no longer holds.\n"
        "}\n"
    )


def _variables_tf(slots: list[tuple[str, str, str]]) -> str:
    return (
        ""
        + "".join(
            f"variable \"capacity_name_{slot}\" {{\n"
            "  type        = string\n"
            f"  description = \"Existing Fabric capacity display name — {label} (D-596; this provider does NOT create capacity).\"\n"
            "}\n\n"
            for slot, label, _wert in slots) +
        "variable \"stages\" {\n"
        "  description = \"Promotion stages for the deployment pipeline (dev -> test -> prod).\"\n"
        "  type        = list(string)\n"
        "  default     = [\"dev\", \"test\", \"prod\"]\n"
        "}\n\n"
        "variable \"role_assignments\" {\n"
        "  description = \"Workspace role assignments: list of {workspace, principal_id, principal_type, role}.\"\n"
        "  type = list(object({\n"
        "    workspace      = string\n"
        "    principal_id   = string\n"
        "    principal_type = string\n"
        "    role           = string\n"
        "  }))\n"
        "  default = []\n"
        "}\n\n"
        "variable \"connections\" {\n"
        "  description = \"Source connections/gateways: list of {name, connectivity_type, gateway_id, details...}.\"\n"
        "  type = list(object({\n"
        "    name              = string\n"
        "    connectivity_type = string          # ShareableCloud | OnPremisesGateway | VirtualNetworkGateway\n"
        "    gateway_id        = optional(string) # for on-prem / VNet gateways\n"
        "  }))\n"
        "  default = []\n"
        "}\n"
    )


def _connections_tf(bp: dict) -> str:
    """`fabric_connection` per source connection (driven by var.connections; secrets in tfvars).

    The blueprint's ingestion sources are listed as a comment so the operator knows which
    connections the platform needs; the actual connection details/credentials stay local.
    """
    srcs = sorted({e.get("source", "") for e in bp.get("ingestion", []) if e.get("source")})
    src_note = ("#   sources needing a connection: " + ", ".join(srcs)) if srcs else \
        "#   (no ingestion sources in the blueprint)"
    return (
        "# Connections / gateways — one fabric_connection per source (research §5).\n"
        "# Driven by var.connections; connection_details + credentials stay in your tfvars (never here).\n"
        f"{src_note}\n"
        "# VERIFY the exact connection_details/credential_details schema per connector at:\n"
        "#   registry.terraform.io/providers/microsoft/fabric/latest/docs/resources/connection\n"
        "resource \"fabric_connection\" \"this\" {\n"
        "  for_each          = { for c in var.connections : c.name => c }\n"
        "  display_name      = each.value.name\n"
        "  connectivity_type = each.value.connectivity_type\n"
        "  gateway_id        = try(each.value.gateway_id, null)\n"
        "  # connection_details { ... }   # per-connector; fill from your local tfvars\n"
        "}\n"
    )


def _deployment_pipeline_tf(bp: dict) -> str:
    """`fabric_deployment_pipeline` with stages (dev->test->prod) + per-stage workspace binding.

    The pipeline is the **stage** mechanism (Stage-Workspaces): its stages promote the same
    item set dev->test->prod. Assigning a workspace to a stage is annotated VERIFY because the
    exact assignment resource is provider-version-dependent.
    """
    workspaces = _unique_workspaces(bp)
    ws_map = "\n".join(f'    "{name}" = fabric_workspace.{_tf_name(name)}.id' for name, _r in workspaces)
    return (
        "# Deployment pipeline — the stage mechanism (dev -> test -> prod) for the workspaces.\n"
        "# Stage-workspaces: the pipeline promotes the same content through its stages.\n"
        "resource \"fabric_deployment_pipeline\" \"this\" {\n"
        "  display_name = \"platform-dp\"\n"
        "  description  = \"Generated from ArchitectureBlueprint — promotes dev -> test -> prod.\"\n"
        "  stages = [for s in var.stages : {\n"
        "    display_name = s\n"
        "    # is_public = false   # optional per stage\n"
        "  }]\n"
        "}\n\n"
        "# Per-stage workspace assignment. VERIFY the assignment resource/shape against the registry:\n"
        "#   registry.terraform.io/providers/microsoft/fabric/latest/docs (deployment_pipeline stage assignment)\n"
        "locals {\n"
        "  pipeline_workspace_ids = {\n"
        f"{ws_map}\n"
        "  }\n"
        "}\n"
    )


def _variable_library_tf() -> str:
    """The Variable Library item (I-19.2) as a Fabric item deployed with Terraform.

    Provider support for a first-class `fabric_variable_library` resource is version-dependent;
    emitted VERIFY-annotated with the honest fallback (deploy the emitted .VariableLibrary item
    via git/fabric-cicd). Ties the landing zone to the config-as-code layer.
    """
    return (
        "# Variable Library (config-as-code, I-19.2) — one place for stage-specific values.\n"
        "# VERIFY provider support: a first-class fabric_variable_library resource is version-\n"
        "# dependent. If unavailable, deploy the emitted `<lib>.VariableLibrary/` item via git\n"
        "# integration (fabric_workspace_git) or fabric-cicd — the item definition already exists\n"
        "# (produced by --emit-varlib). Registry:\n"
        "#   registry.terraform.io/providers/microsoft/fabric/latest/docs\n"
        "#\n"
        "# resource \"fabric_variable_library\" \"platform_config\" {\n"
        "#   workspace_id = fabric_workspace.<dev-workspace>.id\n"
        "#   display_name = \"platform_config\"\n"
        "#   # definition from the emitted .VariableLibrary item (format_version / parts)\n"
        "# }\n"
    )


def _capacity_slots(bp: dict, capacity: str, capacity_non_prod: str
                    ) -> tuple[list[tuple[str, str, str]], dict[str, str]]:
    """Capacity data-source slots and the workspace → slot map (D-596).

    A slot is one ``data "fabric_capacity"`` source. A named capacity is its own slot when it
    declares ``stages`` or carries production; otherwise the workspace falls into its stage
    group's slot (``prod`` / ``non_prod``, per capacity domain if the capacity has one). So a
    blueprint that names only ONE capacity without ``stages`` still gets a separate
    non-production slot — setting ``capacity_name_non_prod`` to the production name in
    ``terraform.tfvars`` is how a deliberate consolidation (D-596 option b) is expressed, visibly.
    Returns ``([(slot, label, tfvars value)], {workspace: slot})``.
    """
    from core.dataarch_engine.blueprint.kapazitaet_stufen import GRUPPEN_LABEL, kapazitaet_fuer, zuordnung

    slots: dict[str, tuple[str, str]] = {}
    ws_slot: dict[str, str] = {}
    for r in zuordnung(bp):
        if r["workspace"] in ws_slot:
            continue
        kap = kapazitaet_fuer(bp, r["domain"], r["stage"] or None) or {}
        name = str(kap.get("name") or "").strip()
        dom = str(kap.get("domain") or "").strip()
        label = GRUPPEN_LABEL[r["gruppe"]] + (f", Domaene {dom}" if dom else "")
        if name and (kap.get("stages") or r["gruppe"] == "prod"):
            slot, wert = _tf_name(name), name
            label = f"{name} ({label})"
        else:
            slot = r["gruppe"] + (f"_{_tf_name(dom)}" if dom else "")
            wert = capacity if r["gruppe"] == "prod" else capacity_non_prod
        slots.setdefault(slot, (label, wert))
        ws_slot[r["workspace"]] = slot
    if not slots:
        slots["prod"] = (GRUPPEN_LABEL["prod"], capacity)
    # insertion order = zuordnung order (production first) — deterministic
    return [(s, lab, w) for s, (lab, w) in slots.items()], ws_slot


def _capacity_tf(slots: list[tuple[str, str, str]]) -> str:
    out = [
        "# Capacity is an Azure ARM resource — reference the existing ones (e.g. a trial capacity).\n"
        "# To CREATE an F-SKU instead, use azurerm_fabric_capacity in a separate azurerm config.\n"
        "# D-596: production and non-production run on separate capacities (smoothing and\n"
        "# throttling act per capacity); the non-production one is pausable and can be small.\n"
        "# Tier-1 workloads (surge_class = mission_critical) may get their own — see CAPACITY_RUNBOOK.md."]
    for slot, label, _wert in slots:
        out.append(f'# {label}\n'
                   f'data "fabric_capacity" "{slot}" {{\n'
                   f'  display_name = var.capacity_name_{slot}\n'
                   f'}}')
    return "\n\n".join(out) + "\n"


def _workspaces_tf(workspaces: list[tuple[str, str]], ws_slot: dict[str, str]) -> str:
    out = ["# Workspaces (one per blueprint workspace; capacity per stage group, D-596)."]
    for name, role in workspaces:
        out.append(
            f'resource "fabric_workspace" "{_tf_name(name)}" {{\n'
            f'  display_name = "{name}"\n'
            f'  capacity_id  = data.fabric_capacity.{ws_slot.get(name, "prod")}.id\n'
            f'  description  = "{role} workspace (generated from ArchitectureBlueprint)"\n'
            f'}}')
    return "\n\n".join(out) + "\n"


def _domains_tf(bp: dict) -> str:
    out = ["# Domains (OneLake data mesh) — fabric_domain is GA; assignment needs Fabric admin context.",
           "# VERIFY the domain-workspace assignment resource name/shape against the registry:",
           "#   registry.terraform.io/providers/microsoft/fabric/latest/docs (fabric_domain_workspace_assignments)."]
    for d in sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        dn = d["name"]
        tf = _tf_name(dn)
        ws_refs = ", ".join(f"fabric_workspace.{_tf_name(w['name'])}.id" for w in d.get("workspaces", []))
        out.append(
            f'resource "fabric_domain" "{tf}" {{\n'
            f'  display_name = "{dn}"\n'
            f'}}\n\n'
            f'resource "fabric_domain_workspace_assignments" "{tf}" {{\n'
            f'  domain_id     = fabric_domain.{tf}.id\n'
            f'  workspace_ids = [{ws_refs}]\n'
            f'}}')
    return "\n\n".join(out) + "\n"


def _roles_tf(workspaces: list[tuple[str, str]]) -> str:
    # Explicit display_name → workspace id map (HCL can't iterate a resource type).
    entries = "\n".join(f'    "{name}" = fabric_workspace.{_tf_name(name)}.id'
                        for name, _role in workspaces)
    return (
        "# Workspace RBAC — driven by var.role_assignments (principals stay in your tfvars).\n"
        "# principal_type: User | Group | ServicePrincipal ; role: Admin | Member | Contributor | Viewer\n"
        "locals {\n"
        "  workspace_ids = {\n"
        f"{entries}\n"
        "  }\n"
        "}\n\n"
        "resource \"fabric_workspace_role_assignment\" \"this\" {\n"
        "  for_each     = { for r in var.role_assignments : \"${r.workspace}-${r.principal_id}-${r.role}\" => r }\n"
        "  workspace_id = local.workspace_ids[each.value.workspace]\n"
        "  principal = {\n"
        "    id   = each.value.principal_id\n"
        "    type = each.value.principal_type\n"
        "  }\n"
        "  role = each.value.role\n"
        "}\n"
    )


def _git_tf(bp: dict, git: dict) -> str:
    gold = [n for n, r in _unique_workspaces(bp) if r in LAKEHOUSE_ROLES]
    target = _tf_name(gold[0]) if gold else _tf_name(_unique_workspaces(bp)[0][0])
    return (
        "# Git integration — connect the gold/dev workspace to a repo branch.\n"
        f'resource "fabric_workspace_git" "{target}" {{\n'
        f'  workspace_id = fabric_workspace.{target}.id\n'
        "  git_provider_details = {\n"
        f'    git_provider_type = "{git.get("provider", "AzureDevOps")}"\n'
        f'    organization_name = "{git.get("organization", "<org>")}"\n'
        f'    project_name      = "{git.get("project", "<project>")}"\n'
        f'    repository_name   = "{git.get("repository", "<repo>")}"\n'
        f'    branch_name       = "{git.get("branch", "<branch>")}"\n'
        f'    directory_name    = "{git.get("directory", "/")}"\n'
        "  }\n"
        "}\n"
    )


def _terraform_md(slots: list[tuple[str, str, str]], git: dict | None) -> str:
    git_cov = "✓ `git.tf`" if git else "— (pass `--git` to emit `git.tf`)"
    return (
        "# Terraform platform skeleton (generated — ADR-0015 / I-19.5)\n\n"
        "Declarative Fabric **landing zone** via the `microsoft/fabric` provider (research §1/§5). "
        "Complementary to the imperative `fab` `provision.sh` — use Terraform for the stateful, "
        "drift-detected skeleton, `fab` for imperative content ops.\n\n"
        "```bash\nterraform init -backend-config=backend.hcl   # remote state; -backend=false for a local try-out\nterraform plan    # capacity names from terraform.tfvars (" + ", ".join(f"capacity_name_{s}" for s, _l, _w in slots) + ")\nterraform apply\n"
        "terraform plan   # re-run = drift detection (provider drift shows as a diff)\n```\n\n"
        "## Automation-Target-Abdeckung (Landing-Zone-Vollständigkeit, I-19.5)\n"
        "| Target | Datei | Status |\n|---|---|---|\n"
        "| Kapazität | `capacity.tf` | ✓ (data sources — bestehende referenzieren; Produktion und Nicht-Produktion getrennt, D-596) |\n"
        "| Stage-Workspaces | `workspaces.tf` + `deployment_pipeline.tf` | ✓ (Stages über die Pipeline) |\n"
        "| Git-Binding | `git.tf` | " + git_cov + " |\n"
        "| Deployment-Pipeline | `deployment_pipeline.tf` | ✓ |\n"
        "| Connections/Gateways | `connections.tf` | ✓ (via `var.connections`) |\n"
        "| Domains | `domains.tf` | ✓ |\n"
        "| Variable-Library | `variable_library.tf` | ✓ VERIFY (Provider-abhängig; sonst Item-Deploy) |\n"
        "| RBAC | `roles.tf` | ✓ (via `var.role_assignments`) |\n\n"
        "**Caveats (preview-gate):** provider is **beta** — pin the version; some resources lack "
        "service-principal support; **capacity is not created here** (reference an existing one via "
        "the `fabric_capacity` data source, or create an F-SKU with `azurerm_fabric_capacity`); "
        "`fabric_domain` needs a **Fabric admin user** context; the deployment-pipeline stage "
        "assignment, `fabric_connection` details and `fabric_variable_library` are annotated "
        "**VERIFY** against the registry (version-dependent). Rollback: `terraform destroy`.\n")


def emit_terraform(bp: dict, capacity: str = "<CAPACITY_NAME>", git: dict | None = None,
                   stages: tuple[str, ...] = ("dev", "test", "prod"),
                   connections: dict | None = None,
                   capacity_non_prod: str = "<CAPACITY_NAME_NON_PROD>") -> dict[str, str]:
    """Return the Terraform landing-zone skeleton as ``path → HCL`` (relative to ``terraform/``).

    Covers the full automation-target set (I-19.5): capacity, workspaces, git, domains, RBAC
    (existing) + connections/gateways, deployment-pipeline (stage mechanism), variable-library.
    Values that carry ids/secrets live in ``terraform.tfvars`` (``var.connections`` /
    ``var.role_assignments``), never in the checked-in ``.tf``. ``capacity`` names the production
    capacity and ``capacity_non_prod`` the non-production one (D-596) where the blueprint does
    not name them in ``platform.capacities[]``.
    """
    workspaces = _unique_workspaces(bp)
    slots, ws_slot = _capacity_slots(bp, capacity, capacity_non_prod)
    cap_vars = "".join(f'capacity_name_{s} = "{w}"\n' for s, _l, w in slots)
    stages_hcl = ", ".join(f'"{s}"' for s in stages)
    out = {
        "terraform/providers.tf": _providers_tf(),
        "terraform/backend.tf": _backend_tf(),
        "terraform/backend.hcl.example": _backend_hcl_example(),
        "terraform/variables.tf": _variables_tf(slots),
        "terraform/capacity.tf": _capacity_tf(slots),
        "terraform/workspaces.tf": _workspaces_tf(workspaces, ws_slot),
        "terraform/domains.tf": _domains_tf(bp),
        "terraform/roles.tf": _roles_tf(workspaces),
        "terraform/connections.tf": _connections_tf(bp),
        "terraform/deployment_pipeline.tf": _deployment_pipeline_tf(bp),
        "terraform/variable_library.tf": _variable_library_tf(),
        "terraform/terraform.tfvars": (
            cap_vars +
            f'stages           = [{stages_hcl}]\n'
            "role_assignments = []\n"
            "connections      = []\n"),
        "terraform/_TERRAFORM.md": _terraform_md(slots, git),
    }
    if git:
        out["terraform/git.tf"] = _git_tf(bp, git)
    return out
