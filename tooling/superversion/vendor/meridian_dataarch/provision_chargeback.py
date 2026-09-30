"""provision_chargeback — make the *official* Fabric chargeback work, don't rebuild it.

Microsoft ships a **Fabric Chargeback app**: it attributes capacity utilisation by workspace,
item and **domain/subdomain**, and is the supported way to answer "which team burned the
capacity". Under Official-First this Baukasten therefore does not build a cost engine.

Two hard facts decide the shape of this module:

1. **The Capacity Metrics app's semantic model is explicitly unsupported for custom use**
   ("Any consumption from, usage of, or modification of the semantic model isn't
   supported"). So querying it to compute our own per-domain cost is off the table — it
   would be building on a contract Microsoft declines to give.
2. **The Chargeback app attributes by Fabric domain, and a workspace that is not assigned
   to a domain lands in "No domain".** Attribution is therefore only as good as the domain
   assignment — and the domain→workspace topology is exactly what this IR already governs.

So the value we add is not a report. It is: **make the official app able to attribute at
all**, and surface the decisions and conflicts it does not handle.

What that means concretely:

* emit the domain topology and the workspace→domain assignment calls from the IR, so
  chargeback does not degrade into one big "No domain" bucket;
* name every workspace that would fall into "No domain" *before* anyone runs the app;
* surface the conflicts that silently make chargeback impossible — private links (the
  Chargeback app does not support them, and our own connectivity emitter is what
  introduces them) and sovereign/government clouds;
* pre-decide the allocation method, which the app deliberately leaves open: consumption,
  equal split, or weighted.

The cost basis stays a `<VERIFY>`: CU counts per SKU are official and stable, but the
price per CU is regional, contract-specific and changes — inventing a number here would
produce a confident-looking chargeback that is simply wrong.
"""
from __future__ import annotations

import json
from typing import Any

# Allocation methods the workshop chooses between. The app reports consumption; turning
# consumption into a *charge* is a policy decision, not a metric.
ALLOCATION_METHODS = {
    "consumption": (
        "Charge each domain its measured CU share. Fairest when domains have genuinely "
        "independent workloads; punishes the domain that happens to run the shared "
        "ingestion."
    ),
    "equal_split": (
        "Split capacity cost evenly across domains. Defensible while workloads are still "
        "ramping and measurement would mostly reflect who onboarded first."
    ),
    "weighted": (
        "Consumption share, but with agreed weights (e.g. shared/platform workloads carried "
        "centrally). Needs the weights agreed up front or it becomes a negotiation every month."
    ),
}

# Conditions under which the official app cannot attribute at all — worth knowing before a
# capacity is bought, not after.
_BLOCKERS = {
    "private_link": (
        "The Fabric Chargeback app does not support environments using private links. If the "
        "connectivity layer provisions managed private endpoints / tenant private link, "
        "chargeback via the app is unavailable and cost attribution needs another route."
    ),
    "gov_cloud": (
        "The Fabric Chargeback app is not supported in government clouds."
    ),
}


def _capacity_cu(sku: str) -> int | None:
    """CU count for an F-SKU, read from the existing SKU table — not restated here."""
    from core.dataarch_engine.blueprint.capacity_recommend import _SKUS  # noqa: PLC0415

    for row in _SKUS:
        if str(row.get("sku", "")).upper() == str(sku).upper():
            return row.get("cu")
    return None


def domain_workspaces(bp: dict[str, Any]) -> dict[str, list[str]]:
    """Domain name → its workspace names, from the IR's mesh topology."""
    out: dict[str, list[str]] = {}
    for domain in bp.get("mesh", {}).get("domains", []) or []:
        name = str(domain.get("name") or "").strip()
        if not name:
            continue
        out[name] = sorted(
            str(w.get("name") or "").strip()
            for w in (domain.get("workspaces") or [])
            if str(w.get("name") or "").strip()
        )
    return dict(sorted(out.items()))


def unattributable_workspaces(bp: dict[str, Any]) -> list[str]:
    """Workspaces the IR knows but no domain claims — these become "No domain" in the app.

    Today this catches the shared/tenant-level workspace, which is exactly the one whose
    cost is most contested. Naming it up front beats discovering an unexplained bucket in
    the first chargeback run.
    """
    claimed = {w for ws in domain_workspaces(bp).values() for w in ws}
    known = set()
    shared = str(bp.get("shared_workspace") or "").strip()
    if shared:
        known.add(shared)
    for entry in bp.get("sharing", []) or []:
        ws = str(entry.get("workspace") or "").strip()
        if ws:
            known.add(ws)
    return sorted(known - claimed)


def blockers(bp: dict[str, Any], environment: dict[str, Any] | None = None) -> list[str]:
    """Conditions that make the official app unusable, with their reason."""
    environment = environment or {}
    found = []
    private = bool(environment.get("private_link")) or any(
        e.get("private") is True or e.get("access_mode") == "mirror"
        and "on-prem" in str(e.get("source_system", "")).lower()
        for e in bp.get("ingestion", []) or []
    )
    if private:
        found.append(_BLOCKERS["private_link"])
    if environment.get("gov_cloud"):
        found.append(_BLOCKERS["gov_cloud"])
    return found


def assignment_calls(bp: dict[str, Any]) -> list[dict[str, Any]]:
    """The Fabric admin calls that make domain attribution possible.

    Domains must exist and workspaces must be assigned to them; without that, every
    workspace reports under "No domain" and the chargeback app has nothing to attribute.
    """
    calls: list[dict[str, Any]] = []
    for domain, workspaces in domain_workspaces(bp).items():
        calls.append({
            "step": f"create domain '{domain}'",
            "method": "POST",
            "path": "/v1/admin/domains",
            "body": {"displayName": domain},
            "note": "Fabric admin only. Skip if the domain already exists.",
        })
        if workspaces:
            calls.append({
                "step": f"assign {len(workspaces)} workspace(s) to '{domain}'",
                "method": "POST",
                "path": "/v1/admin/domains/{domainId}/assignWorkspacesByIds",
                "body": {"workspacesIds": [f"<ID of {w}>" for w in workspaces]},
                "note": "Takes workspace IDs, not names — resolve them first "
                        "(GET /v1/admin/workspaces). Reassigning a workspace that already "
                        "has a domain depends on the 'override workspace assignments' "
                        "tenant setting.",
            })
    return calls


#: Die belegte Quelle fuer Zuordnung **je Operation**, falls die taegliche App nicht reicht:
#: Capacity Operation Events (Learn ``real-time-hub/explore-fabric-capacity-operation-events``,
#: gelesen 30.09.2026). Feldnamen wie dort; nur die, die eine Kostenzuordnung braucht.
OPERATION_EVENT_TYPE = "Microsoft.Fabric.CapacityOperationEvents.Operation"
OPERATION_EVENT_FELDER: tuple[str, ...] = (
    "capacityUnitMs", "utilizationType", "workspaceId", "workspaceName", "workspaceDomain",
    "workspaceParentDomain", "itemId", "itemName", "itemKind", "operationName", "identityType",
    "identityValue", "windowStartTime", "windowEndTime",
)


def _operation_events_lines() -> list[str]:
    return [
        "## Operation-level source (when daily app data is not enough)",
        "",
        f"**Capacity operation events** (`{OPERATION_EVENT_TYPE}`, Real-Time hub → Fabric events)",
        "emit one event per operation that consumes CU — not aggregated by time window. The fields",
        "a cost allocation needs: " + ", ".join(f"`{f}`" for f in OPERATION_EVENT_FELDER) + ".",
        "`capacityUnitMs` is the CU consumption in the smoothing window (`windowStartTime` to",
        "`windowEndTime`, 30 s up to 24 h), `workspaceDomain` carries the domain the app also uses,",
        "and `identityType`/`identityValue` name who ran it. Streaming needs the **capacity admin**",
        "role on that capacity; route the stream into an Eventhouse for history (Learn",
        "`real-time-hub/create-streams-fabric-capacity-operation-events`, read 2026-09-30). The",
        "volume is high on busy capacities — filter by `itemKind` or workspace before storing.",
        "This is a source, not a second chargeback: the allocation method below still applies.",
        "",
    ]


def _markdown(bp: dict[str, Any], sku: str, method: str,
              blocking: list[str], orphans: list[str],
              recommended: str | None = None) -> str:
    domains = domain_workspaces(bp)
    cu = _capacity_cu(sku)

    lines = [
        "# Chargeback — attribute capacity cost to domains",
        "",
        "## What this is and is not",
        "",
        "This is **not** a cost engine. Microsoft ships the **Fabric Chargeback app**, which",
        "attributes capacity utilisation by workspace, item and domain; it is the supported",
        "way to answer who consumed the capacity. Building a second one would also mean",
        "querying the Capacity Metrics app's semantic model, which Microsoft explicitly does",
        "not support for custom use.",
        "",
        "What this layer does instead: make that app able to attribute **at all**, and settle",
        "the decisions it leaves open.",
        "",
        "The Chargeback app's own semantic model is no way around this either: Microsoft",
        "supports it \"only for use by the reports provided in the app\" — consuming, using or",
        "modifying it is unsupported (Learn `enterprise/chargeback-app`, read 2026-09-30). The app",
        "refreshes daily, not in real time.",
        "",
        *_operation_events_lines(),
        "## Blockers",
        "",
    ]
    if blocking:
        lines.append("**The official app cannot be used in this setup:**")
        lines += [f"- {b}" for b in blocking]
        lines += [
            "",
            "Cost attribution then needs another route (e.g. one capacity per domain, so the",
            "Azure bill itself carries the split). Decide this before buying capacity — it is",
            "expensive to change afterwards.",
        ]
    else:
        lines.append("None detected. Prerequisites: capacity admin rights; the app is installed")
        lines.append("into a Pro-licensed workspace so it does not consume the capacity it measures.")

    lines += [
        "",
        "## Attribution readiness",
        "",
        f"| Domain | Workspaces | Attributable |",
        "|---|---|---|",
    ]
    for domain, workspaces in domains.items():
        lines.append(f"| `{domain}` | {len(workspaces)} | {'yes' if workspaces else 'no workspaces yet'} |")

    if orphans:
        lines += [
            "",
            f"**{len(orphans)} workspace(s) belong to no domain** and will report under",
            "*No domain* in the app:",
        ]
        lines += [f"- `{w}`" for w in orphans]
        lines += [
            "",
            "That bucket is usually the shared/platform workspace — the one whose cost is most",
            "argued about. Either assign it to a domain, or decide explicitly that platform cost",
            "is carried centrally (see the allocation method below).",
        ]
    else:
        lines += ["", "Every known workspace is claimed by a domain — nothing lands in *No domain*."]

    lines += [
        "",
        "## Cost basis",
        "",
        f"- Capacity SKU: **{sku}**"
        + (f" = **{cu} CU**" if cu else " — *unknown SKU, CU count not resolved*"),
        # A.10: die Kostenbasis folgt der GESETZTEN Kapazitaet. Weicht die Empfehlung davon ab,
        # steht das hier — gemessen 15.08.2026 rechnete dieses Dokument mit der empfohlenen
        # Kapazitaet, waehrend Blueprint und Direct-Lake-Guardrails desselben Laufs die gesetzte
        # trugen. Zwei Annahmen in einem Paket sind nicht schlimm; zwei Annahmen ohne Hinweis sind
        # es. Konkrete SKU-Werte stehen bewusst nicht hier, sondern in `capacity_recommend`.
        *([f"- Abweichung: die Empfehlung fuer diese Arbeitslast ist **{recommended}**"
           f"{f' = {_capacity_cu(recommended)} CU' if _capacity_cu(recommended) else ''}. "
           f"Gerechnet wird mit **{sku}**, weil der Bauplan sie setzt. Wer auf {recommended} "
           f"startet, rechnet diese Basis neu."]
          if recommended and recommended != sku else []),
        "- Price per CU: `<VERIFY>` — regional and contract-specific. It is deliberately not",
        "  filled in here: a guessed rate produces a confident-looking chargeback that is wrong.",
        "  Take it from the Azure price sheet for the capacity's region and reservation term.",
        "",
        "## Allocation method",
        "",
        f"**Chosen: `{method}`** — {ALLOCATION_METHODS[method]}",
        "",
        "Alternatives considered:",
    ]
    lines += [f"- `{k}` — {v}" for k, v in ALLOCATION_METHODS.items() if k != method]
    lines += [
        "",
        "The app reports consumption; turning consumption into a charge is a policy decision.",
        "Whichever is chosen, agree it *before* the first invoice — retro-fitting an allocation",
        "rule to a number people have already seen is a different conversation.",
        "",
        "## Order of operations",
        "",
        "1. Create the domains and assign the workspaces (`domain_assignment.json`) — without",
        "   this the app attributes everything to *No domain*.",
        "2. Install the Fabric Chargeback app (capacity admin, into a Pro workspace).",
        "3. Configure it with your UTC offset and 14 or 30 days of history.",
        "4. Apply the allocation method above to the reported CU shares.",
    ]
    return "\n".join(lines) + "\n"


def emit_chargeback(bp: dict[str, Any], sku: str = "F64",
                    allocation: str = "consumption",
                    environment: dict[str, Any] | None = None,
                    recommended: str | None = None) -> dict[str, str]:
    """Return the chargeback artifact set (path → content).

    ``recommended`` ist die Kapazitaetsempfehlung fuer die Arbeitslast, falls sie von ``sku``
    abweicht. Sie wird nicht gerechnet, sondern genannt: die Kostenbasis folgt der gesetzten
    Kapazitaet (A.10), und eine abweichende Empfehlung ist eine Information, kein zweiter Wert.
    """
    if allocation not in ALLOCATION_METHODS:
        raise ValueError(
            f"unknown allocation method '{allocation}'; "
            f"choose one of {sorted(ALLOCATION_METHODS)}"
        )

    domains = domain_workspaces(bp)
    if not domains:
        return {}

    blocking = blockers(bp, environment)
    orphans = unattributable_workspaces(bp)

    out = {
        "chargeback/_CHARGEBACK.md": _markdown(bp, sku, allocation, blocking, orphans, recommended),
        "chargeback/domain_assignment.json": json.dumps({
            "_note": "Fabric admin calls that make domain attribution possible. Workspace IDs "
                     "must be resolved first — the assign API takes IDs, not names.",
            "calls": assignment_calls(bp),
        }, indent=2, ensure_ascii=False) + "\n",
    }
    return out
