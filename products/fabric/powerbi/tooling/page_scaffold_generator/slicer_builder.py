"""
Slicer Builder

Builds Power BI slicer visual structures.
"""

import uuid
from typing import Dict, Any, Optional
from .layout_calculator import Position
from products.fabric.powerbi.tooling.schema_registry import VISUAL_SCHEMA as _VISUAL_SCHEMA


class SlicerBuilder:
    """Builds slicer JSON structures for PBIP format."""

    VISUAL_SCHEMA = _VISUAL_SCHEMA
    
    def __init__(self):
        """Initialize slicer builder."""
        self.z_order_base = 5000  # Slicers above visuals
        self.tab_order_base = 1000
    
    def _generate_slicer_id(self) -> str:
        """Generate unique slicer ID."""
        return uuid.uuid4().hex[:20]
    
    def _build_base_slicer(
        self,
        position: Position,
        tab_order: int = None,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Build base slicer structure. Use speaking name when provided (no hex ID)."""
        if tab_order is None:
            tab_order = self.tab_order_base
        slicer_name = name if name is not None else self._generate_slicer_id()

        return {
            "$schema": self.VISUAL_SCHEMA,
            "name": slicer_name,
            "position": {
                "x": position.x,
                "y": position.y,
                "z": position.z if position.z != 10000 else self.z_order_base,
                "height": position.height,
                "width": position.width,
                "tabOrder": tab_order
            },
            "visual": {
                "visualType": "slicer",
                "query": {
                    "queryState": {
                        "Values": {
                            "projections": []
                        }
                    }
                },
                "objects": {
                    "data": [
                        {
                            "properties": {
                                "mode": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "'Dropdown'"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "general": [
                        {
                            "properties": {
                                "orientation": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "1D"
                                        }
                                    }
                                }
                            }
                        }
                    ]
                },
                "drillFilterOtherVisuals": True
            }
        }
    
    def build_time_slicer(
        self,
        position: Position,
        field: str = "dim_date.CalendarYearMonth",
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build time/date slicer.

        Args:
            position: Position and size
            field: Date field reference (default: dim_date.CalendarYearMonth for YYYY-MM sortable slicer)
            name: Speaking name (e.g. Slicer_Date); optional
        
        Returns:
            Slicer JSON structure
        """
        slicer = self._build_base_slicer(position, name=name)
        
        # Add date field projection
        entity, property_name = field.split('.') if '.' in field else ("dim_date", "Date")
        
        slicer["visual"]["query"]["queryState"]["Values"]["projections"] = [
            {
                "field": {
                    "Column": {
                        "Expression": {
                            "SourceRef": {
                                "Entity": entity
                            }
                        },
                        "Property": property_name
                    }
                },
                "queryRef": f"{entity}.{property_name}",
                "nativeQueryRef": property_name
            }
        ]
        
        return slicer
    
    def build_categorical_slicer(
        self,
        position: Position,
        field: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build categorical slicer (org, product, region, etc.).
        
        Args:
            position: Position and size
            field: Field reference (e.g., "dim_org.OrgName")
            name: Speaking name; optional
        
        Returns:
            Slicer JSON structure
        """
        slicer = self._build_base_slicer(position, name=name)
        
        # Add categorical field projection
        entity, property_name = field.split('.') if '.' in field else (field, field)
        
        slicer["visual"]["query"]["queryState"]["Values"]["projections"] = [
            {
                "field": {
                    "Column": {
                        "Expression": {
                            "SourceRef": {
                                "Entity": entity
                            }
                        },
                        "Property": property_name
                    }
                },
                "queryRef": f"{entity}.{property_name}",
                "nativeQueryRef": property_name
            }
        ]
        
        return slicer
    
    def build_mode_switch_slicer(
        self,
        position: Position,
        field: str = "dim_scenario.ScenarioName",
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Build 4th slicer for mode switch (scenario, currency, version).
        
        Args:
            position: Position and size
            field: Field reference (default: dim_scenario.ScenarioName)
            name: Speaking name; optional
        
        Returns:
            Slicer JSON structure
        """
        return self.build_categorical_slicer(position, field, name=name)
