#!/usr/bin/env python3
"""Action-Vertrag (D-833 Schritt 1, SOM-001): was das Schema allein nicht pruefen kann.

Das Schema (`tooling/generator/schemas/action_code.schema.json`) prueft die Form von `parameters`,
`preconditions`, `permitted_role` und `review`. Dieses Tor prueft die Bezuege (Golden Thread:
referenzieren, nicht kopieren):

- V1 jede pruefbare Vorbedingung nennt eine KPI des Katalogs (`core/kpi_catalog/kpis/<id>.yaml`);
- V2 ihr `ref` loest im selben Action Code auf, und dort steht dieselbe `metric_kpi_id` und eine
  Schwelle (`value` oder `lower`/`upper`) bzw. bei der Leitplanke ein `value`;
- V3 jede `role_id` ausser `nicht_belegt` steht in `core/organization/org_roles.yaml`, und ihr Titel
  oder Alias ist der `approver`-Text;
- V4 die `approver` sind genau `governance.approvals_required` (Reihenfolge eingeschlossen),
  `review.required` passt dazu;
- V5 `trigger_level.allowed_values` sind genau die Stufen in `trigger.levels`, `period.grain` ist
  `scope.default_grain`;
- V6 jede Stufe hat genau eine Vorbedingung.

Exit 0 = geprueft, keine Befunde; 1 = Befunde; 2 = nicht geprueft (keine Action Codes gefunden,
Katalog oder Rollenregister fehlt) — "nichts gefunden" ist nicht "nicht gelaufen".

    python tooling/validation/check_action_contract.py [--repo-root .] [--json]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

import yaml

NICHT_BELEGT = "nicht_belegt"


def action_code_dateien(root: Path) -> list[Path]:
    """Dieselbe Auswahl wie Stage 1 (`check_schema_validation.ps1`)."""
    return sorted(
        p for p in (root / "core" / "action_codes").glob("*/*.yaml")
        if p.parent.name != "decision_spines" and not p.name.endswith("_business_case.yaml")
        and p.name != "impactful_15.yaml"
    )


def _aufloesen(ac: dict[str, Any], ref: str) -> Any:
    cur: Any = ac
    for teil in ref.split("."):
        if not isinstance(cur, dict) or teil not in cur:
            return None
        cur = cur[teil]
    return cur


def _hat_schwelle(cond: dict[str, Any]) -> bool:
    th = cond.get("threshold") or {}
    return th.get("value") is not None or (th.get("lower") is not None and th.get("upper") is not None)


def pruefe_code(ac: dict[str, Any], katalog: set[str], rollen: dict[str, dict[str, Any]]) -> list[str]:
    """Befunde eines Action Codes (leer = in Ordnung)."""
    cid = ac.get("id", "?")
    befunde: list[str] = []
    checks = (ac.get("preconditions") or {}).get("checks") or []
    for c in checks:
        if not c.get("pruefbar"):
            continue
        kpi = c.get("kpi_id")
        if kpi not in katalog:
            befunde.append(f"{cid} V1 {c.get('id')}: {kpi} nicht im KPI-Katalog")
        ziel = _aufloesen(ac, str(c.get("ref") or ""))
        if not isinstance(ziel, dict):
            befunde.append(f"{cid} V2 {c.get('id')}: ref {c.get('ref')} loest nicht auf")
            continue
        if ziel.get("metric_kpi_id") != kpi:
            soll = ziel.get("metric_kpi_id")
            befunde.append(f"{cid} V2 {c.get('id')}: kpi_id {kpi} != metric_kpi_id {soll} unter ref")
        if c.get("kind") == "kpi_level" and not _hat_schwelle(ziel):
            befunde.append(f"{cid} V2 {c.get('id')}: keine Schwelle unter ref")
        if c.get("kind") == "volume_guardrail" and (ziel.get("value") is None or not ziel.get("enabled")):
            befunde.append(f"{cid} V2 {c.get('id')}: Leitplanke ohne value oder nicht enabled")
    freigeber = list((ac.get("governance") or {}).get("approvals_required") or [])
    roles = (ac.get("permitted_role") or {}).get("roles") or []
    if [r.get("approver") for r in roles] != freigeber:
        befunde.append(f"{cid} V4: approver {[r.get('approver') for r in roles]} != approvals_required {freigeber}")
    if (ac.get("review") or {}).get("required") != bool(freigeber):
        befunde.append(f"{cid} V4: review.required passt nicht zu approvals_required")
    for r in roles:
        rid = r.get("role_id")
        if rid == NICHT_BELEGT:
            continue
        rolle = rollen.get(rid)
        if rolle is None:
            befunde.append(f"{cid} V3: role_id {rid} nicht in org_roles.yaml")
            continue
        namen = {str(n).strip().lower() for n in [rolle.get("title"), *(rolle.get("aliases") or [])] if n}
        if str(r.get("approver", "")).strip().lower() not in namen:
            befunde.append(f"{cid} V3: role_id {rid} ({rolle.get('title')}) ist nicht '{r.get('approver')}'")
    params = {p.get("type"): p for p in ac.get("parameters") or []}
    levels = sorted(((ac.get("trigger") or {}).get("levels") or {}))
    if (params.get("trigger_level") or {}).get("allowed_values") != levels:
        befunde.append(f"{cid} V5: trigger_level.allowed_values != trigger.levels {levels}")
    if (params.get("period") or {}).get("grain") != (ac.get("scope") or {}).get("default_grain"):
        befunde.append(f"{cid} V5: period.grain != scope.default_grain")
    refs = [c.get("ref") for c in checks if c.get("role") == "trigger"]
    for name in levels:
        n = refs.count(f"trigger.levels.{name}.condition")
        if n != 1:
            befunde.append(f"{cid} V6: Stufe {name} hat {n} Vorbedingungen statt 1")
    return befunde


def lade_katalog(root: Path) -> set[str]:
    return {p.stem for p in (root / "core" / "kpi_catalog" / "kpis").glob("KPI-*.yaml")}


def lade_rollen(root: Path) -> dict[str, dict[str, Any]]:
    doc = yaml.safe_load((root / "core" / "organization" / "org_roles.yaml").read_text(encoding="utf-8"))
    return {r["id"]: r for r in doc["roles"]}


def pruefe(root: Path) -> tuple[int, list[str]]:
    """(Zahl geprueften Codes, Befunde)."""
    katalog, rollen = lade_katalog(root), lade_rollen(root)
    befunde: list[str] = []
    dateien = action_code_dateien(root)
    for p in dateien:
        befunde += pruefe_code(yaml.safe_load(p.read_text(encoding="utf-8")), katalog, rollen)
    return len(dateien), befunde


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    ap.add_argument("--repo-root", type=Path, default=Path(__file__).resolve().parents[2])
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    root = a.repo_root.resolve()
    try:
        n, befunde = pruefe(root)
    except (OSError, KeyError, yaml.YAMLError) as e:
        print(f"check_action_contract: NICHT GEPRUEFT ({type(e).__name__}: {e})", file=sys.stderr)
        return 2
    if n == 0:
        print("check_action_contract: NICHT GEPRUEFT (0 Action Codes gefunden)", file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps({"codes": n, "befunde": befunde}, ensure_ascii=False, indent=2))
    else:
        for b in befunde:
            print(f"FAIL {b}")
        print(f"check_action_contract: {n} Action Codes geprueft, {len(befunde)} Befunde")
    return 1 if befunde else 0


if __name__ == "__main__":
    raise SystemExit(main())
