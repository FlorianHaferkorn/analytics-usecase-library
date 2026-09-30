"""Verified-Answer-KANDIDATEN — Frage→Visual-Vorschläge je KPI (HITL-Pflicht).

"Verified answers" in Power BI sind per Definition von Menschen freigegebene
Antworten. Dieser Generator erzeugt deshalb ausschließlich KANDIDATEN:
deterministisch aus kpi.json (Name/Synonyme) + reporting.json (Ziel-Report)
+ optional data_architecture.json (Visual-/Measure-Hinweis) abgeleitet.
Die Freigabe passiert durch einen Menschen im Power-BI-Service
(Visual auswählen → "Set up a verified answer", siehe ANWENDUNG.md).
"""
from __future__ import annotations

from products.meridian_copilot_readiness.generator.loader import (
    CopilotCore,
    pick_label,
    sources_meta,
)

CANDIDATE_STATUS = "KANDIDAT — Freigabe durch Mensch im Power-BI-Service erforderlich (HITL)"

# Spezifischere Konsumenten zuerst: deren Dashboards sind die besseren Visual-Ziele.
_LEVEL_PRIORITY = {"Functional": 0, "Regional": 1, "Executive": 2}


def _trigger_phrases(kpi: dict) -> list[str]:
    """1–3 deterministische Frage-Formulierungen aus Name/Labels."""
    label_de = pick_label(kpi.get("label"), "de")
    label_en = pick_label(kpi.get("label"), "en")
    phrases = [
        f"Wie ist der aktuelle Stand von {label_de}?",
        f"Liegt {label_de} im Ziel?",
    ]
    if label_en and label_en != label_de:
        phrases.append(f"What is the current {label_en}?")
    else:
        phrases.append(f"Zeig mir {label_de} im Zeitverlauf.")
    return phrases


def _synonyms(core: CopilotCore, kpi: dict) -> list[str]:
    label_de = pick_label(kpi.get("label"), "de")
    label_en = pick_label(kpi.get("label"), "en")
    syn: list[str] = []
    if label_en and label_en != label_de:
        syn.append(label_en)
    for term in core.glossary_terms_for_kpi(kpi):
        if term not in syn and term != label_de:
            syn.append(term)
    return syn


def _target_report(core: CopilotCore, kpi_id: str) -> dict:
    """Empfohlener Ziel-Report aus reporting.json — spezifischster Konsument zuerst."""
    consumers = [
        c for c in core.reporting_consumers
        if kpi_id in (c.get("kpi_ids") or [])
    ]
    consumers_sorted = sorted(
        enumerate(consumers),
        key=lambda pair: (_LEVEL_PRIORITY.get(pair[1].get("level", ""), 99), pair[0]),
    )
    ordered = [c for _, c in consumers_sorted]
    if not ordered:
        return {
            "recommended_report": None,
            "consuming_roles": [],
            "note": "Kein Reporting-Konsument für diese KPI in reporting.json — Ziel-Report manuell wählen.",
        }
    first = ordered[0]
    return {
        "recommended_report": {
            "role": first.get("role"),
            "level": first.get("level"),
            "format": first.get("format"),
            "frequency": first.get("frequency"),
        },
        "consuming_roles": [c.get("role") for c in ordered],
    }


def _decision_forums(core: CopilotCore, kpi_id: str) -> list[str]:
    forums: list[str] = []
    for entry in core.decision_calendar:
        if kpi_id in (entry.get("kpi_ids") or []):
            forums.append(
                f"{pick_label(entry.get('name'), 'de')} ({entry.get('frequency', '—')})"
            )
    return forums


def _visual_hint(core: CopilotCore, kpi: dict) -> str:
    metric = core.metric_for_kpi(str(kpi.get("id")))
    if metric is not None:
        grain = ", ".join(metric.get("grain") or [])
        hint = f"KPI-Visual für Measure '{metric.get('name', '?')}'"
        if metric.get("dax_expr"):
            dax = metric["dax_expr"]
            hint += f" — DAX-Basis: {dax}"
            # S1-Fix (I-10.6): %/points-KPIs liegen auf 0–100-Skala, die DAX-Basis
            # liefert aber ein 0–1-Verhältnis (DIVIDE/Produkt ohne * 100). Ohne
            # Skalierungs-Hinweis zeigt das Visual 0,72 statt 72. Einheit/Formel
            # aus der KPI-Definition bestimmt den Faktor.
            _unit = ((kpi.get("definition") or {}).get("unit") or "").strip().lower()
            if _unit in ("%", "points", "punkte", "pp") and "100" not in dax:
                hint += " · Skalierung × 100 (Wert auf 0–100-Skala gem. KPI-Einheit/-Formel)"
        if grain:
            hint += f"; Grain: {grain}"
        return hint
    data_source = kpi.get("data_source") or {}
    field = data_source.get("field")
    domain_id = data_source.get("domain_id")
    if field or domain_id:
        return (
            f"KPI-Visual auf Feld '{field or '—'}' der Domäne "
            f"{domain_id or '—'} ({core.domain_label(domain_id or '', 'de')})"
        )
    return "Visual manuell wählen — keine Datenquellen-Angabe im Core."


def build_verified_answer_candidates(core: CopilotCore) -> dict:
    candidates = []
    for kpi in core.kpis:
        kpi_id = str(kpi.get("id"))
        candidates.append({
            "kpi_id": kpi_id,
            "kpi_label_de": pick_label(kpi.get("label"), "de"),
            "kpi_label_en": pick_label(kpi.get("label"), "en"),
            "status": CANDIDATE_STATUS,
            "trigger_phrases": _trigger_phrases(kpi),
            "synonyms": _synonyms(core, kpi),
            "target": _target_report(core, kpi_id),
            "visual_hint": _visual_hint(core, kpi),
            "decision_forums": _decision_forums(core, kpi_id),
            "approval": {"approved": False, "approved_by": None, "approved_date": None},
        })

    return {
        "_artifact": "verified_answer_candidates",
        "_organisation": core.org_name(),
        "_status": (
            "ALLE Einträge sind KANDIDATEN. Verified answers sind per Definition "
            "menschlich freigegebene Antworten — Freigabe erfolgt im Power-BI-Service "
            "(Report im Edit-Modus → Visual → 'Set up a verified answer'), "
            "nicht durch dieses Tool. Kein automatischer Import: 'Prep data for AI' "
            "ist Preview und hat keine dokumentierte public API."
        ),
        "_generated_by": "products.meridian_copilot_readiness (deterministisch, kein LLM)",
        "_sources": sources_meta(core),
        "candidates": candidates,
    }
