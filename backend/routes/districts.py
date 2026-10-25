#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Routes: Districts
Serves Rwanda administrative districts and NISR agricultural survey baselines.
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, List
from backend.ingestion.nisr_baseline import list_all_districts, get_district_baseline

router = APIRouter(prefix="/districts", tags=["Districts"])


@router.get("", response_model=List[Dict])
def get_districts() -> List[Dict]:
    """List all Rwandan districts with baseline agricultural summaries."""
    return list_all_districts()


@router.get("/{district_name}")
def get_district(district_name: str) -> Dict:
    """Retrieve detailed NISR agricultural baseline for a district."""
    baseline = get_district_baseline(district_name)
    if not baseline:
        raise HTTPException(status_code=404, detail=f"District '{district_name}' not found")
    return baseline
