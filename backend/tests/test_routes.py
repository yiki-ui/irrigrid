#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite for FastAPI backend routes, polygon optimization, and PDF generation.
"""

import math
import pytest
import requests as _req
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)


def test_health_and_root():
    res = client.get("/health")
    assert res.status_code == 200
    # Render healthCheckPath polls this; must return exactly {"status": "healthy"}
    assert res.json() == {"status": "healthy"}

    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["app"] == "IrriGrid API"


def test_soil_profile_endpoint():
    res = client.get("/api/v1/vegetation/soil-profile?lat=-1.50&lon=29.63&district=Musanze")
    assert res.status_code == 200
    data = res.json()
    assert "name" in data
    assert "field_capacity" in data
    assert "available_water_mm_m" in data
    assert "source" in data


def test_districts_endpoints():
    res = client.get("/api/v1/districts")
    assert res.status_code == 200
    districts = res.json()
    assert len(districts) >= 20

    # Specific district lookup
    m_res = client.get("/api/v1/districts/Musanze")
    assert m_res.status_code == 200
    assert m_res.json()["district"] == "Musanze"
    assert "Volcanic Loam" in m_res.json()["typical_soil"]


def test_climate_and_eto_endpoints():
    w_res = client.get("/api/v1/climate/weather?lat=-1.50&lon=29.63")
    assert w_res.status_code == 200
    assert "t_min" in w_res.json()

    eto_res = client.post("/api/v1/climate/eto", json={
        "tmin": 14.5, "tmax": 25.0, "rhmin": 50.0, "rhmax": 85.0,
        "wind_speed": 2.0, "sunshine_hours": 6.5, "latitude": -1.50,
        "elevation": 1800.0, "day_of_year": 180
    })
    assert eto_res.status_code == 200
    assert eto_res.json()["eto_mm_day"] > 1.0


def test_vegetation_endpoints():
    crops_res = client.get("/api/v1/vegetation/crops")
    assert crops_res.status_code == 200
    assert len(crops_res.json()) >= 10

    soils_res = client.get("/api/v1/vegetation/soils")
    assert soils_res.status_code == 200
    assert len(soils_res.json()) >= 5


def test_optimize_endpoint_with_real_traced_polygon():
    """Verify /optimize returns a valid design for a real multi-vertex traced polygon."""
    # Polygon around a real smallholder farm in Kinigi, Musanze
    traced_polygon = [
        [29.6105, -1.4520],
        [29.6120, -1.4522],
        [29.6118, -1.4535],
        [29.6102, -1.4533],
        [29.6105, -1.4520]
    ]
    res = client.post("/api/v1/optimize", json={
        "crop_name": "Tomato",
        "soil_type": "Volcanic Loam",
        "location_name": "Kinigi, Musanze",
        "polygon_coordinates": traced_polygon,
        "min_eu_threshold": 90.0
    })
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "design_id" in data
    assert "pdf_url" in data

    rec = data["recommended_design"]
    assert rec["emission_uniformity_percent"] >= 90.0
    assert rec["total_cost_rwf"] > 0
    assert len(rec["bom"]) >= 4

    design_id = data["design_id"]
    pdf_res = client.get(f"/api/v1/optimize/{design_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.headers["content-type"] == "application/pdf"
    content = pdf_res.content
    assert content.startswith(b"%PDF-")  # Valid PDF binary header
    assert len(content) > 2000           # Non-empty, fully formed document


def _make_square_polygon(area_ha: float):
    """Return a closed square polygon [lon, lat] of the given area near Musanze."""
    side_m = math.sqrt(area_ha * 10000.0)
    lat0, lon0 = -1.50, 29.63
    dlat = side_m / 111320.0
    dlon = side_m / (111320.0 * math.cos(math.radians(lat0)))
    return [
        [lon0, lat0],
        [lon0 + dlon, lat0],
        [lon0 + dlon, lat0 - dlat],
        [lon0, lat0 - dlat],
        [lon0, lat0],
    ]


def test_large_field_pdf_does_not_crash():
    """50 ha field must produce a valid PDF without OOM crash on Render 512 MB."""
    polygon = _make_square_polygon(50.0)
    res = client.post("/api/v1/optimize", json={
        "crop_name": "Maize",
        "soil_type": "Clay Loam",
        "location_name": "Musanze",
        "polygon_coordinates": polygon,
        "min_eu_threshold": 85.0,
    })
    assert res.status_code == 200
    design_id = res.json()["design_id"]

    pdf_res = client.get(f"/api/v1/optimize/{design_id}/pdf")
    assert pdf_res.status_code == 200
    assert pdf_res.content.startswith(b"%PDF-")
    assert len(pdf_res.content) > 2000


def test_soil_fallback_not_cached():
    """
    When SoilGrids is unreachable the fallback result must NOT be stored in
    _SOIL_CACHE, so the next real request can still hit the live API.
    """
    from backend.ingestion import soilgrids

    key = (round(-2.111, 3), round(30.222, 3))
    soilgrids._SOIL_CACHE.pop(key, None)

    original_get = _req.get

    def _timeout(*args, **kwargs):
        raise _req.exceptions.Timeout("simulated timeout")

    _req.get = _timeout
    try:
        result = soilgrids.get_soil_properties(-2.111, 30.222, district=None)
    finally:
        _req.get = original_get

    assert result["name"] == "Loam"
    assert result["source"] == "Standard Agronomic Default"
    assert result["sand_pct"] is None
    assert result["silt_pct"] is None
    assert result["clay_pct"] is None
    # Fallback must NOT be cached
    assert key not in soilgrids._SOIL_CACHE


def test_nisr_yield_endpoints():
    # Maize in Musanze
    res = client.get("/api/v1/agronomy/nisr-yield/Maize/Musanze")
    assert res.status_code == 200
    data = res.json()
    assert data["crop"] == "Maize"
    assert data["district"] == "Musanze"
    assert data["yield_kg_ha"] == 1905
    assert "NISR" in data["citation"]

    # Banana in Musanze (average of Cooking, Dessert, Beer: (10550+13281+7797)/3 = 10543)
    b_res = client.get("/api/v1/agronomy/nisr-yield/Banana/Musanze")
    assert b_res.status_code == 200
    assert b_res.json()["yield_kg_ha"] == 10543

    # Irish Potato in Musanze
    p_res = client.get("/api/v1/agronomy/nisr-yield/Irish%20Potato/Musanze")
    assert p_res.status_code == 200
    assert p_res.json()["yield_kg_ha"] == 12183

    # Case insensitive
    case_res = client.get("/api/v1/agronomy/nisr-yield/beans/musanze")
    assert case_res.status_code == 200
    assert case_res.json()["yield_kg_ha"] == 1111

    # Null entry in dataset (Irish Potato in Kicukiro is null)
    null_res = client.get("/api/v1/agronomy/nisr-yield/Irish%20Potato/Kicukiro")
    assert null_res.status_code == 404

    # Untracked crops (Tomato, Bell Pepper, Cabbage, Onion only in aggregate)
    for untracked in ["Tomato", "Bell Pepper", "Cabbage", "Onion"]:
        u_res = client.get(f"/api/v1/agronomy/nisr-yield/{untracked}/Musanze")
        assert u_res.status_code == 404
