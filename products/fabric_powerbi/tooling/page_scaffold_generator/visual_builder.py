"""
Visual Builder

Builds Power BI visual placeholder structures.
"""

import uuid
from typing import Dict, Any, Optional
from .layout_calculator import Position


class VisualBuilder:
    """Builds visual JSON structures for PBIP format."""
    
    VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json"
    
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
                "query": {
                    "queryState": {
                        "Data": {
                            "projections": []
                        }
                    }
                },
                "objects": {},
                "drillFilterOtherVisuals": True
            }
        }
    
    def build_kpi_card(
        self,
        position: Position,
        measure_ref: Optional[str] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build KPI Card visual placeholder.
        
        Args:
            position: Position and size
            measure_ref: Optional measure reference (for placeholder)
        
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
        
        visual["visual"]["visualContainerObjects"] = {
            "visualHeader": [
                {
                    "properties": {
                        "showTooltipButton": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        }
                    }
                }
            ]
        }
        
        # Add placeholder measure if provided
        if measure_ref:
            visual["visual"]["query"]["queryState"]["Data"]["projections"] = [
                {
                    "field": {
                        "Measure": {
                            "Expression": {
                                "SourceRef": {
                                    "Entity": "_Measures"
                                }
                            },
                            "Property": measure_ref
                        }
                    },
                    "queryRef": f"_Measures.{measure_ref}",
                    "nativeQueryRef": measure_ref
                }
            ]
        
        return visual
    
    def build_line_chart(
        self,
        position: Position,
        measures: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Line Chart visual placeholder.
        
        Args:
            position: Position and size
            measures: Optional list of measure references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("lineChart", position, name=name)

        # Add line chart-specific objects
        visual["visual"]["objects"] = {
            "legend": [
                {
                    "properties": {
                        "show": {
                            "expr": {
                                "Literal": {
                                    "Value": "true"
                                }
                            }
                        },
                        "showTitle": {
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
    
    def build_waterfall(
        self,
        position: Position,
        measures: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Waterfall Chart visual placeholder.
        
        Args:
            position: Position and size
            measures: Optional list of measure references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("waterfallChart", position, name=name)

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
        measures: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Horizontal Bar Chart visual placeholder (for Ranking slot).
        
        Args:
            position: Position and size
            measures: Optional list of measure references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("clusteredBarChart", position, name=name)

        # Add bar chart-specific objects
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
            ],
            "layout": [
                {
                    "properties": {
                        "clusteredGapSize": {
                            "expr": {
                                "Literal": {
                                    "Value": "10L"
                                }
                            }
                        },
                        "clusteredGapOverlaps": {
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
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Table visual placeholder.
        
        Args:
            position: Position and size
            columns: Optional list of column references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("tableEx", position, name=name)

        # Add table-specific objects
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
        
        return visual
    
    def build_matrix(
        self,
        position: Position,
        columns: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Matrix (Pivot Table) visual placeholder.
        
        Args:
            position: Position and size
            columns: Optional list of column references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("pivotTable", position, name=name)

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
        measures: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Scatter Plot visual placeholder.
        
        Args:
            position: Position and size
            measures: Optional list of measure references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("scatterChart", position, name=name)

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
        measures: Optional[list] = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build Funnel Chart visual placeholder.
        
        Args:
            position: Position and size
            measures: Optional list of measure references
        
        Returns:
            Visual JSON structure
        """
        visual = self._build_base_visual("funnelChart", position, name=name)

        # Add funnel-specific objects
        visual["visual"]["objects"] = {}
        
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

    def build_by_ux_visual_type(
        self,
        ux_visual_type: str,
        position: Position,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build visual from ux_layout_rules visual_type (round-trip from layout editor).
        Maps bracket/editor semantic types to Power BI visualType via existing build_* methods.
        """
        import logging
        logger = logging.getLogger(__name__)
        ux_to_method = {
            "kpi_card": self.build_kpi_card,
            "trend_line": self.build_line_chart,
            "waterfall": self.build_waterfall,
            "bar_chart": self.build_horizontal_bar,
            "stacked_bar": self.build_stacked_bar,
            "hundred_percent_stacked_bar": self.build_stacked_bar,
            "funnel": self.build_funnel,
        }
        method = ux_to_method.get(ux_visual_type)
        if method is None:
            logger.warning("Unknown ux_visual_type %r; defaulting to lineChart (trend)", ux_visual_type)
            method = self.build_line_chart
        return method(position, name=name)
