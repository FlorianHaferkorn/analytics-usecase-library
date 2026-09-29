# Superversion — Unabhängiges Zielbild-Review & PM-Konzeptionierung

> **Status:** Review-/Konzeptdokument · 2026-07-02 · unabhängiges inhaltliches Review
> (Senior PM + SA), kein ADR. **Geprüfte Grundlagen:** `SYNERGY_ALUCA_MERIDIAN.md`,
> `PRODUCT_PLAN.md`, `UMSETZUNGSPLAN_SUPERVERSION.md` (inkl. Ledger bis I-8/I-10),
> Code-Stichproben (`tooling/superversion/`, `core/kpi_catalog/kpis/`, legacy
> `tooling/generator/`, `products/fabric/powerbi/dist/`), Freelancing-Marktdocs
> (`Strategie/_INDEX.md`, `ICP_und_Positionierung.md`). Belege als Pfade; Annahmen ⚠️ UNKLAR.
> **Methodik:** GOI §1 (ehrlich, nicht bestätigend) · Befunde nach Severity · Teil B
> ergänzt den bestehenden I-Plan, dupliziert ihn nicht.

---

## 1. Ergebnis zuerst (TL;DR)

**Die Supervisions-These trägt — aber das Produkt rechnet heute nicht.** Architektur
(P1–P5), Determinismus-Schleuse, Golden-Thread-Gate und die Bau-Disziplin (Ledger,
QA/SA, ehrliche ⚠️-Markierungen) sind überdurchschnittlich solide. Der schwerste Befund
liegt woanders: **Der „Compiler von Bedeutung zu Wirkung" compiliert Bedeutung zu
Struktur, nicht zu Berechnung.** Der Superversion-Pfad emittiert Measures ohne einzige
berechenbare Formel (`BLANK()`-HITL-Platzhalter), weil der governte KPI-Katalog keine
Expression trägt und die vorhandene deterministische DAX-Synthese des Legacy-Generators
nie portiert wurde. Alle sechs Premium-Floors F1–F6 können grün sein, während kein
einziger KPI eine Zahl liefert. Zweitschwerster Befund: **Das Zielbild ist vom
existierenden Markt-Fundament entkoppelt** — ICP, Preislogik und Wettbewerbsanalyse
existieren (Freelancing-Repo), werden aber von keinem Superversion-Dokument referenziert;
die Stack-Agnostik optimiert für einen Käufer, den das eigene ICP explizit ausschließt.

**Konsequenz für den Plan:** I-10 ist die richtige Korrektur-Initiative, greift aber zu
kurz. Vor der Premium-Abnahme (I-10.6) müssen (a) die Expression-Lücke geschlossen,
(b) das zweite Doppelsilo (Python-Emit vs. Legacy-PowerShell-Emit) konsolidiert und
(c) ein minimaler Live-Zertifizierungspfad gebaut werden — sonst nimmt I-10.6 ein
strukturell perfektes, semantisch leeres Produkt ab. Teil B schneidet das in 5 Cuts.

---

## 2. TEIL A — Zielbild-Review (Befunde nach Severity)

### Wo ich zustimme (knapp, keine Wiederholung)

- **Supervisions-These + Option A** (Layer statt Monolith, P5): korrekt, im Code
  eingelöst (Vendoring-Seam ADR-0005, `canonical_contract`-Parität, additive Adapter).
- **Determinismus-Schleuse (P2):** konsequent gelebt (byte-stabile Snapshots, kein LLM
  im Emit-Pfad). Das ist das belastbarste Differenzierungsmerkmal des ganzen Vorhabens.
- **W0-Spike risk-first:** richtige Entscheidung, hat sich ausgezahlt (7/7 → 260 Tests).
- **I-10 vor I-9:** richtig. Produktreife vor Skalierung ist die korrekte Reihenfolge;
  der Kassensturz vom 2026-06-25 („gemerged ≠ läuft beim Kunden") war der ehrlichste
  Moment des Plans.
- **Ehrlichkeits-Kultur im Ledger** (Beta-Labels, docs-derived vs. Vendor-Validator,
  Assoziation≠Kausalität im Wirkungs-Loop): echtes Asset, beibehalten.

### CRITICAL

#### A1 · Expression-Lücke: der Compiler erzeugt keine Berechnung („G8")

Der schwerste inhaltliche Befund, von keinem Dokument (SYNERGY G1–G7, PRODUCT_PLAN,
UMSETZUNGSPLAN) adressiert:

- Der governte KPI-Katalog trägt **keine berechenbare Formel** — nur Prosa-Definition +
  Lineage-Pointer (Beleg: `core/kpi_catalog/kpis/sales.net_sales.amount.yaml`: `business.definition`
  Prosa, `technical.lineage: [fact_sales.Net Sales Amount]`, kein Formel-/DAX-Feld).
- `from_aluca` setzt bewusst `expressions={}` („Stack-Adapter ergänzt dax/sql",
  `tooling/superversion/from_aluca.py:133-134`) — aber **kein Stack-Adapter ergänzt je
  etwas**: das TMDL-Target materialisiert nur vorhandene Expressions, sonst
  deterministischen `BLANK()`-HITL-Platzhalter (Ledger I-3.2).
- Ergebnis: Die gesamte E2E-Kette (Bracket → CanonicalModel → TMDL/PBIR/OSI/Databricks)
  liefert für **alle 16 Use Cases** Semantic Models, in denen **keine einzige Measure
  rechnet** — und passiert dabei `check_pbir` 0 Errors, Golden-Thread-Gate grün,
  Determinismus grün.
- Die Ironie: **ALUCAs Legacy-Generator kann es längst.** `tooling/generator/
  generate_tmdl_measures.ps1` synthetisiert deterministisch echtes DAX aus Katalog+IR
  (Beleg: `products/fabric/powerbi/dist/Commercial.SemanticModel/.../_Measures.tmdl`:
  `measure 'Net Sales Amount' = SUM ( fact_sales[Net Sales Amount] )`). Diese Synthese
  wurde nie in den Superversion-Pfad portiert.

**Ursache:** Invariante I1 („kein DAX-Primat im Source") wurde überdehnt. Neutralität
heißt **neutrale governte Formel + Dialekt-Materialisierung je Stack** — nicht
Formel-Verzicht. Der Embryo der Lösung existiert bereits im eigenen Code: die
`refcalc`-Formel-DSL aus I-4.1 (`sum(col)`, `sum(a)/sum(b)`) ist eine vendor-neutrale
Expression-Sprache — sie lebt nur am falschen Ort (Eval-Daten statt KPI-Katalog).

**Konsequenz:** Ohne Fix ist weder service-assisted Revenue (ab I-3/I-4 laut Plan) noch
customer-operable MVP verkaufbar. → Cut S-1 (Teil B), **vor** I-10.6.

#### A2 · Zweites Doppelsilo: Python-Emit vs. Legacy-PowerShell-Emit

Der Plan bekämpft zu Recht E-1 (Studio-TS-Shadow-Pfad, I-10.2/10.3) — hat aber selbst
ein strukturgleiches zweites Silo erzeugt: Für denselben Use Case produzieren
`generate_tmdl_measures.ps1`→`dist/` (mit DAX) und `from_aluca`→TMDL-Target (mit
`BLANK()`) **zwei verschiedene Semantic Models**. Kein I-Task adressiert Konsolidierung
oder Deprecation des Legacy-Pfads. Das verletzt dieselbe P5-/Doppelsilo-Logik, mit der
E-1 begründet wird — nur eine Ebene tiefer. → in Cut S-1 mitlösen (Paritätstest, dann
Legacy deprecaten).

#### A3 · Zielbild ohne Markt-Bindung: Agnostik optimiert am ICP vorbei

Die Marktseite **existiert** — im Freelancing-Repo: ICP „datenbereiter Mittelstand"
(50–500 MA, Budget 2.000–30.000 EUR/Projekt, Retainer ab ~500 EUR/Monat), Preislogik
(`Geschaeftsmodell.md`, `Festpreis_Paketierung_vs_DBI.md`), Wettbewerbs-Synthese
(`Wettbewerbsanalyse_Deep_Dive_2026-06.md`). **Kein Superversion-Dokument referenziert
sie.** Zwei konkrete Kollisionen:

1. Das ICP führt **„Kein Microsoft-Stack" als Negativ-Kriterium** — die Superversion
   macht „dreifache Stack-Indifferenz" zum Nordstern (§6 Zielzustand 2) und investiert
   in OSI/Databricks/Cube. Der Käufer, für den Agnostik kaufentscheidend wäre, ist per
   ICP ausgeschlossen. Agnostik ist real ein **IP-Durability-/Exit-Hedge** (Nagarro-Pfad,
   Plattform-Risiko-Absicherung) — legitim, aber das Zielbild verkauft es als
   Produkteigenschaft. Ehrlich rahmen und Invest deckeln: I-7 ist abgeschlossen,
   **Stack-Breite einfrieren** bis ein zahlender Bedarf existiert.
2. Budget-Realität 2–30k EUR/Projekt vs. Premium-F1–F6 + customer-operable Studio:
   Das ist Produkt-Ökonomie einer 6-stelligen Plattform, verkauft in 5-stelligen
   Projekten. Das kann aufgehen (Wiederverwendung über N Kunden = Marge), aber **nirgends
   steht das Liefermodell**, das die Brücke schlägt (welches Tier bekommt der
   2k-Assessment-Kunde, welches der 30k-Projekt-Kunde, was kostet der Retainer für
   Studio-Betrieb?). → Cut S-5.

### MAJOR

#### A4 · F6/Value-Zertifizierung ist heute ein Oracle-Selbstvergleich — G1 ist falsch geparkt

Das Value-Gate (I-4.2) vergleicht Werte aus „Engine-Lauf/Values-Datei/refcalc-Oracle"
gegen die refcalc-Referenz — ohne Engine ist es advisory, und **das emittierte DAX wird
nie ausgeführt**. Falsches (oder leeres, s. A1) DAX passiert F6. Der Mechanismus ist
sauber gebaut, aber das Orakel prüft sich selbst. Echte Value-Zertifizierung braucht
Ausführung des Artefakts — realistisch: Deploy in einen Sandbox-Fabric-Workspace +
`executeQueries` (das Tooling existiert: `fab api … executeQueries`, `execute_dax.py`,
AGENTS.md). **Damit ist G1 (Live-Deploy) nicht nur eine Time-to-Value-Lücke, sondern die
Voraussetzung für echtes F6** — als „eigener Track, bewusst nicht" ohne Trigger geparkt
ist es falsch klassifiziert. Es braucht keinen generellen Deploy-Track, aber einen
**minimalen Zertifizierungspfad** (ein Workspace, zwei UCs). → Cut S-4.

#### A5 · Priorisierungs-Disziplin gebrochen — und E-1 ist nicht DER kritische Pfad

Der Plan sagt „LATER erst nach grünem Z2" — trotzdem wurde I-8 (Wirkungs-Loop, explizit
Neuland/LATER) komplett gebaut (I-8.1–8.3 ✅ am 2026-06-25), **am selben Tag**, an dem
der Kassensturz 8 rote Windows-Tests und den Studio-Shadow-Pfad fand. Das ist
Feature-Attraktion vor Produktreife; I-10 korrigiert das zu Recht. Zur Frage „ist E-1
der kritische Pfad?": **Für das customer-operable-Versprechen ja, für Revenue nein.**
Service-assisted Delivery (laut Plan revenue-fähig ab I-3/I-4) braucht kein Studio —
sie braucht rechnende Measures (A1) und ein zertifiziertes Ergebnis (A4). Der kritische
Pfad zum ersten Euro ist **S-1 → S-4**, nicht E-1. E-1 bleibt P0 fürs MVP-Versprechen,
läuft aber parallel, nicht davor.

#### A6 · Doktrin-Drift: SYNERGY widerspricht dem gelebten Plan bei der Core-Heimat

SYNERGY §1: Core entsteht „als eigenes Modul **im Meridian-Repo**, oberhalb von
`pbi_engine`". Gelebt (ADR-0005, UMSETZUNGSPLAN-Kopf): **ALUCA ist Heimat**,
Meridian-Core wird vendored. Die Entscheidung ist gefallen und gut begründet — aber
SYNERGY wurde nie nachgezogen. Jede künftige Session, die SYNERGY als „das Zielbild"
liest (wie diese Review-Aufgabe es vorgibt), erbt die falsche Architektur-Aussage.
Gleiches Muster klein: SYNERGY §11 empfiehlt Superversion-ADRs in Meridians
`DECISIONS.md`; real leben sie in `docs/architecture/adr/`. → Korrektur-Notiz in
SYNERGY (Teil von Cut S-5, 15 Minuten, kein eigener Cut).

#### A7 · Day-2-Betrieb beim Kunden: von keinem Dokument adressiert

Blinder Fleck über alle drei Dokumente: Was passiert **nach** der Übergabe?

- **Round-Trip-Problem:** Kunde editiert den generierten Report in PBI Desktop →
  nächster Generator-Lauf überschreibt? Es gibt keine Regenerier-Politik (ownership je
  Datei, 3-way-merge, „generated — do not edit"-Zonen).
- **Update-Kanal:** Vendored-Meridian-Pin steigt, Bracket-Schema migriert, Studio beim
  Kunden veraltet — es gibt Pin-Sensoren für die Eigen-Entwicklung (I-2.4), aber keinen
  definierten Upgrade-Pfad für ausgelieferte Artefakte/Installationen.
- **Lizenz:** Meridian-Code vendored in ALUCA, ALUCA(-Studio) läuft beim Kunden —
  `IP_und_Lizenz_Term_Sheet.md` existiert im Freelancing-Repo, ist aber mit dem
  Vendoring-Konstrukt nie abgeglichen. ⚠️ UNKLAR: ob das Term Sheet Kunden-seitiges
  Deployment des vendored Codes deckt.

#### A8 · Onboarding/Datenanbindung: „customer-operable" endet vor der härtesten Meile

Der generierte Output bindet an governte Lineage-Namen (`fact_sales[Net Sales Amount]`).
Beim realen Kunden heißt die Tabelle anders — **wer mappt Kundendaten auf das erwartete
Star-Schema?** Das precore-Panel (I-6.2) zeigt Engine-Befunde, aber es gibt keinen
Source-Mapping-Flow, kein Onboarding-Runbook, keine Ziel-Onboarding-Zeit. Meridians
Brownfield-Ingest deckt Bestands-PBI ab, nicht das Greenfield-Daten-Mapping. Für das ICP
(„kein eigenes Data-Team") ist genau das die Kaufhürde. Mindestens: als expliziten
service-assisted Schritt ins Liefermodell schreiben (S-5), ehrlich statt implizit.

### MINOR

- **A9 · DSGVO als Verkaufsargument halb operationalisiert:** Das COMP-Gate (I-4.4,
  XD-002-Test) ist der schwerste Teil und existiert. Was fehlt, ist billig und
  differenzierend: ein **kundengerichtetes Compliance-Deliverable aus dem Gate**
  (DPIA-/Art.-30-Anhang je Use Case, generiert aus `data_protection`-Block + ALUCAs
  `compliance/`-Stack via Documenter). Kein Wettbewerber im Mittelstands-Segment liefert
  das automatisch mit. → in Cut S-3 andocken.
- **A10 · F5 MD-only:** korrekt geledgert (I-10.4 offen), kein neuer Befund.
- **A11 · Wirkungs-Loop als Story, nicht als Beleg:** ehrlich gebaut (UNCOMPUTED,
  kein Auto-Mutate) — aber ohne Live-Daten (A4) bleibt er Demo-Ware. In Pitches als
  „Roadmap", nicht als Feature führen, bis eine echte Attribution existiert.
- **A12 · Aufwands-Schätzungen veraltet positiv:** SYNERGY schätzte `from_aluca` auf
  5–7 PW; real war der Kern in Tagen gebaut. Umgekehrt fehlt jede Schätzung für S-1/S-4.
  Kein Fix nötig, nur: den alten Zahlen nicht mehr trauen.

---

## 3. TEIL B — PM-Konzept + Cut-Plan

### 3.1 PM-Konzept

**Problem (Kunde):** Mittelstand hat Berichte, aber keine Entscheidungen; BI-Projekte
scheitern an fehlender Struktur/Governance, nicht an Tools; Agentur-Reports sind
Einzelstücke ohne governte Bedeutung, nicht wartbar, nicht DSGVO-dokumentiert.

**Zielkunde/ICP:** **referenzieren, nicht neu definieren** (Golden-Thread-Prinzip auf
die eigene Strategie angewandt): `Freelancing/Strategie/ICP_und_Positionierung.md` —
datenbereiter DE-Mittelstand, 50–500 MA, MS-Stack vorhanden/geplant, kein Data-Team,
2–30k EUR/Projekt + Retainer.

**Nutzenversprechen (kundengerichtet, nicht architektur-gerichtet):**
> Governte KPI-Bedeutung wird in Tagen zu einem auditierten, DSGVO-dokumentierten,
> reproduzierbaren Power-BI-Liefergegenstand — mit maschinell geprüfter Kette von der
> Strategie bis zur Zahl, beim Kunden wartbar.

Stack-Agnostik ist **intern** (IP-Hedge, Exit-Option), kein Pitch-Element für dieses ICP.

**Scope-Cut MVP:** 3–5 universelle UCs · Power BI/Fabric only · service-assisted
Delivery zuerst, customer-operable Studio als zweite Stufe · DPIA-Anhang als
Differenzierer. **Später:** weitere Stacks, Industry-Packs, Team/Org (I-9), SaaS.

**Messbare Erfolgskriterien (Produkt-/Markt-Signale, nicht nur Tests):**
1. **M1:** 1 zahlendes Pilot-Engagement, dessen Deliverables aus dem Superversion-Pfad
   kommen (nicht aus Legacy/Handarbeit).
2. **M2:** Time-to-first-certified-report beim Pilot ≤ 5 Arbeitstage ab Datenzugang
   (Messlatte fürs Onboarding, A8). ⚠️ UNKLAR: Zielwert kalibrieren am Pilot.
3. **M3:** BLANK()-Quote der emittierten Measures = 0 für die MVP-UCs (A1-Metrik).
4. **M4:** ≥1 Angebots-Pitch, in dem der generierte DPIA-Anhang nachweislich
   Differenzierungs-Argument war (A9).
5. **M5:** 1 Kunde (oder Proxy-Tester) schließt den Studio-Flow ohne Builder ab
   (bestehende I-6-Messgröße, unverändert).

**Nicht-Ziele (MVP):** 3.+ Stack-Targets · Multi-Tenant/RBAC · Live-SaaS · Industry-
Packs · genereller Live-Deploy-Track (nur der minimale Zertifizierungspfad S-4).

### 3.2 Cut-Plan

Jeder Cut = eine kohärente, lieferbare Scheibe; 1–3 Claude-Code-Sessions; DoD im
GOI-§9-Format; **QA/SA-Doppelreview-Gate vor Cut-Abschluss** (QA = Faktentreue/Tests
echt grün, Opus; SA = Architektur-Kohärenz + P1–P5/I1–I5, Opus) — wie UMSETZUNGSPLAN
§0.4, hier für jeden Cut verbindlich. Bestehende I-Tasks werden referenziert, nicht
neu erfunden.

#### Cut S-1 · Rechenfähigkeit: governte neutrale Expression → deterministisches DAX (NEU, P0)

Schließt A1 + A2. Kein bestehender I-Task deckt das.

- **Ziel:** Jede governte KPI trägt eine neutrale, maschinenlesbare Formel; das
  TMDL-Target materialisiert daraus echtes DAX; Superversion-Emit erreicht Parität mit
  dem Legacy-`dist/`-Output; Legacy-Generator wird deprecated (E-2 geschlossen).
- **Scope-in:** (a) Expression-Grammatik-Entscheid als ADR (Kandidat: `refcalc`-DSL aus
  `eval/refcalc.py` in den Katalog heben; Feld `technical.calculation` im KPI-Schema);
  (b) Katalog-Befüllung für die MVP-UC-KPIs (aus `calc_type` + `lineage` ableitbar, wie
  der Legacy-Generator beweist); (c) deterministische DSL→DAX-Synthese im TMDL-Target
  (`expressions{dax}` wird dort gefüllt — I1 bleibt gewahrt: Source bleibt neutral,
  Formel ist dialektfrei); (d) Paritätstest Superversion-TMDL ≙ `dist/`-Legacy für
  COM-001 (AST-/normalisierter Vergleich, nicht zwingend byte-gleich); (e) Legacy-PS-
  Generator hinter Deprecation-Flag.
- **Scope-out:** komplexe KPIs jenseits sum/ratio/delta (bleiben HITL, aber **gezählt**);
  DSL→SQL-Transpile für andere Stacks (folgt bei Bedarf, Grammatik ist darauf ausgelegt).
- **DoD:** Input = KPI-Katalog + Brackets der 5 MVP-UCs · Output = KPI-Schema +
  Katalog mit `calculation`-Feld; TMDL-Emit ohne `BLANK()` für alle katalog-berechenbaren
  Measures; `hitl_gaps()`-Zähler für den Rest; ADR (nächste freie Nr.) Accepted ·
  Fehlerfall = KPI ohne ableitbare Formel → expliziter HITL-Eintrag im Ledger, nie
  stilles BLANK() · Rollback = `calculation` optional, alte Emits unverändert
  reproduzierbar (Snapshots regenerierbar) · **Prüfung (mechanisch):** pytest inkl.
  Paritätstest + BLANK()-Quote-Assertion = 0 für MVP-KPIs; `check_index --strict` Exit 0;
  **(agent):** QA/SA-Gate.
- **Modell:** ADR + Grammatik-Entscheid **Opus**; Synthese/Tests/Katalog-Befüllung
  **Sonnet**; Katalog-Massendaten **Haiku**.

#### Cut S-2 · Windows-Ship + Studio-Naht (= bestehendes I-10.1 + I-10.2 + I-10.3, P0)

Keine Neuerfindung — Referenz auf den bestehenden Plan, unverändert übernehmen.

- **Ziel/Scope/DoD:** exakt wie I-10.1 (bash-Portabilität, 0 failed auf Windows),
  I-10.2 (E-1-ADR) und I-10.3 (Studio dockt an Python-Core, TS-Shadow deprecated).
- **Einzige Schärfung:** I-10.3-DoD ergänzen um „Studio-Generate nutzt den S-1-Pfad"
  (sonst dockt das Studio an einen Core an, der BLANK() liefert).
- **Modell:** I-10.2 **Opus** (wie geplant), Rest **Sonnet**. Läuft ∥ zu S-1.

#### Cut S-3 · Ehrliche Abnahme + Deliverable (= I-10.4 + erweitertes I-10.6 + A9, P1)

- **Ziel:** DOCX-Deliverable steht; Premium-Abnahme misst auch Rechenfähigkeit;
  DSGVO-Anhang wird Teil des Deliverables.
- **Scope-in:** I-10.4 unverändert (DOCX via `new_document()`-Muster). I-10.6 mit
  **erweitertem DoD**: zusätzlich zu F1–F6 ein „**F0: Rechenfähigkeit**" — Abnahmebericht
  weist je UC die BLANK()-/HITL-Quote aus; MVP-UCs müssen 0 zeigen (Beleg aus S-1).
  Neu (A9): DPIA-/Compliance-Anhang je UC aus COMP-Gate + `data_protection` +
  `compliance/`-Stack im Documenter (MD reicht v1, DOCX via I-10.4-Pfad).
- **Scope-out:** I-10.5 (Wirkungs-Loop-Verträge O-1..O-4) bleibt eigenständig wie geplant.
- **DoD:** Input = System nach S-1/S-2 · Output = `premium-acceptance-F0-F6.md` mit
  Beleg/Kommando je Floor + DPIA-Anhang für ≥1 UC · Fehlerfall = roter Floor → offen
  ausgewiesen, blockt Ship, wird nicht schöngefärbt · Rollback = Abnahme als Findings-
  Liste ohne Ship-Freigabe · **Prüfung:** (agent QA/SA) je Floor grün-belegt oder
  geledgert; (mechanisch) DOCX-Snapshot + Doc-Gen-Tests.
- **Modell:** I-10.6-Abnahme **Opus**; DOCX/DPIA-Bau **Sonnet**.

#### Cut S-4 · Live-Zertifizierungspfad (G1 minimal, als F6-Enabler) (NEU, P1)

Schließt A4. Stuft G1 um: von „bewusst nicht" zu „minimal, zweckgebunden".

- **Ziel:** Das emittierte Artefakt wird einmal wirklich ausgeführt und seine Werte
  gegen die refcalc-Erwartung geprüft — F6 wird vom Selbstvergleich zum echten Gate.
- **Scope-in:** Referenzdaten (I-4.1-YAMLs) in einen Sandbox-Fabric-Workspace laden;
  Semantic-Model-Import (`fab import`) + `executeQueries` je erwartetem KPI
  (`execute_dax.py`-Muster); Vergleich gegen `expected/`-Werte; als **opt-in Gate**
  (`--live`), CI-frei (Tenant-gebunden), Ergebnis-Protokoll ins Abnahme-Dossier (S-3).
  2 UCs genügen (COM-001, SCM-002 — Referenzdaten existieren).
- **Scope-out:** Deploy-Automation in Kunden-Tenants, Gateways, Refresh-Orchestrierung,
  CI-Verdrahtung — bleibt der ausgeklammerte G1-Track.
- **DoD:** Input = S-1-Emit + `eval/data/` + Sandbox-Workspace · Output =
  `live_cert.py`-Lauf: Import + Query + Soll/Ist-Report; absichtlich falsches DAX wird
  rot · Fehlerfall = kein Tenant-Zugang → Gate SKIP mit Grund (Muster I-3.5
  `--require-cli`), nie Fake-Green · Rollback = Gate bleibt opt-in/advisory ·
  **Prüfung (mechanisch):** Lauf-Protokoll Exit 0 + Perturbations-Test rot; (agent) QA.
- **Modell:** kleiner Discovery-Anteil (Tenant/Auth-Weg) **Opus** oder direkt Owner-
  Entscheid; Bau **Sonnet**. ⚠️ UNKLAR: Sandbox-Tenant/Capacity verfügbar? (F64-Trial
  oder PPU reicht für Import+Query.)

#### Cut S-5 · Markt-Bindung + Doktrin-Hygiene (NEU, P1, kein Code)

Schließt A3, A6, A7, A8. Eine Opus-Session, reines Konzept-/Doku-Deliverable.

- **Ziel:** Das technische Zielbild wird an das existierende Markt-Fundament gebunden;
  Day-2 und Onboarding bekommen ein beschlossenes Liefermodell.
- **Scope-in:** Ein Dokument `PRODUCT_MARKET_BRIDGE.md` (Repo-Root): (a) ICP/Preise/
  Wettbewerb per **Referenz** auf die Freelancing-Strategie-Docs (nicht duplizieren —
  Golden Thread); (b) Liefermodell-Tiers (service-assisted Projekt vs. Retainer vs.
  customer-operable Studio) mit Preis-Logik-Anker; (c) **Day-2-Politik**: Regenerier-/
  Ownership-Regeln je Artefakt-Typ (generated-zone vs. customer-zone), Update-Kanal
  (Pin-Bump-Prozess Richtung Kunde), Lizenz-Abgleich mit `IP_und_Lizenz_Term_Sheet.md`
  (⚠️ UNKLAR: deckt es kundenseitiges Vendored-Deployment?); (d) Onboarding-Runbook-
  Skelett mit Ziel-Zeit (M2) inkl. des ehrlichen service-assisted Daten-Mapping-Schritts
  (A8); (e) **SYNERGY-Korrekturnotiz** (A6): Core-Heimat = ALUCA per ADR-0005, ADR-Ort =
  `docs/architecture/adr/`. (f) Stack-Breite-Freeze festschreiben (I-7 = abgeschlossen,
  weitere Targets nur mit zahlendem Bedarf).
- **DoD:** Input = Freelancing-Strategie-Docs + dieses Review · Output = Bridge-Doc +
  SYNERGY-Notiz, beide im Drift-Gate registriert-oder-root · Fehlerfall = Widerspruch
  zwischen Markt-Doc und Zielbild → als Entscheid an Owner eskalieren, nicht glätten ·
  Rollback = Doc bleibt „proposed" · **Prüfung:** `check_index --strict` Exit 0 +
  (agent) SA-Review auf Kohärenz mit P1–P5.
- **Modell:** **Opus** (Trade-offs Liefermodell/Preis-Anker).

#### Reihenfolge & Abweichung vom bestehenden Plan

```
S-1 (Rechenfähigkeit) ─┬─▶ S-3 (Abnahme+Deliverable) ─▶ Ship-Gate
S-2 (= I-10.1/2/3)  ───┤
S-4 (Live-Cert)  ──────┘        S-5 (Markt-Bindung) ∥ zu allem
danach unverändert: I-10.5 · dann I-9 (LATER)
```

- **Abweichung 1:** S-1 ist neu und P0 — der bestehende Plan kennt die Expression-Lücke
  nicht; I-10.6 würde ohne S-1 ein leeres Produkt abnehmen.
- **Abweichung 2:** G1 wird minimal aktiviert (S-4) statt komplett geparkt — als
  F6-Enabler, nicht als Deploy-Track.
- **Abweichung 3:** E-1 bleibt P0, ist aber nicht mehr der alleinige kritische Pfad —
  der Revenue-Pfad läuft über S-1→S-4 (service-assisted), unabhängig vom Studio.
- **Abweichung 4:** Markt-Bindung (S-5) wird erstklassiger Bestandteil des Zielbilds
  statt implizit „im anderen Repo".

---

## 4. Was bewusst NICHT (GOI §3)

- **Kein neuer Gesamt-Plan** — I-1..I-10 bleiben SoT für den Bau; die Cuts ergänzen
  (S-1/S-4/S-5) bzw. referenzieren (S-2/S-3) sie.
- **Kein Re-Review der Code-Mechanik** (Tests, Vendoring-Seam, Adapter-Verträge) — Auftrag
  war Inhalt/Konzept; die Ledger-Belege wurden stichprobenhaft verifiziert, nicht auditiert.
- **Keine Preis-Festlegung** — S-5 verankert die Logik, die Zahlen setzt der Owner.
- **Kein DSL→SQL-Transpiler in S-1** — Grammatik wird transpile-fähig entworfen, gebaut
  wird nur DAX (MVP-Stack); andere Dialekte bei zahlendem Bedarf.
- **Keine Umstufung von I-8/I-9** — Wirkungs-Loop bleibt gebaut-aber-Demo (A11), Team/Org
  bleibt LATER.

## 5. Offene Punkte / UNKLAR

| # | Punkt | Annahme | Klärung durch |
|---|---|---|---|
| U1 | Deckt `generate_tmdl_measures.ps1` alle 16 UCs mit echtem DAX? (nur COM-001/Commercial geprüft) | ja für die dist-Domänen | S-1-Paritätstest |
| U2 | Sandbox-Fabric-Tenant/Capacity für S-4 verfügbar (Kosten/Zugang)? | Trial/PPU reicht | Owner-Entscheid vor S-4 |
| U3 | Deckt das IP-/Lizenz-Term-Sheet kundenseitiges Deployment des vendored Meridian-Codes? | ungeprüft | S-5 (c) |
| U4 | Existiert ein Pilot-Kandidat für M1/M2? | offen | Owner |
| U5 | Zielwert M2 (≤5 Tage Time-to-certified-report) realistisch? | Platzhalter | Kalibrierung am Pilot |
| U6 | `refcalc`-DSL ausdrucksstark genug für die 20 Golden-KPIs (PVM-Effekte, RFM-Scores)? | für sum/ratio/delta ja; Rest HITL | S-1-ADR |
