"""
Slicer Builder

Builds Power BI slicer visual structures.
"""

import uuid
from typing import Dict, Any, Optional
from .layout_calculator import Position


class SlicerBuilder:
    """Builds slicer JSON structures for PBIP format."""
    
    VISUAL_SCHEMA = "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.3.0/schema.json"
    
    def __init__(self):
        """Initialize slicer builder."""
        self.z_order_base = 5000  # Slicers above visuals
        self.tab_order_base = 1000
    
    def _generate_slicer_id(self) -> str:
        """Generate unique slicer ID."""
        return uuid.uuid4().hex[:20]
    
    def _build_base_slicer(self, position: Position, tab_order: int = None) -> Dict[str, Any]:
        """Build base slicer structure."""
        if tab_order is None:
            tab_order = self.tab_order_base
        
        return {
            "$schema": self.VISUAL_SCHEMA,
            "name": self._generate_slicer_id(),
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
                    "title": [
                        {
                            "properties": {
                                "show": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "false"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "header": [
                        {
                            "properties": {
                                "show": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "true"
                                        }
                                    }
                                },
                                "textSize": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "14L"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "background": [
                        {
                            "properties": {
                                "show": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "false"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "border": [
                        {
                            "properties": {
                                "show": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "false"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "dropShadow": [
                        {
                            "properties": {
                                "show": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "false"
                                        }
                                    }
                                }
                            }
                        }
                    ],
                    "items": [
                        {
                            "properties": {
                                "background": {
                                    "solid": {
                                        "color": {
                                            "expr": {
                                                "Literal": {
                                                    "Value": "'#F6F6F6'"
                                                }
                                            }
                                        }
                                    }
                                },
                                "textSize": {
                                    "expr": {
                                        "Literal": {
                                            "Value": "14L"
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
    
    def build_time_slicer(self, position: Position, field: str = "dim_date.Date") -> Dict[str, Any]:
        """
        Build time/date slicer.
        
        Args:
            position: Position and size
            field: Date field reference (default: dim_date.Date)
        
        Returns:
            Slicer JSON structure
        """
        slicer = self._build_base_slicer(position)
        
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
    
    def build_categorical_slicer(self, position: Position, field: str) -> Dict[str, Any]:
        """
        Build categorical slicer (org, product, region, etc.).
        
        Args:
            position: Position and size
            field: Field reference (e.g., "dim_org.OrgName")
        
        Returns:
            Slicer JSON structure
        """
        slicer = self._build_base_slicer(position)
        
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
    
    def build_mode_switch_slicer(self, position: Position, field: str = "dim_scenario.ScenarioName") -> Dict[str, Any]:
        """
        Build 4th slicer for mode switch (scenario, currency, version).
        
        Args:
            position: Position and size
            field: Field reference (default: dim_scenario.ScenarioName)
        
        Returns:
            Slicer JSON structure
        """
        return self.build_categorical_slicer(position, field)
