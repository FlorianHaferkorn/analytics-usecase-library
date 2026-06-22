# ALUCA × Meridian → Superversion: Analyse, Zielbild & ALUCA-Umbau-Fahrplan

> **Status:** Analyse-/Entscheidungsdokument · 2026-06-18 · kein ADR (ADR folgt, s. §10).
> **Auftrag:** Beide IP-Stacks und ihre Toolings funktional vergleichen, gemeinsame
> Lücken benennen, das Framework-Zielbild fixieren und einen konkreten Umbau-Fahrplan
> für ALUCA ableiten. Belege als Dateipfade; Annahmen mit **⚠️ UNKLAR**.
> **Methodik:** Code-gelesen (nicht nur READMEs), QA+SA-Doppelreview (§11).

## Inhalt
1. [TL;DR & zentrale These](#1-tldr)
2. [Funktionsvergleich B1–B11](#2-funktionsvergleich)
3. [Code-Tiefenanalyse (Unterbau)](#3-code-tiefenanalyse)
4. [Gemeinsame Lücken G1–G7](#4-gemeinsame-luecken)
5. [Bauprinzipien P1–P5 (Doktrin)](#5-bauprinzipien)
6. [Framework-Zielbild](#6-zielbild)
7. [Zielarchitektur](#7-zielarchitektur)
8. [Domänen Gov/Eng/Arch — tool-spezifisch & dual-modal](#8-domaenen)
9. [Optionen & Empfehlung](#9-optionen)
10. [ALUCA-Umbau-Fahrplan](#10-fahrplan)
11. [QA/SA-Review & Risiken](#11-qa-sa)

---

## 1. TL;DR & zentrale These {#1-tldr}

**Das Produkt ist ein Supervisions-Layer, kein Merge zweier Tools.** ALUCA und Meridian
bleiben eigenständig lauffähig (P5); die Superversion ist die dünne, deterministische
Orchestrierungs- und Qualitätsschicht *darüber*, die ihre Stärken kombiniert, ihre
Black Boxes schließt und einen einheitlichen Quality-Floor erzwingt.

**Kein Gesamtsieger — komplementäre Hälften** (Code-belegt, §3):
- **ALUCA modelliert die obere Hälfte agnostisch:** Strategie→KPI→UseCase→**Visual-
  Layout**. `VisualType` ist *echt* platform-agnostisch, Compiler subprocess-frei,
  Golden-Thread operationalisiert, DSGVO-Stack vollständig, Studio editierfähig.
- **Meridian modelliert die untere Hälfte im Vollzug:** **Semantic Model→Measure→
  Stack-Datei**. Reife Parser/Audit (~50 PBI-Regeln)/Targets (8)/Gates/DOCX, aber das
  kanonische Modell ist heute **DAX-durchsetzt**, nicht neutral.

**Die zentrale These:** Beide haben ihren Agnostik-Anspruch nur zur Hälfte eingelöst, an
komplementären Enden. Die Superversion verbindet ALUCAs Bedeutungs-/Visual-Schicht mit
Meridians Vollzugs-Schicht über einen **vendor-neutralen Core**, der gegen Datenhaltung,
Semantic Layer und Visualisierung gleichermaßen indifferent ist (§7).

**Wo der neutrale Core lebt (Architektur-Entscheidung, vorher unklar):** Der neutrale
Core entsteht **als eigenes Modul im Meridian-Repo, oberhalb von `pbi_engine`** — nicht
*in* der PBI-Engine (sonst bliebe er PBI-gravitiert). `pbi_engine` wird *ein Konsument*
des neutralen Cores, gleichrangig zu künftigen Stack-Engines. Begründung: Meridian hat
mit `check_core_independence` + Registry-Pattern die reifere Substrat-Disziplin; einen
dritten leeren Repo aufzusetzen widerspräche „Tools leben weiter" (P5) und „nicht neu
erfinden" (P1). ALUCA dockt über `from_aluca` an (additiv), bleibt aber standalone
lauffähig. **⚠️ UNKLAR:** ob der Core sauber *über* pbi_engine zu heben ist, ohne dessen
DAX-Annahmen mitzuschleppen — das ist genau die Frage, die Spike W0 beantwortet.

**Wert-Aufteilung (justiert nach SA-Review):** ~65 % **Vereinheitlichung** vorhandener
Stärken (B1–B11 verbinden), ~20 % **Refactoring** (neutraler Core W1 — ist Umbau, nicht
Erfindung), ~15 % **echtes Neuland** (Wirkungs-Loop W7, Team-Skalierung W8 — heute
nirgends gebaut). Der „auf-Steroiden"-Effekt steckt in den 15 %, ist aber noch *skizziert*,
nicht entworfen.

**⚠️ Korrektur gegenüber frühen Entwürfen:** „Meridian-Chassis ist tool-agnostisch" ist
im Code *nicht* haltbar (§3.3). Der neutrale Core ist **Bauziel**, nicht Zustand.

---

## 2. Funktionsvergleich B1–B11 {#2-funktionsvergleich}

Wertschöpfungskette **Strategie → KPI → Use Case → Semantic Model → Report/Action →
Audit → Deliverable**. Reife: ⬤ produktreif · ◑ funktional · ○ Prototyp/Stub.

| # | Funktionsbereich | ALUCA | Meridian | Superversion nutzt |
|---|---|---|---|---|
| B1 | Strategie-/Bedeutungs-Ontologie (WHY) | ⬤ befüllt (`golden_20.yaml`) | ◑ Schema reich, Instanz nur Aurora | **ALUCA-Content** auf neutralem Schema |
| B2 | Golden-Thread-Engine (Lineage) | ⬤ `registry_builder.py` + 40 Cross-Ref-Checks | ○ kein `validate_golden_thread()` | **ALUCA** → wird Gate |
| B3 | Use-Case-Deklaration + UX-Doktrin | ⬤ Bracket 3-30-300 + Value-Driver | ◑ `use_case.schema.json` + M1-DOCX | **ALUCA-Bracket** + Meridian-Fassade |
| B4 | Kanonisches Modell | ◑ Visual-IR agnostisch, Semantik fehlt | ◑ reif, aber **DAX-primär** | **neu: neutraler Core** aus beiden (§3,§7) |
| B5 | Source-/Migration-Achse | ○ kein Brownfield/Migration | ⬤ brownfield/greenfield/tableau/qlik/looker | **Meridian** + neuer `from_aluca` |
| B6 | Domänen-Engines + Audit | ○ nur Schema/Drift | ⬤ PBI (~50 Regeln) / ◑–○ Rest | **Meridian-PBI** + ALUCA-COMP\*/GT\* |
| B7 | Multi-Stack-Targets | ○ PBI ok, OSS-Stubs | ⬤ 8 live (Registry) | **Meridian-Registry** |
| B8 | Rendering + Official-First | ○ Prototyp, keine MS-CLI | ⬤ headless + `check_pbir` + Pin-Sensor | **Meridian** |
| B9 | Compliance (DSGVO/EU-AI-Act) | ⬤ DPIA/AVV/Art.30 | ◑ Audit-Vollzug, schmaler Doc-Stack | **ALUCA-Breite × Meridian-Vollzug** |
| B10 | Deliverable-Engine (DOCX/XLSX) | ○ keiner | ⬤ Branding + Fassaden + bundles | **Meridian** |
| B11 | Steuerung (CLI/Health/Gates/Skills) | ⬤ Health H1–H8 + GADW-Skills | ⬤ forge + products.yaml + Gates | **Both** |

**Muster:** ALUCA dominiert das *Was/Warum* (B1–B3, B9), Meridian das *Wie/Womit*
(B5–B8, B10). B4 ist die **gemeinsame Baustelle** (neutraler Core), B11 echtes Both.
Genau die saubere Trennung macht die Kombination wertvoll statt redundant.

*(Detaillierte Pro/Contra je B-Bereich: Git-Historie dieses Dokuments, frühere Fassungen.)*

---

## 3. Code-Tiefenanalyse — der Unterbau {#3-code-tiefenanalyse}

Belastbarste Ebene: gelesener Quelltext, nicht Inventar. Reife-% = grobe
Masse-/Vollständigkeits-Schätzung, kein Messwert.

### 3.1 Die zwei Kerne nebeneinander

| Dimension | **ALUCA** | **Meridian** |
|---|---|---|
| Kern-Artefakt | `DashboardSpec` (`generator_core/ir/specs.py`, ~323 Z.) | `CanonicalModel`=`SemanticModel`+`ReportModel` (`pbi_engine/`, Parser ~556 Z.) |
| Agnostik **belegt** | ⬤ `VisualType` „platform-agnostic", `AdapterTarget`={PBIP,METABASE,GRAFANA,SUPERSET,REDASH}, Position 0.0–1.0, Name-Bindings | ◑ Adapter-Vertrag agnostisch, aber `Measure.expression` **primär DAX**; Multi-Dialekt nur Zweitfeld `expressions["sql"]` |
| Power-BI-Leck | `measures_from_ir.py:46` importiert `_build_tmdl_measures`; Canvas hartcodiert | TMDL-Parser komplett PBI-Syntax; `ReportModel` nur bei PBIR; kein Glossar/Domäne/Lineage |
| Sprache/Portierbarkeit | IR-Kern **reines Python, 0 subprocess** (Shell nur in `suggester.py` + äußere Orchestratoren) | reines Python, `check_core_independence` erzwingt 0 Framework-Import |
| Modelliert | obere Hälfte: Strategie→UseCase→**Visual** | untere Hälfte: **Measure-Dialekt**→Stack |

**Pointe:** ALUCAs IR ist beim Visual-Agnostizismus *sauberer* als Meridians
DAX-zentriertes Modell; Meridian ist beim Vollzug massiv reifer. Beide nur zur Hälfte
agnostisch — an komplementären Enden. **ALUCAs IR endet, wo Meridians anfängt.**

### 3.2 Reifegrad je Code-Komponente

| Komponente | ALUCA | Meridian |
|---|---|---|
| Kanonisches Modell / IR | ◑ Visual reif, Semantik fehlt | ◑ reif, DAX-Bias |
| Compiler / Parser | ⬤ BracketCompiler robust | ⬤ TMDL/PBIR + parse-parity |
| PBI-Audit-Regelkatalog | ○ keiner | ⬤ ~50 Regeln, `suggested_fix`, Scoring |
| gov / dataarch / dataeng | ○ keiner | ◑ gov / ○ dataarch / ○ dataeng |
| Target-Adapter | ◑ PBIP reif, OSS funktional–Stub | ⬤ pbir reif (~212 Z.); osi/snowflake/evidence robust; databricks/duckdb/rill/cube graceful-degradation (SQL-Dialekt nötig, kein DAX→SQL-Raten) |
| Rendering + Official-First | ○ Prototyp | ⬤ headless + `check_pbir` + Pin-Sensor |
| Golden-Thread-Engine | ◑ Registry+Drift, keine DAX-Closure | ○ keiner |
| DI (Trigger→Aktion) | ○ minimal | ◑ Trigger ehrlich, **Alert-only** |
| AIS (KI-Analyse) | ○ keiner | ◑ 3-stufig, **Automation-Level 1 hart gecappt** |
| Studio | ◑ **editierfähig** (Next.js/SQLite, Golden-Thread-Flow, Drift-Viewer, multi-LLM) | ○ **View-only** (Single-File-React, Cut 1.1) |
| Steuer-CLI | ◑ PS-Orchestrator + Health H1–H8 | ⬤ `forge` registry-driven |
| Tests/CI | ◑ 57 Python-Tests, CI (stage1/linux-generation) | ⬤ ~145 Test-Dateien, `make check` |

### 3.3 Drei korrigierte Behauptungen (Ehrlichkeit, GOI §1)

1. **„Meridian-Chassis ist tool-agnostisch."** → Halb falsch. DAX-primär,
   PBI-Parser-gebunden. *Konsequenz:* neutraler Core ist Bauziel (§10 W1).
2. **„ALUCA ist PowerShell-lastig im Kern."** → Falsch für den IR-Kern (0 subprocess,
   portierbar). *Konsequenz:* `from_aluca` billiger als gedacht; das einzige PBI-Leck
   ist eine Zeile.
3. **„Meridians 4 Engines sind gleichwertig."** → Falsch. pbi_engine ~80 % der Masse,
   dataeng Stub-nah. *Konsequenz:* „4-Domänen" ist heute 1 Domäne + 3 Gerüste (§8).

### 3.4 Studio — die überraschende Asymmetrie
ALUCAs Studio ist beim **Editing reifer** (echtes Editing + Golden-Thread-Visualisierung
+ Drift-Viewer), Meridians ist View-only (Cut 1.1) — aber Meridian hat ~2,7× mehr
Test-Masse (~145 vs. 57), also ist „ALUCA reifer" auf die *Studio-Editierfähigkeit*
begrenzt, nicht aufs Gesamtprodukt. → **Studio-Frontend-Konzept aus ALUCA, Engine aus
Meridian** — Anbindung sauber über die Supervisions-Schicht, nicht Tool-zu-Tool (s. §10
W5, P5-Hinweis).

### 3.5 `from_aluca`-Portierbarkeit (Code-Schätzung)
IR-Compiler/specs/catalog_readers reines Python (portierbar wie sie sind);
Drift-Scanner-Logik 1:1 nach Python. Echter Neubau nur: IR→`CanonicalModel`-Feld-Mapping
+ Lösen der einen PBI-Import-Zeile. **Grob 5–7 Personen-Wochen** inkl. Tests.

---

## 4. Gemeinsame Lücken G1–G7 {#4-gemeinsame-luecken}

Was **keiner** heute füllt — der Layer erbt sie, statt sie automatisch zu lösen. ⬤
vorhanden · ◑ teilweise · ○ fehlt.

| # | Lücke | ALUCA | Meridian | Schweregrad |
|---|---|---|---|---|
| G1 | Live-Deploy in Kunden-Tenant (Artefakt→Workspace/Refresh) | ○ | ○ | hoch (Time-to-Value) |
| G2 | Closed Loop / Wirkungsmessung (Action→KPI-Effekt) | ○ | ◑ DI advisory | hoch (DI-Reifesprung) |
| G3 | Semantische Output-Evals (nicht nur Syntax) | ◑ | ◑ | mittel-hoch |
| G4 | Physische Modellierungstiefe (Star-Schema/SCD/Partition) | ○ | ◑ | mittel |
| G5 | Team-/Org-Skalierung (über Solo hinaus) | ○ | ○ | hoch (Nagarro-Pfad) |
| G6 | Branchen-Content-Skalierung (über Aurora hinaus) | ◑ | ◑ | mittel |
| G7 | Tool-spezifische Domänentiefe außerhalb PBI | ○ | ◑ | mittel (§8) |

**Muster:** Die Lücken sitzen am **Rand der Wertschöpfung** — davor (G4), danach (G1/G2),
darüber (G5/G6), in der Breite (G3/G7). Der Kern (Strategie→Report deterministisch) ist
stark. Die Ränder sind die Roadmap.

---

## 5. Bauprinzipien P1–P5 (Doktrin, nicht verhandelbar) {#5-bauprinzipien}

Jede Komponente (Skill, Generator, Grounding, Gate, Adapter) wird daran gemessen.

### P1 · Tool-Agnostik als Fundament, Official-First als Konsequenz
Kern ist **Vendor-Neutralität, nicht Microsoft.** Der Core bindet sich an offene,
herstellerneutrale Standards; jeder Anbieter (MS Fabric, dbt, Cube, Snowflake, Google)
ist ein *austauschbarer Adapter*. Official-First gilt **je Stack-Adapter**: für PBI ist
`microsoft/skills-for-fabric` + `powerbi-report-authoring` der *erste* Adapter (Meridian
D-157, ADR-0032; ALUCA ADR-0002), nicht die Basis — ein dbt-/Cube-Adapter tritt
gleichrangig daneben. Pin-Disziplin + Drift-Sensor (D-238). **Lackmustest:** Stack-Wechsel
darf die Bedeutungs-Schicht nicht verändern.
**⚠️ UNKLAR:** wie vollständig offene Semantic-Layer-Standards (OSI/MetricFlow) ALUCAs
*Layout*-Semantik (3-30-300) tragen — Delta = legitimer Eigen-Scope.

### P2 · Determinismus in Generierung & Test — LLM-Freiheit im Authoring
Die Grenze ist die *Phase*, nicht die Rolle:

| Phase | Modus | Begründung |
|---|---|---|
| **Authoring / Ideation** (Use-Case-Findung, KPI-Vorschlag, Layout-Entwurf) | **LLM-Freiheit** | hier ist Probabilistik der Wert |
| **Compile / Generierung** (Spec → TMDL/PBIR/Semantic-Layer) | **strikt deterministisch** | gleicher Input → byte-stabiler Output (ADR-0015) |
| **Test / Gate** (Validierung, Audit, Golden-Thread, Compliance) | **strikt deterministisch** | ein Gate, das mal so/mal so urteilt, ist wertlos |

**Übergangspunkt = HITL-Freigabe:** LLM-Entwurf → validiertes Spec → Freigabe → **ab da
kein LLM mehr.** Jeder Generator/jedes Gate muss ohne KI lauffähig sein.

### P3 · KI nur wo nötig — passendes Modell je Task
Notwendigkeitstest (geht es deterministisch? → kein LLM). Modell-Routing nach
Task-Schwere (Extraktion/Klassifikation → kleines Modell; Reasoning/Synthese → großes;
GOI §3 Haiku/Sonnet/Opus). Strukturierter Zwang: Output gegen JSON-Schema, `temperature=0`,
native tool-calling (Meridian-AIS-Muster vorhanden, Routing fehlt). Token-Budget je
Pipeline-Schritt als messbare Größe (→ Health-Scorecard).

### P4 · Garantierte Mindestqualität (Quality-Floor) überall
Kein Artefakt unter dem Floor — einheitlich über Skills/Generatoren/Grounding/Adapter:
- **Strukturell:** offizielle Stack-Validatoren 0 Errors (`check_pbir`), Schema-Validität.
- **Semantisch:** Golden-Thread-Gate, Audit-Score ≥ Schwelle, COMP\*-Regeln grün.
- **Grounding:** jede KI-Aussage trägt Provenance.
- **Mechanik:** *eine* gemeinsame Gate-Schicht (Meridian `conformance.py` + ALUCA
  Stage-1/Drift), die alle Tools durchlaufen.
- **Messbar:** Floor ist ein Gate, das rot wird — keine Absicht.

### P5 · Supervision statt Monolith — die Tools leben weiter
Der Layer **orchestriert, absorbiert nicht.** ALUCA und Meridian bleiben eigenständig
lauffähig (`check_core_independence`, Fassaden-Prinzip). Der Layer ruft über klare
Verträge auf (`emit()`, forge-Dispatch, MS-Skill), legt Gate/Health/Grounding darüber
und schließt die G-Lücken durch *Verbinden*, nicht Neubau.

### Prinzipien-Konformität heute
| Prinzip | ALUCA | Meridian | Lücke |
|---|---|---|---|
| P1 Agnostik/Official-First | ◑ Doktrin | ⬤ live, aber DAX-Bias | neutraler Core + ALUCA-Renderer→MS-Skill |
| P2 Determinismus | ⬤ | ⬤ | konsistent |
| P3 KI gezielt + Routing | ○ | ◑ kein Routing | Routing + Token-Budget |
| P4 Quality-Floor | ◑ | ⬤ | *eine* Gate-Schicht |
| P5 Supervision | ⬤ | ⬤ | **Layer existiert nicht — das ist das Produkt** |

**Kern:** Vier der fünf Prinzipien sind in *einem* Tool gelebt — vereinheitlichen, nicht
erfinden. Nur P5 (der Layer) ist echter Neubau.
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                              
---

## 6. Framework-Zielbild {#6-zielbild}

**Ein-Satz-Zielbild:** *Ein Supervisions-Framework, das eine strategische Geschäftsfrage
über einen vendor-neutralen Core in ein auf jedem beliebigen Daten-/Semantic-/Visual-
Stack lauffähiges, auditiertes, compliance-geprüftes und in seiner Wirkung messbares
Analytics-Produkt übersetzt — deterministisch ab der Freigabe, ohne semantischen Drift.*

Es ist kein BI-Tool und kein Audit-Tool, sondern ein **Compiler von Bedeutung zu
Wirkung**, der bestehende Tools (ALUCA, Meridian, offizielle MS/dbt/Cube-Toolings)
orchestriert statt ersetzt.

### Sechs Zielzustände (Akzeptanzkriterien des Zielbilds)

1. **Durchgängigkeit.** Strategie→Measure ist eine *maschinell geprüfte* Kette
   (Golden-Thread-Gate). Keine Measure ohne strategischen Anker.
2. **Dreifache Stack-Indifferenz.** Datenhaltung, Semantic Layer und Visualisierung sind
   *unabhängig* wählbar; derselbe Core speist alle (§7). Stack-Wechsel ändert die
   Bedeutung nicht.
3. **Determinismus-Schleuse.** LLM-Freiheit im Authoring, byte-stabile Reproduzierbarkeit
   ab der HITL-Freigabe (P2).
4. **Compliance-by-Design.** DSGVO/EU-AI-Act sind Gate-Regeln über *jedem* Stack, nicht
   nachgelagerte Doku.
5. **Wirkungs-Loop.** Action→KPI-Effekt wird gemessen; aus Decision Support wird Decision
   Intelligence (heute größte Lücke G2).
6. **Skalierung der Form.** Neue Branche = Content-Pack, neue Domäne = Regelsatz, neues
   Team = Org-Schicht — alles über demselben Core (G5/G6). Die Form ist das Asset.

### Bewusst NICHT (Scope-Grenzen)
- Kein Self-Service-BI-Tool (Power BI/Tableau bleiben Render-Targets).
- Kein LLM auf dem Liefer-Pfad (nur im Authoring).
- Kein Daten-Plattform-Ersatz (modelliert/prüft Bedeutung, hostet keine Daten).
- Kein Ersatz von ALUCA/Meridian — beide bleiben eigenständig (P5).

### Zielbild-Reifegrade (Wegmarken) ↔ Fahrplan-Mapping
| Stufe | Zustand | realisiert durch (§10) | Heute |
|---|---|---|---|
| **Z0 Neutral Core** | Core ohne DAX-Primat, ALUCA-IR angedockt, **ein Stack grün via bestehendem Meridian-PBIR-Rendering** | W0 (Spike) → W1 (Core) → W2 (`from_aluca`) | Bauziel, Spike offen |
| **Z1 Durchgängig** | Golden-Thread-Gate grün, ≥2 Stacks emittiert (**Sandbox**; Live-Tenant ist G1-Track, separat) | W3 | Bausteine da, Verkettung offen |
| **Z2 Compliant** | COMP\*-Regeln über alle Stacks + messbar | W4, W6 | Content + Vollzug da, Fusion offen |
| **Z3 Closed Loop** | Wirkungsmessung Action→KPI | W7 | echtes Neuland (G2) |
| **Z4 Skaliert** | Team-/Org-Schicht + tool-spez. Domänen-Packs | W8, W9 | offen (G5/G7) |

Z0/Z1 sind **Sandbox-grün** (Artefakt + Gate, ohne Live-Deploy); der Live-Tenant-Pfad
(G1) ist bewusst ein eigener Track (§10 „bewusst NICHT"). Z0–Z2 nutzen vorhandene
Stärken (niedriges Risiko). Z3/Z4 sind der ~15 %-Neuland-Anteil (§1) — heute *skizziert*,
konkrete Designs folgen nach Z2-Stabilität. Branchen-Content (G6) ist Content-, keine
Architektur-Arbeit und steht außerhalb dieser Wegmarken.

---

## 7. Zielarchitektur {#7-zielarchitektur}

Waagrecht der **Phasen-Flow** (LLM-frei → Schleuse → deterministisch), senkrecht der
**vendor-neutrale Core** mit gleichrangigen Adaptern. Kein Stack — auch nicht OSI — ist
privilegiert.

```
 PHASE 1: AUTHORING (LLM-Freiheit)                    ░ probabilistisch ░
┌───────────────────────────────────────────────────────────────────────┐
│ Geschäftsfrage ─▶ LLM: Use-Case-Entwurf, KPI-Vorschlag, Layout-Idee     │
│   (ALUCA-Bedeutung: golden_20, Bracket 3-30-300, Action-Codes)          │
└───────────────────────────────┬───────────────────────────────────────┘
              ╔═════════════════ ▼ ═══════════════════╗
              ║   HITL-FREIGABE = DIE SCHLEUSE          ║  ← ab hier KEIN LLM
              ║   Entwurf → validiertes JSON/Spec        ║
              ╚═════════════════ ▼ ═══════════════════╝
 PHASE 2: COMPILE + TEST (deterministisch)           ▓ reproduzierbar ▓
┌───────────────────────────────────────────────────────────────────────┐
│ VENDOR-NEUTRALER FRAMEWORK-CORE  (das IP)                               │
│  Strategie→KPI→UseCase→Measure→Visual · kennt KEINEN Stack              │
│  Measure trägt expressions{} je Dialekt (core→dialekt direkt)           │
└───────────────────────────────┬───────────────────────────────────────┘
  ┌──────────┬──────────┬────────┼────────┬──────────┬──────────┐
  ▼          ▼          ▼        ▼        ▼          ▼          ▼
 3 ORTHOGONALE STACK-ACHSEN (gleichrangige Adapter)
 Datenhaltung   ‖  Semantic Layer        ‖  Visualisierung
 Snowflake/        PBI-TMDL/Cube/OSI/        Power BI/Looker/
 Databricks/       MetricFlow/LookML/        Tableau/Evidence/
 Fabric/BigQuery   Databricks MetricViews    Rill/Superset
                                │
 QUERLIEGEND über Phase 2 (für JEDEN Adapter):
┌───────────────────────────────────────────────────────────────────────┐
│ AUDIT  pbi⬤ gov◑ arch○ eng○  + COMP*(DSGVO)/GT*(Golden-Thread)          │
│ GATES  Quality-Gate + validate_golden_thread + Official-First je Stack  │
│ STEUERUNG  forge + products.yaml ‖ Health-Scorecard H1–H8 + GADW-Skills │
└───────────────────────────────────────────────────────────────────────┘
                ▼  DELIVERABLES  DOCX/XLSX-Branding + Fassaden + bundles
```

**Drei Architektur-Invarianten:**
1. **Core ist neutral**, nicht „Meridian-PBI-Modell": `expression` wird ein Dialekt unter
   vielen in `expressions{}`, kein Primärfeld.
2. **Die Schleuse trennt die zwei Determinismus-Regime** (P2).
3. **Official-First je Stack-Adapter** (P1); der Core bleibt unberührt.

---

## 8. Domänen Gov/Eng/Arch — tool-spezifisch & dual-modal {#8-domaenen}

Über der BI-Kette liegen drei weitere Domänen, beide Forderungen im Code halb angelegt:

**Dual-modal (standalone ⇄ integriert) — bereits verdrahtet.** Jede Engine
(`gov_engine`, `dataarch_engine`, `dataeng_engine`) hat `sources/ingest.py` (Brownfield,
*ohne* Framework), `sources/greenfield.py` (Spec, *ohne* Framework) und Meridian-JSON
byPath (*mit* Framework). **Standalone ist der Default; das Framework das optionale
Upgrade.** Audit/Regeln laufen identisch, egal woher das Domänenmodell kommt.

**Tool-spezifisch — die echte Lücke (G7).** Heute prüfen die Engines *generisch*
(DAMA/ISO/TOGAF/dbt-Best-Practices); die Grep-Suche nach Unity Catalog/Purview/Horizon/
Collibra/Great-Expectations kam **leer**. Es fehlt die Ausprägung je Domäne × Plattform:

| Domäne | Generisch (heute) | Tool-spezifisch (Ziel, fehlt) |
|---|---|---|
| **Governance** | DAMA/ISO, DSGVO/EU-AI-Act | Unity Catalog Tags/Lineage · MS Purview · Snowflake Horizon · Collibra |
| **Data Engineering** | dbt Layering/Tests/Lineage | dbt-project-evaluator · Databricks DLT · Snowflake Tasks/Streams · Great Expectations/Soda |
| **Data Architecture** | TOGAF/Data-Mesh/Medallion | Fabric Domains/Workspaces · Databricks Catalog-Topologie · Snowflake DB/Schema-Layout |

**Bauprinzip (konsistent zu §5):** je Domäne **ein neutrales kanonisches Modell**
(existiert) + **generische Regeln** (existieren) + **tool-spezifische Regel-/Adapter-Packs
on top** (fehlen). Die Packs sind Official-First (P1, adoptieren Tool-APIs) und dual-modal
(P5, laufen standalone wie integriert).

---

## 9. Optionen & Empfehlung {#9-optionen}

**Option A — Supervisions-Layer über beiden Tools (Empfehlung).** Neutraler Core als
*neues Modul über* Meridians `pbi_engine` (§1), ALUCA liefert Bedeutung/Visual +
Studio-Frontend-Konzept, Meridian liefert Vollzug/Engine als *Konsument* des Cores; beide
bleiben eigenständig (P5).
*Pro:* maximaler kombinierter Umfang ohne Redundanz; nutzt beide reifen Hälften;
GOI-/Baukasten-konform; kein Wegwurf.
*Contra:* Core-Neutralisierung (DAX-Primat lösen) ist echte Arbeit; zwei Repos
koordinieren.

**Option B — alles in einen neuen Monolith gießen.**
*Pro:* eine Codebase.
*Contra:* teuer, riskant, opfert Meridians `check_core_independence`-Reife und
verletzt P5. **Nicht empfohlen.**

**Empfehlung: Option A.** Begründung nach GOI-Kriterien (Korrektheit > Wartbarkeit >
Robustheit): ein neutraler Core + eine Gate-/Audit-/Target-Schicht ist korrekter und
wartbarer als ein Monolith — und respektiert „Tools leben weiter".

---

## 10. ALUCA-Umbau-Fahrplan {#10-fahrplan}

Ziel: ALUCA so umbauen, dass es als **Bedeutungs-/Visual-Lieferant und Studio-Frontend**
in die Superversion passt — ohne seine Eigenständigkeit zu verlieren (P5). Format nach
GOI §9 (DoD je Work-Package: Input · Output · Fehlerfall · Rollback) und PM-Best-Practice
(Now/Next/Later, risiko-zuerst, jedes WP einzeln mergebar).

### Vorbedingung — W0: Mapping-Spike (entscheidet alles)
- **Was:** `UseCase_Bracket.yaml` + `golden_20.yaml` → Meridian-`CanonicalModel` an *einem*
  Use-Case (COM-001) prototypisieren, durch `check_pbir` jagen.
- **DoD:** Input = COM-001-Bracket + Katalog. Output = valides `CanonicalModel`, das
  `check_pbir` mit 0 Errors passiert. Fehlerfall = Feld-Lücke dokumentiert (welches
  Bracket-Feld hat kein CanonicalModel-Pendant). Rollback = keiner (read-only Spike).
- **Gate:** Fällt W0, ist die ganze These widerlegt → stopp & Re-Design. **Risiko-zuerst.**
- **Aufwand:** klein (Tage).

### NOW (Z0 — neutraler Core andocken)
**W1 · Neutrales Measure-Modell (DAX-Primat lösen).**
- Was: in Meridian `Measure.expression` (DAX-primär) zu gleichrangigem `expressions{}`
  je Dialekt aufweiten; ALUCA-Bracket füllt dialektneutral.
- DoD: Input = Bracket-Measure ohne DAX. Output = `expressions{dax,sql}` aus *einer*
  neutralen Quelle, Power-BI- *und* Databricks-Emit grün. Fehlerfall = fehlender Dialekt
  → HITL-Platzhalter (wie `snowflake.py` heute). Rollback = `expression` bleibt
  Fallback-Feld, abwärtskompatibel.
- ⚠️ UNKLAR: ob Value-Driver-Formeln ein Zwischenfeld brauchen (W0 klärt).

**W2 · `from_aluca` Source-Adapter (Python).**
- Was: ALUCAs IR-Compiler (reines Python, §3.5) als Meridian-Source-Adapter; die eine
  PBI-Import-Zeile (`measures_from_ir.py:46`) lösen.
- DoD: Input = Bracket-Verzeichnis. Output = `CanonicalModel`, das durch Audit+Gates läuft.
  Fehlerfall = fehlendes KPI/Action → bestehende graceful-degradation-Warnung. Rollback =
  Adapter ist additiv, ALUCAs Eigen-Generator bleibt vorerst.
- Hängt an W0/W1. Aufwand mittel (5–7 PW inkl. Tests).

**W3 · Golden-Thread als Gate.**
- Was: `registry_builder.py`-Logik → `validate_golden_thread()` in Meridians `gates.py`.
- DoD: Input = `CanonicalModel` + Katalog. Output = PASS/FAIL je Measure-ohne-Anker.
  Fehlerfall = Broken-Ref blockt (wie ALUCA-Drift heute). Rollback = Gate als WARN
  schaltbar, bis stabil.

### NEXT (Z1/Z2 — Durchgängigkeit & Compliance)
**W4 · COMP\*-DSGVO-Regelmodule** in Meridians Regelkatalog, *gespeist aus* ALUCAs
Compliance-Doku als Single Source (keine Doppelpflege).
- DoD: Input = `CanonicalModel` + PII-Klassifikation. Output = COMP\*-Findings; PII-Measure
  ohne RLS → FAIL. Fehlerfall = fehlende PII-Klassifikation → WARN „unklassifiziert", nicht
  stiller Pass. Rollback = Regeln als WARN statt FAIL schaltbar, bis stabil.

**W5 · Studio-Konsolidierung — über die Supervisions-Schicht, NICHT Tool-zu-Tool.**
ALUCAs Studio-Frontend-Konzept wird das UI; es ruft **beide Tools über die
Supervisions-Schicht** auf (Studio → Layer → {ALUCA-IR | Meridian-Engine}), *nicht* ALUCA
→ Meridian → ALUCA. Damit keine zirkuläre Abhängigkeit; jedes Tool bleibt isoliert
lauffähig (P5).
- DoD: Input = Bracket im Studio. Output = Emit + Gate-Report sichtbar, ohne YAML-Handarbeit.
  Fehlerfall = Tool nicht erreichbar → Studio zeigt Degradation, kein Crash. Rollback =
  Studio fällt auf reinen Viewer zurück (heutiger ALUCA-Stand).
- **⚠️ Risiko:** „Studio ruft beide Tools" erfordert einen stabilen Layer-Vertrag zuerst —
  W5 hängt an W2 (`from_aluca`) und einem definierten Aufruf-Interface.

**W6 · Health-Scorecard auf den neutralen Core umhängen** (statt nur ALUCA-Artefakte);
Token-Budget je Pipeline-Schritt als neue H-Metrik (P3). DoD: H1–H8 laufen gegen
`CanonicalModel`.

### LATER (Z3/Z4 — Neuland, Designs noch offen)
**W7 · Wirkungs-Loop (G2):** Action→KPI-Effekt-Tracking; DI über Advisory hinaus. Design offen.
**W8 · Team-/Org-Schicht (G5):** Mehrbenutzer/Rollen/geteilter Katalog über dem
lokal-first-Studio (Nagarro-Pfad). Design offen.
**W9 · Tool-spezifische Domänen-Packs (G7/§8):** Gov/Eng/Arch je Plattform (Unity
Catalog/Purview/dbt-evaluator/…), Official-First + dual-modal. Pro Pack ein DoD bei
Start. Design offen.

*(Branchen-Content-Packs G6 sind bewusst kein W — Content-, keine Architektur-Arbeit.)*

### Was bewusst NICHT im Fahrplan ist (GOI §3 Transparenz)
- **Kein Deprecaten von ALUCAs Engine** — widerspräche P5; ALUCA bleibt standalone
  lauffähig, der Adapter ist additiv. (Frühere Entwürfe forderten das — verworfen.)
- **Kein neuer Monolith** (Option B verworfen).
- **Kein Live-Deploy (G1)** in diesem Fahrplan — eigener Track, hängt an Tenant-Zugang.
- **Branchen-Content (G6)** ausgeklammert — Content-, keine Architektur-Arbeit.

### Reihenfolge-Logik
W0 ist das Risiko-Tor. W1 ist die teuerste Architektur-Wahrheit (neutraler Core) und
blockt W2. W2/W3 liefern den ersten durchgängigen Pfad (Z1). W4–W6 härten zu Z2. W7–W9
sind das Neuland — erst nach grünem Z2 angehen.

---

## 11. QA/SA-Review & Risiken {#11-qa-sa}

Doppelreview-Protokoll (analog Studio-Charter §6/D-031): QA = Faktentreue gegen Code,
SA = Architektur-Kohärenz.

**QA-Befunde (Grounding):** Alle ⬤/◑/○-Marker, Regelzahlen (~50 PBI), Zeilenzahlen
(556/52–72), Test-Zahlen (ALUCA 57 / Meridian ~53), Adapter-Liste (8) und das
DAX-Primat-Zitat (`tmdl_parser.py:39`) sind code-belegt. Verbleibende ⚠️ UNKLAR sauber
markiert (Value-Driver-Mapping W0, OSI-Layout-Deckung P1).

**SA-Befunde (Kohärenz):** Zielbild (§6) ↔ Architektur (§7) ↔ Fahrplan (§10) sind
durchverbunden (Z0↔W1, Z1↔W2/W3, Z2↔W4–W6, Z3/Z4↔W7–W9). P5 (Tools leben weiter) ist
nach Korrektur konsistent — der Fahrplan deprecatet ALUCA nicht mehr.

**Top-Risiken:**
1. **W1 (neutraler Core) ist teurer als geschätzt** — DAX-Primat sitzt evtl. tiefer als
   ein Feld. *Mitigation:* W0-Spike misst das, bevor W1 startet.
2. **Zwei-Repo-Governance-Kollision** (ALUCA-Drift-Gate vs. Meridian-Charter/DECISIONS).
   *Mitigation:* eine SoT — Superversion-Entscheidungen als ADRs in Meridians
   `meridian/studio/DECISIONS.md` (D-Nummer kollisionsfest, Charter-§9-Prozess); ALUCA-Doktrin
   dort als ADRs einpflegen.
3. **Aurora als einziger Akzeptanztest** (G3). *Mitigation:* zweite Referenz-Ontologie
   (Golden-20) als Eval einziehen.

**Nächste Schritte (GOI §2)**
1. W0-Spike an COM-001 (kleinster belastbarer Beweis, entscheidet die These).
2. ADR in `DECISIONS.md`: Superversion-Architektur + neutraler Core + `from_aluca` (additiv).
3. Bei grünem W0: W1 (neutrales Measure-Modell) priorisieren.
4. Zweite Referenz-Ontologie für Evals (Risiko 3) aufsetzen.
