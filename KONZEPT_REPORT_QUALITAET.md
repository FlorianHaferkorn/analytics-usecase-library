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
| K1 Boutique-Bar definieren | ⬜ offen | | Craft-Core §5 ist der Entwurf; Referenz-Report ausstehend |
| K2 Intent+Design-Spec-Schicht | ⬜ offen | | baut auf C2 (`design_rules.yaml`) auf |
| K3 Maximize Power BI | ⬜ offen | | nutzt R1.6-Schema-Funde; Scope-Cuts aus R1.3/R1.5 |
| K4 Content-Grounding-Layer | ⬜ offen | | Quellentyp-Katalog §6.3 als Grundlage |
| K5 Zweiter Renderer (Web) | ⬜ offen | | Renderer-Wahl offen (Discovery) |
| K6 Boutique-Scorecard im Gate | ⬜ offen | | erweitert C3/R3.3 |
| K7 Rollout + Abnahme | ⬜ offen | | nach K3–K6; je Domäne Screenshot-Abnahme |

---

*Konzept-Ebene über `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`. Craft-Core (§5) geteiltes IP
mit der Meridian-Initiative (Repo Freelancing) — getrennte Tools, gemeinsames
Handwerkswissen. Recherche-Grundlagen: die im Umsetzungsplan zitierte Deep-Research
(2026-07-03) plus etablierter Viz-Kanon (IBCS/ISO 24896, Tufte, Knaflic, Few, Ware).*
