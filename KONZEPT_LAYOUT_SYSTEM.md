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

### 2.2 Was im **Nachbarrepo** existiert — die zweite unterschlagene Hälfte (02.08.2026)

§2.1 hat innerhalb von ALUCA gesucht. Das war zu eng. Der Zwilling `Freelancing/`
(Meridian) hat einen Teil dieses Konzepts **bereits entschieden und geliefert** — in
**ADR-0048** („Viz-Target-Adapter: Vega-Lite + Evidence/DuckDB-WASM + IBCS-Notations-Profil",
Status *Accepted & vollständig umgesetzt, 2026-06-24*, Phasen 1–3):

| Bestehend in `Freelancing/` | Was es ist | Folge für dieses Konzept |
|---|---|---|
| `core/report_design/ibcs.py` | **IBCS als Querschnitts-Profil**: reine Transform-Funktion `apply_ibcs(spec)` über eine Vega-Lite-Spec — *ein* Profil × *N* Adapter, bewusst **nicht** je Adapter dupliziert. Setzt Szenario-Notation AC/PL/FC/PY, Monochrom-Disziplin, Chart-Junk-Entfernung, Varianz-Semantik. `PROFILES = ("default", "ibcs")`. | **L6/L12 haben eine lebende Referenz-Implementierung.** Die Notations-Semantik muss nicht erfunden werden. |
| `core/pbi_engine/target/vegalite.py` | Der **Vega-Lite-Konnektor**. `to_specs()`, `emit()`, `emit_ibcs()`; 14 Visualtyp→Mark-Zuordnungen (`bar·line·area·arc·point·text`), expliziter `_SKIP` für Slicer/Tabelle/Matrix. | **L9 ist zu großen Teilen gebaut** — als *Bindungs*-Aufgabe, nicht als Neubau. |
| `core/pbi_engine/target/` + `evidence_report` | Selbst-hostbarer Report-Container (Evidence + DuckDB-WASM). „Statisch" heißt dort ausdrücklich **kein Server**, *nicht* keine Interaktivität. | Antwort auf die Interaktivitäts-Hälfte des Trilemmas (§3.4) — client-seitig, ohne Fremd-Visual. |
| `meridian/design/brand-tokens.schema.yaml` → `canvas_profiles` | **Der Ort für die Skalierungspolitik.** `powerbi_design_base` 1280×720 · `powerbi_production` 1920×1080 mit `font_size_delta_pt: +2` (begründet: FitToPage skaliert 0,71× herunter) · `web_fluid` mit Breakpoints. Konsumiert von `meridian/design/derivations/pbi_theme.py::_font_delta_for_profile`. | **L13 erweitert das** — es legt kein zweites Profil-Konzept an. |
| ADR-0048 §4, „Negativ / offen" | *„Viz-Adapter brauchen ein eigenes **Gate-Analogon** zu S1–S3 (Spec-Validität, Render-Smoke, IBCS-Konformität) — bewusst Folge-Arbeit."* | Das ist **L11**, dort bereits als offen benannt. L11 erbt damit einen Auftrag, statt einen zu erfinden. |

**Was das korrigiert.** Der Entwurf führte L9 („Vega-Lite-Konnektor") als Neubau und
L12 als reine Erhebung. Beides war ein Stück Parallelwelt: der Konnektor existiert, das
IBCS-Profil existiert, und die Architekturentscheidung *ein Profil × N Adapter* ist
getroffen und begründet. Die ALUCA-Aufgabe ist damit schmaler und ehrlicher benannt:
**die Absichts-Schicht dieses Repos an die vorhandene Meridian-Adapterkette binden** und
die Notations-Abdeckung dort **füllen**, wo sie messbar dünn ist.

**Und wo sie dünn ist, ist gemessen:** `_MARK` in `vegalite.py` kennt sechs Vega-Marks.
Die IBCS-eigenen Darstellungsformen — Wasserfall, Abweichungs-Nadel, Skalenband,
Struktur-/Nadel-Kombination — sind darin **nicht** enthalten. `apply_ibcs` färbt und
entrümpelt eine Spec korrekt; es erzeugt keine IBCS-Chart-*Typen*. Genau diese Lücke ist
der Inhalt von L12.

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

**🟢 Entschieden am 02.08.2026 (Flo): `visual_registry.yaml`.**
Festgehalten in [ADR-0018](docs/architecture/adr/0018-visual-vocabulary-single-authority.md).

Der ursprüngliche Entwurf empfahl hier `Abstract_Visual_Types.md` — *„weil sie echte
Unterscheidungen trifft … und bereits `Semantic Purpose` führt"*. **Die Empfehlung hat der
Messung nicht standgehalten**, und das ist der eigentliche Ertrag dieses Tasks:

| Quelle | Umfang | Erzwungen? |
|---|---:|---|
| `visual_whitelist.md` | 9 | nein — nennt sich verbindlich, kein Checker liest sie |
| `Abstract_Visual_Types.md` | 34 | nur im **deprecated** Prototyp; **24 der 34 von keinem Block verwendet** |
| `visual_registry.yaml` | 25 IDs / 10 Blöcke | **ja** — `visual_library.py`, `check-floor` in Stage 1, Emitter-Test |

Von den 25 gelebten Registry-IDs standen **7** in `Abstract_Visual_Types`; **18 existieren
nur in der Registry**. Sie zur Autorität zu erklären hätte 18 Renames an lebendem,
erzwungenem Code gekostet — damit sie zu einem Dokument passen, dessen 24 von 34 Einträgen
niemand benutzt. Und das Argument `Semantic Purpose` ist überholt: `information_blocks.purpose`
leistet dasselbe besser, mit erlaubten *und* verbotenen Visuals samt Begründung.

Dazu ein Beleg aus dem Betrieb desselben Tages: der neue Block `distribution_spread` ging
ohne `evidence`-Ziel ein und machte **zwei CI-Jobs rot**. Die Registry ist die einzige der
drei Listen, deren Verletzung den Build anhält — die anderen beiden haben geschwiegen.

* **Erledigt:** ADR-0018 geschrieben; `Abstract_Visual_Types.md` und `visual_whitelist.md`
  tragen oben einen Zeiger, ihre Typdefinitionen sind als Historie eingeklappt und
  ausdrücklich als nicht mehr geltend gekennzeichnet; `visual_slot_mapping.yaml` nennt die
  Registry als `authority:`; `check_index.py --strict` grün.
* **Bewusst nicht migriert:** die 24 unbenutzten Typen. Wer einen braucht, nimmt ihn als
  Block-Eintrag mit `source` und `targets` auf — mit Begründungspflicht.
* **Bleibt offen (L2):** die 20 Brackets deklarieren weiter Whitelist-Vokabular
  (`kpi_card` 20×, `trend_line` 18×, `bar_chart` 16×, `waterfall`/`line_chart`/
  `bar_chart_horizontal` je 4×). Sie sind nicht falsch — sie folgen der abgelösten
  Autorität. Die Entscheidung legt nur das **Ziel** der Normalisierung fest.

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

**🟢 Erledigt am 02.08.2026 — die DoD-Annahme war falsch, das Ziel wurde trotzdem erreicht.**

Der Task war als *„mechanisch nach L0/L1-Muster, Modell Sonnet"* geplant: 66 Deklarationen
umbenennen. **Gemessen ist er das nicht.** Das Alt-Vokabular steckt hartkodiert in
**zwölf** Dateien, darunter acht Validatoren, deren Literal-Mengen semantische Gruppen sind
(`_ZERO_BASELINE_VISUALS`, `_ABSOLUTE_BARS`, `_INTRINSIC_DEVIATION`). Eine übersehene Menge
hört still auf zu greifen — und `check_reference_lines` und `check_forbidden_charts` haben
**null** Tests, die ihren Verletzungspfad ausführen. Ein Rename ohne Netz hätte also
Prüfungen abgeschaltet, ohne dass etwas rot wird.

**Was stattdessen gebaut wurde — das Netz, das den Rename überhaupt sicher macht:**

1. **Ein Resolver statt vieler Listen** — `LEGACY_TO_REGISTRY` + `canonical_visual_id()` +
   `CHROME_TOKENS` in der **vorhandenen** `visual_library.py` (kein neuer Speicher; der
   Keim `ALUCA_VISUAL_BLOCK` war schon dort). Alt-Token dürfen leben, solange **eine**
   Stelle sagt, was sie bedeuten.
2. **Ein Gate über alle Vokabularquellen** —
   `test_visual_vocabulary_single_authority.py` (9 Tests) prüft Brackets, `VisualType`,
   drei Autoren-Schemas und die Übersetzungstabelle gegen die Registry.
3. **Der stille Fallback ist weg.** `_VISUAL_TYPE_MAP.get(vt, TREND_LINE)` →
   `UnknownVisualTypeError`.

**Drei Funde, die das Netz sofort zutage gefördert hat:**

| Fund | Bedeutung |
|---|---|
| **`bar_chart_horizontal` stand nie in `_VISUAL_TYPE_MAP`** | **Vier** Bracket-Deklarationen (Main_2/Main_3) sagen „horizontaler Balken" und wurden als **Trendlinie** kompiliert. Still, seit jeher. `line_chart` traf dasselbe — folgenlos, weil das Ziel zufällig stimmte. Genau diese Asymmetrie macht einen stillen Default gefährlicher als einen Abbruch: er ist manchmal harmlos und fällt deshalb nie auf. |
| **Autoren-Schemas erlaubten 8 nicht sanktionierte Typen** | `funnel`, `funnel_chart`, `stacked_bar`, `detail_table`, `kpi_card_hero`, `kpi_card_compact`, `status_tile`, `table_with_databars` — **0 davon in Gebrauch**, alle deklarierbar, alle wären in den Fallback gelaufen. Entfernt. |
| **`stacked_bar` war schema-erlaubt und registry-*verboten*** | `structural_mix` untersagt es begründet („Shows totals, not shares"). Ein Autoren-Schema, das erlaubt, was die Governance untersagt, ist keine Governance. Jetzt als eigener Test. |

**Der Rename ist danach durchgeführt — und die Vorbedingung stellte sich anders dar als
notiert.** `check_forbidden_charts` liest **PBIR** (`pieChart`, `donutChart`, `gauge`,
`treemap`), nicht Bracket-Token: er war nie betroffen. Das war meine Fehlzuordnung, nicht
ein Risiko. Gemessen blieben **sechs** Dateien mit Literalvergleich auf Bracket-Ebene —
davon ein weiterer Fehlalarm (`superset.py` ist nach `VisualType`-Enum verschlüsselt, sein
`"waterfall"` ist ein *Superset*-Chartname).

Statt Tests über die Bruchstelle zu legen, ist die Bruchstelle beseitigt: die Mengen
prüfen jetzt den **kanonisierten** Wert, nicht die Schreibweise des Tages. Ein Rename kann
sie damit nicht mehr ins Leere laufen lassen.

Rename: **66 Deklarationen in 21 Dateien** — `kpi_card`→`kpi_card_with_delta` (21×),
`trend_line`→`line_chart` (19×), `bar_chart`→`horizontal_bar_chart` (17×),
`bar_chart_horizontal`→`horizontal_bar_chart` (5×), `waterfall`→`waterfall_chart` (4×).
Die drei Autoren-Schemas führen jetzt kanonisches Vokabular.

**Vierter Fund beim Rename** — und der einzige, den kein grep, sondern erst ein Test fand:
`visual_builder.py` hatte einen **dritten** stillen Fallback (*„Unknown ux_visual_type
'waterfall_chart'; defaulting to lineChart"*). Er lag hinter einer `alias_map`, die mein
Literal-grep nicht sichtbar machte. Behoben in derselben `alias_map`.

**Beweis der Bedeutungsneutralität:** die Golden Snapshots und
`use_case_storylines.md` änderten sich in **ausschließlich** `visual_type`-Zeilen —
17 rein, 17 raus, keine Position, kein Measure, keine Kante. Bewusst neu erzeugt über die
jeweilige CLI, nicht von Hand.
* **Nebenwirkung, die zu C4 gehört:** die vier `bar_chart_horizontal`-Deklarationen
  kompilieren ab jetzt anders als bisher. Die eingecheckten `dist`-Reports stammen nicht
  aus einem sanktionierten Generator (Meridian-**C4**) — ihre Angleichung hängt an
  derselben offenen Architekturentscheidung.
* **Modell:** Opus (nicht mechanisch, s. o.) · **Umgebung:** CC-Web

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

### L9 · Vega-Lite-Ziel **anbinden** — nicht neu bauen

**Korrigiert am 02.08.2026 (§2.2).** Der Konnektor existiert: `core/pbi_engine/target/vegalite.py`
in `Freelancing/` (ADR-0048 Phase 1, geliefert 2026-06-24), inklusive `emit_ibcs()` und dem
Querschnitts-Profil `core/report_design/ibcs.py`. Ein zweiter Vega-Emitter in ALUCA wäre
exakt die Parallelwelt, die dieses Konzept vermeiden soll.

Die verbleibende Aufgabe ist die **Naht**: ALUCA besitzt die Absicht (`information_blocks`,
`targets`), Meridian besitzt den Emitter. Heute kennt `targets` nur `pbir`.

* **Vorher prüfen (Pflicht):** `core/pbi_engine/target/vegalite.py::_MARK` und `_SKIP` lesen —
  welche `information_block`-Absichten dort schon ein Mark haben und welche nicht. Erst
  danach entscheiden, ob eine Absicht eine *neue* Spec braucht oder nur eine Zuordnung.
* **DoD:** `targets.vegalite` in `visual_registry.yaml` für jeden Block, den `_MARK` trägt,
  mit Beleg; `check-floor --required vegalite` läuft und ist ehrlich (grün nur, wo eine
  Zuordnung wirklich existiert — Lücken bleiben rot statt gefüllt); der Emitter-Test aus L4
  ist über **beide** Konnektoren parametrisiert (das war dort als „kommt mit L9" notiert);
  COM-002 als Exhibit-Set gerendert; Specs gegen das Vega-Lite-Schema validiert.
* **Nicht im Scope:** neue Mark-Typen in Meridian. Fehlt ein Mark (Wasserfall, Nadel), ist
  das ein **L12**-Befund und wird dort mit Notationsvorschrift belegt, bevor jemand ihn baut.
* **Modell:** Opus (Encoding-Entscheidungen) · **Umgebung:** CC-Web (repo-übergreifend)

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

### L12 · IBCS-Visualkatalog von der offiziellen Quelle + Nachbau je Tool

**Vorziehen empfohlen.** Dieser Task hängt an keiner offenen Entscheidung und groundet
gleich drei andere: die Inhalts-Lücke aus L6 (CONDENSE/SIMPLIFY/STRUCTURE), den
Vega-Konnektor (L9) und die Power-BI-Decke (L10).

IBCS gibt seine Notation **visuell vor** — Szenario-Schraffuren, Abweichungsdarstellung,
Wasserfall-Konventionen, Skalenbänder. Das macht diesen Katalog zum billigsten von allen:
er muss nicht erfunden, sondern abgeschrieben und je Zielwerkzeug übersetzt werden.

Umfang:
1. **Erheben** — alle Visualtypen von der offiziellen Quelle (`ibcs.com`, Standard 1.2),
   mit ihrer Notationsvorschrift (Füllart, Achsen, Beschriftung, Vorzeichenkonvention).
2. **Zuordnen** — jeder Typ an einen bestehenden `information_block` der
   `visual_registry.yaml`. Wo keiner passt, ist das ein Befund, kein Anlass für einen
   neuen Block ohne Prüfung.
3. **Nachbauen recherchieren** — je Ziel: **Power BI nativ** (und wo nötig SVG, §3.4),
   **Vega-Lite**, **HTML/React**. Pro Typ und Ziel: geht es, wie, und was kostet es.

**Vorarbeit, die schon existiert — zuerst lesen, dann suchen.** ADR-0048 §2.3 (Freelancing)
benennt zwei OSS-Vorarbeiten ausdrücklich als „Referenz/Reuse prüfen statt blind neu":
**`ruqzuq/standard-charts`** und die **Deneb-Spec-Galerien**. Dazu kommt die gemessene
Ausgangslage aus §2.2: `apply_ibcs` liefert die *Notation* (Füllung, Farbe, Entrümpelung),
`_MARK` liefert **sechs** Vega-Marks — die IBCS-eigenen Chart-*Typen* (Wasserfall,
Abweichungs-Nadel, Skalenband) fehlen. Der Katalog beginnt also nicht bei null, und er
endet nicht bei „ist schon da".

**Entscheidungspunkt Deneb — offen, gehört zu Flo.** Deneb rendert Vega/Vega-Lite *innerhalb*
von Power BI und ist in der Praxis der meistgenannte Weg zu IBCS-naher Notation dort. Deneb
ist aber ein **Custom Visual** und fällt damit unter die Festlegung aus §3.4. Die Folge ist
eine echte Verzweigung, keine Geschmacksfrage:

| Weg | identisches Aussehen | native Interaktivität | Regel §3.4 |
|---|---|---|---|
| native PBI-Visuals | ✗ | ✓ | ✓ |
| Deneb (Vega in PBI) | ✓ | teilweise | **✗ Fremd-Visual** |
| SVG-Measure | ✓ | ✗ | ✓ |

Der Katalog **erhebt und dokumentiert** den Deneb-Weg als belegte Marktpraxis, **wählt ihn
aber nicht**. Solange §3.4 gilt, ist die Eskalationsleiter: nativ → SVG → anderes Zielwerkzeug.
Eine Aufweichung wäre eine Zielbild-Änderung und braucht eine explizite Entscheidung —
dieses Konzept trifft sie nicht.

* **Erst die Version klären (Vorbedingung: L14, s. §8.1/§10.5).** IBCS ist bei **2.0**,
  ausgerichtet auf **ISO 24896:2026**. Ein Katalog gegen 1.2 wäre bei Erhebung schon
  veraltet.
* **Bauvorschrift statt Lizenzbeschaffung (§8.2, verbindlich).** Der Katalog speichert
  **Regel-ID + Fundstelle + eigene Formulierung** — **nie** IBCS-Regeltext, **nie** ihre
  Abbildungen. So ist er kein abgeleitetes Werk, Share-Alike greift nicht, und er bleibt
  für Kunden-Deliverables frei verwendbar. Wer stattdessen transkribiert, macht jedes
  Deliverable, das den Katalog enthält, zu CC-BY-SA-Material.
* **Quellenlage, offen und benannt:** `actionablereporting.com`, `ibcs.com` und die meisten
  Fachquellen sind **in dieser Umgebung** nicht abrufbar — Ursache ist die Egress-Policy,
  nicht die Zielseite (§8). Dieser Task gehört damit in die **VS-Code-Umgebung**, in der
  ohnehin der Power-BI-Augenschein aus L10 stattfindet. Ein Suchauszug ist kein Beleg;
  hier ist das keine Sorgfaltsfrage, sondern eine Umgebungsgrenze.

* **DoD:** je IBCS-Visualtyp eine Zeile mit {Notationsvorschrift, Quelle/Abschnitt,
  `block_id`, Nachbau je Ziel ∈ {nativ · SVG · Extension · nicht möglich}}; die
  `targets`-Einträge aus L3 sind daraus ergänzt, wo belegt; jeder „nicht möglich"-Eintrag
  nennt den Grund; **keine Zuordnung ohne Beleg** — ein Typ ohne gesicherte
  Notationsvorschrift bleibt leer statt geraten.
* **Lizenz beachten:** IBCS steht unter **CC BY-SA 4.0**. Ein daraus abgeleiteter Katalog
  erbt die Share-Alike-Pflicht. Vor der Aufnahme in ein Kunden-Deliverable klären, welcher
  Teil abgeleitetes Werk ist und welcher eigene Übersetzungsleistung — **nicht** stillschweigend
  als reines Eigen-IP führen.
* **Modell:** Opus (Notation ist Bedeutungsarbeit) · **Umgebung:** Erhebung + Vega/HTML
  **CC-Web**; die Power-BI-Nachbau-Verifikation **VS Code** (Desktop-Augenschein, s. L10)

### L13 · Ein Koordinatensystem — Geometrie in Logical Units, Auflösung erst im Konnektor

Das Zielbild verlangt, dieselbe Seite proportional auf verschiedene Leinwandgrößen zu
bringen. Heute tut sie das nicht — und das ist gemessen, nicht vermutet.

**Befund 1 — zwei Basisleinwände, stillschweigend gemischt.** `layout_grid.yaml` rechnet
seine Logical Units gegen die **design_base 1280×720** (`computed.lu_w: 86.67`).
`_OVERVIEW_LAYOUT` in `tooling/generator_core/ir/compiler.py` führt Brüche der Leinwandbreite.
Setzt man beide zusammen, zeigt sich, gegen welche Leinwand die Brüche wirklich geschrieben
wurden — der linke Rand verrät es:

| Leinwand | `lu_w` | `Main_1` x | Spalte | `Main_1` colSpan |
|---|---|---|---|---|
| 1280×720 (design_base) | 86,67 | 21,4 px | **−0,10** | 12,21 / 4,03 |
| 1920×1080 (production) | 140,00 | **32,1 px** | **0,00** | 12,00 / **3,93** |

`0,0167 × 1920 = 32,1 px` — das ist exakt `outer_margin: 32`. Die Brüche sind gegen
**1920×1080** geschrieben, die LU-Rechnung gegen **1280×720**. Auf der Leinwand, für die
`layout_grid.yaml` rechnet, liegt der erste Slot bei Spalte **−0,10**, also außerhalb des
Rasters, und das KPI-Band ist mit 12,21 LU breiter als das Raster hat.

**Befund 2 — auch die richtige Leinwand geht nicht auf.** Selbst bei 1920 landet `Main_1`
auf **3,93** statt 4 Spalten. Ursache ist kein Rundungsfehler, sondern eine Inkonsistenz im
Modell: die Brüche skalieren mit der Leinwand, `gutter: 16` und `outer_margin: 32` sind
**absolute Pixel** und skalieren nicht mit. Eine Größe, die zur Hälfte mitskaliert, ist auf
keiner Leinwand außer der Autorenleinwand korrekt.

**Befund 3 — die 8px-Doktrin regiert die Abstände, nicht die Spaltenbreite.** Die
verbindliche Skala ist **INVARIANT A7** in `meridian/design/brand-tokens.schema.yaml`
(`base_unit: 8`, Stufen `xs 4 · sm 8 · md 16 · lg 24 · xl 32 · 2xl 48 · 3xl 64`,
ausdrücklich: *„No magic number spacing anywhere in the design"*). Die vier Abstände in
`layout_grid.yaml` halten sie ein — 8 · 16 · 32 · 40, alle Vielfache von 8.

Die **Logical Unit** hält sie nicht ein, und das ist kein Versäumnis, sondern eine
Eigenschaft der Konstruktion: sie ist ein **Restwert**, kein gewählter Wert.

```
lu_w = (1280 − 2·32 − 11·16) / 12 = 1040/12 = 86,67 px   ← nicht einmal ganzzahlig
lu_h = ( 720 − 2·32 − 11·16) / 12 =  480/12 = 40,00 px   ← 5×8, aber zufällig
```

Auf der Produktionsleinwand fällt auch der Zufall weg: `lu_w = 140` (17,5×8),
`lu_h = 70` (8,75×8).

**Geprüft, ob sich das durch Parameterwahl heilen ließe** — für welchen Außenrand aus der
8er-Skala wird die LU exakt 8er-rein (Gutter 16, 12×12):

| Leinwand | horizontal | vertikal |
|---|---|---|
| 1280×720 | `outer 24` → `lu_w = 88` (11×8) | `outer 32` → `lu_h = 40` |
| 1920×1080 | `outer 8` → `lu_w = 144` | **keine Lösung** |

Auf **keiner** der beiden Leinwände macht ein Außenrand *beide* Achsen 8er-rein — die
Achsen verlangen verschiedene Ränder. Bei 1920×1080 ist die Vertikale mit 12 Zeilen
überhaupt nicht lösbar (erst bei 9 Zeilen: `outer 8` → 104).

**Entscheidung (Flo, 02.08.2026): Weg (a).** Die 8px-Doktrin gilt weiterhin für **Abstände**
— dort ist sie erzwingbar und wird eingehalten. Sie gilt **nicht** für die Spaltenbreite;
die LU bleibt ein Restwert und darf krumm sein, **weil sie niemand sieht**: Position und
Spanne werden in LU geschrieben, Pixel entstehen nur im Konnektor.

Der Gegenweg (b) — 8er-reine LU erzwingen — ist **verworfen**. Er hätte eines von dreien
gekostet: die 12 Zeilen, die feste Leinwand oder den einheitlichen 16er-Gutter. Und er
hätte den Widerspruch nur verschoben: 12×12 auf 16:9 ist arithmetisch nicht 8er-rein zu
bekommen, jeder dafür verbogene Wert wäre die nächste Sonderregel. Ein Raster, das für
jede Leinwand eine eigene Ausnahme braucht, ist kein Raster.

Daraus folgt eine prüfbare Grenze, die L13 mitliefert: **Abstände** müssen auf der
8er-Skala liegen (das ist erzwingbar und wird geprüft), **abgeleitete LU-Maße** nicht (das
wäre nicht erfüllbar und würde nur zu geduldeten Ausnahmen führen).

**Die Festlegung.** Geometrie wird in **Logical Units** ausgedrückt — Position *und* Spanne,
und **inklusive** Gutter, Außenrand und Innenabstand. Pixel entstehen **ausschließlich** im
Konnektor, aus der Leinwand seines Zielprofils. Ein Bruch der Leinwandbreite kommt in keiner
Autorenquelle mehr vor. Damit ist proportionales Skalieren keine Nachrechnung, sondern eine
Eigenschaft des Modells: dieselbe Slot-Angabe ergibt auf 1280 und auf 1920 dieselbe Spalte.

**Der Ort dafür existiert bereits — es wird keiner angelegt.** `canvas_profiles` in
`meridian/design/brand-tokens.schema.yaml` (Freelancing) führt `powerbi_design_base`,
`powerbi_production` und `web_fluid` und trägt bereits eine begründete Skalierungsregel:
`font_size_delta_pt: +2` für Produktion, weil PBI FitToPage 0,71× herunterskaliert.
Konsumiert wird sie von `pbi_theme.py::_font_delta_for_profile`. **Gemessen ist damit auch
die Lücke:** die Profile skalieren heute **Schrift**, aber **keine Geometrie**. L13 schließt
genau diese Hälfte — im vorhandenen Profil-Mechanismus, nicht daneben.

Für Schriftgrade gilt derselbe Grundsatz und dieselbe Quelle: die dokumentierten additiven
Stufen aus `typography.yaml` bzw. der `font_size_delta_pt` des Profils — **kein** freier
Skalierungsfaktor. Ein Schriftgrad, der aus einer Multiplikation entsteht, ist nicht mehr
gegen die Lesbarkeitsuntergrenze prüfbar, die `typography.yaml` zusichert.

* **Vorher prüfen (Pflicht):** `preview/src/grid/slot-pos.ts` löst genau diesen Vertrag
  bereits korrekt auf — `left = outer + col*(lu-w + gutter)`, als CSS-`calc()` über
  Custom Properties, sodass ein Leinwandwechsel ohne Neuberechnung reflowt. **Das ist die
  Referenzimplementierung**; L13 zieht die Python-Seite darauf nach und erfindet keine
  zweite Formel. `validateSlot()` (Überlauf, 12×12) und `slotsOverlap()` sind dort
  ebenfalls schon vorhanden.
* **DoD:**
  1. `_OVERVIEW_LAYOUT` und `_DETAIL_LAYOUT` führen LU-Angaben (`col/row/cs/rs`) statt
     Leinwandbrüche; die Pixel-Auflösung liegt in **einer** Funktion, die die Formel aus
     `slot-pos.ts` spiegelt — durch einen Test gegen deren Werte belegt, nicht durch
     Nachlesen.
  2. `canvas_profiles` trägt die Geometrie-Auflösung (Leinwand + `gutter`/`outer_margin` je
     Profil), sodass ein Profilwechsel Spalten **erhält**. Beleg: derselbe Slot ergibt auf
     1280 und 1920 dieselbe Spalte und dieselbe Spanne — als Test, nicht als Zusicherung.
  3. Ein Check meldet **rot**, wenn eine Autorenquelle wieder Pixel oder Leinwandbrüche
     führt. Er wird in die **bestehende** Stage-1-Kette gehängt, nicht als neuer Runner.
  4. Derselbe Check erzwingt INVARIANT A7 dort, wo sie gilt: jeder **Abstand** in
     `layout_grid.yaml` (`gutter`, `outer_margin`, `internal_padding`, `zone_gap`) liegt
     auf der 8er-Skala. **Abgeleitete** LU-Maße sind davon ausdrücklich ausgenommen —
     mit der Begründung im Code, nicht nur hier, sonst „repariert" der nächste Durchgang
     die 86,67 zurück.
  5. Die beiden Befunde oben sind behoben und der Beweis steht als Testfall im Repo —
     `Main_1` ergibt **4,00**, nicht 3,93.
* **Fallstrick, benannt:** das ist eine **verhaltensändernde** Umstellung. Die erzeugten
  `dist`-Reports verschieben sich um wenige Pixel. Ein Drift-Test, der die alten Werte
  einfriert, würde die Korrektur als Fehler melden — die Referenzwerte werden in **einem**
  Schritt mitgezogen, mit der Verschiebung als Begründung im Commit.
* **Modell:** Opus (die Umstellung ist geometrisch, nicht mechanisch) · **Umgebung:** CC-Web
  (die Auflösung ist rechenbar; der Augenschein in Desktop gehört zu L10)

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

L12 ──┬──▶ L6   (füllt CONDENSE/SIMPLIFY/STRUCTURE mit echten IBCS-Regeln)
      ├──▶ L9   (Notationsvorschrift je Vega-Spec)
      └──▶ L10  (was nativ geht, was SVG braucht)
      ▲
      └─ startet SOFORT — keine Vorbedingung

L13 ──┬──▶ L8   (Layout in `from_aluca` — braucht ein tragfähiges Koordinatensystem)
      ├──▶ L9   (dieselbe Geometrie muss im zweiten Ziel ankommen)
      └──▶ L10  (SVG-Größen sind sonst gegen die falsche Leinwand gerechnet)
      ▲
      └─ startet SOFORT — keine Vorbedingung
```

**L0 blockiert alles.** Ohne eine Autorität für das Vokabular baut jede weitere Schicht
auf zwei widersprüchlichen Listen auf.

**L12 und L13 hängen an nichts** und sind die beiden einzigen Tasks, die *vor* der
L0-Entscheidung echten Boden schaffen: L12 die Notation, L13 die Geometrie. Beide
groundet dieselbe Beobachtung — was übersetzt werden soll, muss zuerst eindeutig
ausgedrückt sein.

---

### 5.1 L6 — warum drei SUCCESS-Gruppen leer BLEIBEN

Nach dem Schließen der Auszeichnungs-Lücke sind `CONDENSE`, `SIMPLIFY` und
`STRUCTURE` weiterhin mit 0 Regeln belegt. Das ist ein **Inhalts**-Befund, kein
Auszeichnungsfehler — und er wird nicht wegdefiniert.

Es gibt Regeln mit ähnlichem Ziel: `entity_ranking/max_entities_30s` (Miller,
Arbeitsgedächtnisgrenze) zielt auf Informationsdichte, `BC-LAYOUT-01/02`
(`Layout_Grid_System.md`) auf Gliederung, `entity_ranking/sort_by_deviation_not_alpha`
(Few) auf Ordnung. Sie als IBCS auszuzeichnen wäre **eine Fälschung der Herkunft**:
sie würden dann als „beim Wechsel des Layout-Systems austauschbar" gelten, obwohl
eine perzeptuelle Regel unabhängig von jeder Notation gilt. Genau diese Unterscheidung
ist der Zweck der Sicht.

Die Lücke schließt sich, wenn echte IBCS-Regeln aus diesen Gruppen aufgenommen werden
— Fachkuration gegen den Standardtext, nicht Umetikettierung. `test_empty_groups_are_a_content_gap_not_a_tagging_gap`
hält die Grenze fest und benennt beide Fälle im Fehlertext.

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

**Repo-interne Belege (02.08.2026, im Nachbarrepo `Freelancing/` gemessen — §2.2):**

* `docs/adr/0048-viz-target-adapters-vega-evidence-ibcs.md` — Accepted & umgesetzt
  2026-06-24; Phasen 1–3; §2.2 IBCS als Querschnitts-Profil, §2.3 Lizenz-Leitplanken +
  OSS-Vorarbeiten, §4 offenes Gate-Analogon
* `core/report_design/ibcs.py` · `core/pbi_engine/target/vegalite.py`
* `meridian/design/brand-tokens.schema.yaml` → `canvas_profiles` ·
  `meridian/design/derivations/pbi_theme.py::_font_delta_for_profile`
* `core/templates/page_templates/preview/src/grid/slot-pos.ts` (ALUCA) — die bereits
  korrekte LU→CSS-Auflösung

**Nicht belegt und deshalb nicht als Grundlage verwendet:**

* **`actionablereporting.com`** und die meisten Fachquellen — Abruf liefert **HTTP 403**.
  **Ursache korrigiert am 02.08.2026:** das ist *nicht* die Zielseite, sondern die
  **Egress-Policy dieser Umgebung**. Nachgewiesen über `$HTTPS_PROXY/__agentproxy/status`:
  `connect_rejected — gateway answered 403 to CONNECT (policy denial)` für
  `www.ibcs.com`, `www.designtokens.org`, `styledictionary.com`, `www.iso.org` und weitere.
  Erreichbar sind im Wesentlichen `github.com` und `learn.microsoft.com`.
  **Folge:** Recherche in dieser Umgebung liefert für die meisten Quellen nur
  Such-Auszüge, keinen Volltext. Für L12 heißt das: der Katalog ist hier **nicht**
  abschließend erhebbar und gehört in die VS-Code-Umgebung, die ohnehin für L10 vorgesehen
  ist. Das ist eine Umgebungsgrenze, kein Quellenmangel.

### 8.1 Korrektur: ISO 24896 ist veröffentlicht — und IBCS ist bei 2.0

Bis zum 02.08.2026 stand hier, ISO/AWI 24896 sei ein *laufendes Projekt* und kein
veröffentlichter Standard. **Das ist überholt.** Gemessen statt erinnert:

* **ISO 24896:2026 „Notation for business reporting"** ist am **11.06.2026** veröffentlicht
  worden, nach einstimmiger Annahme durch die beteiligten ISO-P-Member.
  <https://www.iso.org/standard/88366.html> · <https://www.ibcs.com/iso-24896/>
* Der Standard beruht auf den IBCS-Vorschlägen, **im Kern auf UNIFY und CHECK** der
  SUCCESS-Formel — nicht auf allen sieben Gruppen.
* **IBCS Standards 2.0** ist erschienen und **auf ISO 24896 ausgerichtet**, mit
  angepasster Terminologie aus der ISO-Redaktion. <https://www.ibcs.com/ibcs-version-2-0/>

**Was daraus folgt, und es ist nicht kosmetisch.** Dieses Konzept ist durchgängig gegen
**IBCS 1.2** geschrieben. L12 hätte einen Katalog gegen eine **abgelöste Fassung** erhoben
und die SUCCESS-Auszeichnung in L6 gegen eine überholte Terminologie geprüft. Die
Versionsfrage ist damit **Vorbedingung von L12**, nicht Nacharbeit.

### 8.2 Lizenz — welche wir brauchen, und warum vermutlich keine

Die Frage „welche Lizenz brauchen wir?" hat eine erfreuliche Antwort, wenn man die drei
Ebenen trennt, die hier gern zusammenfallen.

**Nachgeschlagen am 02.08.2026:** IBCS **2.0 steht weiterhin unter CC BY-SA 4.0**. Die
IBCS Association ist ein *not-for-profit* und veröffentlicht die Standards kostenlos unter
dieser Lizenz; 2.0 wurde am **11.06.2026** freigegeben — am selben Tag, an dem ISO 24896
erschien. Die Sorge aus dem ersten Entwurf, 2.0 könnte hinter die ISO-Bezahlschranke
wandern, ist damit **entkräftet**.
<https://www.ibcs.com/ibcs-version-2-0/> · <https://www.ibcs.com/creative-commons-faq/>
(*Such-Ebene* — `ibcs.com` selbst ist hier gesperrt, s. §8; mehrere konvergente Treffer
inkl. einer eigenen „Creative Commons FAQ"-Seite. In VS Code am Primärtext bestätigen.)

| Ebene | Was es ist | Brauchen wir eine Lizenz? |
|---|---|---|
| **Die Notationsregeln als Idee** — „Ist = gefüllt, Plan = Kontur, Forecast = schraffiert" | Ein Verfahren, kein Sprachwerk. Urheberrecht schützt den **Text** eines Standards, nicht die darin beschriebene Methode. | **Nein.** Unser `apply_ibcs()` implementiert Ideen, keinen Text. Deshalb steht in ADR-0048 §2.3 zu Recht „IBCS-Notation frei implementieren". |
| **Der IBCS-Standardtext und seine Abbildungen** | Sprachwerk unter **CC BY-SA 4.0** | **Nur wenn wir ihn übernehmen.** Dann ist unser Dokument ein abgeleitetes Werk und **erbt Share-Alike** — es muss selbst unter CC BY-SA stehen und weitergegeben werden dürfen. |
| **ISO 24896:2026** | ISO-Dokument, regulär **kostenpflichtig**, *nicht* CC | **Zum Lesen ja, eine gekaufte Einzellizenz** — ohne Weitergaberecht. Kein Copy-Paste ins Repo, in kein Deliverable. Das ist die **neue** Einschränkung, die es unter 1.2 nicht gab. |
| **Die Marke „IBCS®" / „IBCS Certified"** | Kennzeichenrecht, unabhängig vom Urheberrecht | Nie ein Zertifizierungs-Claim ohne Zertifizierung. Ausweisung bleibt **„IBCS-Notation (uncertified)"** (ADR-0048 §2.3). |

**Daraus folgt eine Bauvorschrift, keine Lizenzbeschaffung.** Der Katalog aus L12 wird so
gebaut, dass er **gar kein abgeleitetes Werk ist**: gespeichert werden **Regel-ID +
Fundstelle + unsere eigene Formulierung** — nie ihr Regeltext, nie ihre Abbildungen.
Dann greift Share-Alike nicht, nichts ist ansteckend, und der Katalog bleibt für
Kunden-Deliverables frei verwendbar. Ein Zitat mit Quellenangabe bleibt selbstverständlich
zulässig; die Grenze ist der **systematische Nachbau** des Standardtexts.

Umgekehrt gesagt — und das ist der teure Fehler, den diese Vorschrift verhindert: ein
Katalog, der IBCS-Regeltext transkribiert, macht **jedes Deliverable, das ihn enthält**,
zu CC-BY-SA-Material. Der Kunde dürfte es weitergeben. Das ist keine Kleinigkeit für ein
Beratungsprodukt.

**Kein Rechtsrat.** Die Grenze zwischen „eigene Formulierung" und „abgeleitetes Werk" ist
genau die Stelle, an der ADR-0048 §2.3 ohnehin einen **Rechts-Check vor client-facing
Verwendung** verlangt. Die Bauvorschrift oben hält uns mit Absicht weit von dieser Grenze
weg, statt sie auszureizen.

**Was offen bleibt:** das inhaltliche **Delta 1.2 → 2.0**. Die Suche nennt nur
„Terminologie-Angleichung an ISO" — das ist keine Delta-Liste, und darauf lässt sich keine
Regel-Migration stützen. Zu klären in L14.

---

## 10. Abgleich mit externen Quellen (02.08.2026)

Vier parallele Recherchen gegen das Konzept — mit dem ausdrücklichen Auftrag, es zu
*widerlegen*, nicht zu bestätigen. Zwei Vorbemerkungen zur Belastbarkeit:

1. **Die Umgebung begrenzt die Tiefe, nicht die Sorgfalt.** Volltext war fast nur aus
   `github.com` und `learn.microsoft.com` zu bekommen (§8). Alles andere sind
   Such-Auszüge. Wo unten „**belegt**" steht, wurde die Primärquelle gelesen; wo
   „*Auszug*" steht, nicht.
2. **Agentenbefunde sind nachgeprüft, nicht übernommen.** Zwei stellten sich beim
   Nachmessen anders dar als berichtet (unten markiert).

### 10.1 Was uns widerlegt oder korrigiert

| Befund | Beleg | Folge |
|---|---|---|
| **ISO 24896 ist veröffentlicht (11.06.2026), IBCS ist bei 2.0** | **belegt** (iso.org-Katalogeintrag + ibcs.com, über Suche bestätigt) | §8.1 neu. **Vorbedingung für L12** — der Katalog wäre gegen eine abgelöste Fassung erhoben worden. Lizenz von 2.0 offen. |
| **DTCG 2025.10 deckt Modes/Themes NICHT ab** — das liegt im separaten `resolver/`-Modul, das sich selbst als *„preview draft … should not be directly referred to or implemented at this time"* bezeichnet | **belegt** (Spec-Quelldateien im Repo `design-tokens/community-group`) | §3.2 überzeichnete die Reife. **L7** (zweites Layout-System) kann sich nicht auf einen fertigen DTCG-Mechanismus stützen. |
| **DTCG hat benutzerdefinierte Composite-Typen bewusst geschlossen** (PR #86: *„replace the mechanism for user-defined composite types with a set of pre-defined composite types"*); `strokeStyle` deckt nur Linienmuster, **keine Flächenfüllung** | **belegt** (Spec-Repo) | Unser `ibcsScenario` liegt außerhalb des vorgesehenen Erweiterungspfads — und `$extensions` ist laut Spec für **optionale** Metadaten gedacht, während unsere Szenario-Notation renderkritisch ist. **L5-Nacharbeit.** |
| **Unsere `information_blocks` haben drei echte Lücken**: *Distribution* (Histogramm/Boxplot), *Spatial* (Choropleth/Flow Map), *freie Correlation* (Scatter ohne Root-Cause-Rahmen) | **belegt** (FT Visual Vocabulary, Volltext aus GitHub) | **Vor L0** aufnehmen — sonst friert die Vokabular-Entscheidung eine bekannte Lücke ein. |
| **Deneb verliert mehr Interaktivität als unsere L12-Tabelle sagt**: Cross-Filter **oder** Slicing, nicht beides; Slicing nicht auf der Roadmap; Data-Point-Limit (Default 50) | *Auszug* + GitHub-Issue | Unsere §3.4-Ablehnung ist damit **besser** begründet als bisher formuliert — die Zeile „teilweise interaktiv" war zu freundlich. |
| **Vega-Lite ist EIN Renderer, nicht viele.** Wer Vega-Lite „einbettet" (Deneb, Kibana, Observable), bettet denselben Renderer ein — niemand übersetzt in die native Chart-Engine des Wirts | *Auszug*, mehrfach konvergent | §3.3 muss das trennen: unser `targets`-Modell ist echte Übersetzung und hat **kein** etabliertes Vorbild. Das ist Marktlücke *und* Risiko. |
| **Grammatiken haben „Cliffs"** — GoFish (MIT/IEEE VIS) benennt, dass gängige Grammar-of-Graphics-Implementierungen an Mosaics, Waffles, Ribbons scheitern | *Auszug* | Für **L9/L12**: Wasserfall/Nadel/Skalenband könnten in Vega-Lite an einer Ausdrucksgrenze scheitern, nicht nur an einem fehlenden `_MARK`-Eintrag. |
| **`cardVisual` ist von „Show Visuals as Tables" ausgenommen** — *„doesn't apply to the following visuals: slicers, cards, smart narrative, …"* | **belegt** (Microsoft Learn, Volltext) | Betrifft `status_signal → kpi_card_with_delta` — unser **nativer Default**, nicht den SVG-Weg. **Korrektur am Agentenbefund:** der Bericht ordnete das unserem SVG-Pfad zu; nachgemessen ist `bullet_graph` ein `tableEx`. Der Befund ist real, trifft aber die falsche Zeile. Gehört in **L10** als geprüfte Nebenwirkung. |
| **Der Faktor „FitToPage 0,71×" ist falsch etikettiert** | **belegt** (eigene Nachmessung) | `brand-tokens.schema.yaml:121` erklärt ihn korrekt als *ein Anzeigefall*: 1920×1080 auf einem 1366×768-Schirm — und `1366/1920 = 0,7115`. Zeile 205 macht daraus eine **Eigenschaft von FitToPage**. Das ist er nicht: auf einem breiteren Schirm ist der Faktor > 1. **Korrektur am Agentenbefund:** der Bericht hielt die Zahl für gänzlich unbelegt — sie ist belegt, nur als Beispiel, nicht als Konstante. Kommentar in Meridian nachschärfen (**E1**). |

### 10.2 Was standhält — und warum das mehr wert ist als Zustimmung

* **Weg (a) bei L13 ist der Industriestandard, nur explizit gemacht.** Material 3, Carbon,
  Bootstrap und Ant Design halten Abstände als feste 8er-Tokens und lassen Spaltenbreiten
  **relativ** (`%`, `fr`). Niemand benennt „Raster ≠ Abstands-Skala" als Entscheidung,
  **weil die Frage in CSS nie gestellt werden muss** — der `fr`-Resolver des Browsers löst
  sie zur Laufzeit. PBIR hat keinen solchen Resolver; unser Konnektor-Schritt übernimmt
  genau dessen Rolle. (*Auszug*)
* **`slot-pos.ts` hat einen externen Zwilling:** Grafana/`react-grid-layout` hält Position
  und Größe in Grid-Units und löst mit dokumentierter Formel in Pixel auf. Das Muster ist
  etabliert, nicht ausgedacht. (*Auszug*)
* **LU entspricht strukturell Androids `dp`, unser Schrift-Delta dessen `sp`** — die
  Trennung Layout-Einheit / Schrift-Einheit ist bei uns bereits da, nur unbenannt.
* **Kein gefundenes System modelliert „Absicht" als mehrzielfähiges Artefakt** mit
  Boden/Decke. Semantic-Layer-Werkzeuge (Cube, dbt, Malloy) geben die Darstellung
  ausdrücklich ab. Das ist ein Negativbefund — schwächer als ein Beleg, aber konsistent
  über drei unabhängige Recherchen.

### 10.3 Wo andere weiter sind — konkrete Übernahmekandidaten

| Vorbild | Was es kann | Für uns |
|---|---|---|
| **Style Dictionary 4** (Transforms / Formats / Platforms) | Ein neues Ziel = Config-Eintrag + Formatter, kein neues Skript | **L5** hat „Ableitung nach PBI-Theme/CSS" offen — genau das, wofür dieses Muster existiert. Official-First (D-156) zu Ende gedacht heißt: dahinter hängen, nicht nachbauen. |
| **Superset 6.0** | Zieht Tokens bis auf die **Chart-Ebene** eines BI-Tools durch (`echartsOptionsOverridesByChartType`, inkl. kategorialer Paletten) | Der einzige gefundene Präzedenzfall „Design Tokens bis ins Chart" in einem BI-Tool. Vorlage für die PBI-Theme-Ableitung. (*Auszug*) |
| **Draco / Draco2** (UW IDL) | Visualisierungs-Designregeln als **Constraints** (ASP/Clingo), maschinell prüfbar, Gewichte aus Wahrnehmungsexperimenten | Blaupause für das in ADR-0048 §4 offene **Gate-Analogon** (= **L11**): IBCS-Regeln als Prädikate gegen die *Spec* prüfen — deterministisch, ohne Rendering, ohne LLM. |
| **Tokens Studio `permutateThemes`** | Mehrere Achsen gleichzeitig (Marke × Modus × Dichte) | **L7**: „Layout-System × Canvas-Profil" ist dieselbe Mehrdimensionalität, bei uns noch nicht gedacht. (*Auszug*) |

### 10.4 Neu aufgenommen

* **L14 · IBCS-Version klären (2.0 / ISO 24896)** — Vorbedingung für L12 und L6.
  Vorbereitet in **§10.5**; die Lizenzfrage ist in **§8.2** bereits beantwortet.
  **DoD:** die zwölf Fragen aus §10.5 sind beantwortet **oder** ausdrücklich als ungeprüft
  markiert; maßgebliche Fassung festgelegt; Delta 1.2 → 2.0 als Liste oder als „nicht
  ermittelbar" notiert; §4/§8 dieses Konzepts nachgezogen; die Bauvorschrift aus §8.2 steht
  als harte Bedingung im L12-DoD. **Umgebung: VS Code** (`ibcs.com`/`iso.org` sind hier
  gesperrt). **Modell:** Opus (Lizenz- und Notationsfragen sind Bedeutungsarbeit).

### 10.5 L14 — vorbereitete Prüfliste für die VS-Code-Umgebung

Von hier aus ist alles getan, was ohne Zugriff auf `ibcs.com` und `iso.org` geht. Was
bleibt, ist Abarbeiten. Jede Zeile ist so formuliert, dass die Antwort **belegbar** ist —
und „nicht ermittelbar" ist eine zulässige Antwort, Raten nicht.

**A · Fassung und Delta** (blockiert L12 und L6)

| # | Frage | Wo nachsehen | Warum es uns trifft |
|---|---|---|---|
| A1 | Ist **2.0** die maßgebliche Fassung, oder wird 1.2 weiter gepflegt? | `ibcs.com/ibcs-version-2-0/`, `ibcs.com/ibcs-standards-1-2/` | Bestimmt, wogegen L12 erhebt. |
| A2 | Gibt es eine **Änderungsliste** 1.2 → 2.0 (Changelog, Vorwort, Migrationshinweis)? | Standardtext 2.0, Vorwort/Anhang | Ohne sie ist jede Regel-Migration geraten. |
| A3 | Sind die **SUCCESS-Gruppen** in 2.0 unverändert (SAY·UNIFY·CONDENSE·CHECK·EXPRESS·SIMPLIFY·STRUCTURE)? | 2.0, Gliederung | `layout_systems.py` prüft genau gegen diese sieben. Ändert sich die Gliederung, ändert sich unsere Abdeckungsrechnung. |
| A4 | Haben sich **Regelcodes** geändert (unsere belegten: `U4`, `E3`)? | 2.0, Regelverzeichnis | Diese Codes stehen als `source` in `visual_registry.yaml`. Stille Umnummerierung würde unsere Herkunftssicht falsch machen. |
| A5 | Was fordern **CONDENSE, SIMPLIFY, STRUCTURE** konkret — mit Regel-IDs? | 2.0, die drei Kapitel | Unsere drei leeren Gruppen. Der eigentliche Inhaltsauftrag von L6. |
| A6 | Ändert 2.0 die **Szenario-Notation** (AC/PL/FC/PY: Füllart, Deckkraft)? | 2.0, Notationskapitel | `color_semantics.yaml → ibcs_scenario` und `report_design/ibcs.py::_SCENARIO_FILL` hängen daran. |

**B · ISO 24896 — nur was wir wirklich brauchen**

| # | Frage | Wo nachsehen | Warum |
|---|---|---|---|
| B1 | Deckt ISO 24896 wirklich nur **UNIFY und CHECK** ab? | `iso.org/standard/88366.html` (Scope-Abschnitt ist frei einsehbar) | Wenn ja, betrifft der ISO-Teil genau die zwei Gruppen, die bei uns schon belegt sind — dann ist der Kauf **verzichtbar** und IBCS 2.0 (frei) reicht. **Diese Frage entscheidet über Kosten.** |
| B2 | Brauchen wir das ISO-Dokument überhaupt, oder genügt IBCS 2.0? | Ergebnis aus B1 | Erst kaufen, wenn B1 einen echten Mehrwert zeigt. |
| B3 | Falls gekauft: welche **Nutzungsbedingungen** (Einzelplatz, Weitergabe, Zitat)? | ISO-Lizenzbedingungen beim Kauf | Bestimmt, ob überhaupt jemand außer der lesenden Person etwas davon hat. |

**C · Lizenz — bestätigen, nicht neu klären** (Antwort steht in §8.2)

| # | Frage | Wo nachsehen | Status |
|---|---|---|---|
| C1 | Steht 2.0 unter **CC BY-SA 4.0**? | `ibcs.com/creative-commons-faq/`, `ibcs.com/terms-of-use/` | Auf Such-Ebene **bestätigt** — am Primärtext gegenlesen. |
| C2 | Verlangt die Namensnennung eine **bestimmte Form** (Wortlaut, Logo, Link)? | Creative-Commons-FAQ + Terms of Use | Bestimmt, wie unsere `source`-Felder und Deliverable-Fußnoten aussehen müssen. |
| C3 | Gibt es **Markenauflagen** zur Nennung von „IBCS®" in Produktkommunikation? | Terms of Use | Wir schreiben „IBCS-Notation (uncertified)" — prüfen, ob das ihren Auflagen genügt. |

**Nicht Teil von L14 — bewusst:** der Visualkatalog selbst. Das ist L12. L14 klärt nur,
**wogegen** L12 erhebt und **unter welchen Bedingungen**. Die Trennung ist Absicht: sonst
beginnt die Erhebung, bevor die Fassung feststeht — genau der Fehler, den §8.1 gerade
aufgedeckt hat.

### 10.6 Die drei fehlenden Absichten — entschieden am 02.08.2026

Der externe Abgleich (§10.1) nannte drei Absichten, die das FT Visual Vocabulary führt und
wir nicht: **Distribution, Spatial, freie Correlation**. Ein externer Katalog ist aber kein
Bedarfsnachweis — er ist ein *Chart-Auswahl*-Werkzeug, unsere Registry eine
*Report-Slot*-Taxonomie. Maßgeblich ist deshalb der eigene Korpus: **20 Brackets, 139
KPIs**, gemessen statt geschätzt.

**Ergebnis: eine von drei.**

| Absicht | Befund im eigenen Korpus | Entscheidung |
|---|---|---|
| **Distribution** | Dreifach unabhängig belegt: **FIN-001** *„Overdue AR aging buckets (0-30d, 31-60d, 61-90d, >90d) required for DSO diagnostic depth"* · **XD-001** *„Distribution of open-case age (share of cases open > SLA target, > 2× target)"* · **SCM-003** *„Averaging MAPE across SKUs hides bias and small-denominator distortion"* | ✅ **Aufgenommen** als Block `distribution_spread` |
| **Spatial** | **Kein einziger Fund.** Geo-Dimensionen sind reichlich da (`region` 174×, `plant` 142×, `location` 89×, `country` 34×) — aber ausschließlich als *Vergleichsdimension*, die `entity_ranking` bereits bedient. Die Suche nach echten Geo-Fragen (Route, Korridor, Nachbarschaft, Einzugsgebiet) ergab **null Treffer**; alle vermeintlichen `map`-Treffer waren `MAPE` (Mean Absolute Percentage Error) und „map to". | ❌ **Verworfen** |
| **freie Correlation** | 6× `scatter`, 13× `driver of`, 1× „vs. price" — der Zusammenhang zwischen zwei Kennzahlen erscheint im Korpus **immer** als Treiberfrage, nie als freie Exploration. `root_cause_context` deckt das bereits ab (`scatter_plot`, `condition: needs_root_cause = true`). | ❌ **Verworfen** |

**Warum die beiden Absagen keine Bequemlichkeit sind.** §3.1 sagt: das Atom ist die
**Absicht**, und ein Block existiert, um eine Entscheidung zu ermöglichen — nicht, um einen
Katalog zu vervollständigen. Eine Karte trägt nur dann etwas bei, wenn **Geographie selbst**
Bedeutung hat (Nachbarschaft, Entfernung, Route). Wo „Region" nur ein Etikett für einen
Vergleich ist, ist der sortierte Balken die **bessere** Antwort — Positionskodierung auf
gemeinsamer Skala schlägt Flächen- und Farbkodierung (S2, Cleveland & McGill). Und freie
Korrelation ist eine **Analyse**-Absicht; unser Produkt ist Reporting. Beide Absagen sind
umkehrbar, sobald ein Bracket eine echte Geo- oder Explorationsfrage stellt — der Befund
ist datiert und die Messung wiederholbar.

**Abgrenzung des neuen Blocks**, weil die Nachbarn nahe liegen:

| Block | Frage |
|---|---|
| `structural_mix` | „Woraus besteht das Ganze?" — Anteil, Summe = 100 % |
| `entity_ranking` | „Welche Einheit ist die schlechteste?" — Rang |
| **`distribution_spread`** | **„Wie breit streut es, und gibt es einen Schwanz?"** |

Die *Darstellung* kann in allen drei Fällen ein Balken sein — die **Absicht** ist es nicht.
Und nur die Absicht steuert, ob jemand den Schwanz überhaupt zeigt. Deshalb verbietet der
Block ausdrücklich das Sortieren nach Wert (`bucket_order_preserved`, Schweregrad **error**:
sortierte Bänder sind keine Verteilung mehr) und die Einzel-Mittelwertkarte — mit SCM-003
als Beleg, nicht als Meinung.

**Nebenbefund, der nicht versteckt wird.** Mit dem `targets.vegalite`-Eintrag des neuen
Blocks meldet `check-floor` jetzt einen zweiten Konnektor: **`vegalite` 1/10**. Das ist
keine Verschlechterung, sondern das erste Mal, dass die Lücke **sichtbar** ist, die L9
schließen muss. `powerbi` bleibt 10/10 und ist der einzige Pflicht-Konnektor — der Check
bleibt grün, sagt aber ab sofort die Wahrheit über den zweiten.
* **L1 — die drei Absichten sind entschieden (02.08.2026), s. §10.6.** Eine aufgenommen,
  zwei begründet verworfen. Damit ist L0 nicht mehr durch eine offene Vokabularfrage
  vorbelastet.
* **L5 Nacharbeit** — `ibcsScenario` spec-konform unterbringen; Style Dictionary als
  Build-Schicht prüfen statt nur DTCG zu emittieren.
* **L10 Nebenwirkung** — `cardVisual` ist von „Show Visuals as Tables" ausgenommen;
  gehört in die Tabelle der geprüften Nebenwirkungen.
* **L9 Risiko** — Ausdrucksgrenzen der Grammatik („Cliffs") vor dem ersten Mark prüfen.

---

## 9. Ledger — Status (hier abhaken)

| Task | Status | Datum | Notiz |
|---|---|---|---|
| **L14 IBCS-Version klären** | ⬜ **offen — zuerst, vorbereitet** | | **neu 02.08.** ISO 24896 seit 11.06.2026 veröffentlicht, IBCS bei **2.0**. Vorbedingung für L12 **und** L6. **Lizenzfrage beantwortet (§8.2):** 2.0 bleibt CC BY-SA 4.0, wir brauchen für die Implementierung **keine** Lizenz — nur die Bauvorschrift „Regel-ID + eigene Formulierung, kein Regeltext". ISO-Dokument nur kaufen, wenn Frage **B1** einen Mehrwert zeigt. Offen bleibt das **Delta 1.2 → 2.0**. Prüfliste mit 12 Fragen steht in **§10.5** — **VS Code**, Quellen hier gesperrt. |
| L0 Vokabular-Autorität | 🟢 **erledigt** | 2026-08-02 | **`visual_registry.yaml`** (ADR-0018). Die Konzept-Empfehlung `Abstract_Visual_Types.md` hat der Messung nicht standgehalten: 24 der 34 Typen unbenutzt, nur 7 der 25 gelebten IDs dort vorhanden — 18 Renames an erzwungenem Code für nichts. Beide `.md` sind Zeiger + eingeklappte Historie, `visual_slot_mapping.yaml` zeigt auf die Registry. Schließt Meridian-**B4**. |
| L1 Intent-Katalog | 🟡 teilw. | 2026-08-01/02 | **Vokabular-Lücke geschlossen (§10.6):** von den drei extern gefundenen Absichten ist **eine** aufgenommen — `distribution_spread`, dreifach im eigenen Korpus belegt (FIN-001 AR-Aging, XD-001 Case-Age, SCM-003 „averaging hides bias"). **Spatial** und **freie Correlation** begründet verworfen: null Geo-Fragen in 20 Brackets (alle `map`-Treffer waren `MAPE`), Korrelation erscheint immer als Treiberfrage und ist von `root_cause_context` gedeckt. Damit ist L0 nicht mehr vorbelastet. Restumfang von L1 (Bestätigung/Schließung der übrigen Blöcke) bleibt offen. |
| L2 Bracket-Normalisierung | 🟢 **erledigt** | 2026-08-02 | **DoD erfüllt: 0 Deklarationen außerhalb der SoT-Liste.** 66 Deklarationen in 21 Dateien umbenannt, drei Autoren-Schemas kanonisiert. Die DoD-Annahme „mechanisch“ war falsch — zuerst musste das Netz gebaut werden (Resolver in der vorhandenen `visual_library.py`, Gate mit 9 Tests, stiller `TREND_LINE`-Fallback durch harten Abbruch ersetzt), dann die sechs Literalvergleiche auf kanonisierte Werte umgestellt. **Vier Funde:** `bar_chart_horizontal` fehlte in `_VISUAL_TYPE_MAP` (4 Deklarationen kompilierten still als Trendlinie); 8 nicht sanktionierte Typen aus den Schemas entfernt; `stacked_bar` war schema-erlaubt und registry-**verboten**; `visual_builder.py` hatte einen **dritten** stillen Fallback hinter einer `alias_map` — den fand kein grep, sondern ein Test. **Zwei eigene Fehlalarme korrigiert:** `check_forbidden_charts` liest PBIR, `superset.py` ist enum-verschlüsselt — beide waren nie betroffen. Snapshot-Diff: ausschließlich `visual_type`, 17 rein / 17 raus. |
| L3 Konnektor-Vertrag | 🟢 **erledigt** | 2026-08-01 | `targets` + `replaces` in `AllowedVisual`; `pbip_type` bleibt Alias. Evidence-Boden von 0/9 auf 8/9 aus dokumentierten Mappings. Bekannte Lücke: `structural_mix`. |
| L4 Konnektor-Gate | 🟢 **erledigt** | 2026-08-01 | `check-floor` in der **bestehenden** Visual-Library-CLI (kein neuer Checker), in Stage 1 verdrahtet und dort sichtbar grün. Rot-Pfade getestet. **Bewusst offen:** die Parametrisierung des Emitter-Tests über mehrere Konnektoren braucht einen zweiten Emitter — heute gibt es nur `targets.pbir`. Kommt mit L9. |
| L5 DTCG-Tokens | 🟢 **erledigt** | 2026-08-01 | `design_tokens.py` **erzeugt** DTCG aus den YAMLs (37 Tokens, 10 Gruppen) — die YAMLs bleiben Autorenquelle, weil **8** Konsumenten sie lesen. Drift-Check in Stage 1. Ableitung nach PBI-Theme/CSS steht noch aus. |
| L6 Layout-System IBCS | 🟡 teilw. | 2026-08-01 | **Kein neuer Regelspeicher** — Herkunftssicht über die 3 vorhandenen. 69 Regeln: 15 IBCS / 21 Fremdstandard / 33 Hausregel. **Auszeichnungs-Lücke geschlossen:** alle 15 IBCS-Regeln tragen jetzt eine SUCCESS-Gruppe (SAY 1, UNIFY 7, CHECK 3, EXPRESS 4). **Inhalts-Lücke bleibt bewusst offen:** CONDENSE/SIMPLIFY/STRUCTURE unbelegt — s. u. |
| L7 Zweites System (Schnitt-Test) | ⬜ offen | | |
| L8 Layout in `from_aluca` | ⬜ offen | | schließt Meridian-**C4** |
| L9 Vega-Lite-Ziel anbinden | ⬜ offen | | **Umfang korrigiert 02.08.** — Konnektor existiert in Meridian (ADR-0048 Ph. 1, `vegalite.py` + `ibcs.py`). Aufgabe ist die Naht `targets.vegalite`, nicht der Neubau. |
| L10 Power-BI-Decke | ⬜ offen | | **VS Code** |
| L11 Fidelity-Scorecard | ⬜ offen | | erweitert K6; erbt das in ADR-0048 §4 offen benannte Gate-Analogon (Spec-Validität, Render-Smoke, IBCS-Konformität) |
| **L12 IBCS-Visualkatalog** | ⬜ **offen — vorziehen** | | Offizielle Quelle + Nachbau je Tool. Groundet L6-Inhaltslücke, L9 und L10 zugleich; hängt an keiner Entscheidung. **02.08. ergänzt:** OSS-Vorarbeiten aus ADR-0048 §2.3 zuerst prüfen (`ruqzuq/standard-charts`, Deneb-Galerien); gemessene Lücke = IBCS-Chart-*Typen* (Wasserfall/Nadel/Skalenband), nicht die Notation; **Deneb-Entscheid** dokumentiert, nicht getroffen (Fremd-Visual, §3.4); Quelle `actionablereporting.com` **403 → offen**. CC-BY-SA-Pflicht beachten. |
| **L13 Ein Koordinatensystem** | ⬜ **offen — vorziehen** | | **neu 02.08.** Geometrie in LU statt Leinwandbrüchen, Auflösung erst im Konnektor. Gemessen: `_OVERVIEW_LAYOUT` ist gegen **1920×1080** geschrieben, `layout_grid.yaml` rechnet gegen **1280×720** → erster Slot bei Spalte −0,10; und selbst bei 1920 ergibt `Main_1` **3,93** statt 4, weil `gutter`/`outer_margin` absolut bleiben. Erweitert `canvas_profiles` (Meridian) — die skalieren heute Schrift, keine Geometrie. Referenz: `slot-pos.ts`. Verhaltensändernd → `dist`-Referenzwerte mitziehen. **Entschieden 02.08. (Flo):** 8px-Doktrin (INVARIANT A7) gilt für **Abstände**, nicht für die abgeleitete LU — Weg (b) „8er-reine LU erzwingen" ist **verworfen**. Beleg: auf keiner der beiden Leinwände macht ein Außenrand beide Achsen 8er-rein; bei 1920×1080 ist die Vertikale mit 12 Zeilen gar nicht lösbar. |
