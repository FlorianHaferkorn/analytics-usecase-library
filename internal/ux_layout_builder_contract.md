# UX Layout → Power BI Builder: Contract & Implementation Spec

**Ziel:** Das Ergebnis des Layout-/Mockup-Tools wird 1:1 in den Power-BI-Report übernommen. Ein einziger Vertrag (`ux_layout_rules` im UseCase_Bracket) ist Quelle für sowohl Layout-Editor als auch Page-Scaffold-Generator.

---

## 1. Vertrag: Schema `ux_layout_rules`

**Autorität:** `tooling/ai/schemas/usecase_bracket.schema.json` (Abschnitt `ux_layout_rules`).

### 1.1 Struktur (Kurzreferenz)

| Pfad | Typ | Beschreibung |
|------|-----|--------------|
| `report_structure` | string | z. B. `2-Page-Lead` |
| `page_1_summary.title` | string | Seitentitel Summary |
| `page_1_summary.component_3s` | object | **Ein** KPI-Card (3-Sekunden-Layer) |
| `page_1_summary.component_3s.kpi_id` | string | North-Star-KPI (Pflicht) |
| `page_1_summary.component_3s.visual_type` | string | Semantischer Typ; für 3s nur `kpi_card` zugelassen |
| `page_1_summary.component_30s` | array | Diagnostik-Visuals (30-Sekunden-Layer); **Reihenfolge = Slot-Reihenfolge** |
| `page_1_summary.component_30s[].visual_type` | string | **Pflicht.** Erlaubte Werte siehe Abschnitt 1.2. |
| `page_1_summary.component_30s[].kpi_id` | string | Ein KPI (optional wenn `kpi_ids` gesetzt) |
| `page_1_summary.component_30s[].kpi_ids` | string[] | Mehrere KPIs für zusammengesetzte Visuals (z. B. Variance) |
| `page_2_execution.title` | string | Seitentitel Execution |
| `page_2_execution.component_300s` | object | Evidence-Tabelle + Action-Panel (kein `visual_type` pro Slot) |
| `page_2_execution.component_300s.evidence_grain` | string | Grain der Evidence-Tabelle (nicht `transaction_line`) |
| `page_2_execution.component_300s.evidence_columns` | string[] | Spalten für die Tabelle |
| `page_2_execution.component_300s.action_panel` | boolean | Action-Panel anzeigen |
| `page_2_execution.component_300s.payload_mode` | enum | `full` \| `summary` \| `minimal` |

### 1.2 Erlaubte `visual_type`-Werte (component_3s / component_30s)

Semantische Bezeichner, die der Builder in Power-BI-`visualType` übersetzt:

| `visual_type` (Bracket/Editor) | Power BI visualType | VisualBuilder-Methode |
|--------------------------------|---------------------|------------------------|
| `kpi_card` | `cardVisual` | `build_kpi_card` |
| `trend_line` | `lineChart` | `build_line_chart` |
| `waterfall` | `waterfallChart` | `build_waterfall` |
| `bar_chart` | `clusteredBarChart` | `build_horizontal_bar` |
| `hundred_percent_stacked_bar` | `hundredPercentStackedBarChart` | `build_stacked_bar` |
| `funnel` | `funnelChart` | `build_funnel` |

Pro Slot sind nur bestimmte Typen erlaubt (Whitelist in `tooling/ux_layout_editor/config/slot_to_visual_allowed.yaml`). Der Layout-Editor schreibt nur gültige Kombinationen; der Builder nutzt den gespeicherten `visual_type` direkt.

### 1.3 Slot-Reihenfolge (report_structure)

Für **2-Page-Lead** (Overview-Seite) gilt die Reihenfolge aus `tooling/ux_layout_editor/config/slot_order_by_report.yaml`:

- `component_30s[0]` → Slot **Trend** (Position im Layout)
- `component_30s[1]` → Slot **Variance**
- (später erweiterbar: Ranking, Mix, Funnel …)

Der Builder verwendet diese Reihenfolge, um **Position** (Layout) und **Typ** (aus `visual_type`) zu kombinieren.

---

## 2. Builder-Anpassungen (umgesetzt)

- **ConfigLoader:** `_apply_from_component_30s` setzt bei `waterfall` `needs_variance`; `get_page_config("overview")` liefert `component_3s` und `component_30s`.
- **VisualBuilder:** `build_by_ux_visual_type(ux_visual_type, position, name)` mappt ux-Typ → passende `build_*`-Methode.
- **PageBuilder:** `build_page_structure(..., component_30s=..., slot_order=...)` baut 30s-Visuals aus den exakten `visual_type`-Werten.
- **ScaffoldGenerator:** Übergibt `component_30s` und `slot_order` an den PageBuilder.

---

## 3. Datenfluss

```
Layout-Editor (WYSIWYG + Dropdowns)
    → speichert nur → UseCase_Bracket.yaml (ux_layout_rules)

ConfigLoader.get_page_config(use_case_id, "overview")
    → liest Bracket, liefert slots + component_3s + component_30s

PageBuilder.build_page_structure(slots, template, …, component_30s=..., slot_order=...)
    → für jedes component_30s[i]: Position = visual_positions[slot_order[i]],
      Typ = component_30s[i]["visual_type"] → VisualBuilder.build_by_ux_visual_type(...)

PBIPWriter
    → erhält page_structure mit den vom Bracket vorgegebenen Visual-Typen
```

Layout-Preview erfolgt im UX Layout Editor (Live-Preview mit echten Charts); HTML-Mockup wurde entfernt. Damit ist das Ergebnis des Layout-Editors dasselbe wie die Builder-Eingabe und erscheint 1:1 im Power-BI-Report.
