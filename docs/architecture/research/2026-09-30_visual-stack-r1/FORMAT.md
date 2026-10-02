# R1 Referenzkorpus — gemeinsames Ausgabeformat (alle vier Stränge)

Datei: `<strang>.yaml` in diesem Ordner. YAML-Liste, ein Eintrag je Muster/Regel:

```yaml
- id: <strang>-001            # ibcs | editorial | product | fabric
  pattern: kurzer Name des Musters/der Regel
  description: 1-3 Sätze, was genau (konkret, nicht "modern und clean")
  source:
    title: ...
    publisher: ...
    url: ...                    # direkte URL der Fundstelle
    date_published: YYYY-MM-DD | YYYY | unbekannt
    date_accessed: 2026-09-30
    kind: primary | secondary   # primary = Urheber des Standards/Systems selbst
  evidence: "wörtliches Zitat <= 25 Wörter"   # oder null, wenn nur Abbildung
  parameters:                   # messbare Werte, NUR wenn die Quelle sie nennt, sonst {}
    beispiel_stroke_px: 2
  applies_to:
    purposes: []                # aus: time_comparison, deviation_from_target, compare_categories,
                                # contribution_to_change, part_to_whole, correlation, flow_between_stages,
                                # driver_breakdown, distribution, evidence_detail, value_verdict
    idioms: []                  # aus: area_stacked bar_absolute bar_ranking bar_stacked boxplot bullet
                                # column_time decomposition_tree deviation_bar donut dumbbell histogram
                                # indexed_line kpi_card_bullet kpi_card_spark kpi_card_sparkbar line
                                # lollipop matrix_bullet matrix_delta_pill matrix_evidence matrix_sparkline
                                # sankey scatter slope small_multiples stacked_100 waterfall_buildup
                                # waterfall_pvm waterfall_variance  — oder NEU:<name>, wenn keine passt
    style_pack: <kandidat>      # z. B. ibcs, editorial, modern_product, fluent, swd, tufte
    layer: idiom | style | token | layout | interaction | selection_logic
  confidence: from_source | inferred   # inferred = eigene Ableitung, nicht in der Quelle belegt
```

Regeln: Primärquellen vor Sekundärquellen. Keine erfundenen URLs, Regel-IDs oder Zahlen —
was nicht belegbar ist, `confidence: inferred` oder weglassen. Zusätzlich `<strang>_summary.md`
(max. 60 Zeilen): wichtigste Erkenntnisse, Lücken, Widersprüche zwischen Quellen, offene Fragen.
