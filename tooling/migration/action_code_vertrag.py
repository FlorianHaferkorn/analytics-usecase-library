#!/usr/bin/env python3
"""Action-Vertrag D-833 Schritt 1 (SOM-001): vier Felder je Action Code aus dem Bestand ableiten.

Ein Action Code soll sagen, mit welchen Parametern er laeuft, wann er ausfuehrbar ist, wer ihn
freigeben darf und in welchem Zustand eine neue Ausfuehrung beginnt (Schema
`tooling/generator/schemas/action_code.schema.json`, `definitions.parameter`, `precondition`,
`review_state`). Die Werte kommen nur aus Feldern, die der Code schon traegt; was dort nicht steht,
wird `nicht_belegt` (Leerstelle), nie geschaetzt:

- `parameters`: `period` aus `scope.default_grain`, `trigger_level` aus `trigger.levels`, je
  Eintrag von `scope.default_perspective` (Pflicht) und `scope.supported_slices` (optional) ein
  `dimension_member`. Die Spalte (`binding`) nennt der Bestand nirgends -> `nicht_belegt`.
- `preconditions`: je Stufe mit `metric_kpi_id` eine pruefbare `kpi_level`-Pruefung, die auf die
  Bedingung verweist (`ref`), statt Vergleich und Schwelle zu kopieren; eine aktive
  `volume_guardrail` als Leitplanke; Stufen mit `composite_rule`/`lifecycle_rule` (nur Prosa) als
  `pruefbar: false`, `status: nicht_belegt`.
- `permitted_role`: je Eintrag von `governance.approvals_required` die Rolle gleichen Titels oder
  Alias aus `core/organization/org_roles.yaml`; ohne Treffer `nicht_belegt`.
- `review`: `required` = es gibt mindestens einen Freigeber; `state: vorgeschlagen`.

Bestehende Felder werden nie ueberschrieben: ein Code, der ein Feld schon traegt, behaelt es
(wer `nicht_belegt` von Hand fuellt, verliert nichts beim naechsten Lauf).

    python -m tooling.migration.action_code_vertrag --report        # Zaehlung, schreibt nichts
    python -m tooling.migration.action_code_vertrag --apply         # fehlende Felder einfuegen
    python -m tooling.migration.action_code_vertrag --check         # Exit 1, wenn ein Code ein Feld nicht traegt
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

import yaml

REPO = Path(__file__).resolve().parents[2]
ACTION_CODES = REPO / "core" / "action_codes"
ORG_ROLES = REPO / "core" / "organization" / "org_roles.yaml"
NICHT_BELEGT = "nicht_belegt"
FELDER = ("parameters", "preconditions", "permitted_role", "review")
START_ZUSTAND = "vorgeschlagen"


def action_code_dateien(root: Path = ACTION_CODES) -> list[Path]:
    """Dieselbe Auswahl wie Stage 1 (`check_schema_validation.ps1`)."""
    return sorted(
        p for p in root.glob("*/*.yaml")
        if p.parent.name != "decision_spines" and not p.name.endswith("_business_case.yaml")
        and p.name != "impactful_15.yaml"
    )


def rollen_index(org_roles: Path = ORG_ROLES) -> dict[str, str]:
    """Titel und Aliase (klein geschrieben) -> role_id."""
    doc = yaml.safe_load(org_roles.read_text(encoding="utf-8"))
    out: dict[str, str] = {}
    for r in doc["roles"]:
        for name in [r["title"], *(r.get("aliases") or [])]:
            out[str(name).strip().lower()] = r["id"]
    return out


def _snake(text: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return s if s and s[0].isalpha() else f"p_{s}"


def parameter(ac: dict[str, Any]) -> list[dict[str, Any]]:
    scope = ac.get("scope") or {}
    levels = (ac.get("trigger") or {}).get("levels") or {}
    out: list[dict[str, Any]] = [
        {"name": "period", "type": "period", "required": True, "grain": scope["default_grain"],
         "source_field": "scope.default_grain"},
        {"name": "trigger_level", "type": "trigger_level", "required": True,
         "allowed_values": sorted(levels), "source_field": "trigger.levels"},
    ]
    namen = {p["name"] for p in out}
    for feld, pflicht in (("default_perspective", True), ("supported_slices", False)):
        for label in scope.get(feld) or []:
            name = _snake(str(label))
            if name in namen:
                continue
            namen.add(name)
            out.append({"name": name, "label": str(label), "type": "dimension_member", "required": pflicht,
                        "binding": NICHT_BELEGT, "source_field": f"scope.{feld}"})
    return out


def vorbedingungen(ac: dict[str, Any]) -> dict[str, Any]:
    tr = ac.get("trigger") or {}
    checks: list[dict[str, Any]] = []
    for name, lv in sorted((tr.get("levels") or {}).items()):
        cond = (lv or {}).get("condition") or {}
        ref = f"trigger.levels.{name}.condition"
        if cond.get("metric_kpi_id"):
            checks.append({"id": f"level_{name.lower()}", "role": "trigger", "kind": "kpi_level", "ref": ref,
                           "kpi_id": cond["metric_kpi_id"], "pruefbar": True})
        else:
            kind = "composite_rule" if "composite_rule" in cond else "lifecycle_rule"
            checks.append({"id": f"level_{name.lower()}", "role": "trigger", "kind": kind, "ref": ref,
                           "pruefbar": False, "status": NICHT_BELEGT})
    vg = (((tr.get("evaluation") or {}).get("minimum_data") or {}).get("volume_guardrail") or {})
    if vg.get("enabled") and vg.get("metric_kpi_id"):
        checks.append({"id": "volume_guardrail", "role": "guardrail", "kind": "volume_guardrail",
                       "ref": "trigger.evaluation.minimum_data.volume_guardrail", "kpi_id": vg["metric_kpi_id"],
                       "pruefbar": True})
    return {"combine": "guardrails_all_and_trigger_any", "checks": checks}


def berechtigte_rolle(ac: dict[str, Any], rollen: dict[str, str]) -> dict[str, Any]:
    freigeber = list((ac.get("governance") or {}).get("approvals_required") or [])
    return {"source_field": "governance.approvals_required",
            "roles": [{"approver": str(a), "role_id": rollen.get(str(a).strip().lower(), NICHT_BELEGT)}
                      for a in freigeber]}


def pruefung(ac: dict[str, Any]) -> dict[str, Any]:
    return {"required": bool((ac.get("governance") or {}).get("approvals_required")), "state": START_ZUSTAND}


def ableiten(ac: dict[str, Any], rollen: dict[str, str]) -> dict[str, Any]:
    """Die vier Felder, wie der Bestand sie hergibt."""
    return {"parameters": parameter(ac), "preconditions": vorbedingungen(ac),
            "permitted_role": berechtigte_rolle(ac, rollen), "review": pruefung(ac)}


def _yaml_block(felder: dict[str, Any]) -> str:
    return yaml.safe_dump(felder, sort_keys=False, allow_unicode=True, default_flow_style=False, width=110)


def einfuegen(text: str, felder: dict[str, Any]) -> str:
    """Fuegt die Felder als Block vor dem Schluessel `quality_rules:` ein (sonst ans Ende). Kommentare und
    Formatierung des Bestands bleiben unberuehrt."""
    block = _yaml_block(felder)
    m = re.search(r"(?m)^quality_rules:", text)
    if m:
        return text[: m.start()] + block + text[m.start():]
    return text.rstrip("\n") + "\n" + block


def zaehlung(codes: dict[str, dict[str, Any]]) -> dict[str, Any]:
    """Zaehler fuer Bericht und Test: Codes, Felder, Leerstellen je Feld."""
    leer = {"parameters.binding": 0, "preconditions.status": 0, "permitted_role.role_id": 0}
    eintraege = {"parameters": 0, "preconditions.checks": 0, "preconditions.pruefbar": 0, "permitted_role.roles": 0}
    codes_mit_leerstelle = {k: 0 for k in leer}
    for ac in codes.values():
        p = [x for x in ac.get("parameters") or []]
        c = (ac.get("preconditions") or {}).get("checks") or []
        r = (ac.get("permitted_role") or {}).get("roles") or []
        eintraege["parameters"] += len(p)
        eintraege["preconditions.checks"] += len(c)
        eintraege["preconditions.pruefbar"] += sum(1 for x in c if x.get("pruefbar"))
        eintraege["permitted_role.roles"] += len(r)
        n = {"parameters.binding": sum(1 for x in p if x.get("binding") == NICHT_BELEGT),
             "preconditions.status": sum(1 for x in c if x.get("status") == NICHT_BELEGT),
             "permitted_role.role_id": sum(1 for x in r if x.get("role_id") == NICHT_BELEGT)}
        for k, v in n.items():
            leer[k] += v
            codes_mit_leerstelle[k] += 1 if v else 0
    return {"codes": len(codes),
            "mit_allen_feldern": sum(1 for ac in codes.values() if all(f in ac for f in FELDER)),
            "eintraege": eintraege, "nicht_belegt": leer, "codes_mit_nicht_belegt": codes_mit_leerstelle,
            "review_state": sorted({(ac.get("review") or {}).get("state") for ac in codes.values()} - {None})}


def lade(dateien: list[Path]) -> dict[str, dict[str, Any]]:
    return {str(p.relative_to(REPO)): yaml.safe_load(p.read_text(encoding="utf-8")) for p in dateien}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--apply", action="store_true")
    g.add_argument("--check", action="store_true")
    g.add_argument("--report", action="store_true")
    a = ap.parse_args(argv)
    dateien = action_code_dateien()
    rollen = rollen_index()
    if a.apply:
        for p in dateien:
            text = p.read_text(encoding="utf-8")
            ac = yaml.safe_load(text)
            fehlend = {k: v for k, v in ableiten(ac, rollen).items() if k not in ac}
            if fehlend:
                p.write_text(einfuegen(text, fehlend), encoding="utf-8", newline="\n")
    codes = lade(dateien)
    z = zaehlung(codes)
    if a.check:
        ohne = sorted(k for k, ac in codes.items() if not all(f in ac for f in FELDER))
        for k in ohne:
            print(f"FEHLT: {k}", file=sys.stderr)
        print(f"action_code_vertrag: {z['mit_allen_feldern']}/{z['codes']} Codes mit allen {len(FELDER)} Feldern")
        return 1 if ohne or not codes else 0
    print(json.dumps(z, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
