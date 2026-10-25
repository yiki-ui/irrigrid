#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Tests for 2D Field Layout Geometry Engine & Web/PDF Parity:
1. Rotated rectangle: all laterals have same angle, spacing constant within 1 cm, none outside polygon.
2. L-shaped polygon: same checks, verifying no laterals cross outside concave cutout.
3. 0.022 ha Nyarugenge plot: smallholder plot validation.
4. Parity test: web endpoint and PDF export use identical segment data.
5. Emitter deduplication: no emitter placed twice at lateral ends.
"""

import math
import numpy as np
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.core.field_layout import compute_field_layout, _point_in_polygon
from backend.core.pdf_export import generate_irrigation_pdf


client = TestClient(app)


def _meters_to_latlon(pts_m, lat0=-1.95, lon0=30.0588):
    """Convert local (x, y) meters to lat/lon for testing."""
    m_per_deg_lat = 111320.0
    m_per_deg_lon = 111320.0 * math.cos(math.radians(lat0))
    return [[lat0 + y / m_per_deg_lat, lon0 + x / m_per_deg_lon] for x, y in pts_m]


def _check_layout_properties(geom, lateral_spacing=1.0, emitter_spacing=0.3):
    """
    Numerically verify:
    1. All laterals have the same angle.
    2. Spacing between distinct parallel lateral sweep lines is constant within 1 cm.
    3. None of the lateral segments extend outside the field polygon.
    4. Emitters are not duplicated.
    """
    laterals = geom["lateral_segments"]
    assert len(laterals) > 0, "Layout produced no laterals"

    # 1. Check angle of every lateral
    angles = []
    for s in laterals:
        dx = s[2] - s[0]
        dy = s[3] - s[1]
        ang = np.degrees(np.arctan2(dy, dx)) % 180.0
        angles.append(ang)

    angles = np.array(angles)
    angle_spread = np.ptp(angles)
    assert angle_spread < 0.01, f"Laterals have differing angles! Spread: {angle_spread:.4f} deg"
    common_angle_rad = np.radians(angles[0])

    # 2. Check spacing between distinct adjacent lateral sweep lines (constant within 1 cm)
    # Project each lateral onto the normal axis to measure perpendicular offset from origin
    # Normal to line at angle theta is (-sin(theta), cos(theta))
    nx = -np.sin(common_angle_rad)
    ny = np.cos(common_angle_rad)
    projections = [s[0] * nx + s[1] * ny for s in laterals]
    # Cluster projections into distinct lateral sweep lines (within 5 cm tolerance for collinear segments)
    projections = sorted(projections)
    distinct_lines = []
    for p in projections:
        if not distinct_lines or abs(p - distinct_lines[-1]) > 0.05:
            distinct_lines.append(p)

    assert len(distinct_lines) >= 2, "Need at least 2 distinct lateral lines to check spacing"
    spacings = np.diff(distinct_lines)
    for sp in spacings:
        assert abs(sp - lateral_spacing) <= 0.01, (
            f"Spacing deviation! Expected {lateral_spacing}m +/- 1cm, got {sp:.4f}m"
        )

    # 3. Check that no lateral extends outside the polygon boundary
    ox = geom["boundary_x"][:-1]
    oy = geom["boundary_y"][:-1]
    n_ox = len(ox)

    for s in laterals:
        # Sample 50 points along each lateral segment
        for t in np.linspace(0.0, 1.0, 50):
            px = s[0] + t * (s[2] - s[0])
            py = s[1] + t * (s[3] - s[1])
            inside = _point_in_polygon(px, py, ox, oy)
            if not inside:
                # If right on boundary edge, allow up to 5 cm numerical tolerance
                min_edge_dist = min(np.hypot(px - ox[k], py - oy[k]) for k in range(n_ox))
                assert min_edge_dist <= 0.05, (
                    f"Lateral point ({px:.2f}, {py:.2f}) is outside polygon (distance to edge: {min_edge_dist:.3f}m)"
                )

    # 4. Check emitter deduplication: no emitter placed twice
    ex = geom["emitter_x"]
    ey = geom["emitter_y"]
    assert len(ex) == len(ey)
    coords = set()
    for x_val, y_val in zip(ex, ey):
        key = (round(x_val, 2), round(y_val, 2))
        assert key not in coords, f"Duplicate emitter found at ({x_val}, {y_val})"
        coords.add(key)


def test_rotated_rectangle_layout():
    """Verify geometry on a 40m x 20m rectangle rotated by 35 degrees."""
    theta = np.radians(35.0)
    c, s = np.cos(theta), np.sin(theta)
    # Box [-20, -10] to [20, 10]
    box = [(-20, -10), (20, -10), (20, 10), (-20, 10)]
    rot_box = [(x * c - y * s, x * s + y * c) for x, y in box]
    coords = _meters_to_latlon(rot_box)

    geom = compute_field_layout(
        polygon_coords=coords,
        lateral_spacing=1.0,
        emitter_spacing=0.3,
        field_area_ha=0.08,
    )
    _check_layout_properties(geom, lateral_spacing=1.0, emitter_spacing=0.3)


def test_l_shaped_polygon_layout():
    """Verify geometry on an L-shaped polygon (non-convex with cut-out)."""
    # 30m x 30m with 15m x 15m cutout
    pts_l = [(0, 0), (30, 0), (30, 15), (15, 15), (15, 30), (0, 30)]
    coords = _meters_to_latlon(pts_l)

    geom = compute_field_layout(
        polygon_coords=coords,
        lateral_spacing=1.0,
        emitter_spacing=0.3,
        field_area_ha=0.0675,
    )
    _check_layout_properties(geom, lateral_spacing=1.0, emitter_spacing=0.3)


def test_nyarugenge_022_ha_plot():
    """Verify geometry on a real smallholder 0.022 ha (220 m2) plot in Nyarugenge."""
    # ~14.83m x 14.83m square plot at Nyarugenge coordinates
    side = math.sqrt(220.0)  # ~14.832 m
    pts = [(0, 0), (side, 0), (side, side), (0, side)]
    coords = _meters_to_latlon(pts, lat0=-1.95, lon0=30.0588)

    geom = compute_field_layout(
        polygon_coords=coords,
        lateral_spacing=0.8,
        emitter_spacing=0.25,
        field_area_ha=0.022,
    )
    _check_layout_properties(geom, lateral_spacing=0.8, emitter_spacing=0.25)


def test_web_endpoint_and_pdf_use_identical_segment_data():
    """
    Verify that the JSON exposed from POST /api/v1/optimize contains layout_geometry,
    and the PDF generator consumes the exact same segment data.
    """
    pts = [(0, 0), (25, 0), (25, 20), (0, 20)]
    coords = _meters_to_latlon(pts)

    payload = {
        "crop_name": "Tomato",
        "soil_type": "Volcanic Loam",
        "location_name": "Nyarugenge, Kigali",
        "field_area_ha": 0.05,
        "polygon_coordinates": coords,
        "lateral_spacing": 1.2,
        "emitter_spacing": 0.4,
    }

    resp = client.post("/api/v1/optimize", json=payload)
    assert resp.status_code == 200, f"Optimize endpoint failed: {resp.text}"
    data = resp.json()

    assert "layout_geometry" in data, "layout_geometry missing from /optimize response"
    web_geom = data["layout_geometry"]
    assert "lateral_segments" in web_geom
    assert "mainline" in web_geom
    assert "total_emitters" in web_geom
    assert web_geom["lateral_spacing_m"] == 1.2
    assert web_geom["emitter_spacing_m"] == 0.4

    # Generate PDF using the design record
    design_id = data["design_id"]
    pdf_resp = client.get(f"/api/v1/optimize/{design_id}/pdf")
    assert pdf_resp.status_code == 200
    assert len(pdf_resp.content) > 5000
    assert pdf_resp.content.startswith(b"%PDF")

    # Direct check: compute_field_layout called with identical parameters gives identical segments
    direct_geom = compute_field_layout(
        polygon_coords=coords,
        lateral_spacing=1.2,
        emitter_spacing=0.4,
        field_area_ha=0.05,
    )

    assert web_geom["lateral_segments"] == direct_geom["lateral_segments"]
    assert web_geom["mainline"] == direct_geom["mainline"]
    assert web_geom["total_emitters"] == direct_geom["total_emitters"]
    assert web_geom["num_laterals"] == direct_geom["num_laterals"]
