# ADR 0016 — Manufacturing Industry Pack (`OPS-IND-M001`): Differentiation-Angle Discovery

- **Status:** Proposed. Wie bei ADR-0009/0014: ein Discovery-ADR mit inhaltlicher Tragweite
  wird nie eigenmächtig auf Accepted gesetzt — das braucht Maintainer-Ratifikation, nachzutragen
  sobald sie stattfindet.
- **Date:** 2026-07-15
- **Scope:** Nur die **Frage, ob ein echter, nicht-duplizierender Manufacturing-Differenzierungswinkel
  existiert** — und, falls ja, welcher, mit welchem Beleg. **Keine KPI-/Action-Code-Autorenschaft,
  kein Code.** Das bleibt bewusst ausgeklammert, bis (a) die noch offene Recherche-Lücke geschlossen
  ist und (b) ein echter Zielkunde/Zielsegment feststeht (s. Open Points).
- **Supersedes:** —
- **Related:** [`0004…`](0004-industry-variant-use-case-tier-taxonomy.md) (EXT/IND-Taxonomie,
  Sektor-Register — `M`=Manufacturing bereits reserviert für `OPS-IND-M001`),
  [`../../../internal/project_mgmt/KNOWN_GAPS.md`](../../../internal/project_mgmt/KNOWN_GAPS.md) §7
  (die sechs Industry/Extension-UCs, `DEC-SPINE-OPS-OEE` **nicht** salvaged — fehlender Action-Code),
  [`../../../PRODUCT_PLAN.md`](../../plans/PRODUCT_PLAN.md) (Meridian-Skizze-Korrektur),
  [`../../../UMSETZUNGSPLAN_SUPERVERSION.md`](../../plans/UMSETZUNGSPLAN_SUPERVERSION.md) (I-9.3,
  vorherige Ledger-Zeile „Prämisse widerlegt")

---

## Context

Die vorherige I-9.3-Bearbeitung (Ledger, 2026-07-10) stellte fest: die im `docs/plans/PRODUCT_PLAN.md`
behauptete „Meridian hat eine Skizze"-Prämisse war unbelegt (repo-weite Suche: 0 Treffer) und
wurde korrigiert. Tieferer Befund damals: der Ziel-UC `OPS-IND-M001` „OEE" ist inhaltlich bereits
weitgehend durch generischen Operations-Content abgedeckt — `OPS-001` (OEE/Availability/
Performance/Quality, Action-Codes `O-O1.1/.3/.4`), `OPS-002` (Asset Performance: MTBF/MTTR/
PM-Compliance/unplanned downtime), `OPS-003` (Quality & Yield: First-Pass-Yield/Scrap%/Rework%/
COPQ/Reklamationsrate) decken zusammen das komplette Six-Big-Losses/TPM-Rahmenwerk generisch ab.
Ohne belegten, nicht-duplizierenden Branchen-Winkel wäre jede `OPS-IND-M001`-Autorenschaft entweder
eine Re-Derivation von `OPS-001` oder erfundener Content ohne Fachbasis — DoD-Fehlerfall-Klausel
„Kundenkontext nötig → als bewusst-offen markieren, nicht raten" griff, I-9.3 blieb offen.

**Diese Session:** auf Nutzeranfrage ein `deep-research`-Workflow-Durchlauf (6 Such-Winkel, 24
Quellen, 3-Voten-Adversarial-Verifikation) gegen genau diese Frage: gibt es einen real,
standard-gestützten Differenzierungswinkel, der `OPS-001/002/003` NICHT dupliziert? Ergebnis:
**ja, zwei** (Festlegung 1/2 unten) — beide strukturell/taxonomisch belegt, keiner davon liefert
fertige KPI-Namen zum Übernehmen. Ein zweiter, vertiefender Durchlauf (auf Nutzeranfrage „beide
Blickwinkel vertiefen") sollte die exakten KPI-Kataloge und die offene Batch-vs-diskret-Abgrenzung
klären — **scheiterte vollständig** (zwei unabhängige Versuche, 0 von insgesamt 47 Quellen
lieferten verwertbaren Content) an einem persistenten Fetch-/Proxy-Problem in dieser Sandbox,
nicht an fehlender Evidenz der zugrunde liegenden Standards. Diese Umgebungsgrenze wird hier
ehrlich als offen geführt (Präzedenz: F1/F6-Teil2 in `premium-acceptance-F0-F6.md`), nicht
stillschweigend übergangen.

## Decision

**Zwei evidenzbasierte Kandidaten-Differenzierungswinkel für `OPS-IND-M001` werden als Proposed
festgehalten — beide sind Struktur-/Taxonomie-Gerüst, kein fertiger KPI-Katalog, und keiner
schließt den anderen aus (könnten zu zwei getrennten Sub-Scopes werden, s. Open Points O-4).**

1. **Festlegung 1 — ISO-22400-Granularität (Work-Unit/Production-Order statt Plant-Level).**
   Peer-reviewed (IFAC-PapersOnLine 2018, Varisco/Johnsson/Mejvik/Schiraldi/Zhu, INCOM Bergamo):
   ISO 22400s KPIs sind nur auf hoher, generischer Abstraktionsebene definiert; das Paper schlägt
   ein Drei-Scope-Klassifikationsmodell vor — **Work Order / Work Unit / Production Order** —, das
   dieselbe KPI-Definition auf feinerer Granularität neu spezifiziert. `OPS-001`s Six-Big-Losses/OEE
   ist implizit Plant-/Linien-Ebene; ein Manufacturing-Pack, der dieselben KPI-Konzepte auf
   **Maschinen-Instanz-Ebene (Work Unit)** oder **Batch/Los-Ebene (Production Order)** anwendet, ist
   ein echter, standard-gestützter Winkel — liefert aber keine KPI-Namen, nur eine
   Skalierungsmethode; neue KPIs müssten auf diesem Gerüst frisch **authored** werden.
2. **Festlegung 2 — ISA-88-Batch-Genealogie (physisches/prozedurales/Rezept-Modell).**
   ANSI/ISA-88.00.01 ("Batch Control") definiert ein physisches Modell (Enterprise→Site→Area→
   Process Cell→Unit→Equipment/Control Module), ein Prozedur-Modell (Procedure→Unit Procedure→
   Operation→Phase) und ein Rezept-Modell (General/Site/Master/Control Recipe) — eine Taxonomie,
   die per Grep nachweislich komplett in `core/` fehlt (0 Treffer für die ISA-88-Begriffe) und in
   `OPS-001/002` nicht vorkommt. ISA-88 selbst ist ein Kontrollsystem-/Datenmodellierungs-Standard,
   **keine KPI-Sammlung** (die eigenen dokumentierten Adoptions-Vorteile sind Implementierungs-
   kosteneinsparungen — 30 % Erstprojekt, 80 % Folgeprojekte —, keine Metriken). Könnte einen
   Batch/Los-Genealogie-Winkel für Prozess-/Batch-Fertiger strukturieren — aber auch hier: kein
   KPI ist direkt aus dem Standard übernehmbar, jeder müsste frisch auf dieser Struktur authored
   werden.

**Bewusst NICHT festgelegt:** welcher der beiden Winkel (oder beide) tatsächlich zu
`OPS-IND-M001` wird, welche konkreten KPI-Namen/Formeln entstehen, und ob das Ziel diskrete oder
Batch-/Prozessfertigung ist — alles hängt an den Open Points unten.

## Open Points

- **O-1 Exakter ISO-22400-2-KPI-Katalog (inkl. Formeln) — blockiert durch Sandbox-Fetch-Ausfall.**
  Zwei unabhängige `deep-research`-Vertiefungsversuche (10 + 7 Quellen) scheiterten vollständig
  (0 extrahierte Claims) — sowohl offizielle Standard-Seiten (iso.org, ANSI-Preview) als auch
  offen zugängliche Sekundärliteratur (NIST-PDF, LTH-Whitepaper, DiVA-Thesis, ScitePress/SciSpace-
  Paper) lieferten HTTP-403 oder leeren Content, inklusive eigener manueller `WebFetch`-Versuche.
  Ein unverifizierter Suchschnipsel (nicht durch Volltext-Lesen bestätigt) nennt 34 KPIs
  (u. a. Worker Efficiency, Allocation Ratio, Throughput Rate, Allocation/Utilization Efficiency,
  klassische Availability×Effectiveness×Quality-OEE) — **als unverifiziert markiert, nicht als
  Fakt zu behandeln.** Nächster Schritt: erneuter Versuch, sobald die Fetch-Umgebung wieder
  funktioniert, oder Zugriff auf die reale ISO-22400-2-Norm (kostenpflichtig, ~CHF 200) durch
  einen Menschen.
- **O-2 ISA-88 Batch-vs-diskret-Abgrenzung — ebenfalls blockiert.** Der erste Recherche-Durchlauf
  verwarf explizit (0-3 Stimmen) die Annahme, ISA-88 sei sauber „nur Batch, nicht diskret"
  abzugrenzen — die reale Grenze bleibt ungeklärt, da der Vertiefungsversuch (19 Quellen) ebenfalls
  0 Claims lieferte. Ohne diese Klärung ist unklar, ob Festlegung 2 exklusiv Batch-/Prozessfertiger
  anspricht oder breiter.
- **O-3 SEMI E10 (Equipment-RAM/Utilization) und APQC PCF — keine Recherche-Traktion.** Beide in
  der Ausgangsfrage genannt, aber in keinem der drei Durchläufe (0 überlebende Claims) belegt oder
  widerlegt — reine Abdeckungslücke, kein Gegenbeweis. Bräuchten einen eigenen, fokussierten
  Recherche-Durchlauf, sobald Fetch wieder funktioniert.
- **O-4 Zielkunde/Zielsegment — bewusst offen, nicht ratbar.** Auf explizite Nachfrage bestätigt
  (2026-07-15): **kein Zielkunde für Manufacturing vorhanden.** Ob ein erster Pack auf diskrete
  Fertigung (Festlegung 1, Work-Unit-Granularität) oder Batch-/Prozessfertigung (Festlegung 2,
  ISA-88-Genealogie) zielen soll — oder beide als getrennte Sub-Packs —, sowie ob reale
  MES-/IoT-Systeme die jeweils nötige Granularität überhaupt liefern können, ist eine
  Kundenkontext-Frage. DoD-Fehlerfall-Klausel („Kundenkontext nötig → als bewusst-offen markieren,
  nicht raten") — dieselbe Behandlung wie ADR-0009s O-1/O-2 und ADR-0014s O-2/O-5.
- **O-5 Fehlender Action-Code blockiert die Spine-Salvage unabhängig von O-1..O-4.**
  `DEC-SPINE-OPS-OEE` wurde beim §7-Salvage **nicht** übernommen, weil sie den nicht-existenten
  Action-Code `O-P2.1` referenziert (`KNOWN_GAPS.md` §7). Selbst nach Klärung von O-1..O-4 muss vor
  jeder `OPS-IND-M001`-Autorenschaft entweder `O-P2.1` neu authored oder die Spine auf einen
  existierenden Action-Code umgemappt werden.

## Consequences

**Positive**
- I-9.3 ist nicht mehr bei „keine belegbare Differenzierung gefunden" hängen geblieben — zwei
  reale, zitierfähige Winkel liegen vor, für den Moment, in dem O-4 (Zielkunde) geklärt ist.
- Die Sandbox-Fetch-Grenze (O-1/O-2/O-3) ist präzise dokumentiert statt stillschweigend als
  „nichts gefunden" fehlinterpretiert zu werden — Präzedenz F1/F6-Teil2 fortgeführt.
- Kein Code, kein Risiko: reine Recherche-/Entscheidungsdokumentation, nichts an Autorenschaft
  vorweggenommen.

**Negative / Kosten**
- Beide Winkel liefern Struktur, keine fertigen KPIs — der eigentliche Autorenschafts-Aufwand
  (KPI-Definitionen, Action-Codes, Bracket, Factsheet, `DecisionSpine_UseCase_Map.yaml`-Eintrag)
  bleibt vollständig offen und ist an O-4 (Zielkunde) gebunden.
- O-1/O-2/O-3 bleiben so lange unklar, bis entweder die Sandbox-Fetch-Umgebung sich erholt oder
  ein Mensch die Primärquellen (kostenpflichtige Normen) direkt einsieht.

## Alternatives considered

- **Sofort mit Festlegung 1 ODER 2 authoren, ohne O-1..O-4 zu klären.** Verworfen: würde entweder
  erfundene KPI-Formeln (ohne verifizierten ISO-22400-Katalog) oder eine falsche Batch-vs-diskret-
  Annahme (ohne geklärtes O-2) in den governten Core schreiben — genau das Muster, das die
  DoD-Fehlerfall-Klausel verhindern soll.
- **I-9.3 als endgültig „nicht machbar" schließen.** Verworfen: die Recherche zeigt reale,
  zitierfähige Differenzierung existiert — das Problem ist eine temporäre Sandbox-Fetch-Grenze
  und ein fehlender Zielkunde, kein grundsätzliches Fehlen von Substanz.
- **Auf den generischen `OPS-001`-Content ohne jede Differenzierung authoren.** Verworfen: exakt
  das Re-Derivations-Problem, das die ursprüngliche I-9.3-Analyse identifiziert hat.

## References

- Internal: [`../../../internal/project_mgmt/KNOWN_GAPS.md`](../../../internal/project_mgmt/KNOWN_GAPS.md) §7,
  [`0004-industry-variant-use-case-tier-taxonomy.md`](0004-industry-variant-use-case-tier-taxonomy.md),
  [`../../../PRODUCT_PLAN.md`](../../plans/PRODUCT_PLAN.md)
- External (Festlegung 1): Varisco, Johnsson, Mejvik, Schiraldi, Zhu — "KPIs for Manufacturing
  Operations Management: driving the ISO22400 standard towards practical applicability", IFAC-
  PapersOnLine, INCOM 2018 (Bergamo) —
  [ResearchGate](https://www.researchgate.net/publication/325929673_KPIs_for_Manufacturing_Operations_Management_driving_the_ISO22400_standard_towards_practical_applicability),
  [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S2405896318313508)
- External (Festlegung 2): [ISA — ISA-88 Series of Standards](https://www.isa.org/standards-and-publications/isa-standards/isa-88-standards)
  (ANSI/ISA-88.00.01, "Batch Control")
