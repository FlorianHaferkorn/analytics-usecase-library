---
last-reviewed: 2026-09-29
shelf-life-days: 90
---
# Fabric-Neuerungen FabCon Europe 2026 — Aufgaben für ALUCA

**Pickup-Brief.** Eine neue Sitzung kann jede offene Aufgabe hier direkt übernehmen. Ablauf und
Übernahme-Prompt stehen unten. Anlass: FabCon Europe + SQLCon, Barcelona, 28.09.–01.10.2026.

Grundlage, Stand 29.09.2026:
- Microsoft Learn „What's new in Microsoft Fabric“ (Einträge bis Sep 2026)
- Learn-Fachseiten und PyPI/npm

Nicht verwendet: Den Keynote-Blog vom 28.09. weist der Egress-Proxy ab; nur Such-Snippets sind bekannt.

**Gegenstück:** Meridian führt denselben Plan als Initiative I-21 (Freelancing-Repo,
`docs/plans/PLAN_FabCon_EU_2026_Fabric_Nachzug_2026-09-29.md`). Die Aufgaben-IDs hier sind dieselben.

## Parität (Meridian D-577, Modus a — Spiegel mit Sensor)
- **A** = ALUCA-eigener Code, wird hier geändert.
- **M→A** = gespiegelter Meridian-Code (`tooling/superversion/vendor/meridian_dataarch/`). **Nie hier
  direkt ändern.** Die Änderung landet zuerst in Meridian. Danach hier:
  1. `python scripts/check_dataarch_mirror.py --write --ref <meridian-commit>`
  2. `python -m pytest tooling/tests/ products/ -q`
- Keine Aufgabe darf die Unterschiede zu Meridian vergrößern (Liste in D-577): Fabric-Pins,
  PBIR-Schema-Pins, Speichermodus, Deployment, Copilot-Readiness.

## Vor Code zu entscheiden (Florian)
| # | Frage | Blockiert |
|---|---|---|
| E-1 | Gemeinsamer Speichermodus: Direct Lake (Meridian-Default) · Import (ALUCA heute) · Modus als Parameter | W2.1 |
| E-2 | Eigener Grounding-MCP (Meridian ADR-0049) neben Fabric IQ MCP (GA) | — (nur Meridian) |
| E-3 | Deployment-Default (Meridian-Code `deployment-pipelines` vs. ADR-0050 „zuerst 4 und 1“) | W2.6 |
| E-4 | Policy Weaver (Quellrechte Snowflake/Databricks → OneLake-Rollen) adoptieren | W1.5 |
| E-5 | Lieferweg der Ontologie-Inhalte nach Fabric IQ: RDF/OWL-Turtle über die Import-Funktion + Kontextpaket für den Ontology agent · TMDL-Item-Definition per API · „Generate from semantic model“ | W4.3 |
| E-6 | Gemeinsame Geschäftsobjekt-Schicht (Entity types) und ein KPI-ID-Schema mit Meridian (heute `sales.net_sales.amount` hier, `KPI-FIN-001` dort) | W4.6 |
| E-7 | Fabric Planning als Blueprint-Option und Angebot | W4.7 (Option) |

## Aufgaben und Stand

Legende Status: `offen` · `in Arbeit (Branch, Datum)` · `erledigt (Datum, PR #)` · `blockiert (Grund)`.

| ID | Aufgabe | Art | Status | DoD (Out · Prüfung) |
|---|---|---|---|---|
| **W0.3a** | **`fabric-cli>=1.0.0` ist das falsche Paket.** Gemessen 29.09.2026 per PyPI-JSON: `fabric-cli` ist der „FABRIC Python Client“ (fabric-testbed, latest 0.8); `>=1.0.0` ist damit unerfüllbar. Microsofts CLI heißt `ms-fabric-cli` (latest 1.7.0) | A | offen | `products/fabric/powerbi/deployment/resources/requirements.txt` auf `ms-fabric-cli==<Meridian-Pin>` · frisches venv: `pip install -r …` läuft durch, `fab --version` |
| W0.3b | `fabric-cicd>=0.1.30` exakt pinnen, gleicher Wert wie Meridian (latest 1.3.0 am 29.09.) | A | offen | gleicher Pin in beiden Repos · `pytest products/fabric/powerbi/deployment` (falls vorhanden) + Import-Smoke `fabric_release.py` |
| W0.4 | `powerbi-report-author`: Pin 0.1.1, npm latest **0.4.0** (Meridian-Sensor 29.09.); 0.1.4 ergab 694 Befunde (`docs/architecture/pbir_cli_014_triage.md`) | A (mit M) | offen | Triage 0.4.0 analog zur 0.1.4-Triage, Pin-Entscheid gleich wie Meridian · Stage 1 grün |
| W0.2 | „OneLake Security GA since May 2026“ im gespiegelten `provision_governance.py` belegen oder kennzeichnen | M→A | offen | Spiegel nachgezogen, Sensor ohne Drift |
| W1.1 | **Capacity overage** (GA Sep 2026, bei F-SKUs standardmäßig an): Overage-Limit bzw. „aus“ als Pflichtangabe | A (+M→A) | offen | `tooling/superversion/capacity.py` + `internal/proposal_costing/` (Modell, Templates) tragen den Parameter ohne Default · Tests `internal/proposal_costing/tests`, pytest grün |
| W1.2 | Echtzeit-Capacity (Capacity Overview Events → Eventstream → Eventhouse + Alarm; Dashboard aus Jumpstart-Accelerator) | M→A | offen | Spiegel nachgezogen; `docs/operational/rollout_and_alerting_standard.md` verweist darauf |
| W1.3 | Surge Protection je Workspace (Preview) als Parameter | M→A | offen | Spiegel nachgezogen |
| W1.4 | Tenant-Settings-API: Preview-Caveat neu messen | M→A | offen | Spiegel nachgezogen |
| W1.5 | OneLake-Rollen auf gespiegelten Items (Preview, nur Read) + Policy-Weaver-Test | M→A | blockiert (E-4 nach Test) | Spiegel nachgezogen |
| W1.6 | Workspace-Monitoring-Item: Create-API? | M→A | offen | Spiegel nachgezogen |
| W2.1 | Speichermodus nach E-1. Heute Import-Modus, und `GoldDataPath` ist ein lokaler Windows-Pfad (`dist/*/definition/expressions.tmdl`) | A | blockiert (E-1) | Blueprints/Orchestrator erzeugen den gewählten Modus; Pfad als Parameter/Variable Library · Stage 1 + pytest grün, Desktop-Laden per `CLAUDE_CLI_PBI_DESKTOP_TASKS.md` |
| W2.2 | Runtime 2.0 / MLV-Kompatibilität | M→A | offen | Spiegel nachgezogen |
| W2.3 | MLV Event-driven Refresh | M→A | offen | Spiegel nachgezogen |
| W2.4 | dbt Job (GA Sep 2026) auch für den OSS-/dbt-Pfad prüfen | A | offen | Notiz in `products/_INDEX.md`-Bereich OSS, ggf. Adapter |
| W2.6 | Deployment-Default nach E-3; `deployment/scripts/fabric_release.py` angleichen | A (+M→A) | blockiert (E-3) | gleiche Default-Strategie wie Meridian · pytest |
| W3.2 | Copilot-Readiness-Parität: kein Gegenstück zu Meridians `meridian_copilot_readiness` (AI instructions, Verified answers, AI data schema); heute nur manuell (`tmdl_best_practices.md`) | A | offen | Produkt gespiegelt oder Unterschied in D-577 deklariert · Florian entscheidet |
| W3.3 | Q&A endet Feb 2027: Wert von `cultures/*.tmdl` und Gate H8 (`products/fabric/powerbi/docs/linux-generation.md`) neu bewerten | A | offen | Gate behalten/umwidmen mit Beleg (nutzt Copilot das linguistische Schema? → Learn) |
| W3.4 | Data Agent: eingestellte Wege (Assistants API, Data-Agent-Integration in Copilot in Power BI, beide 26.08.2026) | M→A | offen | Spiegel nachgezogen |
| W3.5 | Power BI Modeling MCP: Doku nennt 0.1.9, npm latest 1.0.0, Learn „lokal GA“ | A | offen | `products/fabric/powerbi/docs/references/powerbi-modeling-mcp-setup.md` aktualisiert, gleicher Stand wie Meridian-Pin |
| W3.6 | PBIP: Regel „Desktop does not watch files“ (`.claude/rules/connect-pbid.md`) gegen das Desktop-Update Aug 2026 testen; PBIR-Schema-Pins (`schema_registry.py`: visualContainer 2.9.0, Theme 2.154) mit Meridian (2.3.0 / 2.145) angleichen | A | offen | Regel bestätigt/angepasst (Desktop-gated) · Schema-Pins gleich, Stage 1 grün |

### Welle 4 — Ontologie (Fabric IQ) und Fabric Planning

Befund (Learn, 29.09.2026):
- Die neue Ontology-Oberfläche (Preview) definiert Items in TMDL. Die alte JSON-Definition gilt nur noch für Altitems, die alte Oberfläche endet am 31.01.2027.
- Import von RDF/OWL als TTL in ein leeres Item ist möglich (Preview).
- Der Ontology agent (Copilot, Preview) nimmt bis zu 10 Dateien als Kontext und baut Entities und Bindungen aus Workspace-Daten.
- ALUCA hat heute keine Ontologie im Fabric-Sinn, nur KPI-Katalog und Golden-Thread-Registry; eine Geschäftsobjekt-Schicht fehlt.
- Der Fabric-Ontology-Emitter (`sap_ontology.py`) ist Meridian-eigen und nicht gespiegelt.

| ID | Aufgabe | Art | Status | DoD |
|---|---|---|---|---|
| W4.3 | Ontologie-Inhalte aus ALUCA (KPI-YAML, Golden-Thread-Registry `tooling/ontology/`) für Fabric IQ bereitstellen: Registry-Kanten sind Use-Case-/KPI-/Action-Beziehungen, keine Datenbeziehungen; KPI-Definitionen werden Beschreibung/Metric (`explicit` SQL, kein DAX), Action-Codes werden Rule-Statements. Der Emitter selbst entsteht in Meridian (TTL, nach E-5) | M→A (+A) | blockiert (E-5) | ALUCA-Seite liefert die Eingaben im Format, das der Meridian-Emitter erwartet · pytest |
| W4.4 | TMDL-Modelle aus `dist/` so emittieren, dass Fabric „Generate from semantic model“ saubere Entities/Relationships liefert (Keys, Beziehungen, `///`-Beschreibungen) | A | offen (Tenant-gated für die Probe) | Checkliste im Generator-Gate · Stage 1 grün; Probe im Tenant |
| W4.6 | Geschäftsobjekt-Schicht + ID-Schema nach E-6 (Schema-First in `tooling/generator/schemas/`) | A | blockiert (E-6) | Schema gleich wie Meridian · pytest |
| W4.7 | **Fabric Planning** (GA Jul 2026): Plan-Item an genau ein Semantic Model gebunden, Write-back nur in Fabric SQL DB, F-SKU/P1, Abrechnung je 30-Tage-Session (laut Learn: Planner 847 CU-h, Stakeholder 168 CU-h, Viewer 37 CU-h). FIN-Use-Cases mit Plan-Zielen sind die naheliegenden Kandidaten | A | offen (Kalkulation) | `tooling/superversion/capacity.py` + `internal/proposal_costing/` um Planning-Sessions erweitert · Tests grün; Blueprint-Option erst nach E-7 |

## Beobachten statt bauen
Die Watchlist liegt in Meridian (`research/upstream_pins.yaml` → `feature_watch`). Der Wochen-Radar
prüft sie. Ändert sich dort ein Status (Mirroring mit Quellrechten, Copilot im Portal mit Skills,
Deployment plan, Fabric policies, Capacity Operation Events, Prep data for AI API), wird hier eine
Zeile ergänzt.

## Ablauf für eine übernehmende Sitzung
1. Diese Datei lesen, dann `internal/project_mgmt/KNOWN_ERRORS_AND_FIXES.md`, wenn validiert wird.
2. Erste Aufgabe mit Status `offen` in der niedrigsten Welle wählen. `blockiert` überspringen.
   **M→A**-Aufgaben erst, wenn die Meridian-Seite gemergt ist.
3. Branch `runde/<YYYY-MM-DD>-<id>`; Status hier auf `in Arbeit (Branch, Datum)` setzen, im selben PR.
4. Umsetzen, Quality-Gate aus `CLAUDE.md` fahren (mindestens Stage 1 + pytest), Entwurfs-PR.
5. Status auf `erledigt (Datum, PR #)`; neue Fehlerklassen in `KNOWN_ERRORS_AND_FIXES.md`.

**Übernahme-Prompt (zum Einfügen):**
```
Lies internal/project_mgmt/FABRIC_FABCON_EU_2026_PLAN.md und übernimm die erste offene Aufgabe
der niedrigsten Welle (blockierte überspringen, M→A nur nach Meridian-Merge). Folge dem Abschnitt
„Ablauf für eine übernehmende Sitzung“ und den Regeln aus CLAUDE.md/AGENTS.md. Setze den Status in
der Tabelle im selben PR.
```
