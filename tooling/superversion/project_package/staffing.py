"""WB-009: named staffing of a decision alternative, returned to an authorised caller only.

The rate-free comparison says how many hours each rate class (role × location) needs. This
module puts names against those hours: who of the roster can carry them, how many weeks that
takes with the people available, and where nobody is. Names are personal data of colleagues,
so the same rules as the price delta apply:

* the roster lives next to the tenant price canon, outside the repository
  (``$PREIS_KANON_MANDANTEN_DIR/besetzung.yaml``);
* the result is marked ``persist: false`` and is never written; the Studio route answers
  ``no-store`` to an admin and audits only that staffing was viewed, without names;
* a rate class without a person is a gap, never silently merged into another class.

Hours come from ``commercial_impact._side`` (the mirrored core), not from here.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import re
import sys
from pathlib import Path

import yaml

from tooling.superversion import preis_kanon_mandant as pkm

from .alternative_impact import _fingerprint, evaluate_alternative
from .commercial_impact import _side as commercial_side
from .hashes import canonical_sha256
from .repository import ProjectPackageRevisionRepository

VERSION = "1.0.0"
DATEINAME = "besetzung.yaml"


class BesetzungFehlt(RuntimeError):
    """No roster next to the tenant price canon."""


def lade_besetzung(verzeichnis: Path | None = None) -> list[dict]:
    """The roster from ``besetzung.yaml`` next to the tenant file."""
    d = verzeichnis or pkm.mandanten_dir()
    if d is None or not (d / DATEINAME).is_file():
        raise BesetzungFehlt(f"No {DATEINAME} next to the price canon ({pkm.ENV_DIR}).")
    data = yaml.safe_load((d / DATEINAME).read_text(encoding="utf-8")) or {}
    personen = data.get("personen")
    if not isinstance(personen, list):
        raise ValueError(f"{DATEINAME}: `personen` must be a list")
    return personen


def pruefe_besetzung(personen: list[dict], tenant: dict) -> list[str]:
    """Roster rules; empty = fine. Findings name the row, never the person."""
    befunde: list[str] = []
    klassen = set(tenant.get("satzklassen") or {})
    for i, p in enumerate(personen, 1):
        if not isinstance(p, dict) or not str(p.get("name") or "").strip():
            befunde.append(f"Row {i}: name missing")
            continue
        klasse = f"{p.get('rolle')}_{p.get('standort')}"
        if klasse not in klassen:
            befunde.append(f"Row {i}: role/location {klasse} is not a rate class of the price canon")
        stunden = p.get("stunden_je_woche")
        if not isinstance(stunden, (int, float)) or not 1 <= float(stunden) <= 60:
            befunde.append(f"Row {i}: hours per week must be between 1 and 60")
        ab = p.get("verfuegbar_ab")
        if ab not in (None, "") and not isinstance(ab, dt.date):
            try:
                dt.date.fromisoformat(str(ab))
            except ValueError:
                befunde.append(f"Row {i}: available-from must be a date (YYYY-MM-DD)")
    return befunde


def _datum(value) -> dt.date | None:
    if value in (None, ""):
        return None
    return value if isinstance(value, dt.date) else dt.date.fromisoformat(str(value))


def _besetze(hours_by_class: dict[str, float], personen: list[dict]) -> dict:
    klassen, gaps = [], []
    for klasse, stunden in sorted(hours_by_class.items()):
        if stunden <= 0:
            continue
        team = [p for p in personen if f"{p.get('rolle')}_{p.get('standort')}" == klasse]
        if not team:
            gaps.append({"rate_class": klasse, "hours": stunden, "detail": "Nobody on the roster carries this role and location."})
            continue
        kapazitaet = sum(float(p["stunden_je_woche"]) for p in team)
        start = max((d for d in (_datum(p.get("verfuegbar_ab")) for p in team) if d), default=None)
        klassen.append({"rate_class": klasse, "hours": stunden, "weekly_capacity": kapazitaet,
                        "weeks": round(stunden / kapazitaet, 2),
                        "earliest_full_team": start.isoformat() if start else None,
                        "people": [{"name": str(p["name"]).strip(), "hours": round(stunden * float(p["stunden_je_woche"]) / kapazitaet, 2),
                                    "hours_per_week": float(p["stunden_je_woche"])} for p in team]})
    weeks = max((row["weeks"] for row in klassen), default=0.0)
    return {"classes": klassen, "gaps": gaps, "weeks_in_parallel": weeks,
            "people": sorted({person["name"] for row in klassen for person in row["people"]})}


def compare_staffing(repository: ProjectPackageRevisionRepository, project_ref: str, baseline_revision: str,
                     decision_ref: str, option_ref: str, *, tenant: dict | None = None,
                     personen: list[dict] | None = None) -> dict:
    """Named staffing for baseline and alternative. For an authorised caller; never persisted."""
    state = evaluate_alternative(repository, project_ref, baseline_revision, decision_ref, option_ref)
    common = {"schema_version": VERSION, "project_ref": project_ref, "baseline_revision_hash": baseline_revision,
              "decision_ref": decision_ref, "alternative_option_ref": option_ref,
              "personal_data": True, "persist": False, "approval_granted": False}
    if state["blockers"]:
        raise ValueError("Alternative impact is blocked; resolve it before staffing: " + "; ".join(state["blockers"]))
    try:
        tenant = tenant if tenant is not None else pkm.lade_mandant()
        personen = personen if personen is not None else lade_besetzung()
    except (pkm.MandantenwerteFehlen, BesetzungFehlt) as error:
        return {**common, "personal_data": False, "status": "not_checked", "reason": str(error)}
    findings = pkm.pruefe_mandant(tenant) + pruefe_besetzung(personen, tenant)
    if findings:
        return {**common, "personal_data": False, "status": "findings", "findings": findings}
    modules = state["compiler"]["modules"]
    base_hours = commercial_side(tenant, modules.get("plan") or {}, modules["architecture_input"], decision_ref)["hours_by_canon_class"]
    alt_hours = commercial_side(tenant, state["projected"]["plan"] or {}, state["projected"]["architecture_input"], decision_ref)["hours_by_canon_class"]
    if state["before_fingerprint"] != _fingerprint(repository):
        raise RuntimeError("Baseline repository changed during a read-only comparison")
    base, alt = _besetze(base_hours, personen), _besetze(alt_hours, personen)
    return {**common, "status": "evaluated", "roster_fingerprint_sha256": canonical_sha256(json.loads(json.dumps(personen, default=str))),
            "baseline": base, "alternative": alt,
            "delta": {"weeks_in_parallel": {"before": base["weeks_in_parallel"], "after": alt["weeks_in_parallel"]},
                      "people_no_longer_needed": sorted(set(base["people"]) - set(alt["people"])),
                      "people_newly_needed": sorted(set(alt["people"]) - set(base["people"])),
                      "new_gaps": sorted({g["rate_class"] for g in alt["gaps"]} - {g["rate_class"] for g in base["gaps"]})},
            "limitations": ["Hours per rate class come from the price canon through the mirrored core; weeks assume the listed weekly hours are free for this project.",
                            "Names are personal data: shown to admins, not written to the package, outputs or audit trail.",
                            "No calendar, holidays or parallel projects are considered."]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--repository", required=True, type=Path)
    parser.add_argument("--schemas", required=True, type=Path)
    args = parser.parse_args()
    try:
        payload = json.loads(sys.stdin.read(100_001))
        if not isinstance(payload, dict) or set(payload) != {"project_ref", "revision_hash", "decision_ref", "option_ref"}:
            raise ValueError("Invalid staffing request")
        if not re.fullmatch(r"[a-f0-9]{64}", str(payload["revision_hash"])):
            raise ValueError("Invalid request revision")
        value = compare_staffing(ProjectPackageRevisionRepository(args.repository, args.schemas), payload["project_ref"],
                                 payload["revision_hash"], payload["decision_ref"], payload["option_ref"])
        print(json.dumps({"ok": True, "value": value}, ensure_ascii=True))
        return 0
    except (ValueError, OSError, RuntimeError, KeyError) as error:
        print(json.dumps({"ok": False, "error": str(error), "status": 409}))
        return 1
    except Exception as error:  # noqa: BLE001 - the bridge needs JSON, never a bare traceback
        print(json.dumps({"ok": False, "error": f"Staffing failed: {type(error).__name__}", "status": 500}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
