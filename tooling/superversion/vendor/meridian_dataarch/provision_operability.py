"""provision_operability — the E2E completeness layer: is it actually *operable*, not just deployed?

Access control was only one dimension. A delivery also fails when nobody owns the refresh, when the
schedule silently expires, when the model has no descriptions (which degrades every AI answer), or
when editing a pipeline quietly swaps the production identity. Those are not access problems — they
are operability problems, and they are the ones a first implementation forgets.

Grounded in MS Learn (2026-07): *Job scheduler*, *Refresh data / scheduled refresh*, *Understand
semantic models* (ownership), *Direct Lake security integration*, *Prepare your data for AI*,
*Semantic model best practices for data agent*, *Endorsement*, *Information protection*,
*SQL analytics endpoint metadata sync*, *How to use notebooks* (security context).

Tool-Reuse (KRITISCH): the **model-layer** checks already exist in ``pbi_engine``'s rule catalog —
SM006 (tables without description), SM007 (measures without description), SM003 (display folder),
NC001–NC004 (naming). Those run over the emitted TMDL via ``audit_pbip`` and are **not** re-implemented
here. This module checks the layer *upstream* of TMDL — the governed catalog, before a model exists —
and emits the operational runbook that no static rule can express.

Deterministic; emits only, never executes.
"""
from __future__ import annotations

import json
import re
from core.dataarch_engine.blueprint.stack_capabilities import gap_doc_for

_NONWORD_RE = re.compile(r"[^a-z0-9]+")

# Officially load-bearing: the data agent's DAX generation relies SOLELY on model metadata + Prep for
# AI. Missing descriptions are therefore a functional defect for AI answers, not a cosmetic one.
_AI_TABLE_LIMIT = 25          # MS recommendation: <= 25 tables per data-agent source


def _tables(gc: dict) -> list[dict]:
    return sorted(gc.get("tables", []) or [], key=lambda t: t.get("name", ""))


def _measures(gc: dict) -> list[dict]:
    return sorted(gc.get("measures", []) or [], key=lambda m: str(m.get("measure_name", "")))


def check_metadata_completeness(gc: dict) -> dict:
    """What the governed catalog is missing BEFORE a model is generated — naming and documentation.

    Returns ``{findings: [...], counts: {...}}``. Every finding names the object and why it matters.
    The model-layer twin (descriptions inside the emitted TMDL) is pbi_engine's SM006/SM007 — this is
    the upstream check, so the gap is caught before it is baked into a model."""
    findings: list[dict] = []
    tables, measures = _tables(gc), _measures(gc)

    for t in tables:
        n = t.get("name", "")
        if not (t.get("grain") or "").strip():
            findings.append({"object": n, "kind": "table", "issue": "keine Grain-/Beschreibungsangabe",
                             "why": "Das Grain ist die Grundlage jeder Aggregation und speist die "
                                    "Tabellenbeschreibung, die Copilot und Data Agent auswerten"})
        if not re.match(r"^(fact|dim|agg|bridge)_", n.lower()):
            findings.append({"object": n, "kind": "table", "issue": "Name folgt keiner Layer-Konvention",
                             "why": "fact_/dim_/agg_ macht die Rolle im Stern sofort erkennbar — "
                                    "auch für die AI-Feldauswahl"})
        # Der Katalogvertrag führt Spalten als Namen; ein Produzent, der stattdessen Objekte
        # liefert, ließ `sorted()` vorher mit einem TypeError sterben und riss die ganze
        # Operability-Emission mit. Ein unerwarteter Spaltentyp darf höchstens ungeprüft
        # bleiben — er darf nicht den Lauf beenden.
        _names = [str(c.get("name") or "") if isinstance(c, dict) else str(c)
                  for c in (t.get("columns", []) or [])]
        for c in sorted(n for n in _names if n):
            if len(c) <= 2 or re.fullmatch(r"[a-z]?\d+", c.lower()):
                findings.append({"object": f"{n}.{c}", "kind": "column",
                                 "issue": "kryptischer Spaltenname",
                                 "why": "die AI wählt Felder über den Namen; kryptische Namen "
                                        "führen zu falschen Feldern in generierten Abfragen"})

    for m in measures:
        name = str(m.get("measure_name", ""))
        if not m.get("lineage"):
            findings.append({"object": name, "kind": "measure", "issue": "keine Lineage",
                             "why": "ohne Lineage ist weder Herkunft prüfbar noch Drift erkennbar"})
        if name and name.lower() == name and " " not in name:
            findings.append({"object": name, "kind": "measure",
                             "issue": "technischer statt sprechender Name",
                             "why": "Measure-Namen erscheinen unverändert im Report und in "
                                    "AI-Antworten — sie sind Fachsprache, kein Code"})

    counts = {"tables": len(tables), "measures": len(measures),
              "columns": sum(len(t.get("columns", []) or []) for t in tables),
              "findings": len(findings)}
    return {"findings": findings, "counts": counts}


def _metadata_report(gc: dict) -> str:
    res = check_metadata_completeness(gc)
    c, f = res["counts"], res["findings"]
    lines = [
        "# Metadaten-Vollständigkeit — Benennung und Beschreibung", "",
        f"Geprüft: **{c['tables']} Tabellen · {c['columns']} Spalten · {c['measures']} Kennzahlen** → "
        f"**{c['findings']} Befund(e)**.", "",
        "> **Das ist keine Kosmetik.** Der DAX-Generator des Fabric Data Agent stützt sich "
        "**ausschließlich** auf die Metadaten des Semantic Models (Tabellen-/Spaltenbeschreibungen, "
        "Synonyme, Beziehungen, Datentypen) plus die *Prep-for-AI*-Konfiguration. Fehlende oder "
        "kryptische Benennung senkt unmittelbar die Antwortqualität — Anweisungen auf Agent-Ebene "
        "werden für die DAX-Generierung **nicht** ausgewertet.", "",
    ]
    if f:
        lines += ["| Objekt | Art | Befund | Warum es zählt |", "|---|---|---|---|"]
        for x in f:
            lines.append(f"| `{x['object']}` | {x['kind']} | {x['issue']} | {x['why']} |")
    else:
        lines.append("Keine Befunde — Benennung und Grain sind auf dieser Ebene vollständig.")
    lines += [
        "", "## Arbeitsteilung der Prüfungen (kein zweites Silo)", "",
        "| Ebene | Prüft | Wo |", "|---|---|---|",
        "| Governter Katalog (hier) | Grain, Layer-Konvention, sprechende Namen, Lineage | dieser Bericht |",
        "| Semantic Model (TMDL) | Beschreibungen an Tabellen/Measures, Display Folder, Namensregeln | "
        "`pbi_engine`-Regelkatalog (SM006 · SM007 · SM003 · NC001–NC004) über den PBI-Audit |",
        "", "Beide laufen im selben Gate — der Katalog-Check greift *vor* der Modellerzeugung, "
        "der Modell-Check danach.",
    ]
    return "\n".join(lines) + "\n"


def _operations_runbook(gc: dict) -> str:
    """The traps that silently kill a running solution — none of them is an access problem."""
    n_tables = len(_tables(gc))
    over = n_tables > _AI_TABLE_LIMIT
    return "".join(l + "\n" for l in [
        "# Betriebsbereitschaft — was still ausfällt, wenn man es vergisst", "",
        "Gegroundet in MS Learn (2026-07). Jeder Punkt hat schon Produktionen lahmgelegt, und keiner "
        "davon ist ein Berechtigungsproblem.", "",
        "## Identität und Eigentum — die häufigste stille Ursache", "",
        "| Punkt | Was passiert, wenn man es lässt |", "|---|---|",
        "| **Semantic-Model-Eigentum** | Refresh-Einstellungen kann nur der Eigentümer pflegen. Verlässt "
        "die Person das Unternehmen, stirbt die Aktualisierung. → Eigentum auf ein **Dienstkonto/SPN** "
        "übernehmen (*Take over*). |",
        "| **Ausführungsidentität** | Ein Notebook aus einer **Pipeline** läuft unter dem "
        "**zuletzt ändernden Benutzer** der Pipeline; ein **geplanter** Lauf unter dem, der den Zeitplan "
        "zuletzt angelegt/geändert hat. Wer eine Pipeline editiert, tauscht damit unbemerkt die "
        "Produktions-Anmeldung aus. → Pipelines/Zeitpläne unter einem **SPN** führen. |",
        "| **Direct-Lake-Eigentümer braucht Leserecht** | Nicht nur der abfragende Nutzer, auch der "
        "**Eigentümer** braucht Lesezugriff auf die Delta-Quelltabellen — sonst schlägt das Framing mit "
        "„access was denied\" fehl. |",
        "| **Zugangsdaten laufen ab** | Abgelaufene/geänderte Passwörter deaktivieren den Refresh. Nach "
        "dem Erneuern den Zeitplan **wieder aktivieren** — er bleibt sonst aus. |",
        "| **Erneutes Veröffentlichen löst die Gateway-Bindung** | Die Verknüpfung Modell↔Datenquelle "
        "überlebt ein Republish nicht und muss neu gesetzt werden. |",
        "", "## Zeitpläne — die eingebauten Abschaltungen", "",
        "| Mechanismus | Grenze | Folge |", "|---|---|---|",
        "| Fabric Job Scheduler (Pipelines, Notebooks) | ~**10 aufeinanderfolgende Fehler** | Zeitplan "
        "wird **automatisch deaktiviert**, manueller Neustart nötig |",
        "| Fabric Job Scheduler | Ersteller **90 Tage** nicht angemeldet | Zeitplan **läuft ab** → SPN nutzen |",
        "| Power-BI-Refresh (separater Mechanismus!) | **4 aufeinanderfolgende Fehler** | Refresh wird "
        "**deaktiviert** |",
        "| Power-BI-Refresh | **2 Monate** ohne jede Report-Ansicht | Refresh wird **pausiert** |",
        "| Power-BI-Refresh | 8/Tag (Pro) · 48/Tag (Capacity) | darüber hinaus nur via XMLA |",
        "", "> Fehlerbenachrichtigungen gehen standardmäßig **nur an den Eigentümer** — auf einen "
        "Verteiler umstellen, sonst bemerkt niemand den Ausfall.", "",
        "## Direct Lake — Besonderheiten", "",
        "- **Kein Gateway** (weder on-prem noch VNet) für Direct-Lake-Refresh — nur Cloud-Verbindungen.",
        "- **Automatische Aktualisierung** ist standardmäßig an. Schaltet man sie für konsistente "
        "Zeitpunkte ab, muss das **Framing** selbst angestoßen werden, sonst friert der Stand ein.",
        "- **SQL-Endpunkt-Metadatensync** pausiert nach ~**15 Minuten Inaktivität** — neue Tabellen "
        "erscheinen dann verzögert; bei Bedarf gezielt anstoßen.",
        "", "## Refresh-Optionen — Schema und Daten getrennt (I-21 W6.7)", "",
        "Ein Refresh macht standardmäßig erst einen Schema-Sync, dann den Daten-Refresh. Seit August "
        "2026 lassen sich beide trennen und je Tabelle fahren (Desktop und Service; Power BI What's "
        "new August 2026 ohne Preview-Kennzeichen; Learn `power-bi/connect-data/refresh-data` → "
        "*Power BI refresh options* und `power-bi/transform-model/service-edit-data-models` → "
        "*Refresh*, gelesen 29.09.2026).", "",
        "| Option | Wann in dieser Lieferung | Wann nicht |", "|---|---|---|",
        "| **Refresh data only** | Standard nach jedem Laden und nach einem Deploy ohne "
        "Modelländerung: frische Daten, das Schema bleibt wie in Git (TMDL ist die Quelle) | — |",
        "| **Sync schema only** | nur im Entwicklungs-Workspace, wenn eine Gold-Tabelle eine Spalte "
        "bekommen hat und sie ins Modell soll — danach **zurück nach Git committen** | nie in test/"
        "prod: das Modell weicht sonst still vom Git-Stand ab, und der nächste Deploy überschreibt "
        "es wieder |",
        "| **Refresh schema and data** | Desktop-Entwicklung | nicht als Betriebs-Refresh |",
        "| **Refresh je Tabelle** (Model explorer → Tabelle) | nach dem Nachladen einer einzelnen "
        "Gold-Tabelle; automatisiert über die Pipeline-Aktivität *Semantic model refresh* "
        "(Tabellen und Partitionen wählbar, Learn `data-factory/semantic-model-refresh-activity`) | "
        "wenn berechnete Tabellen oder Spalten von der Tabelle abhängen — dann ganzes Modell "
        "(ANNAHME, ungeprüft: Learn nennt die Abhängigkeitsregel für den Tabellen-Refresh nicht) |",
        "",
        "- Im **Ansichtsmodus** des Service bietet der Refresh nur *Refresh data*; Schema-Optionen "
        "erst im Bearbeitungsmodus (Learn, dieselbe Seite) — gewollt, verhindert versehentliche "
        "Schemaänderungen.",
        "- Direct Lake: der geplante Refresh im Workspace macht nur das **Framing**, keinen "
        "Schema-Sync (Learn `fabric/fundamentals/direct-lake-power-bi-desktop`). Eine neue Spalte "
        "in der Lakehouse-Tabelle kommt also nicht von selbst ins Modell; das ist hier gewollt.",
        "", "## Damit AI-Antworten belastbar sind", "",
        "- **Q&A muss aktiviert sein**, sonst ist *Prep data for AI* gesperrt.",
        "- **Prep for AI** konfigurieren: AI-Datenschema (welche Tabellen/Spalten die AI nutzen darf), "
        "geprüfte Antworten, AI-Anweisungen — danach **„Approved for Copilot\"** setzen, sonst sehen "
        "Nutzer einen Warnhinweis.",
        "- **Agent-Anweisungen ersetzen das nicht:** Anweisungen auf Data-Agent-Ebene fließen **nicht** "
        "in die DAX-Generierung. Modellbezogene Vorgaben gehören in Prep for AI.",
        f"- **Höchstens ~{_AI_TABLE_LIMIT} Tabellen je Agent-Quelle**" +
        (f" — dieses Modell hat **{n_tables}** und sollte für den Agent auf die relevanten Tabellen "
         "eingegrenzt werden." if over else f" — dieses Modell liegt mit {n_tables} darunter."),
        "", "## Endorsement und Vertraulichkeit", "",
        "- **Promoted** kann jede:r mit Schreibrecht. **Certified** verlangt, dass der Fabric-Admin die "
        "Zertifizierung im Tenant freischaltet und **Sicherheitsgruppen** (keine Einzelpersonen) als "
        "Prüfer benennt.",
        "- **Verbindliche Vertraulichkeitskennzeichnung** wird in **Purview** konfiguriert, nicht in "
        "Fabric — und greift **nur für Power-BI-Artefakte**, nie für Service Principals oder API-Zugriffe. "
        "Für Lakehouse/Pipeline/Warehouse wird sie nicht erzwungen.",
        "", "## Voraussetzung für unsere eigene Auslieferung", "",
        "- **XMLA-Endpunkt auf *Read Write*** (Capacity-Admin) — ohne das schlägt jeder TMDL-/"
        "Service-Principal-Deploy des Semantic Models fehl.",
    ])


def emit_operability(bp: dict, governed_catalog: dict | None = None) -> dict[str, str]:
    """Return the operability artifact set (path → content): the metadata-completeness report and the
    operations runbook."""
    gc = governed_catalog or {}
    res = check_metadata_completeness(gc)
    return {
        "operability/METADATEN_VOLLSTAENDIGKEIT.md": _metadata_report(gc),
        "operability/BETRIEBSBEREITSCHAFT.md": (
            # Job-Scheduler-Grenzen, Direct-Lake-Besonderheiten und Purview sind Fabric-Betriebsrecht
            # und auf fremden Stacks gegenstandslos — dort der belegte Mechanismus des Ziels.
            gap_doc_for(bp, "operability", "Betriebsbereitschaft") or _operations_runbook(gc)),
        "operability/metadata_findings.json": json.dumps(
            {"schema": "meridian/metadata-completeness/v1", **res}, indent=2, ensure_ascii=False) + "\n",
    }
