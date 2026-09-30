# Copilot readiness — "Prep data for AI" für ALUCA-Use-Cases

Erzeugt deterministisch (kein LLM, kein Netzwerk) die drei Inhalte des Power-BI-Features
**Prep data for AI** (Preview) für einen Use Case:

| Datei | Ziel im Power-BI-Service |
|---|---|
| `ai_instructions.txt` (Eingabefeld) / `ai_instructions.md` (Review) | Prep data for AI → AI instructions |
| `verified_answer_candidates.json` | Report-Visual → „Set up a verified answer“ (nur **Kandidaten**, Freigabe durch einen Menschen) |
| `ai_data_schema.json` | Prep data for AI → AI data schema (Empfehlung include/exclude) |

Quelle der Service-Schritte: [Prepare your data for AI](https://learn.microsoft.com/power-bi/create-reports/copilot-prepare-data-ai);
Einordnung: `../../docs/tmdl_best_practices.md` (Abschnitt Prep for AI). Keine dokumentierte
public API — die Inhalte werden von Hand eingetragen.

```bash
python -m products.fabric.powerbi.tooling.copilot_readiness --usecase COM-001          # schreiben
python -m products.fabric.powerbi.tooling.copilot_readiness --usecase COM-001 --check  # veraltet? Exit 1
```

Ausgabe: `products/fabric/powerbi/dist/copilot_readiness/<Use-Case-Ordner>/` — generiert, nie
von Hand editieren.

## Aufbau: gespiegelter Kern + ALUCA-Adapter

| Teil | Ort | Heimat |
|---|---|---|
| Kern: Zwischenform `CopilotCore` + drei Renderer | `vendor/meridian_copilot_readiness/` (+ `PIN.json`) | Meridian `products/meridian_copilot_readiness/generator` |
| Import-Brücke + Integritätsprüfung | `_vendor.py` | ALUCA |
| Adapter: Katalog, Bracket, Action Codes, Datenverträge → Zwischenform | `adapter.py` | ALUCA |
| Format-Signatur (Parität zu Meridian) | `parity.py`, Referenz `../tests/fixtures/copilot_readiness/meridian_format.json` | ALUCA |

**Spiegel statt Kopie.** Der Kern ist byte-identisch gespiegelt (sha256 je Datei im PIN), wie
`tooling/superversion/vendor/meridian_dataarch/`. Eine Kopie mit umgeschriebenen Importen wäre
für keinen Hash mehr erkennbar; der Spiegel macht Drift in beide Richtungen messbar:
`scripts/check_dataarch_mirror.py` meldet eine lokale Änderung hart und eine Meridian-Änderung
als Drift. Ändern immer zuerst in Meridian, committen, dann:

```bash
MERIDIAN_ROOT=../Freelancing python scripts/check_dataarch_mirror.py --write-copilot
python scripts/check_dataarch_mirror.py --fetch --strict
```

Danach die Format-Referenz neu erzeugen (Anleitung im Kopf von `parity.py`); der Test
`test_format_signature_equals_a_real_meridian_run` bindet sie an den `source_commit` des PIN.

Nicht gespiegelt: `anwendung.py` (Anleitungstext nennt den Meridian Core als Quelle) und
`mcp_grounding.py` (kein Prep-data-for-AI-Inhalt).

## Was der Adapter woher nimmt (Golden Thread: referenzieren, nie definieren)

| Kern-Feld | ALUCA-Quelle |
|---|---|
| KPI-Liste | Bracket: `strategic_kpi_id`, `primary_kpi_ids`, `influencing_kpi_ids`, `supporting_kpi_ids`; eine ID außerhalb des Katalogs bricht ab |
| Name, Definition, Einheit, Richtung, Owner | `core/kpi_catalog/kpis/<id>.yaml`: `kpi_key`, `business.definition`, `business.unit_format`, `good_is`, `governance.business_owner` |
| Alert-Schwelle | L1-Schwelle einer Bracket-Action-Code, die die KPI als `trigger_kpis` führt (Vergleich gegen die gute Richtung, gleiche Einheit) |
| Glossar / Synonyme | `synonyms` der KPI im Katalog |
| Datenquelle, AI data schema | `technical.lineage` → Faktentabelle aus `core/data_contracts/domains` (Schlüssel = exclude) |
| Visual-Hinweis | `technical.measure_name` |
| Geschäftskontext, Nordstern-KPI | Bracket: Titel, Domäne, `value_driver_model.impact_logic`, `strategic_kpi_id`; Rollen aus `core/organization/org_roles.yaml` |
| Ziel-Report, Entscheidungs-Foren | `dist/<Use-Case-Ordner>.Report`; Bracket-Action-Codes (Name, `automation.detection.evaluation_frequency`) |

Ohne Quelle bleibt ein Feld leer, statt geschätzt zu werden: der Katalog führt keine
strategischen Ziele oder Baselines, also nennt die Ausgabe keine.

## Bekannte Grenzen

- Regel- und Anleitungstexte des Kerns sind deutsch, Definitionen bleiben englisch wie im Katalog.
- Die Trigger-Phrasen sind Vorlagen des Kerns; `example_question` aus dem Katalog wird nicht eingespielt.
- Spalten-Synonyme der Datenverträge gehen über das linguistische Schema
  (`../linguistic_schema.py`), nicht über dieses Werkzeug.
