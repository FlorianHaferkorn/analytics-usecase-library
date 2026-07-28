"""provision_monitoring — emit operational monitoring & alerting from a blueprint.

Closes the observability gap: the platform got provisioned, transformed, governed — but nothing
watched it at runtime. This turns the blueprint's workspaces + schedule into the monitoring layer,
at the fidelity Fabric actually supports (grounded in MS Learn 2026-07: *Create alerts for pipeline
runs*, *What is Fabric Activator?*, *Monitor Fabric Capacity Health*, *Well-Architected — operational
excellence*):

- **Pipeline / job failures (workspace-wide)** → enable **workspace monitoring** (job logs land in a
  monitoring Eventhouse) + one **Activator** rule over an `ItemJobEventLogs` **KQL Queryset** — a
  single rule catches every pipeline / refresh / notebook failure, instead of per-item alerts.
- **Scheduled pipeline failures (built-in)** → the pipeline's own *Failure notifications* (email /
  groups on the Schedule) — the zero-infra first line.
- **Capacity throttling** → an Activator rule over **Capacity Overview Events** on
  `backgroundRejectionThresholdPercentage` (and the interactive delay/rejection siblings).

Honest by construction: the KQL query is a real, deployable artifact; Activator rules + workspace-
monitoring enablement are **portal/config** actions (no clean deterministic create API), so they are
emitted as structured rule **specs** + an ordered runbook, never as a faked API call. Alert
recipients come from the caller's ``alerts`` map (never invented) or stay ``<VERIFY>`` placeholders.

This module **does not execute** anything — it only emits text.
"""
from __future__ import annotations

import json
import re

_NONWORD_RE = re.compile(r"[^a-z0-9]+")


def _dirslug(name: str) -> str:
    return _NONWORD_RE.sub("-", (name or "").lower()).strip("-")


def _domains(bp: dict) -> list[dict]:
    return sorted(bp.get("mesh", {}).get("domains", []), key=lambda d: d.get("name", ""))


def _recipients(alerts: dict, key: str) -> list[str]:
    """Recipients for a severity/channel from the caller's map; a VERIFY placeholder if unset."""
    r = (alerts or {}).get(key) or (alerts or {}).get("default") or ["<VERIFY: alert recipient email/Group>"]
    return sorted(dict.fromkeys(r))                       # dedup, deterministic


def _workspace_failures_kql() -> str:
    """A KQL Queryset over ItemJobEventLogs catching ALL failed jobs workspace-wide (pipeline / refresh
    / notebook). Grounded verbatim-shape in MS Learn (workspace-level alerts). Real, deployable."""
    return (
        "// Workspace-wide job failures — deploy as a KQL Queryset, then bind an Activator rule to it.\n"
        "// Prereq: enable Workspace monitoring (writes ItemJobEventLogs into the monitoring Eventhouse).\n"
        "// Catches pipeline, semantic-model refresh and notebook job failures in one rule.\n"
        "ItemJobEventLogs\n"
        "| extend SecondsAgo = datetime_diff('second', now(), ingestion_time())\n"
        "| where JobStatus == 'Failed'\n"
        "| where SecondsAgo <= 540   // Activator must poll more often than this window\n"
        "| order by Timestamp desc\n"
        "| project Timestamp, JobType, ItemName, WorkspaceName, JobStartTime, JobEndTime, JobStatus\n"
    )


def _capacity_throttling_rule(capacity: str, alerts: dict) -> str:
    """Activator rule spec over Capacity Overview Events — grounded thresholds (Monitor Fabric Capacity
    Health). Emitted as a declarative spec (Activator rules are authored in Real-Time Hub / Activator)."""
    spec = {
        "_note": ("Author in Real-Time Hub → Capacity Overview Events → Set alert (or an Activator rule). "
                  "This is the rule to reproduce; there is no deterministic create-API for Activator rules."),
        "source": "Capacity Overview Events",
        "capacity": capacity,
        "groupingField": "capacityId",
        "rules": [
            {"when": "backgroundRejectionThresholdPercentage", "condition": "increases to or above",
             "value": 80, "meaning": "background operations rejected under capacity pressure"},
            {"when": "interactiveRejectionThresholdPercentage", "condition": "increases to or above",
             "value": 80, "meaning": "interactive operations rejected (reports failing)"},
            {"when": "interactiveDelayThresholdPercentage", "condition": "increases to or above",
             "value": 80, "meaning": "interactive operations delayed (reports slow)"},
        ],
        "action": {"type": "email", "to": _recipients(alerts, "capacity"),
                   "subject": "Fabric Capacity Throttling Alert",
                   "note": "Capacity exceeded rejection threshold: @backgroundRejectionThresholdPercentage%"},
        "escalation": "Optionally set action=Run function (UDF) for auto-mitigation (pause/resume, scale).",
    }
    return json.dumps(spec, indent=2, ensure_ascii=False) + "\n"


def _pipeline_failure_runbook(bp: dict, alerts: dict) -> str:
    lines = [
        "# Pipeline failure notifications (built-in — the zero-infra first line)", "",
        "For each scheduled pipeline: open it → **Home → Schedule** → add recipients under **Failure",
        "notifications**. This emails on scheduled-run failure with no extra infrastructure. Use the",
        "workspace-wide Activator rule (see `_MONITORING.md`) for create/update/delete + non-scheduled runs.",
        "", "| Domain | Suggested failure-notification recipients |", "|---|---|",
    ]
    for d in _domains(bp):
        lines.append(f"| {d['name']} | {', '.join(_recipients(alerts, _dirslug(d['name'])))} |")
    lines += ["",
              "Best practice (grounded): alerts must be actionable + escalated; use multi-channel (email/Teams)",
              "and stateful Activator operators (BECOMES/INCREASES), not stateless, to avoid alert spam."]
    return "\n".join(lines) + "\n"


def emit_monitoring(bp: dict, stack: str = "fabric", workspace: str = "<workspace>",
                    capacity: str = "<CAPACITY_NAME>", alerts: dict | None = None) -> dict[str, str]:
    """Return the monitoring/alerting artifact set (path → content). Fabric-specific surfaces (KQL,
    Activator specs) are emitted for the fabric stack; the plan doc is always emitted."""
    alerts = alerts or {}
    doc = [
        "# Monitoring & alerting (generated — grounded MS Learn 2026-07)", "",
        f"Stack: **{stack}**  ·  Workspaces watched: **{len(_domains(bp))} domain(s)**  ·  "
        f"Capacity: **{capacity}**", "",
        "At the fidelity Fabric supports — real artifacts where deployable, specs + runbook where the",
        "surface is portal-authored (honest, never a faked API):", "",
        "| Signal | Artifact | Mechanism | Status |", "|---|---|---|---|",
        "| Any job failure (pipeline / refresh / notebook), workspace-wide | `workspace_job_failures.kql` | "
        "Workspace monitoring → ItemJobEventLogs KQL → Activator rule | deployable KQL + portal rule |",
        "| Scheduled pipeline failure | `pipeline_failure_notifications.md` | built-in Failure notifications | GA, per-pipeline |",
        "| Capacity throttling | `capacity_throttling_alert.json` | Capacity Overview Events → Activator | portal rule spec |",
        "| Compute/storage dashboards | Fabric **Capacity Metrics App** (install) | built-in | GA |", "",
        "## Setup order", "",
        "1. Enable **Workspace monitoring** on each workspace (job logs → monitoring Eventhouse).",
        "2. Create a **KQL Queryset** from `workspace_job_failures.kql`.",
        "3. Create an **Activator** rule on that queryset → email/Teams to the on-call recipients.",
        "4. Create the **capacity** Activator rule from `capacity_throttling_alert.json`.",
        "5. Set built-in **Failure notifications** per scheduled pipeline (`pipeline_failure_notifications.md`).",
        "6. Install the **Capacity Metrics App** for CU/storage dashboards.", "",
        "> Activator must poll more frequently than the KQL time window, else failures are missed. Use",
        "> stateful operators + preview-before-activate to avoid alert spam (grounded).",
    ]
    out: dict[str, str] = {"monitoring/_MONITORING.md": "\n".join(doc) + "\n",
                           "monitoring/pipeline_failure_notifications.md": _pipeline_failure_runbook(bp, alerts)}
    if stack == "fabric":
        out["monitoring/workspace_job_failures.kql"] = _workspace_failures_kql()
        out["monitoring/capacity_throttling_alert.json"] = _capacity_throttling_rule(capacity, alerts)
    return out
