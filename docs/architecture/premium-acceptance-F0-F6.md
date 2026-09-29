# Premium-Floor Acceptance — F0–F6 (I-10.6)

- **Date:** 2026-07-08
- **Scope:** Final acceptance check for the ALUCA Superversion pipeline against
  [`docs/plans/PRODUCT_PLAN.md §2`](../plans/PRODUCT_PLAN.md#2-premium)'s six premium floors (F1–F6),
  plus **F0** ("das Produkt rechnet"), added by [`docs/plans/SUPERVERSION_ZIELBILD_REVIEW.md`](../plans/SUPERVERSION_ZIELBILD_REVIEW.md)
  finding **A1** after discovering F1–F6 could all report green while every measure in
  every use case emitted `BLANK()` — passing every gate while computing nothing.
- **Ran against:** the system state after [I-10.0](adr/0010-kpi-calculation-dsl-and-dax-synthesis.md)
  (+[I-10.0-Folge ADR-0011/0012/0013](adr/), Rechenfähigkeit), [I-10.1](../plans/UMSETZUNGSPLAN_SUPERVERSION.md)
  (Windows-Portabilität), [I-10.3](adr/0007-studio-generate-docks-onto-superversion-core.md)
  (Studio↔Python-Core-Naht), and [I-10.4](../plans/UMSETZUNGSPLAN_SUPERVERSION.md) (DOCX-Deliverable) — the DoD's
  named prerequisites.
- **Method:** every floor below was independently executed in this session (commands run
  for real, output condensed for readability where verbose but never altered in substance —
  exact pass counts/hashes/exit codes are unedited) — not inferred from prior ledger claims
  without re-running them. Per the DoD's own error clause: **a red floor is reported as
  open, never quietly marked green.**

---

## Verdict summary

| Floor | Verdict | One-line reason |
|---|:-:|---|
| **F0** Rechenfähigkeit | 🟢 **grün** (5 MVP-UCs) · 🟡 **offen, geledgert** (11 weitere UCs) | 0/0 BLANK() für die 5 MVP-UCs; 9 einzeln begründete HITL-KPIs über die restlichen 11 UCs, keine stille `BLANK()` |
| **F1** Official validator | 🟡 **teilweise** (Nachmessung 29.09.2026, s. u.) · ursprünglich 🔴 | Superversion-Emit COM-001: 0 Errors im offiziellen Validator 0.1.1, in `superversion.yml` blockierend verdrahtet; die 17 ausgelieferten `dist/`-Reports: 23–25 Errors je Report, nur als Ratsche geprüft |
| **F2** Determinismus | 🟢 **grün** | byte-identischer SHA-256 über 3 `PYTHONHASHSEED`-Werte, frisch reproduziert |
| **F3** Golden Thread | 🟢 **grün** | 0 Error-Verstöße über alle 5 gehärteten MVP-UCs; 4 Advisory-Warnungen offen benannt |
| **F4** Standalone-Smoke | 🟢 **grün** | jedes Layer-Tool läuft eigenständig via CLI, live verifiziert; gov/eng/arch-Engines bleiben Beta |
| **F5** Handover-Doku | 🟢 **grün** | DOCX + MD live erzeugt (I-10.4), Content-Parität getestet |
| **F6** Real evals | 🟢 **grün** (≥2 Referenz-Ontologien) · 🔴 **offen** (Live-DAX-Ausführung) | Value-Gate-Tests grün über 2 Ontologien; Live-Ausführung gegen ein echtes Fabric-Tenant existiert nicht im Repo und ist in dieser Sandbox nicht herstellbar |

> **Nachtrag 29.09.2026:** F1 ist inzwischen teilweise grün (Superversion-Emit gemessen 0
> Errors, `dist/` nicht; Nachmessung im F1-Abschnitt). Rot bleibt der zweite Teil von F6.

**Zwei Floors bleiben ehrlich rot: F1 und der zweite Teil von F6.** Beide sind nicht
"noch nicht gebaut, aber baubar" — beide brauchen eine echte Power-BI/Fabric-Tenant-
Verbindung (installierte, authentifizierte `powerbi-report-author`- bzw. `az`/`fab`-CLI),
die in dieser Sandbox nicht existiert. Details und der nächste Schritt stehen in der
Findings-Liste (§ unten).

---

## F0 — "Das Produkt rechnet" (BLANK()-Quote, A1)

**Behauptung:** jede Measure hat eine echte DAX/SQL-Formel, keine stille `BLANK()`.

**Befund (live ausgeführt):**
```
$ python -m pytest tooling/superversion/tests/test_calculation_coverage.py -q
............................                                             [100%]
28 passed in 1.86s
```
- `test_zero_silent_blank_across_all_16_use_cases` — über alle 16 `UseCase_Bracket.yaml`
  parametrisiert: jede verbleibende `BLANK()` trägt einen expliziten `/// HITL:`-Grund,
  nie eine stille.
- `test_all_5_core_use_cases_are_fully_computed` — die 5 MVP-UCs (COM-001/002/003,
  FIN-002, SCM-002) zeigen `hitl_gaps() == []`: **0 von 0**.
- Über alle 16 UCs (live nachgerechnet):
  ```
  $ python -c "... hitl_gaps() je UC summieren ..."
  total refs: 18   unique KPIs: 9
  ```
  Diese 9 KPIs sind einzeln in [ADR-0013](adr/0013-kpi-calculation-dsl-remaining-11-use-cases.md)
  begründet: 4× Legacy-`BLANK()`-Placeholder (`scm.supplier_risk.score`,
  `ops.safety.incident.count`, `people.digital_adoption.pct`, `people.attrition_risk.pct`),
  2× Grammatik-Limit (`plan.forecast.mape.pct`, `plan.forecast.service_impact.pct`), 3×
  Neuland/unterspezifiziert (`inv.excess_inventory.amount`, `ops.changeover.minutes`,
  `ops.speed_loss.pct`).

**Verdict: grün für die 5 MVP-UCs (das S-1-Kriterium aus der Review), ehrlich offen
für 9 namentlich benannte KPIs über die restlichen 11 UCs** — jede Lücke ist dokumentiert,
keine ist stumm.

**Scope-Hinweis:** die obigen 16 UCs sind der etablierte ADR-0013-Scope
(`core/usecases/core/`). Der Bracket-Baum trägt zusätzlich einen 17. Bracket unter
`core/usecases/industry/` (`COM-IND-R001_Basket_Category_CrossSell`, ein Industry-Variant
per ADR-0004) mit **5 weiteren HITL-KPIs** (`fact_sales.Category Cross-Sell Rate %`,
`Items per Transaction`, `Average Basket Value`, `Promotion Attachment Rate %`,
`RFM Frequency Score`) — live nachgerechnet, ebenfalls alle HITL-getaggt, keine stille
`BLANK()`. Dieser Industry-Bracket war nie im I-10.0-Folge-Scope; hier zur Vollständigkeit
genannt statt unerwähnt zu lassen.

---

## F1 — Official validator, 0 errors

**Behauptung:** `powerbi-report-author validate` (bzw. `check_pbir`) läuft grün gegen
jedes emittierte Artefakt.

**Befund (live ausgeführt):**
```
$ which powerbi-report-author
(exit 1 — nicht gefunden)

$ python -m tooling.superversion.e2e_smoke
[e2e] source: PASS — COM-001_Sales_Performance → model (1 tables, 2 pages)
[e2e] golden_thread: PASS — strategic anchors intact (3 advisory)
[e2e] tmdl: PASS — 1 file(s), hard-rule hook green
[e2e] pbir: SKIP — 'powerbi-report-author' CLI not installed (official gate not run)
[e2e] OK — full chain green.
```
`test_pbir_target.py::test_official_validator_zero_errors` ist mit
`@pytest.mark.skipif(shutil.which(CLI) is None, ...)` markiert und wird in dieser Umgebung
übersprungen, nicht ausgeführt.

**Verdict: rot/offen — in dieser Sandbox nicht belegbar.** Alle strukturellen
Eigen-Checks (PBIR-JSON-Syntax, Struktur, Determinismus) laufen grün, aber das eigentliche
F1-Kriterium — der ECHTE MS-Validator meldet 0 Errors — ist unverifiziert, weil die CLI
hier nicht installiert/erreichbar ist. Das ist ein ehrlicher Sandbox-Gap, kein Code-Defekt:
`e2e_smoke` degradiert korrekt zu `SKIP` statt einen falschen `PASS` vorzutäuschen
(dieselbe Disziplin wie die I-10.1-Fixes für `bash`-Verfügbarkeit).

**Nachmessung 29.09.2026 (Stand oben vom 08.07. bleibt als Beleg stehen):**

- **Verdrahtung, gelesen:** `.github/workflows/superversion.yml` installiert die CLI gepinnt
  (`npm install -g @microsoft/powerbi-report-authoring-cli@0.1.1`) und fährt danach
  `python -m tooling.superversion.e2e_smoke --require-cli` — ohne CLI wird der Schritt rot,
  nicht übersprungen. Der `pytest`-Schritt desselben Jobs läuft **vor** der Installation;
  `test_official_validator_zero_errors` wird dort also weiter übersprungen. Stage 1
  (`stage1.yml`) installiert die CLI nicht; `tooling/tests/test_dist_validator_ratchet.py`
  überspringt sich dort.
- **Lokal gemessen** (CLI 0.1.1 per `npm install` in ein Scratch-Präfix, Python-Umgebung aus
  der CI-`pip`-Liste): `e2e_smoke --require-cli` → `pbir: PASS - check_pbir 0 errors (0 warn)`,
  Exit 0. Gegenprobe: `pytest tooling/tests/test_dist_validator_ratchet.py
  tooling/superversion/tests/test_pbir_target.py tooling/superversion/tests/test_e2e_smoke.py`
  → 46 passed, 0 skipped.
- **`dist/`-Reports, je Report `powerbi-report-author validate --format json`:** 16 × 25 Errors
  (5 Warnings), `FIN-001_Cash_Liquidity_Performance.Report` 23 Errors. Die Ratsche
  (`BASELINE_ERRORS = 25`) hält; die Errors liegen laut Ratschen-Doku im mitgelieferten Theme
  (Übergabepunkt A, Trennung braucht Desktop).
- **Verdict: 🟡 teilweise.** Das F1-Kriterium „offizieller Validator 0 Errors" ist für den
  Superversion-Emit (1 UC) gemessen erfüllt, für die ausgelieferten `dist/`-Reports nicht.
  Diese kommen aus dem deprecated Prototyp-Renderer, nicht aus dem Superversion-Emit
  (Ledger A-18 in `_INDEX.md`). Ein grüner CI-Lauf von `superversion.yml` mit echtem Runner
  ist hier **nicht** gemessen (Actions-Kontingent, `CLAUDE.md`).

---

## F2 — Deterministisch & reproduzierbar

**Behauptung:** byte-stabiler Re-Run derselben Spec.

**Befund (live ausgeführt, dieser Session):**
```
$ for seed in 0 1 42; do
    PYTHONHASHSEED=$seed python -c "... tmdl.emit(model) sha256 ..."
  done
seed=0  004f26bb507e9d180bf0f5f9c5eaf354fbf45561a3ff80b67a3f9c7a72b56146
seed=1  004f26bb507e9d180bf0f5f9c5eaf354fbf45561a3ff80b67a3f9c7a72b56146
seed=42 004f26bb507e9d180bf0f5f9c5eaf354fbf45561a3ff80b67a3f9c7a72b56146
```
Identischer Hash über alle 3 Seeds für dasselbe COM-001-Bracket. Ergänzend grün:
`test_from_aluca.py::test_deterministic_rebuild`/`test_model_to_json_byte_stable`,
`test_tmdl_target.py::test_emit_is_deterministic`, sowie je ein Determinismus-Test in
`test_osi_target.py`/`test_databricks_target.py`/`test_report_documenter.py`
(`test_deterministic`, `test_render_docx_deterministic_content`).

**Verdict: grün**, frisch reproduziert (nicht nur aus dem Ledger übernommen).

---

## F3 — Semantisch verankert (Golden Thread)

**Behauptung:** jede Measure trägt einen strategischen Anker; keine Error-Verstöße.

**Befund (live ausgeführt):**
```
$ python -m tooling.superversion.golden_thread
[golden-thread] COM-001: WARN (0 error, 3 warn)
    WARN [dangling_visual_bind] page_1_summary_30s_2:Plan Sales Amount — ...
    WARN [dangling_visual_bind] page_1_summary_30s_2:Last Year Net Sales Amount — ...
    WARN [dangling_visual_bind] page_1_summary_30s_3:Plan Sales Amount — ...
[golden-thread] COM-002: WARN (0 error, 1 warn)
    WARN [dangling_visual_bind] page_1_summary_30s_3:Plan GM Amount — ...
[golden-thread] COM-003: OK (0 error, 0 warn)
[golden-thread] FIN-002: OK (0 error, 0 warn)
[golden-thread] SCM-002: OK (0 error, 0 warn)
[golden-thread] no error-severity violations.
```
Exit 0 — keine Error-Severity-Verstöße über die 5 gehärteten MVP-UCs
(`GATED_UCS` in `golden_thread.py`). `test_golden_thread.py` (18 Fälle) grün.

**Verdict: grün**, mit einer ehrlichen Einschränkung: das Gate ist bewusst auf die 5
gehärteten MVP-UCs skaliert (nicht alle 16), und trägt 4 Advisory-Warnungen
(`dangling_visual_bind` — Plan-/LY-Vergleichsmesswerte, die visuell gebunden, aber im
Semantic Model noch nicht materialisiert sind) offen benannt statt versteckt.

---

## F4 — Standalone-runnable (je Layer-Tool)

**Behauptung:** jedes Layer-Tool läuft eigenständig gegen einen nackten Stack, ohne
ALUCA-Abhängigkeit.

**Befund (live ausgeführt):**
```
$ python -m tooling.superversion.layer_tools.engines.cli all core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml
[engines] dataarch [beta] mode=ingest: 0 error, 0 warn, 1 info — OK
[engines] dataeng [beta] mode=ingest: 0 error, 0 warn, 2 info — OK
[engines] gov [beta] mode=ingest: 0 error, 0 warn, 0 info — OK

$ python -m tooling.superversion.layer_tools.packs.cli all core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml
[packs] dbt (dbt) [active]: 0 error, 0 warn, 2 info — OK
[packs] purview (Microsoft Purview) [active]: 0 error, 1 warn, 2 info — OK
    WARN [PURVIEW_TABLE_DESCRIBED] table has no description (glossary/catalog completeness): 'fact_sales'
[packs] unity_catalog (Databricks Unity Catalog) [active]: 0 error, 0 warn, 2 info — OK

$ python -m pytest tooling/superversion/tests/test_engines.py tooling/superversion/tests/test_packs.py \
    tooling/superversion/tests/test_visual_library.py tooling/superversion/tests/test_report_documenter.py -q
..........................................................                [100%]
58 passed in 2.87s
```
Jedes Layer-Tool (`report_documenter.py`, `visual_library.py`, `engines/`
gov/dataarch/dataeng, `packs/` dbt/purview/unity_catalog) hat sein eigenes `argparse`-CLI +
`if __name__ == "__main__"`-Einstiegspunkt, live bestätigt lauffähig. Der eine `WARN`
(`purview`, fehlende Tabellenbeschreibung) ist ein reales, nicht-blockierendes Advisory
— absichtlich mit ausgegeben, nicht unterdrückt.

**Verdict: grün**, mit einer ehrlichen Einschränkung: die gov/eng/arch-Engines sind
explizit als **Beta** gelabelt (`[beta]` in der Live-Ausgabe oben) — standalone-lauffähig,
aber nicht als vollständig premium zu verkaufen.

---

## F5 — Dokumentiert zum Handover-Standard

**Behauptung:** gebrandete Business- + Technical-Doku, kein "Tribal Knowledge".

**Befund (live ausgeführt, dieser Session):**
```
$ python -m tooling.superversion.layer_tools.report_documenter \
    core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml \
    --format docx --out /tmp/COM-001_handover.docx
[documenter] wrote /tmp/COM-001_handover.docx
```
37.815 Byte, real erzeugt — Beleg für [I-10.4](../plans/UMSETZUNGSPLAN_SUPERVERSION.md) (DOCX-Deliverable,
diese Session abgeschlossen). MD bleibt byte-exakt Golden-Snapshot-getestet
(`test_matches_golden_snapshot`); MD/DOCX-Content-Parität ist eigens getestet
(`test_md_and_docx_agree_on_content`), sodass beide Formate nicht auseinanderdriften.

**Verdict: grün.**

---

## F6 — Real evals, nicht nur Syntax

**Behauptung:** wertebasierte Checks + ≥2 Referenz-Ontologien (nicht nur ein Demo-Tenant).

### Teil 1 — ≥2 Referenz-Ontologien: grün

**Befund (live ausgeführt):**
```
$ python -m pytest tooling/superversion/tests/test_eval_regression.py -v
test_at_least_two_reference_ontologies PASSED
test_ontology_dataset_loads[COM-001] PASSED
test_ontology_dataset_loads[SCM-002] PASSED
test_ontology_is_self_consistent[COM-001] PASSED
test_ontology_is_self_consistent[SCM-002] PASSED
test_value_gate_green_on_reference_values[COM-001] PASSED
test_value_gate_green_on_reference_values[SCM-002] PASSED
test_value_gate_red_on_perturbation[COM-001] PASSED
test_value_gate_red_on_perturbation[SCM-002] PASSED
9 passed in 0.12s
```
Zwei echte, unterschiedliche Datensätze (`eval/data/commercial_invoice_lines.yaml` für
COM-001, `eval/data/supply_deliveries.yaml` für SCM-002), parametrisiert über
`available_use_cases()` — eine dritte Ontologie würde die Suite automatisch erweitern.
`test_value_gate_red_on_perturbation` beweist zusätzlich, dass das Gate echte Abweichungen
fängt (Sabotage-Experiment), nicht nur eine leere Hülle ist.

### Teil 2 — Live-DAX-Ausführung gegen Referenzwerte (nicht Oracle-Selbstvergleich): rot/offen

**Befund:** `tooling/superversion/eval/value_gate.py`s eigener Docstring (Zeilen 10–11)
benennt die Lücke selbst: das Gate vergleicht die berechneten Werte gegen eine „engine run,
a values file, or (for tests/self-check) the reference oracle `refcalc` over the same
dataset" — für Tests läuft `refcalc` gegen `refcalc`, ein Selbstvergleich (Review-Befund A4).
Eine echte Live-Ausführung existiert nicht:
```
$ find . -iname "live_cert*"
(keine Treffer)
```
Das einzig verwandte Skript, `products/fabric/powerbi/tooling/scripts/execute_dax.py`, ist
ein manuelles, nicht in die Superversion-Pipeline verdrahtetes Utility — es braucht
`az login` (authentifizierte Azure-CLI) + `fab auth login` (authentifizierte Fabric-CLI) +
einen echten Fabric-Workspace mit Dataset. Keins davon existiert in dieser Sandbox.

Der geplante minimale G1-Pfad („Sandbox-Workspace + `executeQueries` gegen Referenzwerte,
2 UCs, opt-in", Review-Cut S-4, `docs/plans/UMSETZUNGSPLAN_SUPERVERSION.md` Zeile 278/357) ist bisher
**nur als Plan dokumentiert, nicht als eigener I-Task oder Code gebaut** — kein
`live_cert.py`, keine Sandbox-Provisionierung, kein `--live`-Opt-in-Gate.

**Verdict: Teil 1 grün; Teil 2 ehrlich rot/offen.** Das ist kein "könnte noch gebaut
werden"-Gap, sondern ein **"braucht eine echte Fabric/Power-BI-Tenant-Verbindung, die diese
Sandbox nicht hat"**-Gap — strukturell derselbe Sandbox-Grund wie F1, hier zusätzlich ohne
lokal installierbare CLI-Abhilfe (ein echter Tenant + Credentials sind erforderlich, nicht
nur ein fehlendes Paket).

---

## Findings-Liste (rote Floors, ehrlich offen)

| # | Floor | Was fehlt | Warum hier nicht schließbar | Nächster Schritt |
|---|---|---|---|---|
| 1 | F1 | `powerbi-report-author`-CLI-Validierung mit echten 0 Errors | CLI nicht installiert/erreichbar in dieser Sandbox | Node+npm-Install von `@microsoft/powerbi-report-authoring-cli` in einer Umgebung mit Netzzugriff auf die Registry (bereits Teil von `.github/workflows/superversion.yml`s CI-Setup — dort läuft dieser Check tatsächlich, hier lokal nicht) |
| 2 | F6 (Teil 2) | Live-DAX-Ausführung gegen ein echtes Fabric-Dataset, verglichen mit Referenzwerten (kein Selbstvergleich) | Braucht einen echten Fabric-Tenant + authentifizierte `az`/`fab`-CLIs — in dieser Sandbox nicht vorhanden und nicht herstellbar | G1-minimal bauen (Sandbox-Workspace-Deploy + `executeQueries`, 2 UCs, opt-in `--live`-Flag mit ehrlichem SKIP-Fallback wie die bestehenden `shutil.which`-Muster) — als eigener I-Task, sobald Tenant-Zugriff verfügbar ist |
| 3 | F0 (Rest-Scope) | 9 benannte KPIs über 11 Nicht-MVP-UCs bleiben `hitl` | Legacy-Datenquellen fehlen (4×), Grammatik-Grenze (2×), unterspezifizierte Business-Regel (3×) | Je in ADR-0013 dokumentiert; kein pauschaler Blocker, sondern 9 einzelne, unterschiedlich geartete Tasks |

Keine dieser drei Zeilen wird als "grün" behauptet. Alle drei sind hier bewusst als offen
geführt, mit einem konkreten, nicht geratenen nächsten Schritt.

---

## Belegkommandos (zum Nachvollziehen)

```bash
# F0
python -m pytest tooling/superversion/tests/test_calculation_coverage.py -q

# F1 (zeigt den Sandbox-Gap)
which powerbi-report-author
python -m tooling.superversion.e2e_smoke

# F2
for seed in 0 1 42; do
  PYTHONHASHSEED=$seed python -c "
from tooling.superversion.from_aluca import from_bracket_file
from tooling.superversion.targets import tmdl
import hashlib
model = from_bracket_file('core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml', 'core/kpi_catalog/kpis')
print(hashlib.sha256('\n'.join(tmdl.emit(model).values()).encode()).hexdigest())
"
done

# F3
python -m tooling.superversion.golden_thread

# F4
python -m tooling.superversion.layer_tools.engines.cli all core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml
python -m tooling.superversion.layer_tools.packs.cli all core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml
python -m pytest tooling/superversion/tests/test_engines.py tooling/superversion/tests/test_packs.py \
  tooling/superversion/tests/test_visual_library.py tooling/superversion/tests/test_report_documenter.py -q

# F5
python -m tooling.superversion.layer_tools.report_documenter \
  core/usecases/core/COM-001_Sales_Performance/UseCase_Bracket.yaml --format docx --out /tmp/COM-001_handover.docx

# F6 (Teil 1)
python -m pytest tooling/superversion/tests/test_eval_regression.py -v
```
