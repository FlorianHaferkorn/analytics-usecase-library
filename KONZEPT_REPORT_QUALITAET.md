# Konzept — Report-Qualität auf Boutique-Niveau (ALUCA)

> **Rolle dieses Dokuments.** Dies ist die **Konzept-Ebene** über dem bestehenden
> Fahrplan [`UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`](UMSETZUNGSPLAN_REPORT_EXZELLENZ.md).
> Der Umsetzungsplan beantwortet *wie/wann* (R-Serie, Ledger); dieses Konzept
> beantwortet *warum und wohin* — es hebt die Zielhöhe von „valide + einheitlich"
> auf „haut den Kunden vom Hocker" und verankert die dafür nötige Architektur.
> Es **ersetzt den Umsetzungsplan nicht**, es erweitert ihn um die Cuts K1–K7 (§8).
>
> **Abgrenzung zu Meridian.** Meridian (Repo `Freelancing`) verfolgt dasselbe Ziel
> mit einem **eigenen, getrennten** Produkt und eigenem Fahrplan. ALUCA und Meridian
> **teilen Wissen** (den Craft-Core §5, die Recherche-Grundlagen), bleiben aber
> **getrennte Tools mit eigener Marke** — nie als ein Werkzeug vermarktet. Der
> Cross-Learning-Abgleich steht in §10.
>
> **Status:** Draft · Stand 2026-07-10 · Scope dieser Session: Konzept + Fahrplan
> (keine Generator-Änderungen — Umsetzung nach Freigabe des Konzepts).

---

## 1. Die ehrliche Diagnose — warum „valide" nicht „exzellent" ist

Die Theorie im Repo ist bereits Weltklasse. `Storytelling_Principles.md` und
`Layout_Grid_System.md` kodieren Knaflic, Few, Tufte, Ware, IBCS auf einem Niveau,
das die meisten Beratungen nie erreichen. **Das Problem ist nicht fehlendes Wissen.**
Es sind vier andere Lücken — jede belegbar am aktuellen Stand:

1. **Execution-Ceiling (das Ausführungsdach).** Der Generator emittiert *strukturell
   korrektes, aber visuell flaches* PBIR. Die Belege stehen im eigenen Ledger:
   Sparklines, Reference-Labels und deviations-gefärbte Zellen wurden in R1.3/R1.5
   als **Scope-Cut** zurückgestellt, weil das PBIR-Schema dafür nicht verifiziert war.
   Genau die Details, die „wow" erzeugen, sind die, die noch nicht emittiert werden.
   Das Ergebnis besteht die Validierung — und sieht trotzdem aus wie Standard-BI.

2. **Storytelling ist templatiert, nicht geerdet.** `big_idea`/`message` entstehen
   aus Lückentext-Templates (`"[Domain] ist [on/off] track — [KPI] ist [Δ]"`). Das
   liest sich *kompetent*, nicht *expertenhaft* — weil hinter dem Satz kein
   Branchen-Benchmark, keine externe Sicht, keine „so what → also"-Kette steht.
   Der Report zeigt Zahlen; er vertritt keine These.

3. **Inhaltstiefe = nur Standard-KPIs.** Es gibt keine „what good looks like"-
   Benchmarks, keinen Sektor-Kontext, nichts, was dem Kunden das Gefühl gibt, *seine*
   Branche zu kennen. Ein Deckungsbeitrag ohne Vergleich zu Branchenüblichkeit ist
   eine Zahl, keine Aussage (verletzt die eigene Anti-Pattern-Regel „fehlender
   Kontext").

4. **Kein sichtbares Craft, keine Marke.** Dem Output fehlt die letzte
   Handwerks-Schicht (Direktbeschriftung statt Legende, IBCS-Abweichungsnotation,
   kuratierte Typografie, ruhige semantische Farbe, komponiertes Weißraum-System).
   Das sind die 10 % Craft, die 90 % der wahrgenommenen Qualität ausmachen.

**Fazit:** ALUCA ist bei „einheitlich + maschinell abgenommen" angekommen (Ziel des
Umsetzungsplans). Boutique-Niveau ist eine **andere Achse** — sie kommt *obendrauf*.

---

## 2. Zielbild — was „Boutique-Niveau" konkret heißt

Referenzklasse: Boutique-Data-Beratungen (Typus datatraining.io), IBCS-konforme
Controlling-Reports, der visuelle Anspruch von FT/Economist-Grafik. Übersetzt in
prüfbare Zielgrößen:

| Dimension | Heute (valide) | Boutique-Ziel (prüfbar) |
|---|---|---|
| **Erste 3 Sekunden** | KPI-Band lesbar | Eine **These** (nicht nur ein Zustand) springt an — Titel = Schlussfolgerung |
| **Chart-Craft** | Chart-Typ korrekt | Deviation-Notation, Direktbeschriftung, ein Highlight, Referenzband — IBCS-Score bestanden |
| **Aussage** | `big_idea` gerendert | Aussage ist **geerdet**: Benchmark/Kontext + Treiber + empfohlene Handlung |
| **Farbe** | ≤4 semantische Farben | Ruhiger Neutral-Grund + **genau ein** Akzent; Farbe trägt immer ein Urteil |
| **Typografie** | Sans, Größenhierarchie | Tabellenziffern, kuratierte Skala, eine Familie, keine Waisen |
| **Marke** | Theme vorhanden | Ein wiedererkennbares, komponiertes ALUCA-Report-Theme — nicht Default-Blau |
| **Renderer** | nur Power BI | Aussage ist **tool-agnostisch**; Power BI ist *ein* Ziel, kein Deckel |

Der Boutique-Test (§9) ist bestanden, wenn ein fachfremder Betrachter in 5 Sekunden
die **These** nennt, in 30 Sekunden den **Grund**, und der Report auf den ersten Blick
wie das Werk *einer bestimmten Firma* aussieht — nicht wie ein Power-BI-Default.

---

## 3. Architektur-Kern — die viz-tool-agnostische Intent+Design-Spec-Schicht

Der Hebel mit der größten Wirkung ist ein **Umbau der Zielrichtung**, nicht mehr
Regeln. Heute ist die Pipeline *Power-BI-förmig*: der Generator, der konservative
Emitter, die native-Visual-Grenze — alles endet in einem `.Report`. Damit ist die
native-Power-BI-Grenze zugleich die Grenze der *gesamten* Qualität.

**Inversion:** Die Exzellenz lebt in einer **Intent+Design-Spec** — einer
deklarativen, renderer-unabhängigen Zwischenschicht zwischen `UseCase_Bracket.yaml`
und jedem Ausgabeformat. Sie trägt:

```
report_intent:                    # WAS gesagt wird
  page:
    message:        "..."         # die These (nicht der Titel)
    decision:       uc.decision_question
    evidence: [ {kpi_id, role, comparison}, ... ]   # nur governte KPIs
    exhibits:
      - message:    "one sentence, one message"
        encoding:   deviation_bar | trend | ranking | matrix
        highlight:  {rule, target}
        annotation: [ {type, at, label} ]
        so_what:    "implication"
        action:     action_code_id
design_spec:                      # WIE es aussieht (tool-agnostisch)
  color_role_map, type_scale, layout_zones, whitespace, semantic_colors
```

Renderer sind **austauschbare Ziele**, jeweils bewertet an *Fidelity* zur Spec:

| Ziel | Wofür | Fidelity-Grenze |
|---|---|---|
| **Power BI / PBIR** | governte Enterprise-Self-Service-Reports | native Visual-Decke — **maximal ausreizen** (§7) |
| **Web / HTML (Evidence.dev, React/visx)** | Boutique-Politur, die Power BI nativ nicht kann | quasi unbegrenzt |
| **PDF / statisch, Vega-Lite/IBCS** | Print-Grade-Exhibits, Angebote, Anhänge | hoch, aber statisch |
| **Fabric App (Rayfin, TS)** | *Watch-Item* — governte Custom-Frontends in Fabric | s. u. |

Die Qualitäts-Scorecard (§9) prüft die **Spec**, nicht ein Format. So hört die
native-Power-BI-Grenze auf, *die* Grenze zu sein — sie ist nur die Fidelity-Grenze
*eines* Ziels. Das ist zugleich anschlussfähig an die bestehende Richtung (ALUCA
kompiliert bereits nach Power BI **und** Evidence.dev/OSS).

> **Fabric App als Watch-Item (kein Workstream).** Microsoft *Fabric Apps* (Preview,
> Rayfin-SDK/CLI, TypeScript, React-Frontend, First-class-Fabric-Item mit OneLake +
> Entra) könnte künftig der governte Ort für den Web-Renderer *innerhalb* Fabrics
> sein. Status Juli 2026: Preview, TS-only, managed SQL-Server-Schema, region-limited,
> Tenant-Admin-gated. **Bewusst kein Investment jetzt** — beobachten über den
> bestehenden Pin-Drift-/Markt-Sensing-Loop, adoptieren wenn reif.

---

## 4. Warum ein IR und keine neuen Regeln

Das Repo hat bereits Regeln (Storytelling_Principles, Layout_Grid_System,
Color_Semantics). Sie scheitern nicht am Inhalt, sondern am **Angriffspunkt**: Regeln
in Prosa können vom Generator *ignoriert* werden (der Ledger belegt genau das —
stilles Dumpen von Mixed-Scale-Charts). Die Intent+Design-Spec macht die Aussage-
Absicht zu **maschinenlesbarer Pflicht** (Draco-Prinzip: Constraints statt
Guidelines) — der Generator *kann* nicht mehr flach emittieren, ohne eine Regel-ID
zu verletzen. Das ist die Brücke zwischen den (guten) Regeln und dem (schwachen)
Output. Cut C2 im Umsetzungsplan (`design_rules.yaml`, `component_300s`-Pflichtfelder)
ist der erste Baustein davon; K2 (§8) verallgemeinert ihn zur vollen Spec.

---

## 5. Der Craft-Core (geteiltes Wissen mit Meridian)

> Dieser Abschnitt ist **bewusst geteiltes IP** zwischen der ALUCA- und der
> Meridian-Initiative. Er ist tool-agnostisch formuliert und in beiden Repos
> spiegelbildlich gepflegt. Die Produkte bleiben getrennt; das *Handwerkswissen* ist
> gemeinsam. Er verschärft die bestehenden Regel-Dokumente zu einer **durchsetzbaren
> Rubrik** — jede Zeile ist als Scorecard-Kriterium (§9) prüfbar.

### 5.1 Farbe — Zurückhaltung als Signal
- **Ein** neutraler Grund (Weiß/sehr helles Grau), **ein** Akzent (Marke), Rest in
  Graustufen. Kontext-Serien immer gedämpft, Fokus-Serie hervorgehoben (mute-and-
  highlight). Nie mehr als der Fokus in Vollfarbe.
- Farbe **nur** semantisch (Urteil: gut/mittel/schlecht) oder als Inhaltsreferenz
  (Marke). Nie dekorativ, nie zur Unterscheidung gleichrangiger Kategorien.
- Semantische Rollen permanent und report-weit identisch; rot/grün nie allein — immer
  mit Icon/Weight (8 % Rot-Grün-Schwäche). Für Varianz colorblind-sicher blau/orange.

### 5.2 Typografie — Ziffern sind das Produkt
- **Eine** Familie, Variation nur über Weight/Größe. **Tabellenziffern** (tabular
  figures) Pflicht für jede vertikal vergleichbare Zahlenspalte.
- Kuratierte Skala (Hero-Wert ≥2× Sekundärwert). Kein ALL-CAPS für Fließtext.
  Zahlen rechtsbündig, Einheiten dezent, Tausender/Dezimal konsistent.

### 5.3 Layout — Weißraum ist komponiert, nicht übrig
- Striktes Grid, alle Kanten aligned; Gruppierung durch Weißraum (Proximity), nicht
  durch Boxen/Rahmen. Zone-Gap > Gutter > Padding.
- **Hero-Insight-Muster:** oben eine dominante Aussage/Zahl, darunter das Stützende.
  Nicht alles gleich groß (flache Hierarchie ist der häufigste Amateur-Tell).

### 5.4 Chart-Craft — die 10 %, die 90 % ausmachen
- **Deviation/Varianz zuerst:** Abweichung vs. Plan/PY als eigene Serie zeigen
  (IBCS), nicht nur zwei absolute Balken nebeneinander. Abweichungsbalken +/-.
- **Direktbeschriftung** an Linienenden statt Legende. Legende ist Leseweg-Kosten.
- **Datenlabels sparsam** — nur Endpunkte, Wendepunkte, das eine Highlight.
- Gitterlinien entfernt/1px hell; keine Hintergrundfüllung, kein 3D/Gradient/Schatten.
- **Referenzlinien/-bänder** für Ziel/Schwelle/Vorperiode (gestrichelt, leichter).
- **Small Multiples** statt überladener Mehrfach-Serie ab >4–5 Serien.
- **Sparklines** in KPI-Karten/Tabellen für Mikro-Trend im 3-Sek-Layer.
- Titel = **Schlussfolgerung** (IBCS „SAY"): „Deckungsbeitrag fällt 12 % ggü. Plan",
  nicht „Deckungsbeitrag nach Monat".

### 5.5 Narrativ & Annotation — die Aussage steht *auf* dem Chart
- Jeder Exhibit trägt **genau eine** Botschaft. Mehr als eine → zwei Exhibits.
- Die „so what?"-Kette ist sichtbar: **Signal → Grund → Implikation → Handlung.**
- Callouts direkt am relevanten Punkt („Okt: Promotion-Launch"), nicht in einer
  Fußnote. Der Leser soll nichts *interpretieren* müssen, was der Autor schon weiß.

### 5.6 Die „Wow"-Checkliste (10 Punkte, prüfbar)
1. Titel jedes Exhibits ist eine Aussage, kein Etikett.
2. Genau ein Highlight pro Chart (pre-attentiv).
3. Abweichung wird als Abweichung gezeigt (nicht vom Leser errechnet).
4. Kein Legenden-Leseweg, wo Direktbeschriftung möglich ist.
5. Ein Akzent, ruhiger Grund; jede Farbe trägt ein Urteil.
6. Tabellenziffern in allen Vergleichsspalten.
7. Jede Zahl hat Kontext (vs. Vorher / Ziel / Benchmark).
8. Weißraum gruppiert; keine dekorativen Rahmen/Boxen.
9. Eine These in 5 Sekunden erfassbar (Hero-Insight).
10. Der Report sieht aus wie *eine bestimmte Firma* — konsistentes, komponiertes Theme.

### 5.7 Anti-Patterns (sofort Stop & Refactor)
Mixed-Scale auf einer Achse · Metric-Overload (>7 pro Zone) · Vanity-Zahlen prominent ·
Zahl ohne Kontext · flache Hierarchie · Pie >3 Segmente / 3D / Doppelachse ·
dekorative Farbe · Default-Theme · Legende statt Direktlabel · Titel-als-Beschreibung.

---

## 6. Storytelling- & Content-Grounding-Modell

Der Sprung von „Zahlen zeigen" zu „These vertreten" hat zwei Teile.

### 6.1 Die Exhibit-Struktur (McKinsey-/IBCS-Muster)
Jeder Exhibit = **Action-Title + Chart + So-What + Next-Action**:
```
Action-Title (Aussage):  "GM fällt 12 % ggü. Plan — getrieben von Preisrealisierung"
Chart (ein Encoding):    Deviation-Bars, Worst-First sortiert, ein Highlight
So-What (Implikation):   "Preisdisziplin in DACH erodiert die Marge stärker als Mix"
Next-Action (governt):   → action_code_id (referenziert, nie neu definiert)
```
Report-Bogen = Kette von Exhibits: **Establish → Complicate → Resolve** (T1→T2/T3→T4).
Jede Seite führt zu genau einer Entscheidung im Zeithorizont des Lesers.

### 6.2 Aussage als Daten, nicht als Prosa
Die `message`/`big_idea` werden zu **strukturierten, geerdeten Feldern** im Bracket:
`claim` + `evidence_kpi_id` + `comparison` (vs plan/PY/benchmark) + `driver_kpi_id` +
`action_code_id`. Der Renderer *komponiert* daraus den Satz; der LLM erfindet nichts.
Das erfüllt zugleich die Grounding-Regeln (§13 Storytelling_Principles): jede Zahl
rückführbar auf eine governte Measure, Provenienz sichtbar, filterkontext-live.

### 6.3 Content-Grounding — Reports, die die Branche kennen
Damit ein Report expertenhaft statt generisch wirkt, braucht jede Domäne einen
**Benchmark-/Kontext-Layer** aus glaubwürdigen öffentlichen Quellen. Dieser wird als
governte, versionierte Referenz gepflegt (nie im Report frei behauptet):

| Domäne | Öffentliche Quellentypen | Story-/Benchmark-Material |
|---|---|---|
| Commercial / Sales | Branchenverbände, Marktreports, Destatis Umsatz-Serien | typische Win-Rates, Preis-/Mix-Bandbreiten, Saisonalität |
| Finance / Marge | Sektor-Kennzahlen, Geschäftsberichte, BVR/Bankenstatistik | Margen-/Cost-Ratio-Benchmarks, DSO/DPO-Üblichkeit |
| Operations / SCM | Fachverbände, Logistik-Indizes, Destatis Produktion | OTIF-/Bestandsreichweite-Normwerte, Durchlaufzeit-Bänder |
| HR / People | Gehaltsstudien, Bundesagentur f. Arbeit, Fluktuationsstudien | Fluktuations-/Time-to-Hire-Benchmarks je Branche |
| Marketing | Plattform-Benchmarks, Verbands-Reports | CAC/CPL/Conversion-Bänder, Kanal-Mix-Üblichkeit |

**Prinzip:** Der Benchmark liefert die dritte Vergleichsachse (neben vs. Vorher /
vs. Ziel), die aus „58 %" eine Aussage macht („58 % — 9 Pp. unter Branchenüblich").
Quellen mit Datum/Beleg im Katalog, Aktualisierung über den Markt-Sensing-Loop.

### 6.4 LLM-gestützte Narrative — geerdet, verifiziert
Chart-grounded generieren (aus sichtbaren Measures), nie freihändig. Zweistufig:
Analyse/Insight-Scoring (depth/correctness/specificity/actionability) **getrennt** von
der Komposition, mit Verifikationsstufe dazwischen (deckt sich mit R5.2). Jeder
numerische Claim braucht eine korrespondierende governte Measure; sonst wird er nicht
gerendert.

---

## 7. Workstream „Maximize Power BI"

„Ein Ziel unter mehreren" darf **nie** Ausrede für mittelmäßiges Power BI werden. Wo
Power BI genutzt wird, wird es an seine *echte* native Decke gefahren — konkret die
im Ledger zurückgestellten Scope-Cuts, jetzt schema-verifiziert nachgezogen:

- **(new) Card-Visual Reference-Labels** (Delta vs. Plan in der Karte) — Schema laut
  R1.6 via `catalog describe cardVisual` real bestätigt, damit nachrüstbar.
- **Sparklines** in Karten/Matrix (natives Feature) für Mikro-Trend im 3-Sek-Layer.
- **Bedingte/Deviation-Zellfarbe** in Detail-Matrizen — über governte DAX-Farb-Measure
  statt PBIR-Hex (löst den R1.3-Scope-Cut sauber, ohne Color_Semantics zu verletzen).
- **IBCS-Varianz-Charts** (Abweichungsbalken, AC/PL/PY-Notation) als Standard-Encoding
  im Ranking-/Varianz-Slot.
- **Komponiertes Marken-Theme** (nicht Default) — ein wiedererkennbares ALUCA-Report-
  Theme über alle 17 Reports.
- **Waterfall-Rollenfix** (Main_2, offener R1.6-Befund: 3 Measures in Y bei `maxPerRole.Y=1`).

Jeder Punkt: erst reales Schema verifizieren (Lehre aus R1.1), dann Generator-Fix +
Vollrollout, kein Ad-hoc-Diff. Native Features zuerst, keine Custom-Visual-Zukäufe
(Leitplanke 4 des Umsetzungsplans bleibt).

---

## 8. Fahrplan (Cuts K1–K7) — erweitert die R-Serie

> Sequenzierung wie im Umsetzungsplan (dünne vertikale Schnitte, Ledger-Abhaken).
> Modell-Zuordnung: **Opus** = Architektur/Schema/Kuration; **Sonnet** = mechanische
> Umsetzung/Rollout. K1–K7 setzen **nach** dem laufenden C1-Piloten an bzw. laufen
> teilweise parallel (Abhängigkeiten in Klammern).

| Cut | Ziel | Kern-Tasks | Modell |
|---|---|---|---|
| **K1 · Boutique-Bar definieren** | Craft-Core (§5) als versionierte, prüfbare Rubrik + ein Referenz-Report (COM-002) als „so soll es aussehen"-Muster | `report_craft_core.md` + Boutique-Scorecard-Kriterien; Referenz-Screenshot/Mockup | Opus |
| **K2 · Intent+Design-Spec-Schicht** | IR (§3) zwischen Bracket und Renderern; Aussage als Daten (§6.2) | Schema `report_intent`/`design_spec`; Bracket-Felder `claim/evidence/driver/action`; Generator liest IR | Opus |
| **K3 · Maximize Power BI** | native Decke ausreizen (§7), Scope-Cuts nachziehen | Reference-Labels, Sparklines, Deviation-Measure, IBCS-Varianz, Marken-Theme, Waterfall-Fix | Opus→Sonnet |
| **K4 · Content-Grounding-Layer** | Benchmark-/Kontext-Katalog je Domäne (§6.3), governt | `benchmark_catalog/` mit Quelle+Datum; Bracket-Referenz `benchmark_id`; Sensing-Loop-Anbindung | Opus |
| **K5 · Zweiter Renderer (Web)** | Boutique-Politur beweisen, wo PBI nicht hinreicht — ein Report über Evidence.dev/visx aus derselben IR | Web-Renderer liest IR; ein COM-002-Web-Exhibit auf Boutique-Bar | Opus→Sonnet |
| **K6 · Boutique-Scorecard im Gate** | „exzellent" wird messbar (§9), zusätzlich zum Validitäts-Gate | Craft-Kriterien als Checks; Schwelle je Report; CI-Artefakt | Sonnet |
| **K7 · Rollout + Abnahme** | 17/17 Reports auf Boutique-Bar; visueller Close-Loop | Regenerierung über IR; LLM-Judge + Screenshot-Abnahme je Domäne | Sonnet + User |

**Abhängigkeiten:** K1 → K2 → (K3 ∥ K4) → K5 → K6 → K7. K1 kann sofort starten;
K3 nutzt R1.6-Befunde; K6 erweitert das Scorecard-Gate aus C3.

---

## 9. Messbarkeit — die Boutique-Scorecard

Erweitert das bestehende Scorecard-Gate (C3/R3.3) um eine **Craft-Achse**. Zusätzlich
zu Validität (Slot-Grid, Bindings, Schema) wird die Rubrik §5.6 als gewichtete Punkte
geprüft; harte Knock-outs bleiben (Mixed-Scale, unsortierte Evidence, Default-Theme,
Legende-statt-Direktlabel, Titel-als-Beschreibung). Zwei Ebenen der Abnahme:

- **Maschinell:** strukturell prüfbare Kriterien (Deviation-Encoding vorhanden,
  ≤1 Highlight, Tabellenziffern, Theme ≠ Default, ≤1 Einheit/Achse, Benchmark-Ref
  gesetzt) → Scorecard-Punkte, Schwelle je Report.
- **Halbautomatisch (LLM-Judge + Mensch):** 5-Dimensionen-Urteil über Screenshots
  (Informativeness, Clarity, Visualization Quality, Narrative Quality, Factual
  Correctness) — Judge urteilt, Mensch entscheidet (deckt R4.2). Fängt, was
  strukturelle Prüfung belegt *nicht* fängt: Overlap, Unlesbarkeit, „fühlt sich
  billig an".

Zielbild erreicht, wenn 17/17 die Boutique-Scorecard ≥ Schwelle bestehen, 0
Knock-outs, und je Domäne eine dokumentierte Screenshot-Abnahme mit bestandenem
5-Sekunden-**Thesen**-Test vorliegt.

---

## 10. Cross-Learning-Register (ALUCA ↔ Meridian — getrennte Tools)

Beide Initiativen teilen Wissen, bleiben aber getrennte Produkte/Marken. Was ALUCA
von Meridian übernehmen kann, und umgekehrt:

| Thema | Von Meridian lernen | An Meridian geben |
|---|---|---|
| Craft-Core (§5) | gemeinsam gepflegt | gemeinsam gepflegt |
| Tool-agnostische Spec | Meridians `meridian/design` Taxonomie (A1–A11), TPL-001..006 als Vorbild für die IR | ALUCAs Golden-Thread-Bindung (Bracket→governte KPI) |
| Web-Renderer | Meridian-Studio (React+visx) + Aurora-Cockpit-Mockups als Boutique-Referenz | ALUCAs Scorecard-/Treue-Check-Disziplin |
| Storytelling | Meridians `action_panel_builder` (Anti-Fabrication) | ALUCAs zweistufiges Insight-Scoring (R5.2) |
| Benchmark-Grounding | — | gemeinsamer Quellentyp-Katalog (§6.3), pro Repo eigene Instanz |
| Over-Plot-Auflösung (BC-CHART-01/07) | **AC-vs-PY-Vergleichsserie statt Fremd-KPI-Overlay** (2026-07-11, Meridian TPL-001 diag-chart): einen überplotteten Multi-KPI-Chart nicht auf ein Single-Measure reduzieren (Info-Verlust), sondern auf **dieselbe Kennzahl + Vorjahres-Serie** (eine Einheit, mehr Tiefe) — Ziel bleibt Referenzlinie. In ALUCA als 2. Auflösungsoption neben dem Single-Measure-Ranking (R1.4) verfügbar | ALUCAs Single-Measure-Ranking-Muster (R1.4, die 8 BC-CHART-01-Fixes) als erste Auflösungsoption |

**Grenze:** kein gemeinsames Deployment, keine gemeinsame Marke, kein „ein Tool".
Geteilt wird ausschließlich Handwerkswissen und Recherche.

---

## 11. Nicht-Ziele & bewusst nicht gemacht (GOI-Pflicht)

- **Kein** Custom-Visual-Framework/-Zukauf (native zuerst — Leitplanke bleibt).
- **Kein** kompletter Theme-Umbau in K1 — Marken-Theme ist ein K3-Baustein.
- **Kein** Investment in Fabric Apps jetzt (Watch-Item, §3).
- **Kein** Aufgeben der Einheitlichkeit — Slot-Grid bleibt normativ, Craft kommt
  obendrauf (nicht statt).
- **Keine** Umsetzung in dieser Session — bewusst Konzept + Fahrplan only (User-Scope).
- **Nicht** entschieden: exakte Boutique-Scorecard-Gewichte und Schwellen (gehören in
  K6 nach Pilot-Erkenntnissen); Wahl des Web-Renderers (Evidence.dev vs. reines visx)
  — offen für K5-Discovery.

---

## 12. Ledger — Status (hier abhaken)

| Cut | Status | Datum | Notiz |
|---|---|---|---|
| K1 Boutique-Bar definieren | 🟡 teilw. | 2026-07-10 | Rubrik als Daten: `core/templates/page_templates/tokens/boutique_craft_rubric.yaml` (30 Regeln/6 Dimensionen, 5 Knock-outs, structural/judge-Modus) + `governance/Boutique_Craft_Rubric.md` (Scoring-Modell + COM-002-Referenz-Scorecard). Befund: COM-002 reißt heute **BC-NARR-01** (Titel = Etikett, nicht Schlussfolgerung) → verfehlt die Bar trotz starker Struktur; Gap→Cut-Mapping zu K2/K3/K4 dokumentiert. Enforcement (Checks + Judge) = **K6**. |
| K2 Intent+Design-Spec-Schicht | 🟡 teilw. | 2026-07-10 | **Intent als Daten (Teil 1):** Bracket-Schema um `message`/`so_what`/`action_code_id` je `component_30s`-Exhibit erweitert (additiv, non-breaking); Validator `tooling/validation/check_exhibit_message.py` erzwingt **BC-NARR-01** (Titel = Aussage, nicht Etikett) via reiner `classify_message`-Heuristik (Label-Pattern `X by Y` → fail; Assertion-Signal EN/DE → pass), 15 Unit-Tests; COM-002-Pilot mit gegroundeten Statement-Messages befüllt (3/3 Statements, 0 Violations). Verifiziert: 256 Schema/Bracket-Tests + 582 Superversion-Golden + Page-DoD (0 failed) + Drift-Gate `--strict` grün. **Bewusst offen (K3):** Generator-Emit (`message` → gerenderter Visual-Titel) + `design_spec`-Teil — braucht PBIR/Windows-Validierung. |
| K3 Maximize Power BI | 🟡 teilw. | 2026-07-10 | **Generator-Emit (Teil 1):** die governte Exhibit-`message` (K2) wird als Visual-Titel gerendert — in **beiden** Generator-Pfaden: (a) `page_scaffold_generator` via neuem `statement_title`-Pfad in `visual_builder.build_by_ux_visual_type` (`_apply_title`-Helper mit Quote-Escaping) — rendert für **alle** Visual-Typen (vorher nur clusteredColumn), (b) `superversion/from_aluca.add` (Titel = message ∨ Label). COM-002-Golden regeneriert — **chirurgischer Diff: nur Main_1/2/3-Titel Label→Statement**, sonst nichts. Verifiziert: +4 statement-title-Tests + 91 Generator-Suite + 582 Superversion-Golden + 15 BC-NARR-01-Tests + `report_quality` 0/0/0 + Drift-Gate grün; **kein COM-001-Regress** (Label-Fallback unverändert). **Bewusst offen:** PBIR-`.Report`-Regenerierung + Desktop-Render-Bestätigung = Maintainer-Schritt (Windows/Fabric, hier nicht renderbar); IBCS-Deviation/Reference-Labels/Sparklines (neues Schema) bleiben separater Cut. |
| K4 Content-Grounding-Layer | 🟡 teilw. | 2026-07-11 | **Grounding-Infrastruktur (fabrikationssicher).** Benchmark-Layer als governte, versionierte Referenz (§6.3): (1) **Quellentyp-Katalog** `core/kpi_catalog/benchmark_sources.yaml` (§6.3-Tabelle als Daten: erlaubte öffentliche Quellentypen + Domänen-Guidance). (2) **Benchmark-Registry** `core/kpi_catalog/benchmarks.yaml` + Schema `tooling/generator/schemas/benchmark.schema.json`. (3) **Provenance-Validator** `check_benchmarks.py` (blockierend): erzwingt Golden Thread (kpi_id → echte KPI), Quellentyp ∈ Katalog, konkrete `source` + ISO-`as_of`, Unit-Sanity → **kein frei behaupteter Branchen-Wert kann in einen Report**. (4) **Pilot recherchiert + belegt:** `ops.oee.pct` World-Class = 85 % (Nakajima 1988, TPM: 90 % Verfügbarkeit × 95 % Leistung × 99 % Qualität; korroboriert über zeitgenössische OEE-Referenzen) — die dritte Vergleichsachse (vs. Benchmark) für OPS-001. 9 Unit-Tests (Validator + Schema-Conformance + „Registry voll geerdet"-Guard). Ins `run_local_ci_check.sh` verdrahtet. **→ 2026-07-11 (Teil 2) — Registry an das Report-Modell verdrahtet:** additives Opt-in `component_3s.benchmark: true` (Schema, non-breaking) zieht die **dritte Achse** in die Hero-Card, **ohne** die primäre `comparison` zu ersetzen. Reverse-Golden-Thread im Validator (`check_bracket_links`): eine Hero-Card mit `benchmark: true` **muss** einen Registry-Eintrag für ihre KPI haben — sonst blockt das Gate. **Pilot OPS-001** (OEE): `benchmark: true` neben `comparison: vs_target` → „OEE 76% vs Ziel 82%, 9 Pp. unter World-Class 85%" (Ziel selbst < World-Class = starke Aussage). 2 zusätzliche Tests (11 gesamt), 947 tooling/products + 582 Superversion (governance-metadata → golden-neutral) + Drift-Gate grün. **→ 2026-07-11 (Teil 3) — Content-Rollout (recherchiert + belegt):** 3 weitere Benchmarks je mit echter öffentlicher Quelle + Datum durch das Provenance-Gate: **FCR** (svc.fcr.pct) World-Class 80% (SQM Group; 70% Branchen-Par), **OTIF** (supply.otif.pct) World-Class 95% (Kaizen/FourKites/MetricHQ; Retail fordert 98%), **NPS** (crm.nps.index, Einheit index) Median 44 (SurveyMonkey >150k Orgs; >60 world-class). Registry jetzt 4/4 grounded, 0 Violations. **→ 2026-07-11 (Teil 4) — Korroboration-Upgrade:** Schema/Validator von Einzelquelle auf **`sources[]`-Liste mit ≥2 unabhängigen Quellen** + beobachtete `range` umgestellt (eine Einzelquelle ist für Branchen-Benchmarks unzuverlässig). Alle 4 nachrecherchiert + korroboriert: OEE (Nakajima + Evocon + Tractian), FCR (SQM Group + MetricNet, range 41–94%), OTIF (Kaizen + FourKites/MetricHQ, range 85–98%), NPS (SurveyMonkey + Retently + Bain, range 0–72). Validator erzwingt ≥2 Quellen je Eintrag + Per-Source-Provenienz + range low≤high; „registry-korroboriert"-Test. **→ 2026-07-11 (Teil 5) — Peer-Relevanz + Quell-Tiering:** ein Cross-Industry-Schnitt führt einen konkreten Kunden in die Irre (NPS-Median 44 lässt B2B-SaaS mit Peer ~35 schlecht aussehen). Modell trennt jetzt **`benchmark_class`: normative** (definierter Universal-Standard — OEE/OTIF, ein Wert gilt) **vs. empirical** (Peer-Verteilung — NPS/FCR, **`segments[]` je Branche Pflicht**; Top-Value = markierter Fallback). Zusätzlich Quell-**`tier`** (primary/large_sample/secondary) mit **≥1 autoritativer Quelle Pflicht** (keine Blog-Häufung). FCR→empirical (Retail 78/Financial 74/Tech 65), NPS→empirical (Retail 45/SaaS 35/Financial 30/Telecom 10); Quellen getiert (Nakajima/Bain primary, SurveyMonkey/MetricNet/SQM large_sample). 15 Tests. **→ 2026-07-11 (Teil 6) — Segment-Resolver:** `resolve_benchmark(benchmark, industry) → (value, basis)` macht aus den Peer-Daten eine Peer-**Zahl**: normative → `universal`; empirical + Branchen-Match → `segment:<Branche>` (Token-Overlap, ≥4-Zeichen-Wörter, generische Tokens raus); kein Match → `cross_industry_fallback` (ehrlich als Fallback markiert, nicht als Peer-Benchmark). Belegt: committete NPS löst „SaaS platform"→35, „Grocery retail"→45, „Mining"→Fallback 44. `industry` ist Deployment-Parameter (ALUCA = Library). 17 Tests. **→ 2026-07-12 (Teil 7) — Hero-Wire (sichtbares Reference-Label):** die aufgelöste Peer-Zahl wird jetzt **sichtbar** im Report-Modell verdrahtet. Der IR-Compiler (`generator_core/ir/compiler.py`) reicht bei `component_3s.benchmark: true` das Reference-Label über den governten Resolver (Tool-Reuse — kein zweiter Resolver) in die Hero-Card (`config.benchmark_reference`) **und** emittiert eine **Reference-Label-Caption** als eigenes Textbox-Visual (`Benchmark_Caption`, Layout-Strip unter der KPI-Band). Ehrlich qualifiziert: normative → „vs. world-class 85%", empirical+Peer → „vs. Retail peer 45", kein Match → „vs. cross-industry 44 (no sector match)". `deployment_industry` als Compiler-Parameter wählt das Segment (Library-Deployment). **Proven-Schema-Disziplin:** die Caption nutzt die **korpus-verifizierte Textbox-Form** (`paragraphs/textRuns`, wie ActionPanel) — eine Card-Reference-*Line* bräuchte ein unverifiziertes PBIR-Objekt und bleibt daher bewusst ungenutzt. Pilot OPS-001 kompiliert die Caption „vs. world-class 85%"; primäre `comparison: vs_target` bleibt additiv erhalten. 6 Tests (Label-Format normative/empirical/Fallback, OPS-001-Compile, Deployment-Industry-Resolution, Adapter-Textbox-Emit). Volle Suite 1444 grün + Drift-Gate grün. **→ 2026-07-12 (Teil 8) — KPI-Rollout auf die korroborierte/segmentierte Bar (recherchiert + belegt):** 4 weitere Benchmarks je mit **echter, web-recherchierter** öffentlicher Quelle (≥2 korroboriert, ≥1 autoritativ) durch das Provenance-Gate, alle **empirical mit Branchen-Segmenten** (peer-relativ): **Inventory Turns** (`inv.turnover`, ratio) — Grocery 13 / Retail 11 / Manufacturing 5,3 (Netstock 2024 + ReadyRatios SEC-Filings); **DSO** (`wc.dso.days`, lower-is-better) — Retail/E-Com 11 / Manufacturing 28 / B2B-Services 52 / Construction 100 (Hackett 2024 Working-Capital via CFO.com + Upflow/oAppsNet); **Forecast-MAPE** (`plan.forecast.mape.pct`, lower-is-better) — FMCG-stabil 15 / Industrial-B2B 30 / Fashion-saisonal 45 (RELEX + ToolsGroup — Genauigkeit ist volatilitäts-, nicht aufwandsgebunden); **Customer Retention** (`crm.retention.pct`) — SaaS 90 / Retail 65 / DTC-E-Com 31 (First Page Sage 2026 + CustomerGauge/Sprinklr — Switching-Cost-Spread). Registry jetzt **8/8 grounded, 0 Violations**; Resolver verifiziert peer-relativ (Grocery→13 Turns, Construction→100 DSO-Tage, Fashion→45% MAPE, DTC→31% Retention). 17 Tests grün. **→ 2026-07-12 (Teil 9) — Deployment-Industry an der Generierungs-Grenze verdrahtet (Resolver jetzt erreichbar):** die Peer-Auflösung war bis hier *unerreichbar* aus der echten Pipeline — der `deployment_industry`-Compiler-Parameter (Teil 7) wurde von nichts gefüttert, also fiel jedes empirische Caption auf „cross-industry" zurück. Da ALUCA eine **Library** ist (Kundenbranche ist per Design ein Deployment-Parameter, **nicht** committet — kein Sektor in `core/`), ist der korrekte Ort die **Generierungs-Grenze**: `--deployment-industry` als CLI-Flag an beiden Entrypoints (`aluca compile` in `generator_core/__main__.py` + `generate_full_report.py` `_ir_generate`), durchgereicht in den `BracketCompiler`. `--dry-run` zeigt jetzt `deployment_industry` + das aufgelöste `benchmark_reference`, damit der/die deployende Berater:in die Wirkung sieht. Ein Deployment, das die Branche kennt, bekommt so peer-relative Captions; unpinned bleibt der **ehrliche** Fallback. Verifiziert live (OPS-001 normative → `universal`, Branche korrekt ignoriert) + CLI-Test (Flag erreicht den Compiler durch den echten Arg-Parser). 199 Generator-/Adapter-/Scaffold-Tests + Drift-Gate grün. **Kein Meridian-Spiegel nötig:** dort liest der Renderer die Branche bereits aus `strategy.json` `organisation.sector` (Loop bereits geschlossen, M5 Teil 7). **→ 2026-07-12 (Teil 10) — erstes EMPIRISCHES Hero-Benchmark (Peer-Auflösung produktiv):** SCM-001 (Inventory Performance, Hero `inv.dio.days`) opted additiv in die Benchmark-Achse (`benchmark: true` neben `comparison: vs_target`) — das **erste** Hero, dessen Referenz-Zahl **sektor-relativ** ist statt eines Universal-Standards. Neues empirisches, web-recherchiertes Benchmark `inv.dio.days` (Days Inventory Outstanding, lower-is-better): **Grocery & Perishables 15 / Apparel & General Retail 40 / Manufacturing 75 Tage** (Netstock 2024 + klarmetrics; range 10–180 inkl. Pharma). **Resolver-Footgun gefixt:** „retail" tauchte erst in zwei Segmenten auf → First-Match schickte jeden Retailer arbiträr ins Grocery-15. Segmente auf **distinkte Kopf-Nomen** umgestellt (grocery vs general retail) → ein Vollsortiment-/Omnichannel-Retailer landet eindeutig bei General-Retail 40, ein expliziter Grocer bei Grocery 15, ein Hersteller bei 75. Live verifiziert über die CLI (`--deployment-industry`): Omnichannel-Retail→40 Tage, Grocery→15, Manufacturing→75, unpinned→ehrlicher Fallback 45. Registry **9/9 grounded, 0 Violations**; Reverse-Golden-Thread grün (SCM-001-Hero hat jetzt Registry-Eintrag). 45 Benchmark-/IR-Tests + volle Suite **1630 grün** (kein Golden-Regress — additive governte Metadaten) + Drift-Gate grün. **→ 2026-07-12 (Teil 11) — normative Quality-Benchmarks (FPY + Scrap) + zweites live-Hero:** 2 **normative** Benchmarks (definierter Standard, universell — **keine** Segmente nötig, anders als die empirischen) web-recherchiert + korroboriert: **First Pass Yield** (`quality.fpy.pct`, higher-is-better) World-Class **98%** (6sigma.us Lean-Six-Sigma primary + Averroes: mature 93–96%, world-class 98,5%+); **Scrap Rate** (`quality.scrap.pct`, lower-is-better) World-Class **≤1%** (symestic large_sample + Fabrico; 2–5% typisch). FPY vs. Scrap bewusst getrennt dokumentiert: 0,5% Scrap bei 82% FPY verbirgt 17,5% Rework (symestics „honest number"). **Live-Hero:** OPS-003 (Quality Yield, Hero `quality.fpy.pct`) opted in die Achse → rendert „vs. world-class 98%" (normativ → `universal`, Branche korrekt ignoriert). Registry **11/11 grounded, 0 Violations**; Reverse-Golden-Thread grün. 2 Tests (normative-resolves-universal + OPS-003-opt-in), volle Suite **1632 grün** (kein Golden-Regress) + Drift-Gate grün. **Kein Meridian-Spiegel:** Aurora governt keine FPY-/Scrap-KPI (OEE subsumiert den Quality-Faktor bereits) — Golden Thread verbietet Referenz auf nicht-existente KPI; sauber ALUCA-only. **Bewusst offen:** Renderer-natives Reference-*Line*-Objekt (Windows/Fabric-gated) bleibt die letzte offene Ausbaustufe der Benchmark-Achse. |
| K5 Zweiter Renderer (Web) | ⬜ offen | | Renderer-Wahl offen (Discovery) |
| K6 Boutique-Scorecard im Gate | 🟡 teilw. | 2026-07-10 | **Drei structural-Regeln verdrahtet.** (1) **BC-NARR-01** (`check_exhibit_message.py`) — Gate via `run_check` + repo-weiter Pytest: 0 Label-Violations erzwungen (nach K7). (2) **BC-CHART-01 Mixed-Scale** (`check_mixed_scale.py`, Knock-out) — Unit-Klassen aus dem KPI-Katalog (`business.unit_format`), flaggt Charts mit ≥2 Einheiten auf einer Achse. **Fund + Fix: 8 reale Mixed-Scale-Defekte** (der R1.4-Gründungsbug, nur COM-002 war gefixt) — **alle 8 gefixt** (2026-07-10): jeder Multi-Unit-Balken auf ein Single-Measure-Ranking reduziert (R1.4-Muster, eine Einheit), z.B. COM-003 Main_2 → `crm.retention.pct`, FIN-001 Main_2 → `fin.cash.ocf` (vs_plan), OPS-003 → `quality.copq.amount`, XD-003 Main_3 → `enterprise.value_at_risk.index`; die gecutteten KPIs bleiben governt (`orchestration.influencing_kpi_ids` + Detail-Matrix). Message je Exhibit passend nachgezogen (41/0/0 BC-NARR-01). **Beide Gates jetzt 0 Violations, voll blockierend** (kein Advisory/Backlog mehr). 2 Goldens (COM-003/SCM-002) regeneriert — Diff nur Titel + `bound_measures` des gefixten Exhibits (3→1). Verifiziert: 1325 Tests grün, Drift-Gate grün. (3) **BC-NARR-04 KPI-Kontext** (`check_kpi_context.py`, advisory/major) — der 3-Sek-Hero (`component_3s`) soll governten Kontext deklarieren (comparison/target). Coverage jetzt **17/17** (Rollout 2026-07-10: `comparison` + `status_logic` je Hero — attainment/strategic → `vs_target`, CLV → `vs_py`, budgetierte Amounts/Rates → `vs_plan`). `comparison` ist governte Metadaten (kein Measure-Binding) → binding-/golden-neutral (582 Superversion grün). Coverage-Regression-Guard `covered ≥ 17`. (4) **BC-CHART-10 Evidence-Sort** (`check_evidence_sort.py`, Knock-out, advisory im Rollout) — die 300-Sek-Evidence-Matrix (`component_300s`) muss eine governte **Worst-First-Sortierung + explizites Top-N** deklarieren (Craft-Core §5.4 / R1.3), nicht als Prosa-Default. Schema um `evidence_sort` (column ∈ `evidence_columns` + direction asc/desc) + `evidence_top_n` erweitert (additiv, optional). **COM-002-Pilot** grounded (`margin.gm.vs_plan.pct` asc, Top-20 — die größte Fehlmenge zuerst); 7 Unit-Tests. **→ 2026-07-11 VOLL AUSGEROLLT:** alle 16 Rest-Brackets governt, Worst-First je `decision_question` verankert (asc wo niedrig schlecht: COM-001 net-sales-vs-plan, FIN-001 cash-vs-plan, OPS-001 OEE, SCM-002 OTIF, XD-001 SLA, XD-004 impact-value, COM-004 promo-ROI, COM-IND-R001 cross-sell; desc wo hoch schlecht: OPS-002 unplanned-downtime, OPS-003 scrap, SCM-001 stockout, SCM-003 MAPE, FIN-002 COGS%, XD-002 overtime, XD-003 value-at-risk, COM-003 revenue-at-risk), Top-20 einheitlich. Gate jetzt **17/17, `--strict` blockierend** (0 Violations), Coverage-Guard `covered ≥ 17`. Governte Metadaten (kein Emit) → golden-neutral (582 Superversion grün). **→ 2026-07-11 (Teil 5) — Scorecard (§9-Kapstein):** `tooling/report_quality/boutique_scorecard.py` aggregiert die 4 verdrahteten structural-Regeln ins gewichtete Rubrik-Modell (global_weight = rule.weight/Dim × Dim.weight, Σ=100), rechnet den erreichten Score über die **gescorte Teilmenge** + Knock-out-Status, meldet **ehrliche Coverage**: aktuell **4/30 Regeln = 16/100 Pkt** auto-scorebar (100 % der Teilmenge grün, 3/5 Knock-outs verifiziert, 0 Fail). Bewusst **nicht certifiable** bis Coverage = 100 (Judge-Regeln offen) — kein Silent-Pass. Injizierbarer Validator-Runner (5 Tests), advisory-Report im `run_local_ci_check.sh`. **→ 2026-07-11 (Teil 6) — BC-BRAND-01 verdrahtet (Coverage-Lift):** `check_custom_theme.py` (Knock-out) prüft strukturell aus dem committeten PBIR — jeder `.Report` muss ein komponiertes Custom-Theme registrieren (`RegisteredResources/*.json` mit `dataColors` + semantischen good/bad-Slots), nie das Renderer-Default. **17/17 grün** (COM-001 nutzt `Aurora_Group__*` statt `Brand_*` — beide valide). In die Scorecard aufgenommen → **5/30 Regeln = 22/100 Pkt, 4/5 Knock-outs verifiziert**, 0 Fail. 5 Tests, `--strict` blockierend im `run_local_ci_check.sh`. **→ 2026-07-11 (Teil 7) — BC-CHART-08 verdrahtet (Tool-Reuse):** `check_forbidden_charts.py` ist eine **dünne CLI über die bestehende `ForbiddenVisualTypes`-Invariante** (`structural_validator.py`) — kein Reimplement der Verbotsliste (pie/donut/gauge/treemap). 17/17 Reports frei davon (Schema-Enum sperrt sie ohnehin schon beim Authoring, die CLI verifiziert das gerenderte PBIR). In die Scorecard → **6/30 = 24,6/100 Pkt**, 4/5 Knock-outs verifiziert, 0 Fail. 4 Tests, `--strict` blockierend. **→ 2026-07-11 (Teil 8) — Scorecard-Regressions-Guard:** `test_live_scorecard_does_not_regress` fährt die **echte** Scorecard (reale Validatoren über Brackets/Dist) und sperrt den Stand als Ratsche: `scored_rules ≥ 6`, `coverage ≥ 24,6 Pkt`, `structural_score_pct == 100` (alle verdrahteten Regeln grün), `knockouts_failed == []`. Bricht ein Rule oder fällt Coverage → rot. Aggregat-Qualität ab jetzt regressionsgeschützt. **→ 2026-07-11 (Teil 9) — Judge-Harness (die `check: judge`-Hälfte):** `tooling/report_quality/judge.py` — `Judge`-Protokoll + `Verdict` + `SpecHeuristicJudge`. Kern-Erkenntnis: mehrere `check: judge`-Regeln sind ohne Render **aus der governten Spec entscheidbar** — die bekommen eine deterministische Heuristik, die render-only-Regeln **enthalten sich ehrlich** (`score=None`, kein Fake). Erste Heuristik **BC-NARR-03** (So-what-Kette signal→reason→implication→action): jedes Message-tragende Exhibit muss `so_what` führen → 41/41 grün. In die Scorecard integriert (injizierbarer `judge`-Param, Default aus): **Coverage 24,6 → 28,6 Pkt, 7/30 Regeln**. 6 Judge-Tests + Regressions-Guard mitgezogen. **→ 2026-07-11 (Teil 10) — LLM-Backend-Naht:** die render-only-Regeln haben jetzt einen echten Integrationspfad. `judge.py` +`build_judge_prompt` (deterministisch), `parse_verdict` (malformed/off-scale → abstain, nie geraten), `LLMJudge(complete, render_provider)` (beide injiziert; fehlt eins → enthält sich), `CompositeJudge` (Spec-Heuristik vor LLM, damit billige deterministische Entscheidungen einen Modell-Call zuvorkommen). Reine Prompt-/Parse-Funktionen unit-getestet (Mock-Modell) → Kontrakt verifiziert **ohne** Modell; Live-Coverage **unverändert 28,6 Pkt** (LLMJudge enthält sich mangels Modell/Render → keine Fake-Coverage). 5 zusätzliche Tests (11 Judge-Tests). **→ 2026-07-12 (Teil 11) — zweite Spec-Heuristik BC-LAYOUT-03 (Hero-Insight):** die Rubrik markiert BC-LAYOUT-03 („ein dominantes Statement führt, Hierarchie nicht flach") konservativ als `judge` — aber der **governte Layout** entscheidet es ohne Render: jede Summary-Seite muss einen Single-Lead-`component_3s`-Hero (eine `kpi_id`) deklarieren, distinkt von den `component_30s`-Exhibits. Deterministische Heuristik ergänzt (17/17 Seiten führen mit Hero → 1.0); fehlt der Hero → flat, 0.0. In die Scorecard: **Coverage 28,6 → 32,6 Pkt, 8/30 Regeln** auto-scorebar. Regressions-Guard geratcht (`scored_rules ≥ 8`, `coverage ≥ 32,6`). 2 Judge-Tests (scores + flat-Bruch). **→ 2026-07-12 (Teil 12) — BC-BRAND-02 strukturell verdrahtet + BC-NARR-02 als ehrlich-nicht-decidbar dokumentiert:** **Befund BC-NARR-02** („eine Aussage pro Exhibit"): naive Spec-Heuristik (Exhibit bindet Measures aus ≥2 KPI-Domänen = 2 Subjekte) produziert **False Positives** — GM-Bridges (margin+sales+cost = *eine* Story) und Vergleichs-Measures (Plan/Last-Year = dasselbe Subjekt) spannen legitim mehrere Domänen (7 Fehl-Flags im Korpus). Ob mehrere Measures *eine* Aussage bilden, braucht semantisches Urteil → BC-NARR-02 bleibt korrekt **judge/abstain** (keine fabrizierte Coverage). **Stattdessen BC-BRAND-02** („konsistente Identität über alle Reports — sieht aus wie eine Firma"): das ist aus dem committeten PBIR decidbar (**strukturell**, nicht judge — daher via Tool-Reuse in `check_custom_theme.py` erweitert, nicht neuer Silo): neue `active_theme()` (liest `report.json` → `themeCollection.customTheme.name`, das *aktive* Theme, nicht bloß registrierte Resources) + `check_consistency()` + `--consistency`-CLI. Befund: alle **17/17 Reports** nutzen aktiv **ein** Theme (`Aurora_Group__Monochromatic__Light`) — die zweite registrierte `Brand_Rose`-Resource ist dormanter Leftover, nicht aktiv → BC-BRAND-02 **grün**. In die Scorecard (WIRED, strukturell wie BC-NARR-01): **Coverage 32,6 → 36,6 Pkt, 9/30 Regeln, 7 strukturelle**. Guard geratcht (`scored_rules ≥ 9`, `coverage ≥ 36,6`). 4 Tests (active_theme/consistency-pass/drift-flag/committed-dist). **→ 2026-07-12 (Teil 13) — BC-CHART-09 (Nullbasierte Balken-Achsen) strukturell verdrahtet:** die kardinal-irreführende Chart-Sünde — ein Balken/Säulen-Chart mit abgeschnittener Werteachse übertreibt Unterschiede (Länge kodiert Wert, ein Nicht-Null-Baseline verzerrt das Flächen-zu-Wert-Mapping). `check_zero_based_axes.py` prüft aus dem committeten PBIR: kein Bar/Column-Visual (`_BAR_TYPES`) darf ein `valueAxis.start ≠ 0` deklarieren (PBIR-Literal-Parse, z.B. „50D"→50). **Verifikations-Regel wie BC-CHART-08** (liest emittierte visual.json, kein unverifizierter Emit nötig, sperrt saubere Generator-Ausgabe als Ratsche ein). Befund: **17/17 Reports, 0 abgeschnittene Achsen** → grün. In die Scorecard (WIRED): **Coverage 36,6 → 39,2 Pkt, 10/30 Regeln, 8 strukturelle**. Guard geratcht (`scored_rules ≥ 10`, `coverage ≥ 39,2`). 5 Tests (Truncation-Erkennung/Null-Start-ok/kein-Start-ok/Linien-ignoriert/committed-dist-frei); Linien-Charts bewusst ausgenommen (dürfen legitim nicht-null starten). Volle tooling-Suite 1460 grün + Drift-Gate grün. **→ 2026-07-12 (Teil 14) — BC-CHART-02 (Deviation-as-Deviation, IBCS) strukturell verdrahtet + realer Defekt gefixt:** eine Plan-/Vorjahres-Abweichung als **absolute Balkenpaare** zu zeigen zwingt den Leser, zwei Totale im Kopf zu subtrahieren — die Aussage IST die Lücke, also gehört sie als Varianz/Waterfall (der Delta selbst) gezeigt. `check_deviation_display.py` prüft aus dem governten Bracket: ein `component_30s`-Exhibit mit `comparison ∈ {vs_plan, vs_py}` und absolutem Bar-`visual_type` ist das Anti-Muster (vs_target exempt — ein Ziel ist natürlich eine Referenzlinie; Waterfall/Linie/Trend exempt). **Realer Fund + Fix: FIN-001 Main_2** (OCF vs. Plan) war `bar_chart`, obwohl seine eigene Message vom „shortfall/OCF-versus-Plan gap" spricht → auf `waterfall` gefixt (deckt sich mit FIN-001 Main_3s vs_target-Waterfall **und** mit dem bereits committeten Dist-Visual, das schon ein `waterfallChart` war — der Fix reduziert Spec↔Dist-Drift). In die Scorecard (WIRED): **Coverage 39,2 → 42,8 Pkt, 11/30 Regeln, 9 strukturelle**. Guard geratcht (`scored_rules ≥ 11`, `coverage ≥ 42,8`). 7 Tests (Bar-Flag/Column-Flag/Waterfall-exempt/vs_target-exempt/Trend-exempt/committed-clean/FIN-001-Waterfall). Volle Suite **1650 grün** (kein Golden-Regress) + Drift-Gate grün. **Bewusst offen:** Renderer + Modell verdrahten → genuine render-only-Regeln; BC-CHART-04 (Declutter, teils unscharf) + BC-CHART-05 (Reference-Line, emit-gated wie BC-CHART-10) = Rest der Chart-Craft-Dimension. |
| K7 Rollout + Abnahme | 🟡 teilw. | 2026-07-10 | **Intent-Rollout (Teil 1) — Backlog geräumt:** BC-NARR-01-Statement-Messages (`message`+`so_what`) für alle 38 offenen Exhibits über 16 Brackets autoriert (COM/FIN/OPS/SCM/XD core + COM-IND-R001), gegroundet in je `decision_question` + Exhibit-KPI (z.B. FIN-001 DSO/DIO/DPO-CCC, SCM-003 MAPE-Bias, FIN-002 COGS). Gate jetzt **41 Statements / 0 advisory / 0 Violations** (war 3/38/0). 4 Superversion-Goldens regeneriert — chirurgisch **title-only**. Verifiziert (unabhängig nachgefahren): 1409 Tests grün, Drift-Gate `--strict` grün, `message` ≤140/`so_what` ≤200. **Bewusst offen:** PBIR-`.Report`-Regenerierung + Screenshot-/LLM-Judge-Abnahme (Windows/Fabric) — der Abnahme-Teil von K7 bleibt offen. |

---

*Konzept-Ebene über `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`. Craft-Core (§5) geteiltes IP
mit der Meridian-Initiative (Repo Freelancing) — getrennte Tools, gemeinsames
Handwerkswissen. Recherche-Grundlagen: die im Umsetzungsplan zitierte Deep-Research
(2026-07-03) plus etablierter Viz-Kanon (IBCS/ISO 24896, Tufte, Knaflic, Few, Ware).*
