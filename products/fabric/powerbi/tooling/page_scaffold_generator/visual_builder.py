"""
Visual Builder

Builds Power BI visual placeholder structures.
"""

import logging
import re
import uuid
from typing import Dict, Any, Optional, List
from .layout_calculator import Position
from products.fabric.powerbi.tooling.schema_registry import VISUAL_SCHEMA as _VISUAL_SCHEMA


#: Obergrenze der Rolle Y bei `waterfallChart` — offizieller Katalog (Pin 0.1.1).
#: Als Konstante, damit sie neben dem Wert in targets/pbir.py auffindbar ist.
_WATERFALL_Y_MAX = 1


def textbox_objects(text: str, align: Optional[str] = None) -> Dict[str, Any]:
    """``visual.objects`` of a PBIR ``textbox`` carrying ``text`` as one paragraph.

    The text lives in ``general.paragraphs[].textRuns[].value`` (plain string, no PBIR
    literal quoting) -- the shape Power BI Desktop writes and the one ``adapters/pbip.py``
    already emits. The former ``text.text`` literal is not a textbox property: the official
    catalogue (``powerbi-report-author formatting describe-object textbox text``, Pin 0.4.0)
    lists only ``fontSize``/``fontFamily``/``color`` there, and ``validate`` reports
    ``PBIR_FORMATTING_PROP_UNKNOWN`` (gemessen 07.10.2026, 15 Header in dist/).
    """
    paragraph: Dict[str, Any] = {"textRuns": [{"value": text}]}
    if align:
        paragraph["horizontalTextAlignment"] = align
    return {"general": [{"properties": {"paragraphs": [paragraph]}}]}


def unquote_literal(value: str) -> str:
    """Plain text of a single-quoted PBIR string literal (``'It''s'`` -> ``It's``).

    Values without the surrounding quotes are returned unchanged, so callers can pass either.
    """
    if len(value) >= 2 and value.startswith("'") and value.endswith("'"):
        return value[1:-1].replace("''", "'")
    return value


class VisualBuilder:
    """Builds visual JSON structures for PBIP format."""

    VISUAL_SCHEMA = _VISUAL_SCHEMA
    
    def __init__(self):
        """Initialize visual builder."""
        self.z_order_base = 10000
        self.tab_order_base = 3000
    
    def _generate_visual_id(self) -> str:
        """Generate unique visual ID."""
        return uuid.uuid4().hex[:20]
    
    def _build_base_visual(
        self,
        visual_type: str,
        position: Position,
        tab_order: int = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build base visual structure. Use speaking name when provided (no hex ID)."""
        if tab_order is None:
            tab_order = self.tab_order_base
        visual_name = name if name is not None else self._generate_visual_id()

        return {
            "$schema": self.VISUAL_SCHEMA,
            "name": visual_name,
            "position": {
                "x": position.x,
                "y": position.y,
                "z": position.z if position.z != 10000 else self.z_order_base,
                "height": position.height,
                "width": position.width,
                "tabOrder": tab_order
            },
            "visual": {
                "visualType": visual_type,
                "drillFilterOtherVisuals": True
            }
        }
    
    def _measure_projection(self, measure_ref: str) -> Dict[str, Any]:
        """Single measure projection for Data role."""
        return {
            "field": {
                "Measure": {
                    "Expression": {"SourceRef": {"Entity": "_Measures"}},
                    "Property": measure_ref
                }
            },
            "queryRef": f"_Measures.{measure_ref}",
            "nativeQueryRef": measure_ref
        }

    def _column_projection(self, entity: str, property_name: str) -> Dict[str, Any]:
        """Single column projection for Data role (e.g. category axis)."""
        return {
            "field": {
                "Column": {
                    "Expression": {"SourceRef": {"Entity": entity}},
                    "Property": property_name
                }
            },
            "queryRef": f"{entity}.{property_name}",
            "nativeQueryRef": property_name
        }

    def build_kpi_card(
        self,
        position: Position,
        measure_ref: Optional[str] = None,
        name: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build KPI Card visual placeholder.
        
        Args:
            position: Position and size
            measure_ref: Optional measure reference (for placeholder)
            name: Optional visual name
            title: Optional display title (visual header)
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("cardVisual", position, name=name)

        # Add card-specific objects
        visual["visual"]["objects"] = {
            "layout": [
                {
                    "properties": {
                        "columnCount": {
                            "expr": {
                                "Literal": {
                                    "Value": "1L"
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        # Cards use "Data" role for measure aggregation
        projections = [self._measure_projection(measure_ref)] if measure_ref else []
        visual["visual"]["query"] = {
            "queryState": {"Data": {"projections": projections}}
        }

        return visual

    def build_narrative_card(
        self,
        position: Position,
        measure_ref: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a cardVisual bound to a single domain-level narrative/action DAX
        measure (Smart_Narrative -> "Narrative Text (<SUFFIX>)", ActionPanel ->
        "Active Actions Text (<SUFFIX>)") -- the measure reads the current page
        filter context and computes its own text, so the visual has no
        formatting objects of its own (verified against the real, committed
        dist/Smart_Narrative and dist/ActionPanel visual.json for COM-002 --
        R2.3-Fund follow-up, replacing the prior generator-synthesized textbox).

        Args:
            position: Position and size
            measure_ref: DAX measure name (e.g. "Narrative Text (COM)")
            name: Optional visual name

        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("cardVisual", position, name=name)
        visual["visual"].pop("drillFilterOtherVisuals", None)
        visual["visual"]["query"] = {
            "queryState": {"Data": {"projections": [self._measure_projection(measure_ref)]}}
        }
        return visual

    def build_kpi_cards_multi(
        self,
        position: Position,
        measure_refs: List[str],
        name: str = "KPI_Cards",
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build a single cardVisual with multiple measures (Power BI "new card" style).
        All KPIs that should appear as cards are shown in one visual.

        Args:
            position: Position and size
            measure_refs: List of measure references (DAX measure names)
            name: Visual name (default KPI_Cards)
            title: Optional display title (visual header)

        Returns:
            Visual JSON structure with multiple Data projections
        """
        visual = self._build_base_visual("cardVisual", position, name=name)
        visual["visual"]["objects"] = {
            "layout": [
                {
                    "properties": {
                        "columnCount": {
                            "expr": {
                                "Literal": {
                                    "Value": str(max(1, min(len(measure_refs), 6))) + "L"
                                }
                            }
                        }
                    }
                }
            ],
            # Auto display units: Power BI auto-scales large amounts to K / M / B.
            # cardVisual (new card) carries the callout in ``value`` (selector default),
            # property ``labelDisplayUnits`` (enum "0" = Auto). ``calloutValue`` is not in the
            # official catalogue for cardVisual (Pin 0.4.0: ``formatting list-objects cardVisual``;
            # ``formatting describe-property cardVisual value labelDisplayUnits``).
            "value": [
                {
                    "properties": {
                        "labelDisplayUnits": {"expr": {"Literal": {"Value": "0D"}}}
                    },
                    "selector": {"id": "default"}
                }
            ]
        }
        # Cards use "Data" role for measure aggregation
        projections = [self._measure_projection(m) for m in measure_refs] if measure_refs else []
        visual["visual"]["query"] = {
            "queryState": {"Data": {"projections": projections}}
        }
        return visual
    
    def build_kpi_delta_card(
        self,
        position: Position,
        measure_ref: str,
        name: str = "KPI_Delta",
        label: Optional[str] = None,
        higher_is_better: bool = True,
        font_size: str = "32D",
    ) -> Dict[str, Any]:
        """Single-value ``cardVisual`` whose callout is semantically coloured by the sign of a
        variance/delta measure (the "is it below plan?" signal). Per card.md a multi-value card
        formats every callout uniformly, so a per-metric colour requires the delta to be its own
        single-value card. Colour uses a diverging ``FillRule`` (linearGradient3) pinned at 0 —
        the verified inline encoding (conditional-formatting.md Type 1; validated against
        powerbi-report-author). ``higher_is_better`` red for below-plan / green for at-or-above;
        flipped for lower-is-better KPIs. ALUCA semantic tokens: red #A4262C, green #107C10,
        neutral #605E5C."""
        visual = self._build_base_visual("cardVisual", position, name=name)
        lo, hi = ("#A4262C", "#107C10") if higher_is_better else ("#107C10", "#A4262C")
        fill = {"solid": {"color": {"expr": {"FillRule": {
            "Input": {"Measure": {"Expression": {"SourceRef": {"Entity": "_Measures"}}, "Property": measure_ref}},
            "FillRule": {"linearGradient3": {
                "min": {"color": {"Literal": {"Value": f"'{lo}'"}}, "value": {"Literal": {"Value": "-0.02D"}}},
                "mid": {"color": {"Literal": {"Value": "'#605E5C'"}}, "value": {"Literal": {"Value": "0D"}}},
                "max": {"color": {"Literal": {"Value": f"'{hi}'"}}, "value": {"Literal": {"Value": "0.02D"}}},
                "nullColoringStrategy": {"strategy": {"Literal": {"Value": "'asZero'"}}},
            }}}}}}}
        objects = {
            "layout": [{"properties": {"columnCount": {"expr": {"Literal": {"Value": "1L"}}}}}],
            "value": [{"properties": {
                "fontSize": {"expr": {"Literal": {"Value": font_size}}},
                "fontColor": fill,
            }, "selector": {"id": "default"}}],
        }
        if label:
            _lit = str(label).strip().replace("'", "''")
            objects["label"] = [{"properties": {
                "show": {"expr": {"Literal": {"Value": "true"}}},
                "text": {"expr": {"Literal": {"Value": f"'{_lit}'"}}},
            }, "selector": {"id": "default"}}]
        visual["visual"]["objects"] = objects
        visual["visual"]["query"] = {"queryState": {"Data": {"projections": [self._measure_projection(measure_ref)]}}}
        return visual

    def build_line_chart(
        self,
        position: Position,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
        title: Optional[str] = None,
        category_entity: str = "dim_date",
        category_property: str = "CalendarYearMonth",
    ) -> Dict[str, Any]:
        """
        Build Line Chart visual placeholder (trend: category axis + measure(s)).
        
        Args:
            position: Position and size
            measures: Optional list of measure references (Y-axis)
            name: Optional visual name
            title: Optional display title
            category_entity: Table for X-axis (default dim_date)
            category_property: Column for X-axis (default CalendarYearMonth for monthly granularity)
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("lineChart", position, name=name)
        # Charts use Category (X-axis) and Y (values) roles so fields land in field wells, not in visual filter
        cat_proj = [self._column_projection(category_entity, category_property)] if (category_entity and category_property) else []
        y_proj = [self._measure_projection(m) for m in measures] if measures else []
        visual["visual"]["query"] = {
            "queryState": {
                "Category": {"projections": cat_proj},
                "Y": {"projections": y_proj},
            }
        }
        return visual
    
    def build_waterfall(
        self,
        position: Position,
        measures: Optional[list] = None,
        name: Optional[str] = None,
        category_entity: str = "dim_date",
        category_property: str = "Date",
    ) -> Dict[str, Any]:
        """
        Build Waterfall Chart visual placeholder.
        
        Args:
            position: Position and size
            measures: Optional list of measure references
            name: Optional visual name
            category_entity: Table for category axis (default dim_date)
            category_property: Column for category axis (default Date)
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("waterfallChart", position, name=name)
        cat_proj = [self._column_projection(category_entity, category_property)] if (category_entity and category_property) else []
        # Rolle Y nimmt bei `waterfallChart` GENAU EIN Measure — Obergrenze aus dem
        # offiziellen Katalog (`powerbi-report-author catalog describe waterfallChart`,
        # Pin 0.1.1), derselbe Wert, den der Superversion-Emitter seit jeher fuehrt
        # (`targets/pbir.py::_PLANS["waterfall"].primary_max == 1`).
        #
        # Gemessen am 03.08.2026: **11 der 17 dist-Reports** banden 2–5 Measures an Y
        # und meldeten deshalb `PBIR_ROLE_MAX_EXCEEDED` beim offiziellen Validator. Zwei
        # Emitter, einer mit Kappung, einer ohne — und ausgeliefert wurde der ohne.
        # Kein Pruefer sah das, weil `validate_bindings.py` die Bindung PRUEFT, nicht
        # ihre Kardinalitaet.
        # ABER: Kappen allein waere ein stiller Bedeutungsverlust, und das ist gemessen,
        # nicht befuerchtet. In OPS-001 stehen `OEE %`, `Availability %`, `Performance %`,
        # `Quality %` an Y — OEE IST das Produkt der drei; in COM-001LY steht die Bruecke
        # `Plan → Preis → Menge → Mix → Ist`. Wer auf die erste Measure kappt, bekommt
        # eine gueltige Datei, die die Zerlegung nicht mehr zeigt.
        #
        # Der Formfehler liegt eine Ebene hoeher: eine Varianzbruecke gehoert bei
        # `waterfallChart` NICHT als N Measures an Y, sondern als EINE Measure plus eine
        # **Category**, die die Schritte aufzaehlt. Das umzustellen ist eine
        # Modellierungsentscheidung am Bracket, keine des Emitters — deshalb wird hier
        # gekappt UND laut gemeldet, und die ausgelieferten Artefakte bleiben unangetastet,
        # bis die Entscheidung getroffen ist.
        y_alle = [self._measure_projection(m) for m in measures] if measures else []
        y_proj = y_alle[:_WATERFALL_Y_MAX]
        if len(y_alle) > _WATERFALL_Y_MAX:
            logging.getLogger(__name__).warning(
                "waterfallChart '%s': %d Measures an Rolle Y, erlaubt ist %d — %s wird "
                "emittiert, %s faellt weg. Das ist vermutlich eine Bruecke und gehoert "
                "als EINE Measure + Category-Schritte modelliert; Bracket-Slot pruefen.",
                name or "?", len(y_alle), _WATERFALL_Y_MAX,
                (measures or ["?"])[0], ", ".join(map(str, (measures or [])[1:])))
        visual["visual"]["query"] = {
            "queryState": {
                "Category": {"projections": cat_proj},
                "Y": {"projections": y_proj},
            }
        }

        # Add waterfall-specific objects
        visual["visual"]["objects"] = {
            "categoryAxis": [
                {
                    "properties": {
                        "innerPadding": {
                            "expr": {
                                "Literal": {
                                    "Value": "30L"
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        return visual
    
    def build_horizontal_bar(
        self,
        position: Position,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
        title: Optional[str] = None,
        category_entity: str = "dim_date",
        category_property: str = "Date",
    ) -> Dict[str, Any]:
        """
        Build Horizontal Bar Chart visual placeholder (category + measure(s)).
        
        Args:
            position: Position and size
            measures: Optional list of measure references
            name: Optional visual name
            title: Optional display title
            category_entity: Table for category axis (default dim_date)
            category_property: Column for category axis (default Date)
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("clusteredBarChart", position, name=name)
        cat_proj = [self._column_projection(category_entity, category_property)] if (category_entity and category_property) else []
        y_proj = [self._measure_projection(m) for m in measures] if measures else []
        visual["visual"]["query"] = {
            "queryState": {
                "Category": {"projections": cat_proj},
                "Y": {"projections": y_proj},
            }
        }
        visual["visual"]["objects"] = {
            "categoryAxis": [
                {
                    "properties": {
                        "innerPadding": {"expr": {"Literal": {"Value": "30L"}}}
                    }
                }
            ],
            # R1.6/R2.3-Fund: clusteredBarChart's real formatting object is
            # "labels", not "dataLabels" (R1.6 schema-verified this on COM-002's
            # Main_3; never ported back into the generator until now).
            "labels": [
                {
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "labelPosition": {"expr": {"Literal": {"Value": "'OutsideEnd'"}}}
                    }
                }
            ]
        }
        # R1.4/R2.3-Fund: clusteredGapSize/clusteredGapOverlaps only mean
        # something when multiple measures cluster per category; inert (and
        # dropped, per R1.4's COM-002 Main_3 precedent) for a single measure.
        if measures and len(measures) > 1:
            visual["visual"]["objects"]["layout"] = [
                {
                    "properties": {
                        "clusteredGapSize": {"expr": {"Literal": {"Value": "10L"}}},
                        "clusteredGapOverlaps": {"expr": {"Literal": {"Value": "false"}}}
                    }
                }
            ]
        return visual

    def build_clustered_column(
        self,
        position: Position,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
        title: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Clustered Column Chart for multi-measure decomposition (e.g. PVM components).

        No category axis — each measure becomes one bar.  Use this instead of waterfallChart
        when decomposing effects (Price/Volume/Mix) that do not have a time or entity dimension.

        Args:
            position: Position and size
            measures: List of measure references (Y-axis, one bar per measure)
            name: Optional visual name
            title: Optional display title

        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("clusteredColumnChart", position, name=name)
        y_proj = [self._measure_projection(m) for m in measures] if measures else []
        visual["visual"]["query"] = {
            "queryState": {
                "Y": {"projections": y_proj},
            }
        }
        # Data labels of cartesian charts are the object "labels"; "dataLabels" is unknown
        # for clusteredColumnChart (official catalogue, Pin 0.4.0), same as for the bar chart.
        visual["visual"]["objects"] = {
            "labels": [
                {
                    "properties": {
                        "show": {"expr": {"Literal": {"Value": "true"}}},
                        "labelPosition": {"expr": {"Literal": {"Value": "'InsideEnd'"}}}
                    }
                }
            ]
        }
        if title:
            self._apply_title(visual, title)
        return visual

    def build_stacked_bar(
        self,
        position: Position,
        measures: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build 100% Stacked Bar Chart visual placeholder (for Mix slot).
        
        Args:
            position: Position and size
            measures: Optional list of measure references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("hundredPercentStackedBarChart", position, name=name)
        # Charts use Category + Y roles (consistent with build_line_chart et al.)
        y_proj = [self._measure_projection(m) for m in measures] if measures else []
        visual["visual"]["query"] = {
            "queryState": {
                "Category": {"projections": []},
                "Y": {"projections": y_proj},
            }
        }

        # Add stacked bar chart-specific objects
        visual["visual"]["objects"] = {
            "valueAxis": [
                {
                    "properties": {
                        "end": {
                            "expr": {
                                "Literal": {
                                    "Value": "1D"
                                }
                            }
                        }
                    }
                }
            ],
            "categoryAxis": [
                {
                    "properties": {
                        "innerPadding": {
                            "expr": {
                                "Literal": {
                                    "Value": "30L"
                                }
                            }
                        }
                    }
                }
            ],
            "layout": [
                {
                    "properties": {
                        "stackedGapSize": {
                            "expr": {
                                "Literal": {
                                    "Value": "1L"
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        return visual
    
    def build_table(
        self,
        position: Position,
        columns: Optional[list] = None,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
        sort_by: Optional[Dict[str, str]] = None,
        top_n: Optional[int] = None,
        top_n_field: Optional[tuple] = None,
        highlight_rule: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Build Table visual placeholder.

        Args:
            position: Position and size
            columns: Optional list of (entity, property) for dimension columns, e.g. [("dim_date", "Date")]
            measures: Optional list of DAX measure names for value columns, e.g. ["Net Sales Amount"]
            name: Optional visual name
            sort_by: Optional {"measure": <DAX measure name>, "direction": "ascending"|"descending"}
                (R2.1 component_300s.sort_by, resolved to a measure name). Emits
                query.sortDefinition with isDefaultSort=true.
            top_n: Optional row limit (R2.1 component_300s.top_n). Requires top_n_field.
                Emits a filterConfig TopN filter ordered by sort_by's measure.
            top_n_field: Optional (entity, property) tuple identifying the row-grain
                dimension column the TopN filter targets (the most granular of
                `columns` -- see MANDATORY_SORT_RENDERED / MAX_EVIDENCE_COLUMNS in
                design_rules.yaml).
            highlight_rule: Optional {"measure": <DAX measure name>, "type": "data_bar"}
                (R2.1 component_300s.highlight_rule). "data_bar" is the only
                schema-verified formatting pattern (R1.3 precedent) -- uses the
                colorblind-safe blue/orange pair (ThemeDataColor 0/3) per
                Color_Semantics_Formatting.md rather than semantic.positive/negative.

        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("tableEx", position, name=name)
        projections = []
        if columns:
            for ent, prop in columns:
                projections.append(self._column_projection(ent, prop))
        if measures:
            for m in measures:
                projections.append(self._measure_projection(m))
        # Table visual always uses "Values" role (column well); "Data" would land in filter
        query: Dict[str, Any] = {"queryState": {"Values": {"projections": projections}}}

        if sort_by and sort_by.get("measure"):
            direction = "Descending" if str(sort_by.get("direction", "")).lower() == "descending" else "Ascending"
            query["sortDefinition"] = {
                "sort": [
                    {
                        "field": {
                            "Measure": {
                                "Expression": {"SourceRef": {"Entity": "_Measures"}},
                                "Property": sort_by["measure"],
                            }
                        },
                        "direction": direction,
                    }
                ],
                "isDefaultSort": True,
            }
        visual["visual"]["query"] = query

        # Add table-specific objects
        objects: Dict[str, Any] = {
            "grid": [
                {
                    "properties": {
                        "gridVertical": {
                            "expr": {
                                "Literal": {
                                    "Value": "false"
                                }
                            }
                        },
                        "gridHorizontal": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        },
                        "gridHorizontalWeight": {
                            "expr": {
                                "Literal": {
                                    "Value": "1L"
                                }
                            }
                        },
                        "rowPadding": {
                            "expr": {
                                "Literal": {
                                    "Value": "8L"
                                }
                            }
                        }
                    }
                }
            ]
        }

        if highlight_rule and highlight_rule.get("measure") and highlight_rule.get("type", "data_bar") == "data_bar":
            objects["columnFormatting"] = [
                {
                    "properties": {
                        "dataBars": {
                            "positiveColor": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 0, "Percent": 0}}}}},
                            "negativeColor": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 3, "Percent": 0}}}}},
                            "axisColor": {"solid": {"color": {"expr": {"ThemeDataColor": {"ColorId": 0, "Percent": 0.7}}}}},
                            "reverseDirection": {"expr": {"Literal": {"Value": "false"}}},
                            "hideText": {"expr": {"Literal": {"Value": "false"}}},
                            "totalMatchingOption": {"expr": {"Literal": {"Value": "1L"}}},
                        }
                    },
                    "selector": {"metadata": f"_Measures.{highlight_rule['measure']}"},
                }
            ]

        visual["visual"]["objects"] = objects

        if top_n and top_n_field and sort_by and sort_by.get("measure"):
            top_ent, top_prop = top_n_field
            order_direction = 2 if str(sort_by.get("direction", "")).lower() == "descending" else 1
            _topn_stem = re.sub(r"[^A-Za-z0-9]", "", sort_by["measure"])[:20]
            visual["filterConfig"] = {
                "filters": [
                    {
                        "name": f"TopN_{_topn_stem}_{name or 'Table'}",
                        "field": {
                            "Column": {
                                "Expression": {"SourceRef": {"Entity": top_ent}},
                                "Property": top_prop,
                            }
                        },
                        "type": "TopN",
                        "filter": {
                            "Version": 2,
                            "From": [
                                {
                                    "Name": "subquery",
                                    "Expression": {
                                        "Subquery": {
                                            "Query": {
                                                "Version": 2,
                                                "From": [
                                                    {"Name": "p", "Entity": top_ent, "Type": 0},
                                                    {"Name": "m", "Entity": "_Measures", "Type": 0},
                                                ],
                                                "Select": [
                                                    {
                                                        "Column": {
                                                            "Expression": {"SourceRef": {"Source": "p"}},
                                                            "Property": top_prop,
                                                        },
                                                        "Name": "field",
                                                    }
                                                ],
                                                "OrderBy": [
                                                    {
                                                        "Direction": order_direction,
                                                        "Expression": {
                                                            "Measure": {
                                                                "Expression": {"SourceRef": {"Source": "m"}},
                                                                "Property": sort_by["measure"],
                                                            }
                                                        },
                                                    }
                                                ],
                                                "Top": top_n,
                                            }
                                        }
                                    },
                                    "Type": 2,
                                },
                                {"Name": "p", "Entity": top_ent, "Type": 0},
                            ],
                            "Where": [
                                {
                                    "Condition": {
                                        "In": {
                                            "Expressions": [
                                                {
                                                    "Column": {
                                                        "Expression": {"SourceRef": {"Source": "p"}},
                                                        "Property": top_prop,
                                                    }
                                                }
                                            ],
                                            "Table": {"SourceRef": {"Source": "subquery"}},
                                        }
                                    }
                                }
                            ],
                        },
                        "howCreated": "User",
                        "isHiddenInViewMode": True,
                    }
                ]
            }

        return visual
    
    def build_matrix(
        self,
        position: Position,
        columns: Optional[list] = None,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Matrix (Pivot Table) visual placeholder.

        Args:
            position: Position and size
            columns: Optional list of (entity, property) for row grouping
            measures: Optional list of DAX measure names for value columns
            name: Optional visual name

        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("pivotTable", position, name=name)
        # Matrix uses Rows + Values roles
        row_proj = []
        if columns:
            for ent, prop in columns:
                row_proj.append(self._column_projection(ent, prop))
        val_proj = [self._measure_projection(m) for m in measures] if measures else []
        visual["visual"]["query"] = {
            "queryState": {"Rows": {"projections": row_proj}, "Values": {"projections": val_proj}}
        }

        # Add matrix-specific objects
        visual["visual"]["objects"] = {
            "grid": [
                {
                    "properties": {
                        "gridVertical": {
                            "expr": {
                                "Literal": {
                                    "Value": "false"
                                }
                            }
                        },
                        "gridHorizontal": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        },
                        "rowPadding": {
                            "expr": {
                                "Literal": {
                                    "Value": "8L"
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        return visual
    
    def build_scatter_plot(
        self,
        position: Position,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Scatter Plot visual placeholder.

        Args:
            position: Position and size
            measures: Optional list of measure references (first → X, second → Y)
            name: Optional visual name

        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("scatterChart", position, name=name)
        # Scatter plot uses X + Y roles
        x_proj = [self._measure_projection(measures[0])] if measures and len(measures) >= 1 else []
        y_proj = [self._measure_projection(measures[1])] if measures and len(measures) >= 2 else []
        visual["visual"]["query"] = {
            "queryState": {"X": {"projections": x_proj}, "Y": {"projections": y_proj}}
        }

        # Add scatter plot-specific objects
        visual["visual"]["objects"] = {
            "categoryAxis": [
                {
                    "properties": {
                        "gridlineShow": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        },
                        "gridlineStyle": {
                            "expr": {
                                "Literal": {
                                    "Value": "'dotted'"
                                }
                            }
                        },
                        "gridlineThickness": {
                            "expr": {
                                "Literal": {
                                    "Value": "1L"
                                }
                            }
                        }
                    }
                }
            ],
            "valueAxis": [
                {
                    "properties": {
                        "gridlineShow": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        },
                        "gridlineStyle": {
                            "expr": {
                                "Literal": {
                                    "Value": "'dotted'"
                                }
                            }
                        },
                        "gridlineThickness": {
                            "expr": {
                                "Literal": {
                                    "Value": "1L"
                                }
                            }
                        }
                    }
                }
            ],
            "markers": [
                {
                    "properties": {
                        "markerSize": {
                            "expr": {
                                "Literal": {
                                    "Value": "-10L"
                                }
                            }
                        },
                        "markerShape": {
                            "expr": {
                                "Literal": {
                                    "Value": "'circle'"
                                }
                            }
                        },
                        "borderShow": {
                            "expr": {
                                "Literal": {
                                    "Value": "false"
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        return visual
    
    def build_funnel(
        self,
        position: Position,
        measures: Optional[List[str]] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Funnel Chart visual placeholder.

        Args:
            position: Position and size
            measures: Optional list of measure references
            name: Optional visual name

        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("funnelChart", position, name=name)
        # Funnel uses Category + Y roles
        y_proj = [self._measure_projection(m) for m in measures] if measures else []
        visual["visual"]["query"] = {
            "queryState": {"Category": {"projections": []}, "Y": {"projections": y_proj}}
        }
        return visual
    
    def build_visual_for_slot(
        self,
        slot_name: str,
        position: Position,
        template: str,
        visual_slot_mapping: Dict[str, Any],
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build visual for a specific slot based on mapping rules.
        
        Args:
            slot_name: Slot name (trend, variance, ranking, etc.)
            position: Position and size
            template: Template type (T1, T2, T3, T4)
            visual_slot_mapping: Visual-to-slot mapping configuration
        
        Returns:
            Visual JSON structure
        """
        # Map slot names to visual builder methods
        slot_to_method = {
            'kpi_summary': self.build_kpi_card,
            'trend': self.build_line_chart,
            'variance': self.build_waterfall,
            'ranking': self.build_horizontal_bar,
            'mix': self.build_stacked_bar,  # 100% Stacked Bar
            'exceptions': self.build_table,
            'prescriptive': self.build_table,
            'root_cause': self.build_scatter_plot,
            'funnel': self.build_funnel,
            'detail_matrix': self.build_table  # Default to table, can be overridden
        }
        
        method = slot_to_method.get(slot_name)
        if not method:
            raise ValueError(f"Unknown slot: {slot_name}")

        return method(position, name=name)

    def _apply_title(self, visual: Dict[str, Any], title: Optional[str]) -> Dict[str, Any]:
        """Set the visual header (PBIR visualContainerObjects.title).

        Single quotes are escaped for the DAX string literal — titles now carry
        free-text exhibit statements (BC-NARR-01) that may contain apostrophes.
        """
        if title and str(title).strip():
            _lit = str(title).strip().replace("'", "''")
            visual["visual"]["visualContainerObjects"] = {
                "title": [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{_lit}'"}}}, "show": {"expr": {"Literal": {"Value": "true"}}}}}]
            }
        return visual

    def build_by_ux_visual_type(
        self,
        ux_visual_type: str,
        position: Position,
        name: Optional[str] = None,
        measures: Optional[List[str]] = None,
        title: Optional[str] = None,
        category_entity: Optional[str] = None,
        category_property: Optional[str] = None,
        statement_title: Optional[str] = None,
        subtitle: Optional[str] = None,
        format_spec: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Build a visual and render its header. Per ``title_policy`` the header is the governed
        **question** for a static report (always true), or the governed **message** when a value/
        dynamic-narrative guarantee backs it. ``subtitle`` carries the framed *expected finding*
        (the message as a hypothesis to verify) in the static case. ``title`` stays the label used
        for naming/tooltip. ``format_spec`` (visual_format_policy.FormatSpec), when supplied, applies
        the governed value-axis (opt-in; default None keeps emission byte-identical)."""
        visual = self._dispatch_ux_visual(
            ux_visual_type, position, name=name, measures=measures, title=title,
            category_entity=category_entity, category_property=category_property,
        )
        if statement_title:
            self._apply_title(visual, statement_title)
        if subtitle:
            self._apply_subtitle(visual, subtitle)
        if format_spec is not None:
            self._apply_value_axis(visual, format_spec)
        return visual

    def _apply_value_axis(self, visual: Dict[str, Any], format_spec: Any) -> Dict[str, Any]:
        """Apply the governed value axis (IBCS zero baseline) to a cartesian visual. A non-zero base
        exaggerates deltas, so bar/column families are pinned to 0 — see visual_format_policy. Only
        touches charts that already carry a categoryAxis (skips cards/tables)."""
        va = getattr(format_spec, "value_axis", None) or {}
        objs = visual.get("visual", {}).get("objects")
        if not va.get("zero_based") or not isinstance(objs, dict) or "categoryAxis" not in objs:
            return visual
        objs.setdefault("valueAxis", [{"properties": {"start": {"expr": {"Literal": {"Value": "0D"}}}}}])
        return visual

    def _apply_subtitle(self, visual: Dict[str, Any], subtitle: Optional[str]) -> Dict[str, Any]:
        """Set the visual sub-header (PBIR visualContainerObjects.subTitle) — the framed
        expected-finding, visually subordinate to the question header."""
        if subtitle and str(subtitle).strip():
            _lit = str(subtitle).strip().replace("'", "''")
            vco = visual["visual"].setdefault("visualContainerObjects", {})
            vco["subTitle"] = [{"properties": {"text": {"expr": {"Literal": {"Value": f"'{_lit}'"}}},
                                                "show": {"expr": {"Literal": {"Value": "true"}}}}}]
        return visual

    def _dispatch_ux_visual(
        self,
        ux_visual_type: str,
        position: Position,
        name: Optional[str] = None,
        measures: Optional[List[str]] = None,
        title: Optional[str] = None,
        category_entity: Optional[str] = None,
        category_property: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build visual from ux_layout_rules visual_type (round-trip from layout editor).
        Maps bracket/editor semantic types to Power BI visualType via existing build_* methods.
        Passes measures and title for data binding and header.

        GOVERNANCE NOTE (air-gapped fallback path): this mapping is INDEPENDENT of the idiom
        library — it is NOT routed through ``tooling/superversion/layer_tools/visual_idioms.py``,
        so the point-authority (governed native visualType), notation profiles and min_size do NOT
        apply here. The governed path is the superversion PBIR emitter; for governed chart choice
        use ``tooling/visual_library/resolve.py``. As a minimum floor this method warns when a
        deny-listed visual is requested (authority: ``visual_library/index.yaml: deny``).
        """
        import logging
        logger = logging.getLogger(__name__)
        normalized_type = (ux_visual_type or "").strip().lower()
        # Deny-list floor (soft): warn + name the sanctioned replacement, never silently pass a
        # governed-forbidden visual. A warning (not a hard error) so it cannot break an existing
        # bracket; the governed generator is where the deny-list is hard-enforced.
        _deny_ux = {
            "gauge": ("gauge", "bullet"), "gauge_chart": ("gauge", "bullet"),
            "pie": ("pie_gt_4", "donut (<=3 parts, IBCS 2.0 EX 2.1) or bar_chart"),
            "pie_chart": ("pie_gt_4", "donut (<=3 parts, IBCS 2.0 EX 2.1) or bar_chart"),
            "radar": ("radar", "bar_chart or line"), "spider": ("radar", "bar_chart or line"),
            "3d": ("three_d", "a 2D chart"), "three_d": ("three_d", "a 2D chart"),
            "funnel": ("color_as_decoration", "bar_chart (worst-first), or sankey for a true flow"),
        }
        _hit = _deny_ux.get(normalized_type)
        if _hit:
            logger.warning(
                "governance: ux_visual_type %r is deny-listed (%s); prefer %s. This air-gapped "
                "fallback does not enforce the idiom library — use the governed generator / "
                "resolve.py for point-authority chart choice.", ux_visual_type, _hit[0], _hit[1])
        alias_map = {
            "line_chart": "trend_line",
            "trend": "trend_line",
            "bar_chart_horizontal": "bar_chart_horizontal",
            "bar_chart_vertical": "bar_chart_vertical",
            "bar_chart_column": "clustered_column",
            "bar_chart": "bar_chart",
            "ranked_bar": "bar_chart_horizontal",
            # PVM decomposition: multiple Y measures, no category axis
            "clustered_column": "clustered_column",
            "pvm_column": "clustered_column",
            "pvm": "clustered_column",
            # Registry-Vokabular (ADR-0018). Ohne diese Zeilen fiel jede umbenannte
            # Deklaration durch alle Zweige in den `logger.warning`-Default und wurde
            # zur Trendlinie — dritter Fund derselben Fehlerklasse an diesem Tag, und
            # der einzige, den ein Test gefangen hat statt eines Menschen.
            "kpi_card_with_delta": "kpi_card",
            "horizontal_bar_chart": "bar_chart_horizontal",
            "column_chart": "bar_chart_column",
            "waterfall_chart": "waterfall",
            "scatter_plot": "scatter",
        }
        normalized_type = alias_map.get(normalized_type, normalized_type)
        measures = measures or []
        title = title or name
        if normalized_type == "kpi_card":
            return self.build_kpi_card(
                position, measure_ref=measures[0] if measures else None, name=name, title=title
            )
        if normalized_type == "trend_line":
            return self.build_line_chart(
                position, measures=measures, name=name, title=title,
                category_entity=category_entity or "dim_date",
                category_property=category_property or "CalendarYearMonth",
            )
        if normalized_type == "bar_chart":
            return self.build_horizontal_bar(
                position, measures=measures, name=name, title=title,
                category_entity=category_entity or "dim_org",
                category_property=category_property or "OrgName",
            )
        if normalized_type == "bar_chart_horizontal":
            return self.build_horizontal_bar(
                position,
                measures=measures,
                name=name,
                title=title,
                category_entity=category_entity or "dim_org",
                category_property=category_property or "OrgName",
            )
        if normalized_type == "bar_chart_vertical":
            # War bis 23.09.2026 build_line_chart -- ein Saeulendiagramm als Linie.
            from tooling.superversion.targets.pbir import plan_for
            return self.build_from_plan(plan_for("column_chart"), position, measures=measures, name=name,
                                        category_entity=category_entity, category_property=category_property)
        if normalized_type == "waterfall":
            # R2.3-Fund follow-up: category_entity/category_property were silently
            # dropped here (never forwarded to build_waterfall), so a Bracket's
            # category_field override on a waterfall component_30s entry had no
            # effect -- always fell through to build_waterfall's own default.
            return self.build_waterfall(
                position, measures=measures, name=name,
                category_entity=category_entity or "dim_date",
                category_property=category_property or "Date",
            )
        if normalized_type == "clustered_column":
            return self.build_clustered_column(position, measures=measures, name=name, title=title)
        if normalized_type in ("stacked_bar", "hundred_percent_stacked_bar"):
            return self.build_stacked_bar(position, measures=measures, name=name)
        if normalized_type == "funnel":
            return self.build_funnel(position, name=name)
        # Alles Uebrige ueber die governte Rollentabelle (tooling/superversion/targets/pbir.py).
        # Bis 23.09.2026 stand hier ein Rueckfall auf lineChart mit einer Log-Warnung. Gemessen
        # beim Ausrollen: FIN-002 Main_2 (`variance_bar`, eine Abweichungsbruecke) und OPS-001
        # Main_3 (`exception_table`, die Ausnahmeliste) erschienen als Liniendiagramm, und kein
        # Tor meldete es. Ein unbekannter Typ ist jetzt ein Fehler, kein anderes Visual.
        from tooling.superversion.targets.pbir import plan_for
        plan = plan_for(ux_visual_type) or plan_for(normalized_type)
        if plan is None or plan.visual_type == "cardVisual":
            raise ValueError(
                f"ux_visual_type {ux_visual_type!r}: weder hier noch in der governten "
                f"Rollentabelle (pbir._PLANS) bekannt -- kein Visual ist besser als ein falsches.")
        return self.build_from_plan(plan, position, measures=measures, name=name,
                                    category_entity=category_entity,
                                    category_property=category_property)

    def build_from_plan(self, plan, position: Position, measures: Optional[list] = None,
                        name: Optional[str] = None, category_entity: Optional[str] = None,
                        category_property: Optional[str] = None) -> Dict[str, Any]:
        """Ein Visual nach der governten Rollentabelle: Typ, Messrolle(n), Gruppierrolle.

        Tabellen (`tableEx`) laufen ueber build_table, damit sie eine Standardsortierung
        tragen -- eine Evidenztabelle ohne Sortierung ist ein Scorecard-Knock-out.
        """
        measures = measures or []
        cat = (category_entity or "dim_org", category_property or "OrgName")
        if plan.visual_type == "tableEx":
            return self.build_table(
                position, columns=[cat], measures=measures, name=name,
                sort_by={"measure": measures[0], "direction": "descending"} if measures else None)
        visual = self._build_base_visual(plan.visual_type, position, name=name)
        primaer = measures if plan.primary_max is None else measures[:plan.primary_max]
        state: Dict[str, Any] = {plan.primary_role: {"projections": [self._measure_projection(m) for m in primaer]}}
        if plan.secondary_role and len(measures) > len(primaer):
            state[plan.secondary_role] = {"projections": [self._measure_projection(measures[len(primaer)])]}
        if plan.dim_roles:
            state[plan.dim_roles[0]] = {"projections": [self._column_projection(*cat)]}
        visual["visual"]["query"] = {"queryState": state}
        return visual
