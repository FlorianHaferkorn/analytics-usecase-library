# Konzept — Layout-System (tool-übergreifend, Layout-Systeme als Plugin)

**Stand:** 2026-08-01 · **Status:** Entwurf zur Abnahme · **Verhältnis zu bestehenden Dokumenten:**
Dieses Konzept **erweitert** [`KONZEPT_REPORT_QUALITAET.md`](KONZEPT_REPORT_QUALITAET.md) §3
(Intent+Design-Spec-Schicht, Cut **K2**) und §7/K5 (zweiter Renderer) um die konkrete,
baubare Schicht darunter. Es ersetzt nichts. Die Modell-Zuordnung folgt
[`UMSETZUNGSPLAN_REPORT_EXZELLENZ.md`](UMSETZUNGSPLAN_REPORT_EXZELLENZ.md) §3.

---

## 1. Zielbild

> Ein Use Case wird **einmal** in analytischer Absicht beschrieben und in **jedem**
> Ziel-Werkzeug so dargestellt, wie es dort am besten geht — mindestens auf dem
> garantierten Niveau, gern darüber.

Vier Eigenschaften, an denen das Zielbild scheitern oder gelingen kann:

| Eigenschaft | Prüfbare Bedeutung |
|---|---|
| **Tool-agnostisch** | Die Storyline nennt die *Absicht* („Fluss zwischen Stufen"), nicht das Visual („Sankey"). |
| **Garantiert** | Jede benutzte Absicht hat in **jedem** registrierten Konnektor eine Darstellung. Kein stiller Qualitätsverlust im Zweit-Tool. |
| **Steigerbar** | Ein Konnektor **darf** eine bessere Darstellung anbieten (Sankey in Vega/React), muss aber deklarieren, welche Boden-Darstellung sie ersetzt. |
| **Deterministisch** | Gleiche Eingabe → gleiches Artefakt. Kein Zufall, keine Modell-Kreativität im Erzeugungspfad. |

**Was ausdrücklich nicht Zielbild ist:** ein einheitliches Aussehen über alle Tools.
Gleichmacherei würde die Decke auf das schwächste Tool senken — das Gegenteil des Ziels.

---

## 2. Ausgangslage — gemessen, nicht erinnert (01.08.2026)

Die folgenden Befunde begründen den Zuschnitt. Alle sind in dieser Form nachgemessen.

| Befund | Beleg |
|---|---|
| **Drei Vokabulare, zwei Autoritäten, keines erzwungen** | `visual_whitelist.md` (9 Typen) nennt sich verbindlich, wird von keinem Checker gelesen. `Abstract_Visual_Types.md` (34) ist `authority:` in `visual_slot_mapping.yaml`, erzwungen nur in `visual_validator.py` — im **deprecated** Generator, und dort nur als Verbotsliste. Dazu `_VISUAL_TYPE_MAP` (10) im IR-Compiler. |
| **Die Brackets folgen der Whitelist, nicht der Registry** | 20 Brackets benutzen 6 Typen; `trend_line` (18×) und `bar_chart` (16×) stehen nur in der Whitelist. Gut die Hälfte aller 66 Deklarationen ist für einen registry-basierten Übersetzer nicht auflösbar. |
| **Konnektor-Abdeckung ist asymmetrisch** | Gegen die 34-Typen-Registry: Power BI 24/34, Evidence/OSS 8/34. 16 Typen existieren nur PBI-seitig, darunter der komplette Slicer-Satz, `matrix`, `scatter_plot`. |
| **Kein sanktionierter Report-Emitter mit vollem Layout** | `superversion.targets.pbir` erzeugt für FIN-002 4 Visuals; der Bestand hat 11. Beide Modi des `page_scaffold_generator` sind deprecated. (Offener Punkt **C4** im Meridian-Backlog.) |
| **Das Canonical Model trägt Layout — der Quell-Adapter füllt es nicht** | `Visual` hat `x/y/width/height/slicer_field`; `from_aluca._page_from_layout()` setzt nichts davon. Die Positionstabellen existieren bereits in `generator_core/ir/compiler.py` (`_OVERVIEW_LAYOUT`, `_DETAIL_LAYOUT`). |

### 2.1 Was bereits existiert — und im ersten Entwurf unterschlagen war

Der erste Entwurf schlug einen neuen Intent-Katalog, neue Konnektor-Dateien und ein neues
Gate vor. **Drei davon gibt es schon.** Nachgemessen:

| Bestehend | Was es ist |
|---|---|
| `visual_registry.yaml` (672 Z.) — `information_blocks` | **Der Intent-Katalog.** 9 Blöcke: `status_signal`, `time_trend`, `variance_explanation`, `entity_ranking`, `exception_list`, `structural_mix`, `prescriptive_action`, `detail_matrix`, `root_cause_context` — je mit `purpose`, Slot-Kompatibilität, erlaubten **und verbotenen** Visuals samt Begründung. |
| Regel im Registry-Kopf | *„Visual substitution is ONLY valid within the same information block."* — **das ist der Boden/Decke-Mechanismus**, bereits formuliert. |
| `tooling/superversion/layer_tools/visual_library.py` | **Die Visual-Library.** Löst Slot → Block auf, kennt erlaubt/verboten/Default je Block mit perzeptueller Evidenz, läuft standalone. |
| `test_visual_library.py::test_pbir_mapping_is_library_sanctioned` | **Die Bindung Emitter ↔ Library** existiert bereits — für Power BI. |
| `design_rules.yaml`, `tokens/boutique_craft_rubric.yaml` (30 Regeln/6 Dim.), `governance/*` | Regelwerk-Substanz, teils IBCS-nah |

**Die eigentliche Lücke ist damit viel kleiner und viel schärfer:** `AllowedVisual` trägt
das Feld **`pbip_type`** — ein Feld, ein Tool. Ebenso `allowed_pbip_types()` /
`forbidden_pbip_types()`. Die Architektur ist richtig und lebt; sie ist nur
**einzieltauglich**.

**Schlussfolgerung (korrigiert):** Es fehlt kein Intent-Katalog, keine Library und kein
Substitutionsprinzip. Es fehlt (a) **eine** Autorität für das *Typ*-Vokabular, (b) die
**Mehrzielfähigkeit** der vorhandenen Library (`pbip_type` → Mapping je Konnektor) und
(c) die Ausweitung der **bereits existierenden** Emitter-Bindung auf alle Konnektoren.

---

## 3. Architektur — vier Schichten, klare Zuständigkeit

```
UseCase_Bracket.yaml            ── WAS entschieden werden soll (Golden Thread)
        │
        ▼
[1] INTENT-KATALOG              ── analytische Absicht als Atom
        │                          "Abweichung gegen Plan", "Fluss zwischen Stufen"
        ▼
[2] LAYOUT-SYSTEM (Plugin)      ── Notation + Regelwerk: IBCS zuerst, weitere möglich
        │                          entscheidet Encoding, Semantik, Dichte, Titel
        ▼
[3] DESIGN-TOKENS (DTCG)        ── Farbe, Typo, Raster, Abstände als JSON
        │
        ▼
[4] KONNEKTOR je Ziel-Tool      ── Boden garantiert, Decke frei
        ├── Power BI / PBIR
        ├── Vega-Lite            (statisch/print, notationstreu)
        ├── HTML/React (Evidence.dev, visx)
        └── DOCX/PDF
```

### 3.1 Warum die Absicht das Atom ist — und nicht der Visualtyp

Ein Sankey ist **kein besserer Balken**. Er beantwortet dieselbe Frage anders. Solange
der Visualtyp deklariert wird, lässt sich „mindestens dasselbe Niveau **oder besser**"
nicht ausdrücken: `bar_chart` in Power BI und `sankey` in Vega sind zwei Deklarationen,
zwischen denen keine Ordnung besteht.

Mit der Absicht als Atom entsteht die Ordnung: *Absicht* → {Boden-Darstellung je Tool,
optionale bessere Darstellung}. Das ist zugleich die IBCS-Logik — **EXPRESS** („choose
proper visualization") ist bei IBCS eine Regel *über* der Darstellung, nicht die
Darstellung selbst.

Die Registry hat dafür bereits eine Spalte: `Semantic Purpose`. Heute Prosa, morgen
Schlüssel. **Kein neues Konzept — ein vorhandenes Feld befördern.**

### 3.2 Warum Design Tokens und nicht eigene Formate

Das Problem „ein visuelles Vokabular, viele Ziel-Technologien" ist außerhalb BI gelöst.
Die **Design Tokens Community Group (W3C)** hat im Oktober 2025 ihre erste stabile
Spezifikation veröffentlicht (`v2025.10`): JSON-Format, plattformübergreifende
Übersetzung, First-Class-Support in Style Dictionary 4.

Official-First (D-156) gilt hier genauso wie bei Microsoft-Tooling: **kein Eigenbau, wo
ein Standard existiert.** Die vorhandenen `tokens/*.yaml` (color_semantics, typography,
layout_grid) werden auf DTCG-Form gebracht, nicht ersetzt.

### 3.3 Zuständigkeit je Tool — und die Begründung

| Tool | Zuständig für | Warum genau dieses | Decke (belegt) |
|---|---|---|---|
| **Power BI / PBIR** | governte Enterprise-Reports, Self-Service, Row-Level-Security, Fabric-Integration | einziges Ziel mit Tenant-Governance + Direct Lake; der Kunde arbeitet darin weiter | **native Visuals** — IBCS wird damit *nachgebaut*, nicht zugekauft (s. §3.4). Wo native Visuals an eine Notationsgrenze stoßen, ist **SVG** der Ausweg, nicht ein Fremd-Visual. |
| **Vega-Lite** | notationstreue, statische Exhibits: Angebote, Anhänge, PDF, Print | deklaratives JSON auf Basis von Wilkinsons *Grammar of Graphics* (UW IDL: Heer, Satyanarayan, Moritz, Wongsuphasawat); portabel, versionierbar, in Python via Altair ansprechbar | statisch; volle Notationskontrolle, daher **das Ziel mit der höchsten IBCS-Treue** |
| **HTML/React** (Evidence.dev, visx) | interaktive Boutique-Politur, alles was PBI nativ nicht kann — Sankey, Small Multiples, Annotationen | keine Visual-Decke; eigener Renderer bereits als Ziel geführt (K5) | praktisch unbegrenzt; Preis = eigener Betrieb |
| **DOCX/PDF** | Deliverables (Meridian `core/docx_branding`) | vorhanden, gepflegt, tool-frei beim Kunden | statisch |

**Kernaussage für die Aufteilung:** Power BI ist nicht das beste Darstellungs-Tool — es
ist das beste **Governance- und Betriebs-Tool**. Deshalb bleibt es Pflichtziel, und
deshalb braucht es die anderen Ziele daneben, statt sie zu ersetzen.

### 3.4 Keine Fremd-Visuals — Festlegung und was daraus folgt

**IBCS wird in Power BI mit nativen Visuals nachgebaut.** Fremd-Visuals (Zebra BI und
andere) sind ausgeschlossen. Stößt eine Notation an die native Grenze, ist die
Eskalation **SVG**, und erst danach ein anderes Ziel-Tool.

*Korrektur der ersten Entwurfsfassung:* Dort stand, IBCS sei nativ „nicht erreichbar",
abgeleitet daraus, dass Zebra BI IBCS-zertifiziert ist. Der Schluss war unzulässig — eine
Zertifizierung belegt, dass *dieses* Produkt geprüft wurde, nicht dass andere Wege
ausscheiden. Der Beleg bleibt im Quellenverzeichnis, seine Aussage ist enger gefasst.

Die Festlegung ist nicht nur Geschmack, sie hat harte Vorteile, die zum
Kundenprodukt-Anspruch passen (POC-vs-Endprodukt, §3.3 Charter):

* **keine Lizenzkosten** und keine Lizenzprüfung beim Kunden,
* **keine Org-Freigabe** für Custom Visuals im Tenant — häufig ein Blocker in regulierten Umgebungen,
* **keine Fremdabhängigkeit** im Deliverable: das PBIP bleibt tool-frei, exakt wie die
  Scope-Grenze es verlangt (kein Kunde muss etwas installieren),
* **Export/Print/Mobile** verhalten sich wie bei Standard-Visuals.

**Erledigt 01.08.2026 — Regel erzwungen, Bullet Graph auf SVG.** Die Registry führte
**zwei** Fremd-Visual-Einträge (`bullet_graph` → „Enlighten Bullet Chart" in
`status_signal`, `alert_list_card` in `exception_list`), und das `AllowedVisual`-Dataclass
hatte mit `custom_visual_name` ein reguläres Feld dafür — der Verstoß war also nicht nur
möglich, sondern vorgesehen.

Umgesetzt:
* Beide Einträge → `pbip_type: tableEx` + **`render_mode: svg_measure`**, mit
  `verify:`-Marker auf L10 (der SVG-Weg selbst ist hier nicht messbar).
* `custom_visual_name` ist **aus dem Dataclass entfernt** und durch `render_mode`
  (`native` | `svg_measure`) ersetzt — was nicht ausdrückbar ist, kann nicht
  versehentlich zurückkehren.
* Neue `ThirdPartyVisualError`, geworfen **beim Laden** der Registry, nicht erst im Test:
  so kann keine Pipeline mit einem Fremd-Visual weiterlaufen, auch nicht die, die den Test
  nicht fährt.
* Zwei Tests: einer prüft den Wächter (mutationsgeprüft — bei deaktiviertem Wächter rot),
  einer die eingecheckte Registry.

**Zu verifizieren, nicht anzunehmen (Task L10):** Der native SVG-Weg in Power BI läuft
über DAX-erzeugte SVG-Data-URIs in einer Tabelle/Matrix (Spalte als *Image URL*
kategorisiert). Ich halte das für den etablierten Weg, habe es in dieser Umgebung aber
**nicht gemessen** — Desktop fehlt hier. L10 prüft es und hält Grenzen fest, statt sie
zu behaupten.

---

## 4. Layout-Systeme als Plugin — IBCS als erstes, nicht als einziges

Ein **Layout-System** ist ein benanntes, versioniertes Regelwerk, das aus einer Absicht
eine Notation macht. IBCS ist das erste, weil es das am besten belegte ist:

* **IBCS 1.2** (2022), 98 Regeln in sieben Gruppen — **SUCCESS**: *Say · Unify · Condense ·
  Check · Express · Simplify · Structure* — über drei Säulen (konzeptionell, perzeptuell,
  semantisch).
* Lizenz **CC BY-SA 4.0** — auf dieser Basis darf gebaut und weitergegeben werden. Das ist
  keine Nebensache: ein Layout-System, das nicht weitergegeben werden darf, taugt nicht als
  Kundenprodukt.
* Seit Juli 2024 Grundlage des ISO-Projekts **ISO/AWI 24896** „Standard notation for
  business reports". Wer heute IBCS baut, baut auf dem Kandidaten für den ISO-Standard.

**Warum trotzdem „Plugin" und nicht „IBCS fest verdrahtet":** IBCS ist eine
Notations-*Konvention* mit klarer Herkunft (Management-Reporting, Hichert). Für Kunden mit
eigenem Corporate-Design, für explorative Analytik oder für Storytelling-lastige
Deliverables gelten andere Regeln. Das System muss ein zweites Layout-System aufnehmen
können, ohne dass die Schichten 1, 3 und 4 angefasst werden. Genau das ist der Test für
den Schnitt — s. Task **L7**.

---

## 5. Tasks mit DoD und Modell-Zuordnung

**Modell-Zuordnung** folgt dem Komplexitäts-Prinzip aus `UMSETZUNGSPLAN_REPORT_EXZELLENZ.md` §3
und ergänzt es um zwei Dimensionen: **Haiku** für mechanische Massenarbeit und die Spalte
**Umgebung**, weil manche Tasks Werkzeug brauchen, das nur in VS Code verfügbar ist
(Power-BI-/Fabric-Skills, Desktop, `fab`).

| Umgebung | Bedeutung |
|---|---|
| **CC-Web** | headless Linux; hier verfügbar: `powerbi-report-author` 0.1.1, `pwsh`, `node`, MS-Learn-Docs-MCP |
| **VS Code** | zusätzlich Power-BI-/Fabric-Skills, Desktop, `fab`, Tenant-Zugriff |

---

### L0 · Vokabular-Autorität entscheiden **(Vorbedingung für alles)**

Eine der beiden Listen wird Single Source of Truth, die andere zeigt darauf.
Empfehlung: **`Abstract_Visual_Types.md`**, weil sie echte Unterscheidungen trifft
(`line_chart` vs. `area_chart` vs. `sparkline`; `bar_chart_horizontal` vs. `_column`),
die `trend_line`/`bar_chart` einebnen — und weil sie bereits `Semantic Purpose` führt,
das Schicht 1 braucht.

* **DoD:** Entscheidung in `docs/architecture/` als ADR; die unterlegene Liste enthält
  oben einen Pointer und keine eigenen Typdefinitionen mehr; `check_index.py --strict` grün.
* **Modell:** Opus · **Umgebung:** CC-Web · **Entscheider:** Flo

### L1 · Bestehende `information_blocks` als Intent-Layer bestätigen und schließen

**Kein neuer Katalog.** Die 9 Blöcke in `visual_registry.yaml` *sind* der Intent-Layer.
Zu tun ist nur, was fehlt: jeden der 34 Registry-Typen genau einem Block zuordnen und die
IBCS-Regelbezüge ergänzen.

* **DoD:** jeder Typ aus der SoT-Liste (L0) ist **genau einem** `block_id` zugeordnet;
  Test in `test_visual_library.py` schlägt fehl bei keiner oder mehrfacher Zuordnung;
  je Block `ibcs_rules[]` gefüllt; **kein** `intent_catalog.yaml` — die Datei wäre eine
  Parallelwelt zur Registry.
* **Modell:** Opus (Zuordnung ist Bedeutungsarbeit) · **Umgebung:** CC-Web

### L2 · Bracket-Vokabular normalisieren

`trend_line` → `line_chart`, `bar_chart` → `bar_chart_horizontal`/`_column`. Der **Slot**
entscheidet (`Main_3` = Ranking → horizontal), nicht der Name.

* **DoD:** 0 Bracket-Deklarationen außerhalb der SoT-Liste; Migration in **einem** Commit
  mit Mapping-Tabelle im Commit-Text; `tooling/tests/` + `products/` grün; Golden-Thread-Gate grün.
* **Modell:** Sonnet (mechanisch nach L0/L1-Muster) · **Umgebung:** CC-Web

### L3 · `AllowedVisual` mehrzielfähig machen — der eigentliche Kern

**Keine neuen Konnektor-Dateien.** Die Registry trägt heute `pbip_type` (ein Feld, ein
Tool). Sie bekommt stattdessen ein Mapping je Konnektor; `visual_library.py` folgt.
Rückwärtskompatibel: `pbip_type` bleibt als Alias auf den Power-BI-Eintrag lesbar, bis
alle Konsumenten umgestellt sind.

* **DoD:** `allowed_visuals[].targets.{powerbi,evidence,vega}` statt `pbip_type`;
  `allowed_pbip_types()` bleibt und delegiert; **Extensions** tragen `replaces:` auf eine
  Boden-Darstellung desselben Blocks; die drei Konsumenten (`visual_library.py`,
  `generator_core/ir/specs.py`, `test_template_manifest_alignment.py`) laufen unverändert
  grün; der `Enlighten Bullet Chart`-Eintrag ist entschieden (entfernt oder als benannte
  Ausnahme dokumentiert, §3.4).
* **Modell:** Opus (Kontrakt-Erweiterung an lebender Schnittstelle) · **Umgebung:** CC-Web

### L4 · Vorhandene Emitter-Bindung auf alle Konnektoren ausweiten

**Kein neuer Checker.** `test_pbir_mapping_is_library_sanctioned` prüft bereits, dass der
emittierte Visualtyp für seinen Informationsblock zugelassen ist — für Power BI. Dasselbe
Prinzip wird über die `targets` aus L3 parametrisiert.

* **DoD:** der Test läuft parametrisiert über alle registrierten Konnektoren; rot, wenn ein
  Block in einem Konnektor keine Darstellung hat; rot bei Extension ohne `replaces`; der
  Befund nennt Konnektor + Block + Use Case; in Stage 1 verdrahtet.
* **Modell:** Sonnet (Muster steht, Ausweitung ist mechanisch) · **Umgebung:** CC-Web

### L5 · Design-Tokens auf DTCG-Form

`tokens/color_semantics.yaml`, `typography.yaml`, `layout_grid.yaml` in DTCG-JSON
(`v2025.10`) überführen; Ableitung nach Power-BI-Theme-JSON und CSS-Variablen.

* **DoD:** `tokens/dtcg/*.tokens.json` valide gegen die DTCG-Spec; ein Generator erzeugt
  daraus PBI-Theme + CSS; Round-Trip-Test (Token → Theme → Token) verlustfrei für Farbe
  und Typo; Alt-YAMLs zeigen auf die Tokens.
* **Modell:** Sonnet · **Umgebung:** CC-Web

### L6 · Layout-System „IBCS" als Plugin implementieren

Regelwerk als Daten: welche Absicht wird nach IBCS wie notiert (Szenario-Schraffuren,
Abweichungsdarstellung, Skalenkonsistenz, Statement-Titel).

* **Vorher prüfen (Pflicht):** `design_rules.yaml` (108 Z.) und
  `tokens/boutique_craft_rubric.yaml` (30 Regeln/6 Dimensionen) enthalten bereits
  Regelsubstanz. Was dort steht, wird **erweitert/umgehängt**, nicht neu geschrieben; ein
  neues `rules.yaml` entsteht nur für das, was in beiden fehlt.
* **DoD:** je Regel ein Bezug auf ihre SUCCESS-Gruppe; die bereits erzwungenen Regeln
  (`title_policy`, `check_deviation_display`, `check_forbidden_charts`) zeigen **auf** die
  Daten statt eigene Konstanten zu führen; Abgrenzungstabelle „bestand schon / neu"
  im Commit; COM-002 rendert unverändert (Regressionstest).
* **Modell:** Opus · **Umgebung:** CC-Web

### L7 · Zweites Layout-System als Schnitt-Test

Ein minimales zweites System (z. B. „Corporate-Neutral": gleiche Absichten, andere
Notation/Palette) — **nur** um zu beweisen, dass der Schnitt trägt.

* **DoD:** Umschalten des Layout-Systems ändert Notation und Tokens, **nicht** Intent-Katalog,
  Konnektoren oder Gate; Diff zeigt Änderungen ausschließlich unter `layout_systems/`;
  beide Systeme rendern COM-002 fehlerfrei.
* **Modell:** Sonnet · **Umgebung:** CC-Web

### L8 · Layout in `from_aluca` binden (schließt C4)

Positionstabelle und Chrome-Slots aus `generator_core/ir/compiler.py` in den Quell-Adapter
ziehen — als **Leser** des governten Systems, nicht als kopierte Tabelle.

* **DoD:** `from_aluca` erzeugt für FIN-002 den vollen Slot-Satz mit Positionen aus
  `layout_grid`; `superversion.targets.pbir` rendert daraus einen Report, der
  `powerbi-report-author validate` mit **0 Errors** besteht; Änderung an `layout_grid.yaml`
  wirkt ohne Codeänderung; C4 im Meridian-Backlog abgehakt.
* **Modell:** Opus (PBIR-Komposition) · **Umgebung:** CC-Web (Validierung offiziell möglich)

### L9 · Vega-Lite-Konnektor (höchste IBCS-Treue)

* **DoD:** je Absicht eine Vega-Lite-Spec; COM-002 als statisches Exhibit-Set gerendert;
  Specs validieren gegen das Vega-Lite-Schema; visueller Abgleich gegen die IBCS-Regeln
  aus L6 dokumentiert.
* **Modell:** Opus (Encoding-Entscheidungen) · **Umgebung:** CC-Web

### L10 · Power-BI-Decke ausreizen — nativ, mit SVG als Eskalation

Je IBCS-Regel aus L6 messen, wie weit **native** Visuals tragen. Wo sie enden, den
SVG-Weg prüfen (DAX-erzeugte SVG-Data-URI, Spalte als *Image URL*) und dessen Grenzen
festhalten: Interaktivität, Tooltips, Barrierefreiheit, Export/Print/Mobile,
Performance bei vielen Zeilen. Fremd-Visuals sind kein Prüfgegenstand (§3.4).

* **DoD:** Tabelle *IBCS-Regel × {nativ · SVG · gar nicht}* mit Beleg je Zeile; für jede
  SVG-Lösung eine notierte Nebenwirkung (mindestens Interaktivität und Export geprüft);
  kein Report behauptet IBCS-Konformität, die er nicht hat; Befunde fließen als Decke
  in L11.
* **Modell:** Opus · **Umgebung:** **VS Code** (Desktop-Augenschein; SVG-Verhalten im
  Service und beim Export ist headless nicht prüfbar)

### L11 · Fidelity-Scorecard je Ziel

Ergänzt die Boutique-Scorecard (K6/§9) um die Frage: *wie nah kommt dieses Ziel an die Spec?*

* **Vorher prüfen (Pflicht):** `tooling/report_quality/report_scorecard.py` existiert und
  bewertet bereits. L11 **erweitert** ihn um die Dimension Ziel-Tool — kein zweiter Scorer.
* **DoD:** Score je (Use Case × Ziel-Tool) mit Begründung je Abzug, im vorhandenen Scorer;
  in `make check` advisory, im Release-Gate hart; Trend über Zeit ablesbar.
* **Modell:** Sonnet · **Umgebung:** CC-Web

---

## 6. Reihenfolge und Abhängigkeiten

```
L0 ──▶ L1 ──▶ L2
        │
        ├──▶ L3 ──▶ L4            (Garantie: Boden/Decke)
        ├──▶ L5 ──▶ L6 ──▶ L7     (Notation: IBCS + Plugin-Beweis)
        └──▶ L8 ──▶ L9 / L10 ──▶ L11
```

**L0 blockiert alles.** Ohne eine Autorität für das Vokabular baut jede weitere Schicht
auf zwei widersprüchlichen Listen auf.

---

## 7. Nicht-Ziele (GOI-Pflicht: was bewusst nicht gemacht wird)

* **Keine Parallelwelt.** Jeder Task nennt oben, was er *erweitert*. Wo der erste Entwurf
  Neubau vorschlug (Intent-Katalog, Konnektor-Dateien, Gate), existierte das Bestehende
  bereits — die Tasks L1/L3/L4/L6/L11 sind deshalb als Erweiterung formuliert und tragen
  eine Vorher-prüfen-Pflicht. **Regel für die Umsetzung:** bevor eine neue Datei entsteht,
  ist zu belegen, dass keine bestehende sie aufnehmen kann.

* **Keine Vereinheitlichung des Aussehens** über Tools — das senkt die Decke aufs
  schwächste Tool.
* **Kein eigenes Token-Format** — DTCG existiert und ist stabil.
* **Keine eigene Notations-Erfindung** — IBCS ist belegt, lizenzkompatibel und
  ISO-Kandidat.
* **Kein LLM im Erzeugungspfad.** Modelle kuratieren und entscheiden (L0/L1/L6), sie
  rendern nicht. Determinismus ist Zielbild-Eigenschaft, nicht Nebenbedingung.
* **Keine Fremd-Visuals**, in keinem Ziel (§3.4). Eskalation bei Notationsgrenzen:
  nativ → SVG → anderes Ziel-Tool. Das hält das Deliverable tool-frei und den Tenant
  freigabefrei.

---

## 8. Quellen (geprüft 01.08.2026)

* IBCS — Standards, SUCCESS-Formel, Version 1.2, CC BY-SA: <https://www.ibcs.com/> ·
  <https://www.ibcs.com/resource/ibcs-standards-book/> ·
  <https://en.wikipedia.org/wiki/International_Business_Communication_Standards>
* Zebra BI als IBCS-zertifizierte Power-BI-Lösung (Rezertifizierung Dez. 2024):
  <https://www.ibcs.com/software/zebra-bi-for-power-bi/> ·
  <https://zebrabi.com/zbi_blog/zebra-bi-for-power-bi-ibcs-certified/>
  — **belegt ausschließlich**, dass dieses Produkt geprüft wurde. **Kein** Beleg dafür,
  dass native Visuals IBCS nicht erfüllen können; der erste Entwurf hatte genau diesen
  Fehlschluss gezogen (s. §3.4).
* Design Tokens Community Group (W3C), erste stabile Fassung `v2025.10`:
  <https://www.designtokens.org/> ·
  <https://www.w3.org/community/design-tokens/2025/10/28/design-tokens-specification-reaches-first-stable-version/> ·
  <https://styledictionary.com/info/dtcg/>
* Vega-Lite — Grammar of Interactive Graphics (UW IDL): <https://vega.github.io/vega-lite/> ·
  <https://dl.acm.org/doi/10.1109/TVCG.2016.2599030> ·
  <https://en.wikipedia.org/wiki/Vega_and_Vega-Lite_visualisation_grammars>

**Nicht belegt und deshalb nicht als Grundlage verwendet:** ISO/AWI 24896 ist ein
*laufendes* Projekt (Start Juli 2024) — ein veröffentlichter ISO-Standard ist es nicht.
Die Aussage im Konzept lautet deshalb „Kandidat", nicht „Standard".

---

## 9. Ledger — Status (hier abhaken)

| Task | Status | Datum | Notiz |
|---|---|---|---|
| L0 Vokabular-Autorität | ⬜ offen | | Entscheidung Flo; Backlog **B4** |
| L1 Intent-Katalog | ⬜ offen | | |
| L2 Bracket-Normalisierung | ⬜ offen | | |
| L3 Konnektor-Vertrag | 🟢 **erledigt** | 2026-08-01 | `targets` + `replaces` in `AllowedVisual`; `pbip_type` bleibt Alias. Evidence-Boden von 0/9 auf 8/9 aus dokumentierten Mappings. Bekannte Lücke: `structural_mix`. |
| L4 Konnektor-Gate | 🟢 **erledigt** | 2026-08-01 | `check-floor` in der **bestehenden** Visual-Library-CLI (kein neuer Checker), in Stage 1 verdrahtet und dort sichtbar grün. Rot-Pfade getestet. **Bewusst offen:** die Parametrisierung des Emitter-Tests über mehrere Konnektoren braucht einen zweiten Emitter — heute gibt es nur `targets.pbir`. Kommt mit L9. |
| L5 DTCG-Tokens | ⬜ offen | | |
| L6 Layout-System IBCS | ⬜ offen | | |
| L7 Zweites System (Schnitt-Test) | ⬜ offen | | |
| L8 Layout in `from_aluca` | ⬜ offen | | schließt Meridian-**C4** |
| L9 Vega-Lite-Konnektor | ⬜ offen | | |
| L10 Power-BI-Decke | ⬜ offen | | **VS Code** |
| L11 Fidelity-Scorecard | ⬜ offen | | erweitert K6 |
