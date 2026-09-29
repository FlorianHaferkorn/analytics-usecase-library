"""provision_fabric_cicd — emit a `fabric-cicd` content-deployment config from a blueprint.

Backend adapter (ADR-0015 follow-up) that renders Microsoft's official content-deployment
tool `fabric-cicd` (research 2026-07-15 landscape doc §1/§5). It complements the Terraform
adapter: Terraform provisions the declarative *skeleton* (workspaces/domains/RBAC/git),
`fabric-cicd` deploys the *item definitions* (notebooks, pipelines, lakehouses, semantic
models, reports) from a Git repo into a target workspace per environment. Both from the same IR.

Emits:
- `deploy.py`   — the deployment entrypoint: a `FabricWorkspace(...)` per environment +
  `publish_all_items` / `unpublish_all_orphan_items`. Workspace GUIDs come from env vars
  (never the repo — Official-First scope boundary).
- `parameter.yml` — the `find_replace` parameterization scaffold for per-environment GUID
  swaps (e.g. the gold lakehouse id referenced by notebooks/pipelines), keyed by stage.
- `_FABRIC_CICD.md` — usage + GA/preview gating and the Terraform/deployment-pipelines split.

Honest by construction: the item-type scope + the swap targets are derived from what the
blueprint actually emits; the per-environment GUIDs are placeholders (they only exist on a
tenant), never invented. This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

_DEFAULT_STAGES = ("dev", "test", "prod")
# The item types this system emits across its cuts (transforms→Notebook, orchestration→
# DataPipeline, provisioning→Lakehouse, pbi_pipeline→SemanticModel/Report,
# provision_ingestion→CopyJob, provision_varlib→VariableLibrary).
#
# Diese Liste muss decken, was der GLEICHE Lauf schreibt. `CopyJob` und `VariableLibrary`
# fehlten bis 10.08.2026, obwohl beide Emitter ihre Verzeichnisse längst anlegen — die
# Items landeten im Kunden-Git und `publish_all_items` ging wortlos daran vorbei. Kein
# Fehler, keine Warnung: was nicht im Scope steht, existiert für fabric-cicd nicht, und
# ein Deploy, der nichts sagt, sieht aus wie ein Deploy, der alles getan hat.
#
# Die Schreibweise ist nicht geraten. `class ItemType(str, Enum)` in
# raw.githubusercontent.com/microsoft/fabric-cicd/main/src/fabric_cicd/constants.py
# (VERSION = "1.2.0", per curl gelesen 10.08.2026) führt genau 29 Werte, darunter
# `COPY_JOB = "CopyJob"` und `VARIABLE_LIBRARY = "VariableLibrary"`; `ACCEPTED_ITEM_TYPES`
# ist daraus gebildet, jeder andere String würde zur Laufzeit abgelehnt.
_DEFAULT_ITEM_TYPES = ("Notebook", "DataPipeline", "Lakehouse", "SemanticModel", "Report",
                       "CopyJob", "VariableLibrary")


def emit_deploy_py(stages: tuple[str, ...], item_types: tuple[str, ...]) -> str:
    ws_lines = "\n".join(
        f'    "{s}": os.environ.get("FABRIC_WS_{s.upper()}", "<{s}-workspace-id>"),' for s in stages)
    it_lines = ", ".join(f'"{t}"' for t in item_types)
    return (
        '"""fabric-cicd deployment entrypoint (generated — ADR-0015).\n\n'
        'Deploys the source-controlled item definitions into the target workspace for one\n'
        'environment. Run per stage: `python deploy.py <environment>`. Workspace GUIDs come\n'
        'from FABRIC_WS_<ENV> env vars (kept out of the repo).\n"""\n'
        "import os\n"
        "import sys\n\n"
        "from azure.identity import ClientSecretCredential\n"
        "from fabric_cicd import FabricWorkspace, publish_all_items, unpublish_all_orphan_items\n\n"
        "WORKSPACES = {\n"
        f"{ws_lines}\n"
        "}\n"
        f"ITEM_TYPE_IN_SCOPE = [{it_lines}]\n\n\n"
        "def credential() -> ClientSecretCredential:\n"
        '    """Service principal from the environment (never from the repo). fabric-cicd requires\n'
        '    token_credential; without it FabricWorkspace raises TypeError."""\n'
        "    return ClientSecretCredential(\n"
        '        tenant_id=os.environ["AZURE_TENANT_ID"],\n'
        '        client_id=os.environ["AZURE_CLIENT_ID"],\n'
        '        client_secret=os.environ["AZURE_CLIENT_SECRET"],\n'
        "    )\n\n\n"
        "def main(environment: str) -> None:\n"
        "    if environment not in WORKSPACES:\n"
        "        raise SystemExit(f\"unknown environment {environment!r}; expected one of {list(WORKSPACES)}\")\n"
        "    workspace = FabricWorkspace(\n"
        "        workspace_id=WORKSPACES[environment],\n"
        "        environment=environment,\n"
        "        repository_directory=os.path.dirname(os.path.abspath(__file__)),\n"
        "        item_type_in_scope=ITEM_TYPE_IN_SCOPE,\n"
        "        token_credential=credential(),\n"
        "    )\n"
        "    publish_all_items(workspace)\n"
        "    unpublish_all_orphan_items(workspace)   # remove items no longer in source\n\n\n"
        'if __name__ == "__main__":\n'
        '    main(sys.argv[1] if len(sys.argv) > 1 else "dev")\n'
    )


def emit_parameter_yml(bp: dict, stages: tuple[str, ...], lakehouse: str) -> str:
    """find_replace scaffold — swap the gold lakehouse GUID per environment across items."""
    replace = "\n".join(f'      {s}: "<{s}-{lakehouse}-lakehouse-guid>"' for s in stages)
    lines = [
        "# fabric-cicd parameterization (generated — ADR-0015).",
        "# Sits at the repo root of the deployed item definitions. Docs: microsoft.github.io/fabric-cicd.",
        "# Microsoft recommends Variable libraries over find/replace where possible; this covers GUID swaps.",
        "find_replace:",
        f"  # Gold lakehouse '{lakehouse}' id differs per workspace → swap it in the items that reference it.",
        f'  - find_value: "<{stages[0]}-{lakehouse}-lakehouse-guid>"',
        "    replace_value:",
        replace,
        '    item_type: "Notebook"        # optional filter (also applies in DataPipeline items)',
        "    # item_name: [...]           # optional: narrow to specific items",
        "",
        "# key_value_replace: []          # JSONPath-targeted swaps (connections, endpoints)",
        "# spark_pool: []                 # per-environment Spark pool bindings",
    ]
    return "\n".join(lines) + "\n"


def emit_fabric_cicd(bp: dict, stack: str = "fabric", stages: tuple[str, ...] = _DEFAULT_STAGES,
                     item_types: tuple[str, ...] = _DEFAULT_ITEM_TYPES,
                     lakehouse: str = "analytics_gold") -> dict[str, str]:
    """Return the fabric-cicd artifact set (path → content). Fabric-specific."""
    if stack != "fabric":
        return {}
    doc = [
        "# fabric-cicd content deployment (generated — ADR-0015)", "",
        "Microsoft's official content-deployment library — deploys the source-controlled item",
        "definitions (Notebook/DataPipeline/Lakehouse/SemanticModel/Report) from Git into a target",
        "workspace per environment. Complements the Terraform skeleton adapter (which provisions the",
        "workspaces/domains/RBAC) — Terraform = *skeleton*, fabric-cicd = *content*.", "",
        "```bash",
        "pip install fabric-cicd",
        f"# per stage ({' / '.join(stages)}):",
        "FABRIC_WS_DEV=<guid> python deploy.py dev",
        "```", "",
        "Deploys `publish_all_items` then `unpublish_all_orphan_items` (source is the single source of",
        "truth; orphans in the workspace are removed). `parameter.yml` handles per-environment GUID swaps.",
        "Authentication: a service principal from `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` /",
        "`AZURE_CLIENT_SECRET` (CI secrets, never committed); fabric-cicd requires `token_credential`.",
        "", "**Pin:** `fabric-cicd==1.3.0` (PyPI, measured 2026-09-29) — pin the version and re-validate on",
        "upgrade; **PBIP (Power BI project) deployment is preview**. Prefer **Variable libraries** over find/replace where the item type",
        "supports them. For in-Fabric workspace-to-workspace promotion instead, use Deployment Pipelines.",
    ]
    return {
        "fabric-cicd/deploy.py": emit_deploy_py(stages, item_types),
        "fabric-cicd/parameter.yml": emit_parameter_yml(bp, stages, lakehouse),
        "fabric-cicd/_FABRIC_CICD.md": "\n".join(doc) + "\n",
    }
