"""WB-009 first increment: rate-free commercial and staffing impact of a decision alternative.

The same hypothetical selection as the WB-008 comparison is evaluated against the tenant
price canon through the mirrored calculation core. This module does no arithmetic on rates
and returns no money: hours per canon role and rate class, delivery bands, capacity notes
and role-coverage gaps, each for baseline and alternative. Prices stay with the core and the
tenant file outside the repository (ADR-0019, ADR-0020). Nothing is written.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

from tooling.superversion import preis_kanon_mandant as pkm

from .alternative_impact import _fingerprint, evaluate_alternative
from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
#: Keys that would carry money or rate content. The output is checked against them before
#: it is returned, so a future change cannot leak a price by adding a field.
FORBIDDEN_KEYS = re.compile(r"(kostensatz|verkaufssatz|satz_eur|preis|price|rate|marge|margin|risiko|risk|eur\b|_eur|festpreis|selbstkosten|cost_value)", re.I)


def _derived(name: str, architecture: dict) -> float:
    selected = set(architecture["environments"]["recommended"])
    if name == "selected_stage_count":
        return float(len(selected))
    if name == "selected_workspace_count":
        return float(sum(1 for row in architecture.get("physical_workspaces", []) if row["environment"] in selected))
    if name == "selected_item_count":
        return float(sum(1 for row in architecture.get("physical_items", []) if row["environment"] in selected))
    raise ValueError(f"Unknown derived quantity: {name}")


def _quantities(canon: dict, architecture: dict) -> tuple[dict[str, float], dict[str, str]]:
    values, provenance = {}, {}
    for name, spec in sorted(canon["quantities"].items()):
        if "derived_from" in spec:
            values[name] = _derived(spec["derived_from"], architecture)
            provenance[name] = f"derived: {spec['derived_from']}"
        else:
            values[name] = float(spec["value"])
            provenance[name] = spec["provenance"]
    return values, provenance


def _side(tenant: dict, plan: dict, architecture: dict, decision_ref: str) -> dict:
    """One package state through the core. Hours and bands only; no money."""
    core = pkm.rechenkern()
    role_map = plan.get("canon_role_map") or {}
    packages, gaps, pairs = [], [], []
    hours_by_role: dict[str, float] = {}
    hours_by_class: dict[str, float] = {}
    demanded = {role for row in plan.get("work_packages", []) for role in row["role_refs"]}
    for row in plan.get("work_packages", []):
        canon = row.get("canon")
        if canon is None:
            if decision_ref in row["decision_refs"]:
                gaps.append({"id": f"unmapped_work_package:{row['id']}", "detail": "Work package linked to the decision has no canon package; its hours are not evaluated."})
            continue
        try:
            package = core.paket(tenant, canon["package_ref"])
        except (KeyError, ValueError, SystemExit):
            gaps.append({"id": f"unknown_canon_package:{row['id']}", "detail": f"Canon package {canon['package_ref']} is not in the tenant file."})
            continue
        quantities, provenance = _quantities(canon, architecture)
        per_role = pkm.stunden_je_rolle(tenant, canon["package_ref"], quantities)
        per_class = core.stunden(package, quantities)
        low, high = core.lieferzeit_band(package, quantities)
        days = pkm.personentage(tenant, canon["package_ref"], quantities)
        for role, value in per_role.items():
            hours_by_role[role] = hours_by_role.get(role, 0.0) + value
        for rate_class, value in per_class.items():
            hours_by_class[rate_class] = hours_by_class.get(rate_class, 0.0) + value
        pairs.append((canon["package_ref"], quantities))
        packages.append({"work_package_ref": row["id"], "package_ref": canon["package_ref"],
                         "quantities": quantities, "quantity_provenance": provenance,
                         "hours_by_canon_role": dict(sorted(per_role.items())),
                         "delivery_band_workdays": [low, high], "band_status": core.lieferzeit_status(package),
                         "person_days_by_role": [{key: item[key] for key in ("rolle", "beteiligung_pct", "tage_min", "tage_max", "herkunft")} for item in days]})
    mapped_canon_roles = {role_map[role] for role in demanded if role in role_map}
    for role in sorted(demanded - set(role_map)):
        gaps.append({"id": f"unmapped_plan_role:{role}", "detail": "Plan role has no canon role mapping."})
    for role in sorted(hours_by_role):
        if role not in mapped_canon_roles:
            gaps.append({"id": f"canon_role_without_plan_demand:{role}",
                         "detail": f"The canon packages need {hours_by_role[role]:g} h of {role}, but no plan role that maps to it is demanded."})
    capacity = pkm.kapazitaetspruefung(tenant, pairs) if pairs else {"fenster_at_parallel": 0.0, "fenster_at_seriell": 0.0, "rollen": [], "vermerke": []}
    return {"packages": packages, "hours_by_canon_role": dict(sorted(hours_by_role.items())),
            "hours_by_canon_class": dict(sorted(hours_by_class.items())),
            "window_workdays": {"parallel": capacity["fenster_at_parallel"], "serial": capacity["fenster_at_seriell"]},
            "capacity_notes": capacity["vermerke"],
            "capacity_by_role": [{key: row.get(key) for key in ("rolle", "stunden", "passt", "vermerk")} for row in capacity["rollen"]],
            "gaps": gaps}


def _delta(before: dict[str, float], after: dict[str, float]) -> dict[str, dict]:
    return {key: {"before": before.get(key, 0.0), "after": after.get(key, 0.0)}
            for key in sorted(set(before) | set(after)) if before.get(key, 0.0) != after.get(key, 0.0)}


def assert_rate_free(value: Any, path: str = "") -> None:
    """Refuse any output key that could carry money or rate content."""
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "price_values_embedded":
                if item is not False:
                    raise ValueError("Commercial impact output must declare price_values_embedded: false")
                continue
            if FORBIDDEN_KEYS.search(str(key)):
                raise ValueError(f"Commercial impact output would carry a rate or price field: {path}{key}")
            assert_rate_free(item, f"{path}{key}.")
    elif isinstance(value, list):
        for index, item in enumerate(value):
            assert_rate_free(item, f"{path}{index}.")


def compare_commercial(repository: ProjectPackageRevisionRepository, project_ref: str, baseline_revision: str,
                       decision_ref: str, option_ref: str, *, tenant: dict | None = None) -> dict:
    """Rate-free commercial comparison. ``tenant`` defaults to the price-canon tenant directory."""
    state = evaluate_alternative(repository, project_ref, baseline_revision, decision_ref, option_ref)
    common = {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
              "decision_ref": decision_ref, "alternative_option_ref": option_ref, "price_values_embedded": False,
              "approval_granted": False, "tenant_actions_performed": False}
    if state["blockers"]:
        raise ValueError("Alternative impact is blocked; resolve it before evaluating commercial impact: " + "; ".join(state["blockers"]))
    try:
        tenant = tenant if tenant is not None else pkm.lade_mandant()
    except pkm.MandantenwerteFehlen as error:
        result = {**common, "status": "not_checked", "reason": str(error)}
        return {**result, "commercial_impact_sha256": canonical_sha256(result)}
    findings = pkm.pruefe_mandant(tenant)
    if findings:
        result = {**common, "status": "tenant_findings", "findings": findings}
        return {**result, "commercial_impact_sha256": canonical_sha256(result)}

    modules = state["compiler"]["modules"]
    base = _side(tenant, modules.get("plan") or {}, modules["architecture_input"], decision_ref)
    alt = _side(tenant, state["projected"]["plan"] or {}, state["projected"]["architecture_input"], decision_ref)
    if state["before_fingerprint"] != _fingerprint(repository):
        raise RuntimeError("Baseline repository changed during a read-only comparison")
    result = {**common, "status": "evaluated",
              "tenant_fingerprint_sha256": canonical_sha256(tenant),
              "baseline": base, "alternative": alt,
              "delta": {"hours_by_canon_role": _delta(base["hours_by_canon_role"], alt["hours_by_canon_role"]),
                        "hours_by_canon_class": _delta(base["hours_by_canon_class"], alt["hours_by_canon_class"]),
                        "window_workdays": {"before": base["window_workdays"], "after": alt["window_workdays"]},
                        "new_gaps": sorted({gap["id"] for gap in alt["gaps"]} - {gap["id"] for gap in base["gaps"]}),
                        "resolved_gaps": sorted({gap["id"] for gap in base["gaps"]} - {gap["id"] for gap in alt["gaps"]})},
              "limitations": ["Hours and bands come from the tenant price canon through the mirrored core; no price, rate or margin is returned.",
                              "Named staffing, calendar dates and proposal documents are not evaluated.",
                              "Quantities are package assumptions or derived from the selected architecture; they are not measured delivery data."]}
    assert_rate_free(result)
    return {**result, "commercial_impact_sha256": canonical_sha256(result)}


def _number(value: float) -> str:
    return f"{value:g}"


def render_proposal_assumptions(result: dict, side: str = "alternative") -> str:
    """Rate-free proposal-assumptions section for one side of an evaluated comparison.

    It lists what the offer rests on: canon packages, quantities with provenance, delivery
    bands, role participation and the open points. Hours per class, rates and prices stay out
    by construction: the renderer reads only these fields.
    """
    if result.get("status") != "evaluated":
        raise ValueError("Proposal assumptions need an evaluated comparison, not " + str(result.get("status")))
    if side not in {"baseline", "alternative"}:
        raise ValueError("Side must be baseline or alternative")
    data = result[side]
    option = result["alternative_option_ref"] if side == "alternative" else "accepted baseline"
    lines = [f"## Proposal assumptions ({option.replace('_', ' ')})", "",
             f"Basis: decision `{result['decision_ref']}`, package revision `{result['baseline_revision_hash'][:12]}`"
             f"{', hypothetical alternative' if side == 'alternative' else ''}. Values are assumptions until confirmed; "
             "no rate, price or named person is part of this section.", ""]
    for row in data["packages"]:
        low, high = row["delivery_band_workdays"]
        lines.append(f"### {row['work_package_ref'].replace('_', ' ')}")
        lines.append("")
        lines.append(f"- Canon package: `{row['package_ref']}`")
        for name, value in sorted(row["quantities"].items()):
            source = row["quantity_provenance"][name]
            lines.append(f"- Quantity {name.replace('_', ' ')}: {_number(value)} ({source})")
        lines.append(f"- Delivery band: {_number(low)}–{_number(high)} workdays ({row['band_status']})")
        roles = ", ".join(f"{item['rolle']} {_number(item['beteiligung_pct'])} %" for item in row["person_days_by_role"])
        if roles:
            lines.append(f"- Role participation: {roles}")
        lines.append("")
    window = data["window_workdays"]
    lines += [f"Delivery window if packages run in parallel: {_number(window['parallel'])} workdays; in sequence: {_number(window['serial'])} workdays.", ""]
    open_points = [gap["detail"] for gap in data["gaps"]] + list(data["capacity_notes"])
    lines.append("### Open points before the offer")
    lines.append("")
    lines += [f"- {item}" for item in open_points] or ["- None recorded."]
    return "\n".join(lines).rstrip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--schemas", required=True, type=Path)
    parser.add_argument("--assumptions", choices=("baseline", "alternative"),
                        help="Also return the rate-free proposal-assumptions section for this side as Markdown")
    args = parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read(100_001))
        if not isinstance(payload, dict) or set(payload) != {"project_ref", "revision_hash", "decision_ref", "option_ref"}:
            raise ValueError("Invalid comparison request")
        if not re.fullmatch(r"[a-f0-9]{64}", str(payload["revision_hash"])):
            raise ValueError("Invalid request revision")
        value = compare_commercial(ProjectPackageRevisionRepository(args.repository, args.schemas), payload["project_ref"],
                                   payload["revision_hash"], payload["decision_ref"], payload["option_ref"])
        if args.assumptions:
            value = {**value, "proposal_assumptions_markdown": render_proposal_assumptions(value, args.assumptions)}
        print(json.dumps({"ok": True, "value": value}, ensure_ascii=True))
        return 0
    except (ValueError, OSError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
