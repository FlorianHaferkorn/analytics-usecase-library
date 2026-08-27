"""provision_cicd — emit CI/CD artifacts from an ArchitectureBlueprint.

Second live-provisioning helper (ADR-0015 follow-up), sibling to ``provision_fabric``.
Turns a blueprint into the CI/CD promotion layer that makes a provisioned medallion
*promotable* (dev -> test -> prod), in two honest-by-construction pieces:

1. **CI gate** (``emit_ci_gate``): a real, drop-in GitHub Actions workflow that runs
   the blueprint's own ``derive -> audit`` as a **merge gate** on a
   ``data_architecture.json``. The blueprint CLI already exits non-zero (2) when
   conformance is not green, so a non-conformant architecture change fails the PR.
   Pure reuse of the existing, already-green conformance tool — no new rule silo.

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
        f"#   provider={git.get('provider', '<GitHub|AzureDevOps>')} repo={git.get('repository', '<repo>')} dir={git.get('directory', '/')}",
        "",
        "# 1. Bind each stage workspace to its stage branch (once).",
    ]
    for name, role in workspaces:
        for st in stages:
            lines.append(f'#   {name} ({role}) @ {st} → branch "{st}"')
            lines.append(f'#   fab api "workspaces/<{name}-{st}-workspace-id>/git/connect" -X POST -i - <<JSON')
            lines.append(f'#   {{"gitProviderDetails":{{"branchName":"{st}","directoryName":"{git.get("directory", "/")}"}}}}')
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
from pathlib import Path

# fabric-cicd is the MS-supported deploy library (Official-First). pip install fabric-cicd
from fabric_cicd import FabricWorkspace, publish_all_items

REPO_DIR = "."                      # item definitions live in the repo (main)
CUSTOMERS = json.loads(Path("customers.json").read_text(encoding="utf-8"))["customers"]

for c in CUSTOMERS:                 # e.g. {{"name":..., "workspace_id":..., "environment":"prod"}}
    print(f"deploying to {{c['name']}} ({{c['workspace_id']}})")
    ws = FabricWorkspace(
        workspace_id=c["workspace_id"],
        environment=c.get("environment", "prod"),   # picks the value-set in parameter.yml
        repository_directory=REPO_DIR,
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


def _deployment_model_doc(model: str, blueprint: dict, stages: tuple[str, ...]) -> str:
    m = _DEPLOYMENT_MODELS[model]
    n_ws = len(_unique_workspaces(blueprint))
    lines = [
        "# Deployment-Modell (generiert — ADR-0050 / I-19.1)", "",
        f"Gewähltes Modell: **{model}** (MS Fabric CI/CD Option {m['option']}).", "",
        "| Achse | Wert |", "|---|---|",
        f"| Source of Truth | {m['sot']} |",
        f"| Merge-/Branching-Ansatz | {m['branching']} |",
        f"| Deployment-Mechanismus | {m['mechanism']} |",
        f"| Approval-Gate | {m['approval']} |",
        f"| Stages | {' → '.join(stages)} |",
        f"| Workspaces im Blueprint | {n_ws} |", "",
        "Belegt: learn.microsoft.com/fabric/cicd/manage-deployment (Choose the best workflow option).", "",
        "## Wo die Validierungs-Gates sitzen (I-19.3 verdrahtet sie)",
        "- **PR-Gate (CI):** `architecture-gate.yml` (Conformance) + Modell-/TMDL-/Katalog-Checks → blockt Merge.",
        "- **Pre-Deploy:** vor `update-from-git`/`fabric-cicd`/Deployment-Pipeline.",
        "- **Post-Deploy:** Smoke (Modell lädt, Refresh, Lineage-Reconcile) vor der nächsten Stage.", "",
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
    return "\n".join(lines) + "\n"


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
              deployment_model: str = _DEFAULT_MODEL) -> dict[str, str]:
    """Return the CI/CD artifact set (path -> content), analogous to ``emit_grounding``.

    ``cicd/architecture-gate.yml`` (stack-agnostic CI gate) + ``cicd/_DEPLOYMENT_MODEL.md`` +
    ``cicd/_RUECKSPRUNG.md`` (der Rückweg einer einzelnen Beförderung, BK-C05) +
    the validation-gate set (``gates/validate.sh`` · ``gates/gates.yml`` · ``gates/_GATES.md``,
    I-19.3) are always emitted. The Fabric CD script is **model-specific** (``deployment_model``,
    ADR-0050 / I-19.1) and has the pre-/post-deploy gate calls wired in:
    deployment-pipelines → ``promote.sh``; git-integration-gitflow → ``promote_gitflow.sh``;
    isv-per-customer → ``deploy_customers.sh`` (+ ``customers.example.json``); items-api-trunk →
    ``deploy_items.sh`` driver + the co-emitted ``fabric-cicd/`` mechanism. Unknown model → ValueError.
    """
    if deployment_model not in _DEPLOYMENT_MODELS:
        raise ValueError(f"unknown deployment_model {deployment_model!r}; "
                         f"choose one of {sorted(_DEPLOYMENT_MODELS)}")
    out = {"cicd/architecture-gate.yml": emit_ci_gate(architecture_path, stack),
           "cicd/azure-pipelines-architecture-gate.yml": emit_ci_gate_azure(architecture_path, stack),
           "cicd/_DEPLOYMENT_MODEL.md": _deployment_model_doc(deployment_model, blueprint, stages),
           "cicd/_RUECKSPRUNG.md": _ruecksprung_doc(deployment_model, blueprint, stages)}
    out.update(emit_gates(architecture_path, stack, blueprint=blueprint))  # I-19.3 + BK-C04
    if stack == "fabric":
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
