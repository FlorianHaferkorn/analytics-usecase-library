# MCP Playbook (Golden Path)

## Ziele
- Deterministisch Berichte aus Spezifikationen bauen (PBIP).
- Semantik aus KPI‑Katalog und Use Cases wiederverwenden.

## Artefakte
- Use Case Ordner: `usecases/{cluster}/{ID}_{Slug}/`
  - `README.md`: Business‑Dokument (Front‑Matter enthalten)
  - `spec.yaml`: Report‑Spec (maschinenlesbar)
- KPI‑Katalog: `/_includes/kpi_catalog/*.md` (YAML‑Blöcke pro KPI)
- Strategy: `/_includes/strategy.yaml` (strategische KPIs + Influence‑Graph)
- Schemas: `/schemas/*.yaml` (Validation)
- PBIR Referenz: `/docs/PBIR_Schema_Reference.md` (Aufbau von PBIP/PBIR Artefakten)

## Best Practices (maschinenlesbar)
- Semantic Model Regeln: `schemas/best_practices/bpa-rules-semanticmodel.json`
  - Einsatz: Bei „Build Measures“ und „Improve Model“ anwenden (nach Katalog/TMDL‑Erzeugung), dann `schemas/lint.rules.yaml` ausführen.
- Report Regeln: `schemas/best_practices/bpa-rules-report.json`
  - Einsatz: Nach dem Erstellen der Seiten/Visuals aus `spec.yaml` prüfen und ggf. Empfehlungen/Fixes anwenden (Visualanzahl, Filter, Objektzahl pro Visual).

Precedence (Konfliktauflösung)
1) `schemas/TMDL_Allowed_Subset.md` + `schemas/lint.rules.yaml`
2) Best‑Practice‑Regeln (`bpa-rules-*.json`)
3) Use‑Case‑Spezifika aus `spec.yaml` (Bindings/Layout)

## Workflow (Mensch → MCP)
1) Authoring (Business): Use Case schreiben/aktualisieren.
2) Enrichment (Data): KPI‑Katalogeinträge für alle KPIs (DAX, lineage, format, folder).
3) Report‑Spec (BI): `spec.yaml` definieren (pages, visuals, bindings, layout, slicers).
4) Build (MCP): validate → build‑measures → build‑report → qa.
   - Siehe Task Guides: `/docs/MCP_Task_Guides.md`

## Commands (Beispiel)
- validate:
  - YAML Schema: `schemas/report_spec.schema.yaml` gegen `spec.yaml`
  - Coverage: `kpis.required_measures` existieren im Katalog
  - TMDL‑Lint: `schemas/lint.rules.yaml`
- build‑measures:
  - Katalog → TMDL Measures (name, expression, formatString, displayFolder, description)
- build‑report:
  - `spec.yaml` → PBIP (pages/visuals/bindings/formatting)
  - wendet `theme_ref` + `template_ref` an (externes Projekt)
  - Abbildung auf PBIR laut `/docs/PBIR_Schema_Reference.md`
  - wende `schemas/best_practices/bpa-rules-report.json` an (Lesbarkeit/Governance‑Heuristiken)
- qa:
  - Assert‑Measures (99_QA), RI‑Gate, Visual‑Bindings vorhanden
  - `schemas/best_practices/bpa-rules-semanticmodel.json` + `schemas/best_practices/bpa-rules-report.json` ohne Blocker

## Definition of Done (Auto‑Report‑Ready)
- UC/README.md: Front‑Matter mit `supports_strategic_kpi`, `action_codes`, `expected_impact`.
- UC/spec.yaml: Mindestens Seite „Overview“ mit Karten, Trend, Ranking, Brücke.
- KPI‑Katalog: Alle referenzierten KPIs vollständig (DAX, lineage, format, folder).
- Strategy: Strategische KPIs gepflegt, Influence‑Graph konsistent.

## Hinweise
- Display‑Namen dürfen Δ/Δ% enthalten; `measure_id`/`kpi_key` bleiben ASCII‑stabil.
- Themes/Layouts werden nur referenziert (Kopplung zum externen Projekt über `theme_ref`/`template_ref`).
