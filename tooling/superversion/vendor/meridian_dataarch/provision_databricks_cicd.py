"""provision_databricks_cicd — CI/CD for the Databricks stack via Asset Bundles (DABs). Idea #2.

Closes one of the honest Fabric-first gaps in the stack-parity matrix: CI/CD on Databricks. Emits a
**Databricks Asset Bundle** (`databricks.yml`: bundle + per-stage targets + a medallion job) plus a
`deploy.sh` (`databricks bundle validate|deploy -t <stage>`) — the official Databricks deployment path,
the peer of Fabric's `fabric-cicd`/deployment-pipelines. Honest by construction: the bundle wires the
gold products as job tasks with `TODO` where cluster/notebook ids go (tenant-specific), never invented.
Deterministic; emits only. Snowflake CI/CD (schemachange/dbt) + the other extended emitters stay
documented gaps in `stack_parity`.
"""
from __future__ import annotations

from typing import Any

import yaml

from core.dataarch_engine.blueprint.provision_transforms import _ident

_DEFAULT_STAGES = ("dev", "test", "prod")


def emit_databricks_cicd(blueprint: dict, stages: tuple[str, ...] = _DEFAULT_STAGES) -> dict[str, str]:
    """Return a Databricks Asset Bundle CI/CD set as ``databricks/cicd/<path> → content``."""
    gold = sorted(p["name"] for p in blueprint.get("medallion", {}).get("gold", {}).get("data_products", []))
    bundle_name = "meridian_medallion"

    # one job task per gold product (silver→gold), sequential via depends_on — a runnable-shaped DAG.
    tasks: list[dict[str, Any]] = []
    for i, product in enumerate(gold):
        task: dict[str, Any] = {
            "task_key": f"build_{_ident(product)}",
            "notebook_task": {"notebook_path": f"../notebooks/gold_{_ident(product)}"},  # TODO: real path
            "job_cluster_key": "medallion_cluster",
        }
        if i:
            task["depends_on"] = [{"task_key": f"build_{_ident(gold[i - 1])}"}]
        tasks.append(task)

    targets = {}
    for stage in stages:
        targets[stage] = {
            "mode": "development" if stage == "dev" else "production",
            "workspace": {"host": f"<{stage}-workspace-url>"},   # TODO: per-stage workspace host
        }

    bundle = {
        "bundle": {"name": bundle_name},
        "targets": targets,
        "resources": {"jobs": {"medallion_build": {
            "name": "medallion_build",
            "job_clusters": [{"job_cluster_key": "medallion_cluster",
                              "new_cluster": {"spark_version": "<lts-runtime>", "num_workers": 2}}],
            "tasks": tasks or [{"task_key": "noop", "notebook_task": {"notebook_path": "../notebooks/noop"}}],
        }}},
    }

    deploy = (
        "#!/usr/bin/env bash\n"
        "# Databricks Asset Bundle deploy (generated — idea #2). Official Databricks CI/CD.\n"
        "# Requires the Databricks CLI (>=0.205) + a configured profile / OIDC in CI.\n"
        "set -euo pipefail\n"
        'STAGE="${1:?usage: deploy.sh <' + "|".join(stages) + '>}"\n'
        'databricks bundle validate -t "$STAGE"\n'
        'databricks bundle deploy -t "$STAGE"\n'
    )
    doc = ["# Databricks CI/CD via Asset Bundles (generated — idea #2)", "",
           f"Bundle `{bundle_name}` with targets **{', '.join(stages)}** and a medallion build job "
           f"(**{len(gold)}** gold task(s), sequential). The Databricks peer of Fabric's fabric-cicd. "
           "**Honest boundary**: notebook paths / cluster runtime / workspace hosts are `TODO` "
           "(tenant-specific) — the bundle wires the strecke, not the tenant secrets.", "",
           "Run: `bash deploy.sh dev` (validate + deploy the bundle for a stage).", ""]

    return {
        "databricks/cicd/databricks.yml": yaml.safe_dump(bundle, sort_keys=False, allow_unicode=True),
        "databricks/cicd/deploy.sh": deploy,
        "databricks/cicd/_DATABRICKS_CICD.md": "\n".join(doc) + "\n",
    }
