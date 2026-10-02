"""kapazitaet_stufen — welche Kapazitaet traegt welchen Workspace, je Stufe (D-596).

D-596 (30.09.2026, Entscheidung Florian): Produktion und Nicht-Produktion laufen auf
getrennten Kapazitaeten, innerhalb der beiden Gruppen konsolidiert. Anlass: Microsoft
empfiehlt eine eigene Kapazitaet je Umgebung (Learn ``enterprise/capacity-planning-*``,
``fundamentals/understand-best-practices-fabric-cicd``, gelesen 29.09.2026), und Smoothing
sowie Drosselung wirken je Kapazitaet — Entwicklungs- und Testlast drosselt sonst die
Produktion. Option (c), eine eigene Kapazitaet je Tier-1-Workload, bleibt ein Angebot und
wird ueber das vorhandene Feld ``workspaces[].surge_class = mission_critical`` sichtbar,
nicht automatisch gebaut.

Der Bauplan traegt die Zuordnung in zwei Feldern, die es beide schon gibt oder die dafuer
dazukommen:

* ``mesh.domains[].workspaces[].stage`` — die Stufe eines Workspace;
* ``platform.capacities[].stages`` — die Stufen, deren Workspaces auf dieser Kapazitaet
  laufen (neu mit D-596), neben dem vorhandenen ``domain``.

Die Aufloesung ist eine reine Funktion und die **eine** Stelle der Regel: Terraform-Emitter
und Kapazitaets-Runbook lesen sie hier, statt sie je fuer sich nachzubauen.

Regel (in dieser Reihenfolge, der erste Treffer gewinnt):

1. Kapazitaet mit passender Domaene **und** passender Stufe;
2. Kapazitaet ohne Domaene mit passender Stufe;
3. Kapazitaet mit passender Domaene ohne ``stages``;
4. Kapazitaet ohne Domaene und ohne ``stages`` (der Einzelkapazitaetsfall von heute).

Ein Workspace ohne Stufe (ungestufter Bauplan) gilt als Produktion: er ist der einzige
Satz, und auf ihm arbeiten die Nutzer.
"""
from __future__ import annotations

from typing import Any

#: Stufe → Stufengruppe (D-596). Alles, was nicht Produktion ist, teilt sich eine Kapazitaet.
STUFENGRUPPE: dict[str, str] = {"prod": "prod", "test": "non_prod", "dev": "non_prod"}
#: Die Stufengruppen in Ausgabereihenfolge.
GRUPPEN: tuple[str, ...] = ("prod", "non_prod")
GRUPPEN_LABEL: dict[str, str] = {"prod": "Produktion", "non_prod": "Nicht-Produktion"}

#: Was offen ist, wenn der Bauplan fuer eine Stufengruppe keine eigene Kapazitaet nennt.
ENTSCHEIDUNG_NICHT_PROD = (
    "D-596: Entwicklung und Test laufen auf einer eigenen, pausierbaren Kapazitaet, getrennt "
    "von der Produktion. Name und SKU der Nicht-Produktions-Kapazitaet im Fabric-Adminportal "
    "ablesen (oder beschaffen) und als `capacities[]` mit `stages: [\"dev\", \"test\"]` in die "
    "Eingaben schreiben. Wer bewusst konsolidiert, schreibt es als Abweichung mit Grund in "
    "`governance.decisions`.")


#: ``platform.capacities[].purpose`` der Kapazitaet, die das zentrale Monitoring-Eventhouse
#: traegt (01.10.2026, OPS-MONITORING: Learn empfiehlt dafuer eine eigene Kapazitaet). Sie
#: traegt keine Arbeits-Workspaces: ohne ``stages`` und ``domain`` fiele sie sonst unter Regel 4
#: und bekaeme jede Stufe, die kein anderer Eintrag beansprucht.
ZWECK_MONITORING = "monitoring"


def ist_monitoring_kapazitaet(cap: dict) -> bool:
    return str(cap.get("purpose") or "").strip().lower() == ZWECK_MONITORING


def monitoring_kapazitaet(bp: dict) -> dict | None:
    """Die Kapazitaet mit ``purpose: monitoring``, falls der Bauplan eine nennt (die erste)."""
    plat = bp.get("platform") or {}
    return next((k for k in plat.get("capacities") or []
                 if isinstance(k, dict) and ist_monitoring_kapazitaet(k)), None)


def stufengruppe(stage: str | None) -> str:
    """Die Stufengruppe eines Workspace. Ohne Stufe: Produktion (siehe Moduldoku)."""
    return STUFENGRUPPE.get(str(stage or "").strip(), "prod")


def _kapazitaeten(bp: dict) -> list[dict]:
    plat = bp.get("platform") or {}
    kaps = [k for k in (plat.get("capacities") or [])
            if isinstance(k, dict) and not ist_monitoring_kapazitaet(k)]
    if not kaps and str(plat.get("capacity") or "").strip():
        kaps = [{"name": str(plat["capacity"]).strip()}]
    return kaps


def kapazitaet_fuer(bp: dict, domain: str, stage: str | None) -> dict | None:
    """Die Kapazitaet, die einen Workspace der Domaene ``domain`` in Stufe ``stage`` traegt."""
    kaps = _kapazitaeten(bp)
    st = str(stage or "").strip() or "prod"

    def passt_dom(k: dict) -> bool:
        return str(k.get("domain") or "").strip() == domain

    def ohne_dom(k: dict) -> bool:
        return not str(k.get("domain") or "").strip()

    def passt_stufe(k: dict) -> bool:
        return st in (k.get("stages") or [])

    def ohne_stufe(k: dict) -> bool:
        return not k.get("stages")

    for bedingung in ((passt_dom, passt_stufe), (ohne_dom, passt_stufe),
                      (passt_dom, ohne_stufe), (ohne_dom, ohne_stufe)):
        treffer = next((k for k in kaps if bedingung[0](k) and bedingung[1](k)), None)
        if treffer is not None:
            return treffer
    return None


def traegt_produktion(bp: dict, cap: dict) -> bool:
    """Traegt diese Kapazitaet Produktions-Workspaces (D-607: dann ``prevent_destroy``)?

    Dieselbe Regel wie ``kapazitaet_fuer`` und die Schema-Beschreibung von
    ``platform.capacities[].stages``: mit ``stages`` entscheidet ``"prod" in stages``; ohne
    ``stages`` traegt die Kapazitaet jede Stufe, die kein anderer Eintrag beansprucht — sie ist
    Produktion, sobald ``kapazitaet_fuer`` fuer die Stufe ``prod`` in irgendeiner Domaene bei ihr
    landet. Geprueft werden die Domaenen des Bauplans und eine unbekannte (leere) Domaene, damit
    eine ungestufte Einzelkapazitaet auch ohne Mesh als Produktion gilt. Im Zweifel Produktion:
    ein faelschlicher Schutz kostet eine Zeile im Diff, ein fehlender die Produktivkapazitaet.
    """
    stufen = cap.get("stages") or []
    if stufen:
        return "prod" in stufen
    dom = str(cap.get("domain") or "").strip()
    domaenen = {dom} if dom else (
        {str(d.get("name") or "") for d in (bp.get("mesh") or {}).get("domains") or []} | {""})
    return any(kapazitaet_fuer(bp, d, "prod") is cap for d in domaenen)


def zuordnung(bp: dict) -> list[dict[str, Any]]:
    """Je Workspace: Domaene, Stufe, Stufengruppe, Kapazitaet (Name oder None), Tier-1-Flag.

    Sortiert nach Stufengruppe, Domaene, Workspace — deterministisch fuer Emitter.
    """
    aus: list[dict[str, Any]] = []
    for d in (bp.get("mesh") or {}).get("domains") or []:
        dname = str(d.get("name") or "")
        for ws in d.get("workspaces") or []:
            kap = kapazitaet_fuer(bp, dname, ws.get("stage"))
            aus.append({
                "workspace": ws["name"],
                "domain": dname,
                "stage": ws.get("stage") or "",
                "gruppe": stufengruppe(ws.get("stage")),
                "kapazitaet": (kap or {}).get("name") or None,
                "kapazitaet_zielbild": bool((kap or {}).get("zielbild")),
                "tier1": ws.get("surge_class") == "mission_critical",
            })
    aus.sort(key=lambda r: (GRUPPEN.index(r["gruppe"]), r["domain"], r["workspace"]))
    return aus


def gruppen_im_bauplan(bp: dict) -> list[str]:
    """Welche Stufengruppen der Bauplan tatsaechlich hat (ungestuft: nur Produktion)."""
    da = {r["gruppe"] for r in zuordnung(bp)}
    return [g for g in GRUPPEN if g in da] or ["prod"]


def befunde(bp: dict) -> list[str]:
    """Abweichungen von D-596. Leer = getrennt oder nicht anwendbar (ungestufter Bauplan).

    Gemeldet wird, wenn Produktion und Nicht-Produktion auf **derselben benannten**
    Kapazitaet landen, und wenn fuer Nicht-Produktion keine eigene Kapazitaet genannt ist.
    """
    rows = zuordnung(bp)
    if not any(r["gruppe"] == "non_prod" for r in rows):
        return []
    aus: list[str] = []
    prod = {r["kapazitaet"] for r in rows if r["gruppe"] == "prod" and r["kapazitaet"]}
    nprod = {r["kapazitaet"] for r in rows if r["gruppe"] == "non_prod" and r["kapazitaet"]}
    for gemeinsam in sorted(prod & nprod):
        aus.append(f"Kapazitaet `{gemeinsam}` traegt Produktion und Nicht-Produktion — "
                   "Abweichung von D-596; Grund in `governance.decisions` festhalten oder trennen.")
    kaps = _kapazitaeten(bp)
    if not any(set(k.get("stages") or []) & {"dev", "test"} for k in kaps):
        aus.append("Keine Kapazitaet mit `stages: [dev, test]` im Bauplan — " + ENTSCHEIDUNG_NICHT_PROD)
    return aus


def tier1_workspaces(bp: dict) -> list[str]:
    """Produktions-Workspaces mit ``surge_class = mission_critical`` — Kandidaten fuer D-596 (c)."""
    return sorted(r["workspace"] for r in zuordnung(bp)
                  if r["tier1"] and r["gruppe"] == "prod")
