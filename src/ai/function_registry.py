#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Function Registry for Agentic AI System
Defines all UI actions that the AI can call via Groq function calling
"""

from typing import Dict, List, Any

# ── Function Definitions ──────────────────────────────────────────────────────

UI_FUNCTIONS: List[Dict[str, Any]] = [
    # ── Location Functions ─────────────────────────────────────────────────
    {
        "name": "set_location",
        "description": "Set the field location by province and district in Rwanda",
        "parameters": {
            "type": "object",
            "properties": {
                "province": {
                    "type": "string",
                    "description": "Province name (e.g., 'Kigali', 'Eastern', 'Western', 'Northern', 'Southern')"
                },
                "district": {
                    "type": "string",
                    "description": "District name (e.g., 'Nyarugenge', 'Gasabo', 'Kicukiro')"
                }
            },
            "required": ["province", "district"]
        },
        "ui_method": "set_location_from_ai",
        "category": "location"
    },
    
    # ── Design Parameter Functions ─────────────────────────────────────────
    {
        "name": "set_crop_type",
        "description": "Select the crop type for irrigation design",
        "parameters": {
            "type": "object",
            "properties": {
                "crop": {
                    "type": "string",
                    "enum": ["maize", "beans", "rice", "wheat", "potato", "tomato", "banana", "coffee", "tea"],
                    "description": "Crop type to grow"
                }
            },
            "required": ["crop"]
        },
        "ui_method": "set_crop_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_field_area",
        "description": "Set the field area in hectares",
        "parameters": {
            "type": "object",
            "properties": {
                "area_ha": {
                    "type": "number",
                    "description": "Field area in hectares (0.1 to 100)",
                    "minimum": 0.1,
                    "maximum": 100
                }
            },
            "required": ["area_ha"]
        },
        "ui_method": "set_area_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_soil_type",
        "description": "Set the soil type for the field",
        "parameters": {
            "type": "object",
            "properties": {
                "soil_type": {
                    "type": "string",
                    "enum": ["clay", "sandy", "loam", "silt", "clay_loam", "sandy_loam", "silt_loam"],
                    "description": "Soil type"
                }
            },
            "required": ["soil_type"]
        },
        "ui_method": "set_soil_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_water_source",
        "description": "Set the water source type",
        "parameters": {
            "type": "object",
            "properties": {
                "source_type": {
                    "type": "string",
                    "enum": ["River/Stream", "Well/Borehole", "Lake/Pond", "Municipal", "Rainwater Harvesting"],
                    "description": "Water source type"
                }
            },
            "required": ["source_type"]
        },
        "ui_method": "set_water_source_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_emitter_flow_rate",
        "description": "Set the emitter flow rate in liters per hour",
        "parameters": {
            "type": "object",
            "properties": {
                "flow_rate_lph": {
                    "type": "number",
                    "description": "Emitter flow rate in liters per hour (0.5 to 20)",
                    "minimum": 0.5,
                    "maximum": 20
                }
            },
            "required": ["flow_rate_lph"]
        },
        "ui_method": "set_emitter_flow_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_emitter_spacing",
        "description": "Set the spacing between emitters in meters",
        "parameters": {
            "type": "object",
            "properties": {
                "spacing_m": {
                    "type": "number",
                    "description": "Emitter spacing in meters (0.1 to 5)",
                    "minimum": 0.1,
                    "maximum": 5
                }
            },
            "required": ["spacing_m"]
        },
        "ui_method": "set_emitter_spacing_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_lateral_spacing",
        "description": "Set the spacing between lateral pipes in meters",
        "parameters": {
            "type": "object",
            "properties": {
                "spacing_m": {
                    "type": "number",
                    "description": "Lateral spacing in meters (0.5 to 10)",
                    "minimum": 0.5,
                    "maximum": 10
                }
            },
            "required": ["spacing_m"]
        },
        "ui_method": "set_lateral_spacing_from_ai",
        "category": "design"
    },
    
    {
        "name": "set_operating_pressure",
        "description": "Set the system operating pressure in bar",
        "parameters": {
            "type": "object",
            "properties": {
                "pressure_bar": {
                    "type": "number",
                    "description": "Operating pressure in bar (0.5 to 3)",
                    "minimum": 0.5,
                    "maximum": 3
                }
            },
            "required": ["pressure_bar"]
        },
        "ui_method": "set_pressure_from_ai",
        "category": "design"
    },
    
    # ── Visualization Functions ────────────────────────────────────────────
    {
        "name": "toggle_slope_heatmap",
        "description": "Show or hide slope heatmap in 3D terrain view",
        "parameters": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "True to show, False to hide"
                }
            },
            "required": ["enabled"]
        },
        "ui_method": "toggle_slope_from_ai",
        "category": "visualization"
    },
    
    {
        "name": "toggle_drip_layout",
        "description": "Show or hide drip irrigation layout in 3D view",
        "parameters": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "True to show, False to hide"
                }
            },
            "required": ["enabled"]
        },
        "ui_method": "toggle_drip_from_ai",
        "category": "visualization"
    },
    
    {
        "name": "toggle_boundary_wall",
        "description": "Show or hide field boundary wall in 3D view",
        "parameters": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "True to show, False to hide"
                }
            },
            "required": ["enabled"]
        },
        "ui_method": "toggle_boundary_wall_from_ai",
        "category": "visualization"
    },
    
    {
        "name": "toggle_flow_arrows",
        "description": "Show or hide water flow direction arrows in 3D view",
        "parameters": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "True to show, False to hide"
                }
            },
            "required": ["enabled"]
        },
        "ui_method": "toggle_flow_arrows_from_ai",
        "category": "visualization"
    },
    
    {
        "name": "toggle_hydraulic_zones",
        "description": "Show or hide hydraulic zone segmentation in 3D view",
        "parameters": {
            "type": "object",
            "properties": {
                "enabled": {
                    "type": "boolean",
                    "description": "True to show, False to hide"
                },
                "n_zones": {
                    "type": "integer",
                    "description": "Number of zones (3-6)",
                    "minimum": 3,
                    "maximum": 6
                }
            },
            "required": ["enabled"]
        },
        "ui_method": "toggle_hydraulic_zones_from_ai",
        "category": "visualization"
    },
    
    # ── Calculation Functions ──────────────────────────────────────────────
    {
        "name": "run_design_calculation",
        "description": "Run the irrigation system design calculation with current parameters",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "ui_method": "run_design_from_ai",
        "category": "calculation"
    },
    
    {
        "name": "analyze_design",
        "description": "Analyze the current irrigation design and provide recommendations",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "ui_method": "analyze_design_from_ai",
        "category": "analysis"
    },
    
    # ── Query Functions ────────────────────────────────────────────────────
    {
        "name": "get_current_state",
        "description": "Get current field data, design parameters, and UI state",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "ui_method": "get_state_for_ai",
        "category": "query"
    },
    
    {
        "name": "get_design_results",
        "description": "Get the results of the last design calculation",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "ui_method": "get_design_results_for_ai",
        "category": "query"
    },
    
    {
        "name": "get_terrain_info",
        "description": "Get terrain information including slope and elevation",
        "parameters": {
            "type": "object",
            "properties": {}
        },
        "ui_method": "get_terrain_info_for_ai",
        "category": "query"
    }
]


def get_function_definitions_for_groq() -> List[Dict[str, Any]]:
    """
    Convert function registry to Groq tool definitions format.
    
    Returns:
        List of tool definitions for Groq API
    """
    tools = []
    for func in UI_FUNCTIONS:
        tool = {
            "type": "function",
            "function": {
                "name": func["name"],
                "description": func["description"],
                "parameters": func["parameters"]
            }
        }
        tools.append(tool)
    return tools


def get_function_descriptions_text() -> str:
    """
    Get human-readable descriptions of all functions for system prompt.
    
    Returns:
        Formatted string with function descriptions
    """
    lines = []
    current_category = None
    
    for func in UI_FUNCTIONS:
        category = func.get("category", "other")
        if category != current_category:
            lines.append(f"\n### {category.upper()} FUNCTIONS")
            current_category = category
        
        params = func["parameters"].get("properties", {})
        param_str = ", ".join([f"{k}: {v.get('type', 'any')}" for k, v in params.items()])
        lines.append(f"- {func['name']}({param_str}): {func['description']}")
    
    return "\n".join(lines)


def get_function_by_name(name: str) -> Dict[str, Any] | None:
    """
    Get function definition by name.
    
    Args:
        name: Function name
        
    Returns:
        Function definition or None if not found
    """
    for func in UI_FUNCTIONS:
        if func["name"] == name:
            return func
    return None
