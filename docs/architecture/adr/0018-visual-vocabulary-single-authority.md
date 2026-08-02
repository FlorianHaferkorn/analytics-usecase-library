# ADR-0018 — `visual_registry.yaml` ist die einzige Autorität für das Visualtyp-Vokabular

| Feld | Wert |
|---|---|
| Status | **Accepted** (02.08.2026) |
| Entscheider | Florian Haferkorn |
| Kontext | `KONZEPT_LAYOUT_SYSTEM.md` Task **L0** (Vorbedingung für L1/L2) · Meridian-Backlog **B4** |
| Betrifft | `core/templates/page_templates/visual_registry.yaml` · `Abstract_Visual_Types.md` · `visual_whitelist.md` · `tokens/visual_slot_mapping.yaml` · `tooling/superversion/layer_tools/visual_library.py` |
| Bezug | ADR-0006 (Adapter-Vertrag) · ADR-0017 (Generator v2) |

## 1. Kontext

Das Repo führte **drei** Listen zulässiger Visualtypen. Gemessen am 02.08.2026:

| Quelle | Umfang | Erzwungen? |
|---|---:|---|
| `visual_whitelist.md` | 9 | **Nein.** Nennt sich „verbindlich für alle Templates und Übersetzer" — kein Checker liest sie. Trägt die `evidence:*`-Mappings. |
| `Abstract_Visual_Types.md` | 34 | Als `authority:` in `visual_slot_mapping.yaml` genannt; erzwungen nur in `visual_validator.py` im **deprecated** `page_scaffold_generator`, und dort nur als Verbotsliste. **24 der 34 Typen werden von keinem Block verwendet.** |
| `visual_registry.yaml` (`information_blocks`) | 25 `visual_id` in 10 Blöcken | **Ja.** `visual_library.py` (Laden bricht bei Fremd-Visuals hart ab), `check-floor` in der Stage-1-Kette, Emitter-Bindungstest. |

Dazu ein viertes, kleineres Enum: `_VISUAL_TYPE_MAP` (10 Typen) im IR-Compiler.

**Die Überlappung ist der entscheidende Befund.** Von den 25 gelebten Registry-IDs stehen
**7** in `Abstract_Visual_Types`; **18 existieren nur in der Registry** (`bullet_graph`,
`variance_bar`, `contribution_table`, `impact_effort_scatter`, `banded_column_chart`,
`kpi_card_with_delta`, …).

Der ursprüngliche Konzeptentwurf empfahl `Abstract_Visual_Types.md` — mit dem Argument, sie
treffe feinere Unterscheidungen und führe bereits eine Spalte `Semantic Purpose`. **Diese
Empfehlung hält der Messung nicht stand:** sie zur Autorität zu erklären hieße, 18 von 25
lebenden, erzwungenen IDs umzubenennen, damit sie zu einem Dokument passen, dessen 24 von
34 Einträgen niemand benutzt. Dokumentation schlüge laufenden Code. Und das Argument
`Semantic Purpose` ist überholt: `information_blocks.purpose` leistet dasselbe besser —
mit erlaubten *und* verbotenen Visuals samt perzeptueller Begründung je Eintrag.

**Ein Beleg aus dem laufenden Betrieb, nicht aus der Theorie.** Am 02.08.2026 wurde der
Block `distribution_spread` ohne `evidence`-Ziel eingecheckt. Zwei CI-Jobs wurden rot
(`test_known_second_connector_gap_is_exactly_recorded`). Die Registry ist die einzige der
drei Listen, deren Verletzung den Build anhält — die beiden anderen haben zu demselben
Vorgang geschwiegen.

## 2. Entscheidung

**`core/templates/page_templates/visual_registry.yaml` ist die alleinige Autorität für das
Visualtyp-Vokabular.** Sie wird *de jure*, was sie *de facto* bereits ist.

1. **`Abstract_Visual_Types.md` und `visual_whitelist.md` verlieren ihre Typdefinitionen**
   und tragen oben einen Zeiger auf die Registry. Sie bleiben als **historische Belege**
   erhalten (Herkunft der `evidence:*`-Mappings, die L3 in `targets` überführt hat), sind
   aber nicht mehr normativ.
2. **`visual_slot_mapping.yaml`** nennt die Registry als `authority:`, nicht mehr
   `Abstract_Visual_Types.md`.
3. **Ein Typ existiert nur als Eintrag eines `information_block`.** Es gibt keine
   freistehende Typliste mehr. Wer einen neuen Typ braucht, nimmt ihn mit `source`
   (perzeptuelle oder Standard-Begründung) und `targets` je Konnektor auf — oder er
   existiert nicht.
4. Die 24 unbenutzten Typen aus `Abstract_Visual_Types` werden **nicht** migriert. Ein
   Vokabular, das niemand verwendet, ist kein Vokabular, sondern eine Wunschliste.

## 3. Begründung

* **Erzwingbarkeit schlägt Vollständigkeit.** Eine Liste, die niemand prüft, ist keine
  Autorität — sie ist eine Meinung mit Dateinamen. Genau das war der Zustand: „es gibt
  heute keine lebende Instanz, die sagt, welche Visuals zulässig sind" (B4).
* **Der Typ ist nicht das Atom.** `KONZEPT_LAYOUT_SYSTEM.md` §3.1 setzt die **Absicht** als
  Atom. Eine freistehende Typliste widerspricht dem strukturell: sie erlaubt einen Typ ohne
  die Frage, die er beantwortet. Die Registry kann das nicht — dort *ist* ein Typ die
  Antwort auf einen Block.
* **Mehrzielfähigkeit lebt nur in der Registry.** `targets` (Konnektor → nativer Typ) und
  `replaces` (Boden-Fallback einer Extension) haben in den beiden `.md`-Dateien keine
  Entsprechung. Das Zielbild „ein Use Case, mehrere Viz-Tools" ist ohne sie nicht
  ausdrückbar.
* **Kein Rename-Risiko.** Die Gegenoption hätte 18 IDs, ihre Tests, die Emitter-Bindung und
  die `dist`-Artefakte angefasst — für keinen fachlichen Gewinn.

## 4. Konsequenzen

**Positiv:** eine Autorität, maschinell erzwungen; neue Typen können nicht ohne Absicht und
ohne Begründung entstehen; `check-floor` misst die Konnektor-Abdeckung gegen genau diese
Liste.

**Negativ / Folgearbeit:**

* **Die 20 Brackets benutzen bis heute Whitelist-Vokabular** — `kpi_card` (20×),
  `trend_line` (18×), `bar_chart` (16×), `waterfall` / `line_chart` /
  `bar_chart_horizontal` (je 4×). Gut die Hälfte aller Deklarationen ist für einen
  registry-basierten Übersetzer nicht auflösbar. Das ist **Task L2** und war vor dieser
  Entscheidung genauso nötig; die Entscheidung legt nur das Ziel der Normalisierung fest.
* `_VISUAL_TYPE_MAP` im IR-Compiler bleibt vorerst ein viertes Enum. Es ist heute
  Übersetzungstabelle, nicht Autorität — die Zusammenführung gehört zu L2, nicht hierher.
* Die 24 nicht migrierten Typen sind dokumentiert verloren. Wer einen davon vermisst, holt
  ihn über einen Block zurück — bewusst mit Begründungspflicht.

## 5. Alternativen, die verworfen wurden

* **`Abstract_Visual_Types.md` als Autorität** (die ursprüngliche Konzept-Empfehlung) —
  verworfen aus den Gründen in §1: 18 Renames an lebendem Code für ein Dokument mit 24
  toten Einträgen.
* **Registry als Autorität, `Abstract_Visual_Types.md` als nicht-normative
  Kandidatenliste** — erwogen und verworfen: eine zweite Liste, auch als „nicht normativ"
  deklariert, läuft erfahrungsgemäß wieder auseinander und wird beim nächsten Lesen erneut
  für verbindlich gehalten. Genau dieser Zustand wird hier beendet.
* **`visual_whitelist.md` als Autorität** — 9 Typen decken die 10 Blöcke nicht ab.
