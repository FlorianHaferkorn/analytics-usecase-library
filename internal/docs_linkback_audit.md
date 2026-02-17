# SSOT Link-back Audit – Fehlende Link-backs bei abgeleiteten Views

**Datum:** 2026-02-17  
**Regel (SSOT):** When a non-canonical file mentions a canonical concept, it must include a short link-back block near the top (siehe core/strategy_operating_model/operating_model/reference/single_source_of_truth.md § Link-back pattern).

---

## Bereits erledigt (Link-back umgesetzt am 2026-02-17)

- `core/usecases/core/XD-003_Executive_KPI_Overview/Business_Factsheet.md` – Link-back auf KPI_Catalog.md (Core Content Review Behebung).
- `core/strategy_operating_model/operating_model/ux_design_system.md` – Link-back auf reporting_principles.md.
- `core/kpi_catalog/README.md` – Link-back auf KPI_Catalog.md.
- `core/semantic_models/domains/Commercial/README.md` – Link-back auf domains.md.
- `core/semantic_models/core_action_ready/README.md` – Link-back auf ActionReady_SemanticModel_Blueprint.md.
- `core/strategy_operating_model/README.md` – Link-back auf Root-README.md.
- `core/templates/page_templates/README.md` – Link-back auf ux_design_system.md.
- `core/templates/measure_templates/README.md` – Link-back auf measure_system.md.
- `core/strategy_operating_model/operating_model/reference/ActionReady_SemanticModel_Blueprint.md` – Link-back auf semantic_layer.md; zusätzlich Encoding in der Überschrift behoben (`EUR"` → `—`, Titel vereinheitlicht zu „ActionReady Semantic Model — Full Blueprint“).

---

## Nicht geprüft / optional

- **Use case Business Factsheets** (Key business questions → company_strategy §6): Plan priorisiert nur XD-003; andere Facts sheets optional.
- **UseCase_Inventory.md**: Generierte Datei; Link-back ggf. im Generator (tooling/ontology/registry_builder.py) oder in einer Vorlage hinterlegen.
- **Domain READMEs** unter `core/semantic_models/domains/*/README.md`: Nur Commercial hat ein README; dieses hat bereits Link-back auf domains.md. Andere Domains (Operations, Finance, etc.) haben nur Measure_Dictionary_*.md, kein README – bei künftiger Anlage gleiches Muster wie Commercial.
- **Showcase-Varianten** unter `showcases/*`: Beispiel-Implementierung; Link-back optional.
- **products/fabric_powerbi/docs/***, **tooling/ai/*.schema.json**: Außerhalb core bzw. keine Prosa-Dateien; nach Bedarf.

---

## Nächster Schritt

Bei neuen abgeleiteten Views (z. B. weitere Domain-READMEs) Link-back-Block nach SSOT-Vorlage ergänzen und hier unter „Bereits erledigt“ eintragen.
