#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: Agronomy
Serves agronomy data including NISR SAS 2025 Seasonal Agricultural Survey yields.
"""

import json
from pathlib import Path
from typing import Dict, Optional
from fastapi import APIRouter, HTTPException

router = APIRouter(prefix="/agronomy", tags=["Agronomy"])

_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "nisr_yield.json"
_nisr_data: Optional[Dict] = None


def _get_nisr_data() -> Dict:
    global _nisr_data
    if _nisr_data is None:
        with open(_DATA_PATH, mode="r", encoding="utf-8") as f:
            _nisr_data = json.load(f)
    return _nisr_data


@router.get("/nisr-yield/{crop}/{district}")
def get_nisr_yield(crop: str, district: str) -> Dict:
    """
    Retrieve NISR 2025 SAS Season A yield for a crop and district.
    Only Maize, Beans, Irish Potato, and Banana are individually tracked.
    Banana yields average Cooking Banana, Dessert Banana, and Banana for Beer.
    Returns 404 for untracked crops (e.g. Vegetables aggregate) or missing district data.
    """
    data = _get_nisr_data()
    dist_map = data.get("district_yield_kg_ha", {})

    # Case-insensitive district lookup
    matched_entry = None
    resolved_district = district
    for dist_key, dist_val in dist_map.items():
        if dist_key.lower() == district.strip().lower():
            matched_entry = dist_val
            resolved_district = dist_key
            break

    if matched_entry is None:
        raise HTTPException(status_code=404, detail=f"District '{district}' not found in NISR dataset")

    crop_lower = crop.strip().lower()
    yield_val: Optional[int] = None
    resolved_crop = crop

    if crop_lower == "maize":
        yield_val = matched_entry.get("Maize")
        resolved_crop = "Maize"
    elif crop_lower == "beans":
        yield_val = matched_entry.get("Beans")
        resolved_crop = "Beans"
    elif crop_lower in ("irish potato", "potato"):
        yield_val = matched_entry.get("Irish Potato")
        resolved_crop = "Irish Potato"
    elif crop_lower == "banana":
        resolved_crop = "Banana"
        vals = [
            matched_entry.get("Cooking Banana"),
            matched_entry.get("Dessert Banana"),
            matched_entry.get("Banana for Beer"),
        ]
        valid_vals = [v for v in vals if v is not None]
        if valid_vals:
            yield_val = round(sum(valid_vals) / len(valid_vals))
    else:
        # Untracked crops like Tomato, Bell Pepper, Cabbage, Onion only exist under Vegetables_aggregate
        raise HTTPException(
            status_code=404,
            detail=f"Crop '{crop}' is not individually tracked by NISR SAS district surveys"
        )

    if yield_val is None:
        raise HTTPException(
            status_code=404,
            detail=f"No NISR yield data recorded for '{crop}' in '{resolved_district}'"
        )

    return {
        "crop": resolved_crop,
        "district": resolved_district,
        "yield_kg_ha": yield_val,
        "unit": "kg/ha",
        "citation": data.get("citation", "National Institute of Statistics of Rwanda (NISR) Seasonal Agricultural Survey, 2025, Season A")
    }
