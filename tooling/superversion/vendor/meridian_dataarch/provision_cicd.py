"""provision_cicd — emit CI/CD artifacts from an ArchitectureBlueprint.

Second live-provisioning helper (ADR-0015 follow-up), sibling to ``provision_fabric``.
Turns a blueprint into the CI/CD promotion layer that makes a provisioned medallion
*promotable* (dev -> test -> prod), in two honest-by-construction pieces:

1. **CI gate** (``emit_ci_gate``): a real, drop-in GitHub Actions workflow that runs
   the blueprint's own ``derive -> audit`` as a **merge gate** on a
   ``data_architecture.json``. The blueprint CLI already exits non-zero (2) when
   conformance is not green, so a non-conformant architecture change fails the PR.
   Pure reuse of the existing, already-green conformance tool — no new rule silo.
   **Seit R8 (30.09.2026) nicht mehr Teil der Kundenlieferung:** der Workflow ruft unser
   Werkzeug auf und laeuft deshalb nur in einem Repo, das es traegt (Lieferanten-Seite).
   ``emit_cicd`` liefert stattdessen ``gates/gates.yml`` + ``gates/azure-pipelines-gates.yml``
   als PR-Pflicht-Check; die Funktionen bleiben als Vorlage fuer die Lieferanten-Pipeline.

2. **CD promotion** (``emit_cd_promotion``): a ``fab`` script that wires Fabric
   **Git integration** + **Deployment Pipelines** (stages dev/test/prod, one
   workspace per stage) grounded in the documented Fabric REST surface
   (``/deploymentPipelines``, ``/workspaces/{id}/git/connect``), reached via
   ``fab api``. Endpoints/payloads that need tenant-specific IDs are emitted as
   explicit VERIFY templates rather than invented — honest by construction, exactly
   like ``provision_fabric``.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

from core.dataarch_engine.blueprint.provision_gates import (
    emit_gates,
    post_deploy_gate_line,
    pre_deploy_gate_line,
)

_DEFAULT_STAGES = ("dev", "test", "prod")

# Deployment models = the four canonical MS Fabric release-process options (ADR-0050,
# learn.microsoft.com/fabric/cicd/manage-deployment). The chosen model is a first-class
# input (I-19.1): it decides branch structure, merge/approval gates and mechanism.
_DEPLOYMENT_MODELS = {
    "deployment-pipelines": {
        "option": 3, "sot": "Fabric-Workspace (Git nur bis dev)", "branching": "Trunk-based",
        "mechanism": "Deployment-Pipelines-APIs", "approval": "Environments/Release-Manager",
        "script": "promote.sh", "supported": True,
    },
    "git-integration-gitflow": {
        "option": 1, "sot": "Git", "branching": "GitFlow (ein Primär-Branch je Stage)",
        "mechanism": "Fabric Git-APIs (update-from-git)", "approval": "PR-Reviews je Stage-Branch",
        "script": "promote_gitflow.sh", "supported": True,
    },
    "isv-per-customer": {
        "option": 4, "sot": "Git (main)", "branching": "Trunk-based",
        "mechanism": "Items-APIs / fabric-cicd je Kunden-Workspace", "approval": "Environments",
        "script": "deploy_customers.sh", "supported": True,
    },
    "items-api-trunk": {
        "option": 2, "sot": "Git (main)", "branching": "Trunk-based",
        "mechanism": "fabric-cicd / Bulk-Import (Build-Env-Transform)", "approval": "Environments",
        "script": "deploy_items.sh", "supported": True,  # driver + co-emitted fabric-cicd mechanism
    },
}
_DEFAULT_MODEL = "deployment-pipelines"

# D-592 (30.09.2026): der Deploy-Weg folgt der Netzhaltung. Quelle ist die vorhandene
# Entscheidung `PLAT-NET` (Profilfeld `entscheidungen`, dieselbe, die `provision_apply` in
# Schritte uebersetzt) — kein zweites Feld. Inbound-geschuetzt heisst: der Workspace nimmt
# eingehend nur noch freigegebene Netze an. Dann erreichen Deployment Pipelines ihn nicht
# (MS Learn `cicd/cicd-security`: "Deployment pipelines aren't currently supported for workspace
# with inbound access protection"; `security/security-workspace-level-private-links-support`:
# eine Pipeline erreicht keinen Workspace mit „deny public access", und ein zugewiesener
# Workspace laesst sich nicht mehr einschraenken; beide gelesen 30.09.2026).
NETZ_ENTSCHEIDUNG = "PLAT-NET"
#: PLAT-NET-Werte mit Inbound-Schutz auf Workspace-Ebene. `ip_firewall` zaehlt dazu: MS fuehrt
#: die IP-Firewall unter „workspace inbound access protection"
#: (`security/security-workspace-enable-inbound-access-protection`). Dass Deployment Pipelines
#: gerade an der IP-Firewall scheitern, steht dort nicht ausdruecklich — ANNAHME, ungeprueft; die
#: Einordnung ist die vorsichtige. `private_link_tenant` schuetzt den Mandanten, nicht den
#: Workspace; fuer Pipelines nennt die Tenant-Private-Link-Seite keine Grenze.
NETZ_INBOUND_GESCHUETZT: frozenset[str] = frozenset({"private_link_workspace", "ip_firewall"})
#: Deploy-Wege, die den Ziel-Workspace ueber den Pipeline-Dienst erreichen muessen.
_MODELLE_OHNE_INBOUND: frozenset[str] = frozenset({"deployment-pipelines"})
#: Git-basiert nach ADR-0050 (zuerst Option 4/1). Option 1 ist der Einzelkunden-Weg; Option 4
#: faechert auf viele Kunden-Workspaces auf und bleibt die ausdrueckliche Wahl.
MODELL_GESCHUETZT = "git-integration-gitflow"
MODELL_UNGESCHUETZT = _DEFAULT_MODEL


def netzhaltungen(entscheidungen: dict | None) -> set[str]:
    """Alle getroffenen PLAT-NET-Werte, Basis-ID und je Domaene aufgefaecherte IDs.

    Eine Pipeline spannt alle Stufen-Workspaces; ist **einer** geschuetzt, erreicht sie ihn
    nicht. Deshalb zaehlt jede Auffaecherung, nicht nur die Basis-ID."""
    from core.dataarch_engine.blueprint.decision_proposals import FANOUT_TRENNER
    return {str(v) for k, v in (entscheidungen or {}).items()
            if v not in (None, "") and (k == NETZ_ENTSCHEIDUNG
                                        or str(k).startswith(NETZ_ENTSCHEIDUNG + FANOUT_TRENNER))}


def inbound_geschuetzt(entscheidungen: dict | None) -> bool:
    """True, wenn PLAT-NET einen Workspace eingehend abschirmt (D-592)."""
    return bool(netzhaltungen(entscheidungen) & NETZ_INBOUND_GESCHUETZT)


def deployment_model_fuer(entscheidungen: dict | None, explizit: str | None = None) -> str:
    """Der Deploy-Weg aus der Netzhaltung (D-592); ``explizit`` gewinnt, ausser im Konflikt.

    Ohne ausdrueckliche Wahl: geschuetzt → ``git-integration-gitflow``, sonst
    ``deployment-pipelines``. Ausdruecklich Deployment Pipelines bei Inbound-Schutz ist kein
    Vorrang, sondern ein Widerspruch, den erst der Tenant melden wuerde → ``ValueError``."""
    if explizit is not None and explizit not in _DEPLOYMENT_MODELS:
        raise ValueError(f"unknown deployment_model {explizit!r}; "
                         f"choose one of {sorted(_DEPLOYMENT_MODELS)}")
    geschuetzt = inbound_geschuetzt(entscheidungen)
    if explizit is None:
        return MODELL_GESCHUETZT if geschuetzt else MODELL_UNGESCHUETZT
    if geschuetzt and explizit in _MODELLE_OHNE_INBOUND:
        werte = ", ".join(sorted(netzhaltungen(entscheidungen) & NETZ_INBOUND_GESCHUETZT))
        raise ValueError(
            f"deployment_model {explizit!r} widerspricht {NETZ_ENTSCHEIDUNG} = {werte} (D-592): "
            "Deployment Pipelines erreichen keinen Workspace mit Inbound-Schutz, und ein "
            "Workspace in einer Pipeline laesst sich nicht mehr einschraenken (MS Learn "
            "cicd/cicd-security). Git-basiert deployen (--deployment-model "
            f"{MODELL_GESCHUETZT} oder isv-per-customer / items-api-trunk) oder "
            "--deployment-model weglassen, dann folgt der Weg der Netzhaltung.")
    return explizit


def _herleitung(entscheidungen: dict | None, explizit: str | None) -> str:
    """Eine Zeile fuer `_DEPLOYMENT_MODEL.md`: woher das Modell kommt (D-592)."""
    if explizit is not None:
        return "Herkunft: ausdrücklich gewählt (`--deployment-model`)."
    if inbound_geschuetzt(entscheidungen):
        return (f"Herkunft: abgeleitet aus `{NETZ_ENTSCHEIDUNG}` (Inbound-Schutz) nach D-592 — "
                "Deployment Pipelines erreichen geschützte Workspaces nicht, deshalb Git-basiert "
                "(ADR-0050).")
    return (f"Herkunft: abgeleitet aus `{NETZ_ENTSCHEIDUNG}` (kein Inbound-Schutz) nach D-592 — "
            "Deployment Pipelines, weil sie beim Kunden die geringste Git-Reife verlangen.")


def _unique_workspaces(blueprint: dict) -> list[tuple[str, str]]:
    """De-duplicated (name, role) workspace list across all domains, sorted."""
    seen: dict[str, str] = {}
    for d in sorted(blueprint.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", "")):
        for ws in d.get("workspaces", []):
            seen.setdefault(ws["name"], ws.get("role", ""))
    return sorted(seen.items())


def emit_ci_gate(architecture_path: str = "data_architecture.json",
                 stack: str = "fabric", python_version: str = "3.11") -> str:
    """Return a GitHub Actions workflow (YAML) that gates merges on blueprint conformance.

    The workflow derives the blueprint from ``architecture_path`` and runs the
    conformance audit; the CLI exits 2 when a pattern is red, failing the PR. Runs in
    the repo that hosts the engine (or where it is pip-installed) — the gate is part of
    the delivery pipeline, not a customer-runtime dependency (Official-First boundary).
    """
    return f"""# architecture-gate — blueprint conformance as a merge gate (ADR-0015).
# Generated from an ArchitectureBlueprint; runs derive -> audit on {architecture_path}.
# The blueprint CLI exits 2 when any OneLake pattern is red, so a non-conformant
# architecture change fails this check and blocks the merge.
name: architecture-gate
on:
  pull_request:
    paths:
      - "{architecture_path}"
      - "**/{architecture_path}"
  workflow_dispatch: {{}}
jobs:
  conformance:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"
      - name: Install deps
        run: pip install jsonschema
      - name: Derive + audit (blueprint conformance gate)
        run: |
          python -m core.dataarch_engine.blueprint.cli \\
            --architecture "{architecture_path}" --dest _arch_out --stack {stack}
      - name: Upload blueprint artifacts
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: architecture-blueprint
          path: _arch_out
"""


def emit_secret_scan(python_version: str = "3.11") -> str:
    """GitHub-Actions-Workflow: Geheimnis-Scan auf jedem PR (I-21 W5.4 e).

    Der CI/CD-Leitfaden verlangt „never commit credentials“, die Azure-Sicherheitsbaseline (IM-8)
    einen Credential-Scanner auf Code. Erste Wahl bleibt GitHub Secret Scanning mit Push Protection
    in den Repo-Einstellungen; dieser Job ist das Tor für Repos ohne diese Funktion. Werkzeug:
    `detect-secrets` (PyPI, gepinnt 1.5.0, gemessen 29.09.2026) — pip-basiert wie das
    Architektur-Gate, ohne Lizenzschlüssel."""
    return f"""# secret-scan — fail the PR when a credential-like string is committed (I-21 W5.4 e).
# First choice: enable GitHub Secret Scanning + Push Protection in the repository settings.
# This job is the gate for repos without it. To accept a reviewed false positive, create a
# baseline once (`detect-secrets scan > .secrets.baseline`) and review it in the PR.
name: secret-scan
on:
  pull_request: {{}}
  workflow_dispatch: {{}}
jobs:
  detect-secrets:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "{python_version}"
      - name: Install detect-secrets (pinned)
        run: pip install detect-secrets==1.5.0
      - name: Scan working tree
        run: |
          if [ -f .secrets.baseline ]; then
            git ls-files -z | xargs -0 detect-secrets-hook --baseline .secrets.baseline
          else
            detect-secrets scan --all-files > _secrets.json
            python -c "import json,sys; r=json.load(open('_secrets.json'))['results']; print(json.dumps(r, indent=1)); sys.exit(1 if r else 0)"
          fi
"""


def emit_ci_gate_azure(architecture_path: str = "data_architecture.json",
                       stack: str = "fabric", python_version: str = "3.11") -> str:
    """Return the **Azure Pipelines** twin of ``emit_ci_gate`` — same gate, other CI host.

    The Fabric side of CI/CD (Git integration, Deployment Pipelines, ``fabric-cicd``) is already
    provider-agnostic (``git_provider_type = GitHub | AzureDevOps``); only the merge gate itself is
    CI-host-specific, so both are emitted and the customer keeps the one matching their host.
    Same semantics as the GitHub gate: derive → audit, CLI exit 2 on a red pattern fails the PR.
    """
    return f"""# architecture-gate — blueprint conformance as a merge gate (ADR-0015), Azure Pipelines.
# Twin of cicd/architecture-gate.yml (GitHub Actions) — keep whichever matches your CI host.
# The blueprint CLI exits 2 when any OneLake pattern is red, failing this check and blocking the PR.
trigger: none          # PR-only gate; the branch build does not need to re-run it
pr:
  paths:
    include:
      - "{architecture_path}"
pool:
  vmImage: ubuntu-latest
steps:
  - task: UsePythonVersion@0
    displayName: Use Python {python_version}
    inputs:
      versionSpec: "{python_version}"
  - script: pip install jsonschema
    displayName: Install deps
  - script: |
      python -m core.dataarch_engine.blueprint.cli \\
        --architecture "{architecture_path}" --dest _arch_out --stack {stack}
    displayName: Derive + audit (blueprint conformance gate)
  - task: PublishPipelineArtifact@1
    displayName: Publish blueprint artifacts
    condition: always()
    inputs:
      targetPath: _arch_out
      artifact: architecture-blueprint
"""


def emit_cd_promotion(blueprint: dict, stages: tuple[str, ...] = _DEFAULT_STAGES,
                      stage_capacities: dict | None = None,
                      git: dict | None = None) -> str:
    """Return a bash `fab` script wiring Git integration + Deployment Pipelines.

    ``stages`` names the promotion stages (default dev/test/prod). ``stage_capacities``
    maps a stage name -> capacity name (the dev capacity defaults to ``$CAP``).
    ``git`` optionally carries ``{provider, organization, project, repository,
    branch, directory}`` for the workspace<->git connect step. IDs the emitter cannot
    know (workspace GUIDs, pipeline GUIDs) are left as VERIFY placeholders.
    """
    stage_capacities = stage_capacities or {}
    git = git or {}
    workspaces = _unique_workspaces(blueprint)

    lines: list[str] = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "# ArchitectureBlueprint -> Fabric CI/CD promotion (ADR-0015). Generated; review before running.",
        "# Wires Git integration + Deployment Pipelines (dev->test->prod) for each workspace.",
        "# Grounded in the Fabric REST surface (learn.microsoft.com/fabric/cicd):",
        "#   POST /v1/workspaces/{id}/git/connect         — connect a workspace to a git branch",
        "#   POST /v1/deploymentPipelines                 — create a pipeline (stages)",
        "#   POST /v1/deploymentPipelines/{id}/stages/{stageId}/assignWorkspace",
        "#   POST /v1/deploymentPipelines/{id}/deploy     — promote content stage->stage",
        "# reached via `fab api <endpoint> -X POST -i <body.json>` (confirm flags: fab api -h).",
        'CAP="${CAP:-<CAPACITY_NAME>}"',
        "",
        "# Authenticate first (fab >= 1.6 defaults to command-line mode when a command is passed):",
        "#   fab auth login",
        "",
        f"# Promotion stages: {' -> '.join(stages)}",
    ]
    for st in stages:
        cap = stage_capacities.get(st)
        lines.append(f'#   {st}: capacity {cap if cap else ("$CAP" if st == stages[0] else "<" + st + "-capacity>")}')
    lines.append("")

    if not workspaces:
        lines.append("# (no workspaces in blueprint — nothing to promote)")
        lines.append('echo "CD promotion script complete."')
        return "\n".join(lines) + "\n"

    # 1. Git integration for the first-stage (source) workspaces.
    dev = stages[0]
    lines.append(f"# 1. Git integration — connect each {dev}-stage workspace to a git branch")
    if git:
        branch = git.get("branch", f"<{dev}-branch>")
        lines.append(f"#    provider={git.get('provider', '<AzureDevOps|GitHub>')} "
                     f"repo={git.get('repository', '<repo>')} branch={branch} "
                     f"dir={git.get('directory', '/')}")
    else:
        lines.append("#    provide --git {provider,organization,project,repository,branch,directory} to fill the body")
    for name, role in workspaces:
        lines.append(f'# {name} ({role}) — connect + initialize + pull')
        lines.append(f'#   fab api "workspaces/{name}.Workspace/git/connect" -X POST -i <{name}_git.json>   # VERIFY body')
        lines.append(f'#   fab api "workspaces/{name}.Workspace/git/initializeConnection" -X POST')
    lines.append("")

    # 2. One deployment pipeline per workspace, stages assigned.
    lines.append("# 2. Deployment pipeline per workspace (stages assigned; target stages auto-create on first deploy)")
    for name, role in workspaces:
        pipe = f"{name}-dp"
        lines.append(f"# {name} ({role}) -> pipeline '{pipe}'")
        stage_defs = ",".join(f'{{"displayName":"{st}"}}' for st in stages)
        lines.append(f'#   fab api "deploymentPipelines" -X POST -i - <<JSON   # VERIFY: capture the returned id')
        lines.append(f'#   {{"displayName":"{pipe}","stages":[{stage_defs}]}}')
        lines.append("#   JSON")
        lines.append(f'#   fab api "deploymentPipelines/<{pipe}-id>/stages/<{dev}-stage-id>/assignWorkspace" '
                     f'-X POST -i - <<JSON')
        lines.append(f'#   {{"workspaceId":"<{name}-workspace-id>"}}')
        lines.append("#   JSON")
    lines.append("")

    # 3. Promote.
    lines.append(f"# 3. Promote {dev} -> {' -> '.join(stages[1:]) if len(stages) > 1 else '(single stage)'}")
    for name, _role in workspaces:
        pipe = f"{name}-dp"
        for i in range(len(stages) - 1):
            src, dst = stages[i], stages[i + 1]
            lines.append(f'#   fab api "deploymentPipelines/<{pipe}-id>/deploy" -X POST -i - <<JSON   # {src} -> {dst}')
            lines.append(f'#   {{"sourceStageId":"<{src}-stage-id>","targetStageId":"<{dst}-stage-id>"}}')
            lines.append("#   JSON")
    lines.append("")
    lines.append('echo "CD promotion script complete."')
    return "\n".join(lines) + "\n"


def _git_directory(git: dict, workspace: str, n_workspaces: int) -> str:
    """Git-Ordner je Workspace. Mehrere Workspaces auf einem Branch brauchen je einen eigenen
    Ordner (Learn `fundamentals/understand-best-practices-fabric-cicd`, Git folder settings,
    Szenario 2: z. B. `/workspace/staging` und `/workspace/presentation`); derselbe Ordner für alle
    ließe die Workspaces sich gegenseitig überschreiben (I-21 W5.4 a)."""
    if n_workspaces <= 1:
        return git.get("directory", "/")
    base = git.get("directory", "/workspace").rstrip("/")
    return f"{base}/{workspace}"


def emit_gitflow_promotion(blueprint: dict, stages: tuple[str, ...] = _DEFAULT_STAGES,
                           git: dict | None = None) -> str:
    """CD via **Git integration + GitFlow** (MS Option 1): one primary branch per stage,
    promotion by PR between stage branches, deploy by Fabric ``update-from-git`` per workspace.

    Honest by construction: branch names + endpoints are derived; tenant workspace GUIDs and the
    PR/approval step (a human GitFlow action) are VERIFY placeholders, never invented commands.
    """
    git = git or {}
    workspaces = _unique_workspaces(blueprint)
    lines = [
        "#!/usr/bin/env bash", "set -euo pipefail",
        "# ArchitectureBlueprint -> Fabric CD (GitFlow / MS Option 1). Generated; review before running.",
        "# GitFlow: a primary branch per stage; promotion = PR between stage branches (human approval),",
        "# deployment = Fabric Git 'update-from-git' from each stage branch to its workspace.",
        "# Grounded in learn.microsoft.com/fabric/cicd (Git APIs):",
        "#   POST /v1/workspaces/{id}/git/connect          — bind a workspace to a git branch",
        "#   POST /v1/workspaces/{id}/git/updateFromGit    — pull the branch into the workspace",
        "",
        f"# Stage branches (GitFlow): {', '.join(stages)}",
        f"#   provider={git.get('provider', '<GitHub|AzureDevOps>')} repo={git.get('repository', '<repo>')} dir={git.get('directory', '/workspace')}/<workspace> (ein Ordner je Workspace)",
        "",
        "# 1. Bind each stage workspace to its stage branch (once).",
    ]
    for name, role in workspaces:
        for st in stages:
            lines.append(f'#   {name} ({role}) @ {st} → branch "{st}"')
            lines.append(f'#   fab api "workspaces/<{name}-{st}-workspace-id>/git/connect" -X POST -i - <<JSON')
            lines.append(f'#   {{"gitProviderDetails":{{"branchName":"{st}","directoryName":"{_git_directory(git, name, len(workspaces))}"}}}}')
            lines.append("#   JSON")
    lines += ["", "# 2. Promote by PR between stage branches, then update-from-git into the target workspace."]
    for i, st in enumerate(stages):
        if i > 0:
            lines.append(f'#   PR: {stages[i-1]} → {st}  (review + approve — GitFlow gate; do this in GitHub/ADO)')
        for name, _role in workspaces:
            lines.append(f'#   {name} @ {st}: fab api "workspaces/<{name}-{st}-workspace-id>/git/updateFromGit" -X POST '
                         f'-i - <<JSON')
            lines.append('#   {"remoteCommitHash":"<head-of-branch>","conflictResolution":'
                         '{"conflictResolutionType":"Workspace","conflictResolutionPolicy":"PreferRemote"}}')
            lines.append("#   JSON")
    lines += ["", 'echo "GitFlow promotion script complete."']
    return "\n".join(lines) + "\n"


def emit_isv_release(blueprint: dict, git: dict | None = None) -> str:
    """CD for the **ISV / per-customer** model (MS Option 4): one ``main`` as source of truth,
    deployed per customer workspace via ``fabric-cicd`` (Items APIs), trunk-based.

    Emits a fabric-cicd driver that loops customers from a local manifest (customers.example.json).
    Customer workspace GUIDs + per-customer parameters live in that manifest, never in the repo.
    """
    git = git or {}
    return f'''#!/usr/bin/env python3
"""ArchitectureBlueprint -> Fabric CD (ISV / per-customer, MS Option 4). Generated.

Trunk-based: `main` is the single source of truth; each customer gets the same item set deployed
to their own workspace via fabric-cicd (Microsoft-supported). Approval = per-environment gates in
GitHub/ADO. Customer workspace ids + per-customer parameters come from customers.json (local, not
committed — like connections/governance maps).
"""
import json
import os
from pathlib import Path

# fabric-cicd is the MS-supported deploy library (Official-First). pip install fabric-cicd==1.3.0
from azure.identity import ClientSecretCredential
from fabric_cicd import FabricWorkspace, publish_all_items

REPO_DIR = "."                      # item definitions live in the repo (main)
CUSTOMERS = json.loads(Path("customers.json").read_text(encoding="utf-8"))["customers"]
# Service principal from the environment (CI secrets, never committed).
CREDENTIAL = ClientSecretCredential(
    tenant_id=os.environ["AZURE_TENANT_ID"],
    client_id=os.environ["AZURE_CLIENT_ID"],
    client_secret=os.environ["AZURE_CLIENT_SECRET"],
)

for c in CUSTOMERS:                 # e.g. {{"name":..., "workspace_id":..., "environment":"prod"}}
    print(f"deploying to {{c['name']}} ({{c['workspace_id']}})")
    ws = FabricWorkspace(
        workspace_id=c["workspace_id"],
        environment=c.get("environment", "prod"),   # picks the value-set in parameter.yml
        repository_directory=REPO_DIR,
        token_credential=CREDENTIAL,                # required by fabric-cicd
    )
    publish_all_items(ws)           # add unpublish_all_orphan_items(ws) if you prune per customer
print("ISV per-customer release complete.")
'''


def emit_items_release(stages: tuple[str, ...] = _DEFAULT_STAGES) -> str:
    """CD driver for the **Items-API / Trunk** model (MS Option 2): trunk-based; ``main`` is the
    single source of truth and ``fabric-cicd`` deploys the item definitions per environment.

    Thin by design: the deploy **mechanism** is the co-emitted ``fabric-cicd/deploy.py`` (Tool-Reuse,
    Official-First); this driver only loops the stages and calls ``deploy.py <environment>``. Workspace
    GUIDs come from ``FABRIC_WS_<STAGE>`` env vars (never the repo).
    """
    lines = [
        "#!/usr/bin/env bash",
        "set -euo pipefail",
        "# ArchitectureBlueprint -> Fabric CD (Items-API / Trunk, MS Option 2). Generated; review before running.",
        "# Trunk-based: `main` = SoT; fabric-cicd deployt die Item-Definitionen je Environment.",
        "# Mechanik = ../fabric-cicd/deploy.py (co-emittiert). Workspace-GUIDs via FABRIC_WS_<STAGE> (env, nie Repo).",
        'HERE="$(cd "$(dirname "$0")" && pwd)"',
        'DEPLOY="$HERE/../fabric-cicd/deploy.py"',
        "",
        f"# Promotion stages: {' -> '.join(stages)}",
    ]
    for st in stages:
        var = f"FABRIC_WS_{st.upper()}"
        lines.append(f'echo "deploying items to {st}"')
        lines.append(f'{var}="${{{var}:-<{st}-workspace-id>}}" python "$DEPLOY" {st}   # VERIFY: {st} workspace GUID')
    lines += ["", 'echo "Items-API trunk release complete."']
    return "\n".join(lines) + "\n"


def _deployment_model_doc(model: str, blueprint: dict, stages: tuple[str, ...],
                          herkunft: str = "") -> str:
    m = _DEPLOYMENT_MODELS[model]
    n_ws = len(_unique_workspaces(blueprint))
    lines = [
        "# Deployment-Modell (generiert — ADR-0050 / I-19.1)", "",
        f"Gewähltes Modell: **{model}** (MS Fabric CI/CD Option {m['option']}).", "",
        *([herkunft, ""] if herkunft else []),
        "| Achse | Wert |", "|---|---|",
        f"| Source of Truth | {m['sot']} |",
        f"| Merge-/Branching-Ansatz | {m['branching']} |",
        f"| Deployment-Mechanismus | {m['mechanism']} |",
        f"| Approval-Gate | {m['approval']} |",
        f"| Stages | {' → '.join(stages)} |",
        f"| Workspaces im Blueprint | {n_ws} |", "",
        "Belegt: learn.microsoft.com/fabric/cicd/manage-deployment (Choose the best workflow option).", "",
        "## Wo die Validierungs-Gates sitzen (I-19.3 verdrahtet sie)",
        "- **PR-Gate (CI):** `gates/gates.yml` bzw. `gates/azure-pipelines-gates.yml` (`validate.sh pr` "
        "+ eigene Prüfungen in `validate.local.sh`) → blockt Merge. Blueprint-Konformität und die "
        "übrigen Artefakt-Prüfungen laufen beim Lieferanten vor der Übergabe; eine Änderung an "
        "`data_architecture.json` wird dort neu erzeugt und geprüft (`CONFORMANCE.md`).",
        "- **Pre-Deploy:** vor `update-from-git`/`fabric-cicd`/Deployment-Pipeline.",
        "- **Post-Deploy:** Smoke (Modell lädt, Refresh, Lineage-Reconcile) vor der nächsten Stage.",
        "- **Refresh nach dem Deploy:** *Refresh data only* — das Schema kommt aus Git, nicht aus "
        "einem Schema-Sync im Ziel; *Sync schema only* nur im Entwicklungs-Workspace mit "
        "anschließendem Commit (Tabelle in `operability/BETRIEBSBEREITSCHAFT.md`, I-21 W6.7).", "",
    ]
    if model == "git-integration-gitflow":
        lines += ["## GitFlow", f"Je Stage ein Primär-Branch ({', '.join(stages)}); Promotion = PR zwischen "
                  "Stage-Branches (Review = Approval); Deployment = `promote_gitflow.sh` (update-from-git)."]
    elif model == "isv-per-customer":
        lines += ["## ISV / per-Customer", "Ein `main` als SoT; `deploy_customers.sh` (fabric-cicd) deployt je "
                  "Kunden-Workspace aus `customers.json` (lokal, nicht committet). Approval = Environments."]
    elif model == "deployment-pipelines":
        lines += ["## Deployment-Pipelines", "Git nur bis `dev`; Promotion dev→test→prod über Fabric "
                  "Deployment-Pipelines (`promote.sh`). Low-code, Fabric-nativ."]
    else:  # items-api-trunk
        lines += ["## Items-API / Trunk", "Ein `main` als SoT; `deploy_items.sh` loopt die Stages und ruft "
                  "die **co-emittierte** `fabric-cicd/deploy.py` (`python deploy.py <env>`; Workspace-GUIDs "
                  "via `FABRIC_WS_<STAGE>`). Build-Env-Transform über `fabric-cicd/parameter.yml`. Approval = "
                  "Environments. Mechanik = Tool-Reuse aus `--emit-fabric-cicd`, gleiche `fabric-cicd/`-Location."]
    lines += ["", *_ZEITPLAN_ABSCHNITT, "", *_QUOTE_ABSCHNITT]
    return "\n".join(lines) + "\n"


#: I-21 W5.4 f — Befund 29.09.2026, als Abschnitt im Modell-Dokument, weil er je Stage wirkt.
_ZEITPLAN_ABSCHNITT = (
    "## Zeitpläne: per REST je Stage, nicht als `.schedules` im Item",
    "Learn (`fundamentals/understand-best-practices-fabric-cicd`, gelesen 29.09.2026) empfiehlt, "
    "Zeitpläne als `.schedules`-Datei in die Item-Definition von Notebooks und Pipelines zu legen. "
    "Das Format dieser Datei ist auf Learn nicht beschrieben (nur ein Bildschirmfoto; Suche am "
    "29.09.2026 ohne Definitionsseite). Diese Lieferung legt Zeitpläne deshalb weiter per REST an "
    "(`orchestration/schedule.json`, `POST …/jobs/{jobType}/schedules`) — **je Stage einmal**, "
    "denn ein REST-Zeitplan wandert mit keinem Deployment mit. Umgekehrt würde ein `.schedules` "
    "im Item in jede Stage mitwandern, auch nach `dev`. Umstieg erst, wenn das Format dokumentiert ist.",
)

#: I-21 W2.8 a — Unified Quota je Identität (Learn `rest/api/fabric/articles/throttling`, 29.09.2026).
_QUOTE_ABSCHNITT = (
    "## API-Quote je Identität",
    "Fabric drosselt REST-Aufrufe je Identität (Benutzer, Service Principal, Managed Identity): "
    "500 Aufrufe/min Platform-APIs, 200/min Job Scheduler, 500/min Long-Running Operations, "
    "festes 60-s-Fenster ohne anteilige Erholung. Ein Deploy-SPN, der auch Monitoring und Agenten "
    "bedient, teilt sich eine Quote mit ihnen. Empfehlung: je Zweck ein eigener SPN (Deploy, "
    "Monitoring, Agenten). Ein 429 trägt `errorCode`: `RequestBlocked` → `Retry-After` abwarten; "
    "`CapacityLimitExceeded` → exponentiell zurückweichen und die Kapazität prüfen, sofort "
    "wiederholen hilft nicht.",
)


# --- Rücksprung einer einzelnen Beförderung (BK-C05, 20.08.2026) -------------------------
#
# Der Kanon belegte diesen Punkt bis 20.08.2026 mit ``platform/platform_down.sh``. Das ist der
# **Rückbau der ganzen Plattform** — es löscht, was der Apply-Plan aufgebaut hat. Der Fall, den
# der Betrieb wirklich hat, ist der kleine: eine Beförderung ist in einer Stage gelandet und muss
# wieder weg, während die Plattform steht.
#
# Der Rückweg ist modellabhängig, weil der Hinweg es ist: wer über Deployment-Pipelines befördert,
# springt anders zurück als wer per ``update-from-git`` je Stage-Branch deployt. Deshalb steht der
# Text hier neben ``_DEPLOYMENT_MODELS`` und nicht in einem eigenen Modul.
#
# Der Datenabgleich hängt am Zugriffsmodus der Quelle (``ingestion[*].access_mode``) und nicht am
# Deployment-Modell — die drei Modi verlieren beim Rücksprung Unterschiedliches, und genau das
# steht in der Tabelle. Eine allgemeine Checkliste hätte für ``shortcut`` dieselbe Zeile wie für
# ``copy``, obwohl bei ``shortcut`` gar keine Kopie in Fabric liegt, die auseinanderlaufen könnte.

_RUECKSPRUNG_SCHRITTE = {
    "deployment-pipelines": [
        "Auf dem `{dev}`-Branch die Änderung zurücknehmen (`git revert` auf den Commit der "
        "fehlerhaften Beförderung), über einen Pull Request. Der Rückweg ist eine Änderung wie "
        "jede andere und geht denselben Weg.",
        "`{dev}`-Workspace aus Git aktualisieren (`update-from-git`), damit die Quelle der "
        "Beförderung wieder den alten Stand trägt.",
        "`bash cicd/promote.sh` erneut fahren: {kette}. Die Pipeline befördert vorwärts, auch "
        "wenn der Inhalt der alte ist — rückwärts befördern ist nicht der Weg.",
    ],
    "git-integration-gitflow": [
        "Auf dem Stage-Branch der betroffenen Stage die Änderung zurücknehmen "
        "(`git revert` auf den Commit der fehlerhaften Beförderung), über einen Pull Request — "
        "die Review ist hier das Approval.",
        "`bash cicd/promote_gitflow.sh` für diese Stage fahren; `update-from-git` zieht den "
        "zurückgenommenen Stand in den Workspace.",
        "Den Revert in die weiteren Stage-Branches nachziehen ({kette}), sonst holt die nächste "
        "reguläre Beförderung den Fehler zurück.",
    ],
    "isv-per-customer": [
        "Auf `main` die Änderung zurücknehmen (`git revert` auf den Commit der fehlerhaften "
        "Beförderung), über einen Pull Request.",
        "`python cicd/deploy_customers.sh` **nur für die betroffenen Kunden-Workspaces** fahren. "
        "Die Kundenliste steht lokal in `cicd/customers.json`; wer sie ungefiltert fährt, "
        "deployt in Mandanten, die den Fehler nie gesehen haben.",
        "Für jeden nicht zurückgesetzten Kunden-Workspace festhalten, dass er den alten Stand "
        "noch trägt — sonst zeigt die Flotte zwei Stände und niemand weiß, welcher wo gilt.",
    ],
    "items-api-trunk": [
        "Auf `main` die Änderung zurücknehmen (`git revert` auf den Commit der fehlerhaften "
        "Beförderung), über einen Pull Request.",
        "`bash cicd/deploy_items.sh` für die betroffene Stage fahren; `fabric-cicd` schreibt die "
        "Item-Definitionen des zurückgenommenen Standes.",
        "Die Build-Env-Transformation (`fabric-cicd/parameter.yml`) mitprüfen: sie ist Teil des "
        "Standes und kann die eigentliche Ursache sein, auch wenn die Item-Definition unauffällig "
        "aussieht.",
    ],
}

_ABGLEICH_JE_MODUS = {
    "shortcut": ("In Fabric liegt keine Kopie. Zu prüfen ist der Shortcut-Pfad selbst: zeigt er "
                 "nach dem Rücksprung wieder auf das Ziel, das der alte Stand erwartet? Und "
                 "trägt die Quelle inzwischen ein Schema, das der alte Stand nicht liest?"),
    "mirror": ("Die Spiegelung läuft als eigener Dienst weiter. Zu prüfen ist, ob sie nach dem "
               "Rücksprung noch läuft und wie weit sie hinterher ist — nicht ein Zeilenvergleich "
               "gegen eine Sicherung, die es hier nicht gibt."),
    "copy": ("Hier ist der Rücksprung wirklich gefährlich: die Pipeline hat Zeilen geschrieben, "
             "und der Wasserstand ist mitgewandert. Fährt der alte Stand danach los, liest er ab "
             "dem neuen Wasserstand und überspringt still, was dazwischen liegt. Wasserstand auf "
             "den Zeitpunkt vor der Beförderung zurücksetzen und den Lauf einmal beobachten."),
}


def _ruecksprung_doc(model: str, blueprint: dict, stages: tuple[str, ...]) -> str:
    """Return ``cicd/_RUECKSPRUNG.md`` — der Rückweg einer einzelnen Beförderung (BK-C05).

    Aus dem Bauplan abgeleitet und nicht frei geschrieben: die Abgleich-Zeilen kommen aus
    ``ingestion`` (je Quelle ihr ``access_mode``), die Freigabe-Zeilen aus
    ``mesh.domains[*].data_products``. Ohne Bauplan bleiben beide Tabellen leer und sagen das.
    """
    m = _DEPLOYMENT_MODELS[model]
    bp = blueprint or {}
    strecken = [i for i in (bp.get("ingestion") or []) if i.get("source")]
    produkte = [(d.get("name", ""), pname)
                for d in ((bp.get("mesh") or {}).get("domains") or [])
                for pname in (d.get("data_products") or [])]
    dev = stages[0]
    kette = " → ".join(stages)

    z = [
        "# Rücksprung einer Beförderung (generiert — BK-C05)", "",
        "Der Rückbau der ganzen Plattform steht in `platform/platform_down.sh`. Hier geht es um "
        "den kleinen Fall, den der Betrieb wirklich hat: eine Beförderung ist in einer Stage "
        "gelandet, richtet Schaden an und muss wieder weg, während die Plattform steht.", "",
        "## Der Rückweg führt über Git", "",
        "Fabric kennt keinen Ein-Klick-Rücksprung. Der Weg zurück heißt „aus Git erneut "
        "bereitstellen\" und nicht „zurückdeployen\". Drei Eigenschaften der "
        "Bereitstellungskette prägen ihn:", "",
        "| Eigenschaft | Folge für den Rücksprung |", "|---|---|",
        "| Eine Bereitstellung kopiert **Definitionen, keine Daten** | Der Rücksprung dreht den "
        "Code zurück und die Daten nicht. Der Abgleich unten ist deshalb ein eigener Schritt und "
        "kein Nebeneffekt. |",
        "| Selektives Bereitstellen trägt **Löschungen nicht** weiter | Was die fehlerhafte "
        "Fassung angelegt hat, steht nach dem Rücksprung noch da. Es muss von Hand weg, sonst "
        "bleibt ein Element ohne Entsprechung in Git zurück. |",
        "| Es gibt **keine Vergleichs-API** | Wer wissen will, was zwischen zwei Stufen "
        "auseinandersteht, stellt die Item-Definitionen selbst gegeneinander. Kein Aufruf sagt "
        "es einem. |", "",
        "Belegt: MS Learn, Fabric CI/CD (`deployment-pipelines-authoring-cli`, gelesen "
        "16.08.2026) — keine Compare-API, Bereitstellungsregeln nur über die Oberfläche, höchstens "
        "300 Elemente je Bereitstellung. Bei mehr als 300 betroffenen Elementen zerfällt auch der "
        "Rücksprung in mehrere Bereitstellungen.", "",
        f"## Die Schritte (Modell: {model})", "",
        f"Source of Truth: {m['sot']}. Mechanismus: {m['mechanism']}. Stages: {kette}.", "",
    ]
    for nr, schritt in enumerate(_RUECKSPRUNG_SCHRITTE[model], start=1):
        z.append(f"{nr}. " + schritt.format(dev=dev, kette=kette))
    z += [
        f"{len(_RUECKSPRUNG_SCHRITTE[model]) + 1}. Die Elemente löschen, die die fehlerhafte "
        "Fassung angelegt hat und die Git nicht mehr kennt. Diesen Schritt nimmt niemand ab; er "
        "ist die zweite Zeile der Tabelle oben.",
        f"{len(_RUECKSPRUNG_SCHRITTE[model]) + 2}. `bash gates/validate.sh post-deploy` fahren. "
        "Der Rückweg ist eine Bereitstellung und bekommt dieselben Gates wie der Hinweg — ein "
        "Rücksprung, der ungeprüft durchgeht, ist die zweite Änderung ohne Gate.", "",
        "## Der Datenabgleich", "",
        "Der Code ist nach den Schritten oben zurück. Die Daten sind es nicht. Was zu prüfen ist, "
        "hängt am Zugriffsmodus der Quelle und nicht am Deployment-Modell.", "",
        "| Ladestrecke | Modus | Was nach dem Rücksprung zu prüfen ist | geprüft am | von |",
        "|---|---|---|---|---|",
    ]
    if strecken:
        for i in strecken:
            modus = i.get("access_mode", "copy")
            hinweis = _ABGLEICH_JE_MODUS.get(modus, _ABGLEICH_JE_MODUS["copy"])
            z.append(f"| `{i['source']}` | {modus} | {hinweis} |  |  |")
    else:
        z.append("| _keine Ladestrecke im Bauplan_ |  |  |  |  |")
    z += [
        "", "Für jedes Gold-Produkt kommt eine zweite Frage dazu: hat es seit der fehlerhaften "
        "Beförderung aktualisiert? Ein Bericht, der auf Zahlen aus der falschen Fassung steht, "
        "sieht nach dem Rücksprung unverändert aus, bis er das nächste Mal lädt.", "",
        "| Gold-Produkt | Domäne | letzte Aktualisierung | vor oder nach der Beförderung | "
        "erneut geladen am |", "|---|---|---|---|---|",
    ]
    if produkte:
        for dom, prod in produkte:
            z.append(f"| `{prod}` | {dom} |  |  |  |")
    else:
        z.append("| _kein Gold-Produkt im Bauplan_ |  |  |  |")
    z += [
        "", "## Die Übung vor der Übergabe", "",
        "Einmal, bevor die Plattform übergeben wird, und mit einer harmlosen Änderung — eine "
        "Beschreibung an einem Element genügt. Geübt wird der ganze Weg: befördern, Rücksprung, "
        "Abgleich. Wer den Rücksprung zum ersten Mal im Ernstfall geht, misst dabei, wie lange "
        "er dauert.", "",
        f"In welcher Stage geübt wird, entscheidet der Kunde. Eine Übung in `{dev}` ist "
        f"risikolos und misst den Weg nicht, der zählt; eine Übung in `{stages[-1]}` misst ihn "
        "und braucht ein Zeitfenster. Wir tragen den Wert deshalb nicht vor.", "",
        "| Was | Wert |", "|---|---|",
        "| geübt am |  |", "| von |  |", "| geübte Änderung |  |",
        "| Stage, in der geübt wurde |  |",
        "| Dauer vom Entschluss bis zum alten Stand |  |",
        "| Was nicht von selbst zurückkam |  |", "",
        "Die letzte Zeile ist die wichtigste. Sie ist der Grund für die Übung: alles andere steht "
        "schon oben in diesem Dokument.", "",
    ]
    return "\n".join(z) + "\n"


# --- Branch-Regel für den Integrations-Branch (I-21 W5.4 d, 29.09.2026) --------------------
#
# Learn `fundamentals/understand-best-practices-fabric-cicd` (gelesen 29.09.2026): eine Quelle
# der Wahrheit im Integrations-Branch, Änderungen nur per Pull Request. Ohne Regel kann jeder mit
# Schreibrecht direkt auf den Branch schieben, und die beiden Tore (PR-Gates, Geheimnis-Scan)
# laufen nur, wenn jemand freiwillig einen PR aufmacht.
#
# Form: GitHub-Repository-Ruleset (REST `POST /repos/{owner}/{repo}/rulesets`). Feldnamen und
# Pflichtfelder gemessen am 29.09.2026 gegen die OpenAPI-Beschreibung
# `github/rest-api-description` (api.github.com.json, info.version 1.1.4): `pull_request` verlangt
# die fünf Parameter unten, `required_status_checks` verlangt `required_status_checks` und
# `strict_required_status_checks_policy`, eine Prüfung verlangt `context`.

#: Die Job-Namen der beiden mitgelieferten Tore. Ein GitHub-Check trägt den Job-Namen als
#: Kontext; ändert jemand den Job-Namen, läuft die Regel ins Leere — daher hier als Feld.
#: Bis 30.09.2026 stand hier `conformance` (Job aus `architecture-gate.yml`): der rief in der
#: Kunden-CI unser Werkzeug auf, war ohne es immer rot und hätte so jeden PR blockiert (R8).
#: `gates` ist der Job aus `gates/gates.yml`.
RULESET_STATUS_CHECKS = ("gates", "detect-secrets")


def _integration_branches(deployment_model: str, stages: tuple[str, ...], git: dict) -> list[str]:
    """Die geschützten Branches: bei GitFlow ein Primär-Branch je Stage, sonst der eine
    Integrations-Branch (``git.branch``, Vorgabe ``main``)."""
    if deployment_model == "git-integration-gitflow":
        return list(stages)
    return [git.get("branch") or "main"]


def emit_branch_ruleset(deployment_model: str = _DEFAULT_MODEL,
                        stages: tuple[str, ...] = _DEFAULT_STAGES, git: dict | None = None,
                        approvals: int = 1) -> str:
    """GitHub-Ruleset (JSON): nur PR in den Integrations-Branch, Tore als Pflicht-Checks."""
    import json
    branches = _integration_branches(deployment_model, stages, git or {})
    ruleset = {
        "name": "integration-branch-pr-only",
        "target": "branch",
        "enforcement": "active",
        "conditions": {"ref_name": {"include": [f"refs/heads/{b}" for b in branches],
                                    "exclude": []}},
        "rules": [
            {"type": "deletion"},
            {"type": "non_fast_forward"},
            {"type": "pull_request", "parameters": {
                "dismiss_stale_reviews_on_push": True,
                "require_code_owner_review": False,
                "require_last_push_approval": True,
                "required_approving_review_count": approvals,
                "required_review_thread_resolution": True}},
            {"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [{"context": c} for c in RULESET_STATUS_CHECKS]}},
        ],
    }
    return json.dumps(ruleset, indent=2, ensure_ascii=False) + "\n"


def _branch_rule_doc(deployment_model: str, stages: tuple[str, ...], git: dict) -> str:
    branches = _integration_branches(deployment_model, stages, git)
    liste = ", ".join(f"`{b}`" for b in branches)
    return "\n".join([
        "# Branch-Regel für den Integrations-Branch (generiert — I-21 W5.4 d)", "",
        f"Geschützt: {liste} (Modell `{deployment_model}`). Änderungen kommen nur per Pull Request "
        "hinein; direktes Schieben, Force-Push und Löschen sind gesperrt. Pflicht-Checks sind die "
        "beiden mitgelieferten Tore: "
        + ", ".join(f"`{c}`" for c in RULESET_STATUS_CHECKS) + ".", "",
        "Beleg: Learn `fundamentals/understand-best-practices-fabric-cicd` (gelesen 29.09.2026) — "
        "Quelle der Wahrheit im Integrations-Branch, Beiträge über Pull Requests.", "",
        "## GitHub", "",
        "```bash",
        'gh api "repos/{owner}/{repo}/rulesets" -X POST --input cicd/branch-ruleset.json   '
        "# gh setzt owner/repo aus dem aktuellen Repo",
        "```", "",
        "Die Check-Namen sind die Job-Namen aus `gates/gates.yml` und `secret-scan.yml`. Wer "
        "einen Job umbenennt, muss die Regel mitziehen — sonst wartet jeder PR auf einen Check, der "
        "nie kommt.", "",
        "## Azure DevOps", "",
        "Branch policies je geschütztem Branch (Learn `azure/devops/repos/git/branch-policies`, "
        "gelesen 29.09.2026). Zwei Werte setzt, wer die Regel anlegt, als Umgebungsvariable: "
        "`ADO_REPO_ID` (aus `az repos list`) und `ADO_GATE_PIPELINE_ID` (Build-Definition, die "
        "`gates/azure-pipelines-gates.yml` fährt, aus `az pipelines list`).", "",
        "```bash",
        *[line for b in branches for line in (
            f"az repos policy approver-count create --branch {b} --repository-id \"$ADO_REPO_ID\" "
            "--minimum-approver-count 1 --creator-vote-counts false --allow-downvotes false "
            "--reset-on-source-push true --blocking true --enabled true",
            f"az repos policy build create --branch {b} --repository-id \"$ADO_REPO_ID\" "
            "--build-definition-id \"$ADO_GATE_PIPELINE_ID\" --display-name validation-gates "
            "--manual-queue-only false --queue-on-source-update-only true --valid-duration 0 "
            "--blocking true --enabled true")],
        "```", "",
    ]) + "\n"


# --- Branch workspaces (I-21 W2.7 b + W2.8 c) -------------------------------------------------

def _branch_workspaces_doc(blueprint: dict) -> str:
    """Runbook: Branch-Workspace-Admin-Profil, Selective Branching, Änderungen vergleichen.

    Portal-Einstellung, keine öffentliche API dafür gefunden (Learn gelesen 29.09.2026) — daher
    Runbook statt Aufruf."""
    ws = [n for n, r in _unique_workspaces(blueprint) if r != "reporting"]
    quelle = f"`{ws[0]}`" if ws else "der Entwicklungs-Workspace"
    return "\n".join([
        "# Branch-Workspaces für Entwickler (generiert — I-21 W2.7 b, W2.8 c)", "",
        "Entwickler zweigen aus dem Entwicklungs-Workspace einen eigenen Feature-Workspace ab, ohne "
        "selbst Workspaces anlegen oder Kapazität zuweisen zu dürfen. Das trägt das "
        "**Branch workspace admin profile (Preview)**.", "",
        "Beleg: Learn `cicd/git-integration/branch-workspace-admin-profile` und "
        "`cicd/git-integration/branched-workspace` (gelesen 29.09.2026).", "",
        f"## Admin-Profil einrichten (einmal, auf {quelle})", "",
        "Workspace settings → Git integration → Branch workspaces → **Allow branch workspace admin "
        "profile** an.", "",
        "| Feld | Vorgabe dieser Lieferung | Warum |", "|---|---|---|",
        "| Role assignment | Contributor | kleinste Rolle, die Items anlegen kann |",
        "| Admins | eine **Sicherheitsgruppe**, keine Person | bei Contributor ist mindestens ein "
        "Admin Pflicht; eine Person verlässt irgendwann den Tenant und macht das Profil ungültig |",
        "| Capacity | eigene Entwicklungs-Kapazität, nicht die Produktions-Kapazität | Feature-Arbeit "
        "soll die Produktion nicht drosseln |",
        "| Contributor darf Branch wechseln | aus | Branch-Wechsel überschreibt alle Items des "
        "Workspaces |", "",
        "## Die Identität, unter der alles läuft", "",
        "Der Workspace-Admin, der das Profil **zuletzt speichert**, wird zur *consented identity*: "
        "jedes spätere Abzweigen legt Workspaces unter seiner Identität an, weist Kapazität zu und "
        "verbindet Git. Speichert ein anderer Admin, wechselt die Identität still mit. Deshalb "
        "speichert das Profil nur ein benannter Betriebs-Admin, und jede Änderung wird "
        "protokolliert:", "",
        "| gespeichert am | von (consented identity) | Anlass |", "|---|---|---|",
        "|  |  |  |", "",
        "## Was das Profil ungültig macht", "",
        "- Kapazität und Git-Repository liegen in verschiedenen Regionen, und der Tenant-Schalter "
        "gegen regionsübergreifende Operationen ist an.",
        "- Die consented identity verliert ein Recht, die Kapazität wird pausiert, oder ein Admin "
        "aus der Liste verlässt den Tenant. Das Profil ist dann bis zur Reparatur nicht nutzbar.",
        "- Auf einem Branch-Workspace selbst lässt sich kein Profil anlegen.", "",
        "## Abzweigen, vergleichen, zurückführen", "",
        "- **Selective Branching:** „Select items individually“ zweigt nur die benötigten Items ab. "
        "Abhängigkeiten müssen mit („select related items“), sonst scheitert das Abzweigen. Ein "
        "späterer Branch-Wechsel setzt die Auswahl zurück und holt alle Items.",
        "- **Änderungen vergleichen:** Source control → Changes bzw. Updates → Review changes "
        "zeigt den Unterschied seit dem letzten Sync, vor Commit und vor Update. File-level "
        "Commit ist laut Learn Preview.",
        "- **Related branches:** der Reiter zeigt Branch-Workspace und Quell-Workspace zueinander.",
        "- Zurück in den Integrations-Branch geht es nur per Pull Request (`_BRANCH_RULE.md`).", "",
        "## Abzweigen per API statt Portal (I-21 W6.6, Preview)", "",
        "Für wiederholbares Abzweigen (z. B. je Ticket ein Feature-Workspace) ersetzt eine "
        "Automatisierung den Portal-Knopf *Branch out*. Learn nennt dafür die Reihenfolge: erst "
        "Workspace vorbereiten, Git-Branch anlegen und die Git-Verbindung des Workspaces "
        "einrichten, **danach** die Beziehung setzen (Learn `cicd/git-integration/"
        "branched-workspace` und REST `core/git/create-workspace-relation`, gelesen 29.09.2026).", "",
        "| Schritt | Aufruf | Beleg |", "|---|---|---|",
        "| 1 | Workspace anlegen, Kapazität zuweisen | Fabric REST Core (Workspaces) |",
        "| 2 | Branch im Git-Provider anlegen (vom Branch des Quell-Workspaces) | Git-Provider |",
        "| 3 | `POST /v1/workspaces/{branchId}/git/connect`, dann `…/git/initializeConnection` | "
        "wie das CI/CD-Setup-Skript dieser Lieferung |",
        "| 4 | `POST /v1/workspaces/{branchId}/git/workspaceRelations` mit "
        "`{\"relatedWorkspaceId\": \"{baseWorkspaceId}\", \"relationType\": \"Base\"}` → 201 | "
        "REST `create-workspace-relation` (Preview) |", "",
        "- **Rechte:** Admin auf dem Branch-Workspace, mindestens Contributor auf dem "
        "Quell-Workspace; Scope `Workspace.ReadWrite.All`. Service Principal und Managed Identity "
        "werden unterstützt — die Automatisierung läuft unter dem Deploy-SPN, nicht unter einer "
        "Person (gleiche Begründung wie beim Admin-Profil).",
        "- **Fehlercodes, die die Automatisierung auswerten muss:** "
        "`WorkspaceRelationRootDirectoryMismatch` (nicht dasselbe Repository-Stammverzeichnis — "
        "Schritt 3 prüfen), `WorkspaceRelationBaseIsBranch` (Quelle ist selbst ein Branch), "
        "`WorkspaceRelationTargetHasBranches`, `WorkspaceRelationAlreadyExists`; 429 mit "
        "`Retry-After`.",
        "- **Was die API nicht ersetzt:** Selective Branching und das Admin-Profil bleiben "
        "Portal-Schritte; die Beziehung verschwindet, sobald der Branch-Workspace von Git getrennt "
        "oder der Quell-Workspace gelöscht wird.",
        "- Die API ist laut Learn Preview („not recommended for production use“) — für "
        "Entwickler-Workspaces vertretbar, nicht für die Stufen dev/test/prod.", "",
        "**Status UNKLAR:** Learn führt Branched Workspaces, Selective Branching und Compare im "
        "What's-new-Archiv als Preview (März 2026), die FabCon-Folie vom 29.09.2026 als GA. "
        "Nachprüfung 05.10.2026.", "",
    ]) + "\n"


# --- Deployment plan (I-21 W2.7 a, Preview) -------------------------------------------------
#
# Belegt, Learn gelesen 29.09.2026: `cicd/deployment-plan/deployment-plan-overview`,
# `…/deployment-plan-sample-plans` (plan.yml-Struktur), `…/deployment-plan-actions`,
# `…/deployment-plan-automation`. Der Plan ist ein Workspace-Item; in Git liegt er als
# `plan.yml` im Item-Ordner. Eine Gruppe deployt genau ein Item; Reihenfolge nur über
# `dependsOn`; Aktionen (Notebook, Pipeline, Dataflow Gen2, Copy job, UDF; Job-Typ `Execute`)
# laufen vor oder nach dem Item. Eine Aktion kann nur ein Item fahren, das im Ziel schon steht —
# darum deployt die erste Gruppe das Gate-Notebook selbst (Muster „Validate before anything
# deploys“).

DEPLOYMENT_PLAN_SCHEMA = ("https://developer.microsoft.com/json-schemas/fabric/item/"
                          "deploymentPlan/definition/plan/1.0.0/schema.json")
#: Dokumentierte Grenze (deployment-plan-overview, „Deployment plan size limits“).
DEPLOYMENT_PLAN_MAX_NAME = 60
#: Workspace-Rolle → Gruppen in Deploy-Reihenfolge (Schlüssel, Item-Typ).
_PLAN_GROUPS_BY_ROLE = {
    "bronze": (("Bronze_Lakehouse", "Lakehouse"),),
    "silver": (("Silver_Lakehouse", "Lakehouse"),),
    "gold": (("Gold_Lakehouse", "Lakehouse"),),
    "mixed": (("Bronze_Lakehouse", "Lakehouse"), ("Silver_Lakehouse", "Lakehouse"),
              ("Gold_Lakehouse", "Lakehouse")),
    "reporting": (("Semantic_Model", "SemanticModel"),),
}
_GATE_GROUP = "Gate_Notebook"


def _plan_groups(blueprint: dict, role: str) -> list[tuple[str, str]]:
    groups = list(_PLAN_GROUPS_BY_ROLE.get(role, ()))
    bronze = (blueprint.get("medallion") or {}).get("bronze") or {}
    if bronze.get("enabled") is False:   # Bronze ausgelagert → kein Bronze-Item im Workspace
        groups = [g for g in groups if g[0] != "Bronze_Lakehouse"]
    return groups


def _plan_yml(groups: list[tuple[str, str]]) -> str:
    """plan.yml-Vorlage. `${logicalId:<Schlüssel>}` löst `resolve_plan.py` aus den `.platform`-
    Dateien im Git-Ordner auf — die logicalIds entstehen erst im Tenant und werden nie geraten."""
    z = [f"$schema: {DEPLOYMENT_PLAN_SCHEMA}", "version: 1.0.0", "groups:",
         f"  - name: {_GATE_GROUP}", f"    logicalId: ${{logicalId:{_GATE_GROUP}}}"]
    prev = _GATE_GROUP
    for key, _typ in groups:
        z += [f"  - name: {key}", f"    logicalId: ${{logicalId:{key}}}",
              "    dependsOn:", f"      - groupName: {prev}",
              "    postActions:", f"      - name: Gate {key}", "        job:",
              "          type: Execute", f"          logicalId: ${{logicalId:{_GATE_GROUP}}}"]
        prev = key
    return "\n".join(z) + "\n"


def _plan_items_json(groups: list[tuple[str, str]], gate_notebook: str) -> str:
    import json
    items = {_GATE_GROUP: f"{gate_notebook}.Notebook"}
    for key, typ in groups:
        items[key] = f"<{key.lower()}-item-name>.{typ}"
    return json.dumps({
        "_comment": ("Gruppe -> Item-Ordner im Git-Ordner des Workspaces (ANZEIGENAME.TYP). "
                     "Platzhalter <...> vor dem Auflösen ersetzen; resolve_plan.py bricht sonst ab."),
        "items": items}, indent=2, ensure_ascii=False) + "\n"


_RESOLVE_PLAN_PY = '''#!/usr/bin/env python3
"""Löst die ${logicalId:GRUPPE}-Platzhalter einer plan.yml-Vorlage auf (generiert — I-21 W2.7).

Aufruf:  python resolve_plan.py PLAN_ORDNER GIT_ORDNER
Liest PLAN_ORDNER/plan.template.yml und items.json, schlägt je Gruppe die logicalId in
GIT_ORDNER/ITEM_ORDNER/.platform (config.logicalId) nach und schreibt plan.yml.
Bricht mit Exit 1 ab, wenn ein Platzhalter offen bleibt, ein Item fehlt oder eine logicalId
leer bzw. die Null-GUID ist — ein halb aufgelöster Plan wird nie geschrieben.
"""
import json
import re
import sys
from pathlib import Path

_NULL = "00000000-0000-0000-0000-000000000000"
_PLATZHALTER = re.compile(r"\\$\\{logicalId:([A-Za-z0-9_]+)\\}")


def resolve(plan_dir: Path, git_dir: Path) -> tuple[str, list[str]]:
    vorlage = (plan_dir / "plan.template.yml").read_text(encoding="utf-8")
    items = json.loads((plan_dir / "items.json").read_text(encoding="utf-8"))["items"]
    fehler: list[str] = []
    ids: dict[str, str] = {}
    for key in sorted(set(_PLATZHALTER.findall(vorlage))):
        ordner = items.get(key)
        if not ordner:
            fehler.append(f"{key}: kein Eintrag in items.json")
            continue
        if "<" in ordner:
            fehler.append(f"{key}: Platzhalter nicht ersetzt ({ordner})")
            continue
        platform = git_dir / ordner / ".platform"
        if not platform.is_file():
            fehler.append(f"{key}: {platform} fehlt (Item nicht im Git-Ordner committet?)")
            continue
        lid = (json.loads(platform.read_text(encoding="utf-8")).get("config") or {}).get("logicalId", "")
        if not lid or lid == _NULL:
            fehler.append(f"{key}: logicalId in {platform} leer oder Null-GUID")
            continue
        ids[key] = lid
    if fehler:
        return "", fehler
    return _PLATZHALTER.sub(lambda m: ids[m.group(1)], vorlage), []


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    text, fehler = resolve(Path(argv[1]), Path(argv[2]))
    if fehler:
        for f in fehler:
            print(f"FEHLER {f}", file=sys.stderr)
        return 1
    (Path(argv[1]) / "plan.yml").write_text(text, encoding="utf-8")
    print(f"plan.yml geschrieben ({Path(argv[1]) / 'plan.yml'})")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
'''


def _deployment_plan_doc(deployment_model: str, plans: list[tuple[str, str, list]]) -> str:
    anhang = {
        "deployment-pipelines": ("Deploy Stage Content",
                                 "POST /v1/deploymentPipelines/{id}/deploy?beta=true",
                                 '{"options":{"deploymentPlan":{"itemId":"<plan-item-id>",'
                                 '"referenceType":"ByItemId"}}}'),
        "git-integration-gitflow": ("Update From Git",
                                    "POST /v1/workspaces/{id}/git/updateFromGit?beta=true",
                                    '{"options":{"deploymentPlan":{"logicalId":"<plan-logical-id>",'
                                    '"referenceType":"ByLogicalId"}}}'),
    }
    z = [
        "# Deployment plan (generiert — I-21 W2.7 a, **Preview**)", "",
        "Der Plan legt Reihenfolge und Nach-Aktionen fest: zuerst das Gate-Notebook, dann die "
        "Schichten in Medaillon-Reihenfolge, nach jeder Schicht einmal das Gate. Fabric verbindet "
        "die Plan-Reihenfolge mit der Lineage; der Plan hebt keine Lineage-Abhängigkeit auf.", "",
        "Beleg: Learn `cicd/deployment-plan/*` (gelesen 29.09.2026).", "",
        "## Pläne dieser Lieferung", "",
        "| Workspace | Rolle | Gruppen in Reihenfolge |", "|---|---|---|",
    ]
    for ws, role, groups in plans:
        z.append(f"| `{ws}` | {role} | {' → '.join([_GATE_GROUP] + [g for g, _ in groups])} |")
    z += [
        "", "Ein Plan deployt in genau einen Workspace je Lauf, daher ein Plan je Workspace.", "",
        "## Voraussetzungen (Tenant-gated)", "",
        "- Tenant-Setting **Users can create deployment plan (preview) items** für die "
        "Entwicklergruppe an.",
        "- Mindestens Contributor im Quell-Workspace.",
        "- Automatisierung: Token mit `Item.Execute.All` zusätzlich zum Scope der Operation, "
        "URL mit `?beta=true`.",
        "- Das Gate-Notebook (`items.json` → `Gate_Notebook`) muss es im Workspace geben. Dieser "
        "Emitter erzeugt es nicht; es fährt die Prüfungen aus `gates/` im Tenant und endet mit "
        "Fehler, wenn eine rot ist.", "",
        "## Ablauf", "",
        "1. Plan-Item einmal im Entwicklungs-Workspace auf dem Canvas anlegen und committen — so "
        "entsteht der Item-Ordner mit `.platform` im Git.",
        "2. `items.json` ausfüllen (Anzeigename je Gruppe), dann "
        "`python cicd/deployment_plan/resolve_plan.py cicd/deployment_plan/WORKSPACE "
        "GIT_ORDNER`.",
        "3. Das erzeugte `plan.yml` in den Item-Ordner des Plans kopieren, per PR mergen.",
        "4. Beim Deployment den Plan anhängen — jedes Mal, ein Standard-Plan lässt sich nicht "
        "hinterlegen.", "",
        "## Anhängen je Deployment-Modell", "",
    ]
    if deployment_model in anhang:
        name, pfad, body = anhang[deployment_model]
        z += [f"Modell `{deployment_model}`: **{name}**", "", "```http", pfad, "```", "",
              "```json", body, "```", ""]
    else:
        z += [f"Modell `{deployment_model}` deployt mit `fabric-cicd`. **`fabric-cicd` "
              "unterstützt keine Deployment plans** (Learn, deployment-plan-automation). Mit Plan "
              "geht es nur über **Bulk Import Item Definitions** (selbst Preview):", "",
              "```http", "POST /v1/workspaces/{id}/items/bulkImportDefinitions?beta=true", "```",
              "", "```json",
              '{"options":{"allowPairingByName":false,"deploymentPlan":{"logicalId":'
              '"<plan-logical-id>","referenceType":"ByLogicalId"}}}', "```", "",
              "Ohne Umstieg bleibt der Plan hier wirkungslos — er wird dann nur für Git-Update "
              "im Entwicklungs-Workspace genutzt.", ""]
    z += [
        "Der Plan wirkt auch bei Git-Update und REST, also dort, wo Inbound-Schutz Deployment "
        "Pipelines ausschließt (D-592: dort deployt diese Lieferung Git-basiert).", "",
        "## Was der Plan nicht tut", "",
        "- **Kein Rollback:** scheitert ein Item oder eine Aktion, bleibt Deployedes stehen, der "
        "Rest kommt nicht. Rückweg: `_RUECKSPRUNG.md`.",
        "- Keine Workspace-Einstellungen, Identitäten, Verbindungen, Gateway-Bindungen, "
        "Spark-Settings — die müssen im Ziel stehen, bevor eine Aktion sie braucht.",
        "- Er schaltet den aktiven Wertesatz einer Variable Library nicht um.",
        "- Eine Aktion wartet nicht auf nachgelagerte Dienste (z. B. SQL-Endpunkt). Wer das "
        "braucht, wartet im Notebook selbst.",
        "- Gruppen laufen nie parallel. Höchstens 20 Nach-Aktionen je Gruppe, Namen höchstens "
        f"{DEPLOYMENT_PLAN_MAX_NAME} Zeichen, Plan höchstens 1 MB.", "",
        "**Schema nicht gegengeprüft:** die Schema-URL im `$schema` war am 29.09.2026 aus dieser "
        "Umgebung nicht abrufbar. Die Struktur folgt dem Learn-Beispiel "
        "(`deployment-plan-sample-plans`); ANNAHME, ungeprüft gegen das Schema.", "",
    ]
    return "\n".join(z) + "\n"


def emit_deployment_plan(blueprint: dict, deployment_model: str = _DEFAULT_MODEL,
                         gate_notebook: str = "nb_gate") -> dict[str, str]:
    """Deployment-plan-Vorlagen je Workspace + Auflöser + Runbook (Preview, nur hinter Flag)."""
    out: dict[str, str] = {}
    plans: list[tuple[str, str, list]] = []
    for ws, role in _unique_workspaces(blueprint):
        groups = _plan_groups(blueprint, role)
        if not groups:
            continue
        for key, _typ in groups:
            if len(key) > DEPLOYMENT_PLAN_MAX_NAME:
                raise ValueError(f"Gruppenname {key!r} > {DEPLOYMENT_PLAN_MAX_NAME} Zeichen")
        base = f"cicd/deployment_plan/{ws}"
        out[f"{base}/plan.template.yml"] = _plan_yml(groups)
        out[f"{base}/items.json"] = _plan_items_json(groups, gate_notebook)
        plans.append((ws, role, groups))
    out["cicd/deployment_plan/resolve_plan.py"] = _RESOLVE_PLAN_PY
    out["cicd/deployment_plan/_DEPLOYMENT_PLAN.md"] = _deployment_plan_doc(deployment_model, plans)
    return out


def _wire_bash_gates(script: str) -> str:
    """Inject real pre-/post-deploy gate calls (I-19.3) into a bash CD script.

    Pre-deploy right after ``set -euo pipefail`` (before any promotion), post-deploy at the
    end (after the promotion block). The gate calls are runnable even while the fab commands
    are VERIFY stubs — the gates are real, the deploy is the template.
    """
    script = script.replace(
        "set -euo pipefail\n", "set -euo pipefail\n\n" + pre_deploy_gate_line() + "\n", 1)
    return script.rstrip("\n") + "\n\n" + post_deploy_gate_line() + "\n"


def _wire_python_gates(script: str) -> str:
    """Inject real pre-/post-deploy gate calls (I-19.3) into the ISV python CD driver."""
    script = script.replace("import json\n", "import json\nimport subprocess\n", 1)
    script = script.replace(
        "for c in CUSTOMERS:",
        'subprocess.run(["bash", "gates/validate.sh", "pre-deploy"], check=True)  '
        "# I-19.3 pre-deploy gate\n\nfor c in CUSTOMERS:", 1)
    return script.replace(
        'print("ISV per-customer release complete.")',
        'subprocess.run(["bash", "gates/validate.sh", "post-deploy"], check=True)  '
        '# I-19.3 post-deploy gate\nprint("ISV per-customer release complete.")', 1)


def emit_cicd(blueprint: dict, architecture_path: str = "data_architecture.json",
              stack: str = "fabric", stages: tuple[str, ...] = _DEFAULT_STAGES,
              stage_capacities: dict | None = None, git: dict | None = None,
              deployment_model: str | None = None,
              deployment_plan: bool = False,
              entscheidungen: dict | None = None) -> dict[str, str]:
    """Return the CI/CD artifact set (path -> content), analogous to ``emit_grounding``.

    ``cicd/secret-scan.yml`` + ``cicd/_DEPLOYMENT_MODEL.md`` +
    ``cicd/_RUECKSPRUNG.md`` (der Rückweg einer einzelnen Beförderung, BK-C05) +
    the validation-gate set (``gates/validate.sh`` · ``gates/gates.yml`` · ``gates/_GATES.md``,
    I-19.3) are always emitted. The Fabric CD script is **model-specific** (``deployment_model``,
    ADR-0050 / I-19.1) and has the pre-/post-deploy gate calls wired in:
    deployment-pipelines → ``promote.sh``; git-integration-gitflow → ``promote_gitflow.sh``;
    isv-per-customer → ``deploy_customers.sh`` (+ ``customers.example.json``); items-api-trunk →
    ``deploy_items.sh`` driver + the co-emitted ``fabric-cicd/`` mechanism. Unknown model → ValueError.
    Immer dazu: ``cicd/branch-ruleset.json`` + ``cicd/_BRANCH_RULE.md`` (I-21 W5.4 d), auf Fabric
    ``cicd/_BRANCH_WORKSPACES.md`` (W2.7 b). ``deployment_plan=True`` ergänzt die Deployment-plan-
    Vorlagen unter ``cicd/deployment_plan/`` (W2.7 a, Preview).

    D-592: ohne ``deployment_model`` folgt der Weg der Netzhaltung (``entscheidungen`` →
    ``PLAT-NET``, :func:`deployment_model_fuer`); Deployment Pipelines bei Inbound-Schutz →
    ValueError.
    """
    herkunft = _herleitung(entscheidungen, deployment_model)
    deployment_model = deployment_model_fuer(entscheidungen, deployment_model)
    # R8 (30.09.2026): kein `architecture-gate.yml` mehr im Kundenbaum — er rief in der
    # Kunden-CI `python -m core.dataarch_engine.blueprint.cli`. PR-Tor ist `gates/gates.yml`.
    out = {"cicd/secret-scan.yml": emit_secret_scan(),
           "cicd/_DEPLOYMENT_MODEL.md": _deployment_model_doc(deployment_model, blueprint, stages,
                                                       herkunft),
           "cicd/_RUECKSPRUNG.md": _ruecksprung_doc(deployment_model, blueprint, stages)}
    out.update(emit_gates(architecture_path, stack, blueprint=blueprint))  # I-19.3 + BK-C04
    # I-21 W5.4 d: der Integrations-Branch nimmt nur PRs an; stack-unabhängig wie die Tore.
    out["cicd/branch-ruleset.json"] = emit_branch_ruleset(deployment_model, stages, git or {})
    out["cicd/_BRANCH_RULE.md"] = _branch_rule_doc(deployment_model, stages, git or {})
    if stack == "fabric":
        out["cicd/_BRANCH_WORKSPACES.md"] = _branch_workspaces_doc(blueprint)
        if deployment_plan:   # I-21 W2.7 a — Preview, nur auf Wunsch
            out.update(emit_deployment_plan(blueprint, deployment_model))
        if deployment_model == "deployment-pipelines":
            out["cicd/promote.sh"] = _wire_bash_gates(
                emit_cd_promotion(blueprint, stages, stage_capacities, git))
        elif deployment_model == "git-integration-gitflow":
            out["cicd/promote_gitflow.sh"] = _wire_bash_gates(
                emit_gitflow_promotion(blueprint, stages, git))
        elif deployment_model == "isv-per-customer":
            out["cicd/deploy_customers.sh"] = _wire_python_gates(emit_isv_release(blueprint, git))
            out["cicd/customers.example.json"] = (
                '{\n  "customers": [\n'
                '    {"name": "aurora", "workspace_id": "<aurora-prod-workspace-id>", "environment": "prod"}\n'
                '  ]\n}\n')
        elif deployment_model == "items-api-trunk":
            # Co-emit the fabric-cicd mechanism (Tool-Reuse, same fabric-cicd/ location) + a gated driver.
            from core.dataarch_engine.blueprint.provision_fabric_cicd import emit_fabric_cicd
            out.update(emit_fabric_cicd(blueprint, stack=stack, stages=stages))
            out["cicd/deploy_items.sh"] = _wire_bash_gates(emit_items_release(stages))
    return out
