#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid 2D Field Layout Geometry Engine
Ported from desktop gui/field_layout_2d.py — real geometry, not approximations.

Algorithm (matches desktop app exactly):
  1. Convert polygon lat/lon to local planar metres (centroid origin).
  2. Find the polygon edge nearest to the water-source point using
     point-to-segment distance (no Shapely needed — pure numpy).
  3. Rotate the whole coordinate frame so that nearest edge is horizontal (X axis).
  4. Sweep lateral lines (vertical in rotated frame) across the field, clipping
     each to stay inside the polygon via point-in-polygon ray casting.
  5. Emitters placed at uniform spacing along each clipped lateral segment.
  6. Unrotate all geometry back to world (metric) coordinates for JSON output.
"""

import numpy as np
from typing import List, Optional, Tuple, Dict, Any


# ── Low-level geometry helpers (ported verbatim) ─────────────────────────────

def _latlon_to_metres(coords: List[List[float]]):
    """Convert [[lat, lon], ...] to local planar metres. Returns (x, y, lon0, lat0, mpl, mpp)."""
    arr = np.array(coords, dtype=float)
    if np.abs(arr[:, 0]).mean() > 15.0 and np.abs(arr[:, 1]).mean() < 10.0:
        arr = arr[:, [1, 0]]
    lat0 = arr[:, 0].mean()
    lon0 = arr[:, 1].mean()
    m_per_deg_lat = 111320.0
    m_per_deg_lon = 111320.0 * np.cos(np.radians(lat0))
    x = (arr[:, 1] - lon0) * m_per_deg_lon
    y = (arr[:, 0] - lat0) * m_per_deg_lat
    return x, y, lon0, lat0, m_per_deg_lon, m_per_deg_lat


def _polygon_bbox(x, y):
    return float(x.min()), float(x.max()), float(y.min()), float(y.max())


def _point_in_polygon(px: float, py: float, poly_x, poly_y) -> bool:
    n = len(poly_x)
    inside = False
    j = n - 1
    for i in range(n):
        xi, yi = poly_x[i], poly_y[i]
        xj, yj = poly_x[j], poly_y[j]
        if ((yi > py) != (yj > py)) and (
            px < (xj - xi) * (py - yi) / (yj - yi + 1e-12) + xi
        ):
            inside = not inside
        j = i
    return inside


def _point_to_segment_dist(px, py, ax, ay, bx, by):
    """Shortest distance from P to segment AB; returns (dist, foot_x, foot_y)."""
    dx, dy = bx - ax, by - ay
    seg_len_sq = dx * dx + dy * dy
    if seg_len_sq < 1e-12:
        return float(np.hypot(px - ax, py - ay)), float(ax), float(ay)
    t = max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / seg_len_sq))
    cx, cy = ax + t * dx, ay + t * dy
    return float(np.hypot(px - cx, py - cy)), float(cx), float(cy)


def _nearest_edge(poly_x, poly_y, src_x: float, src_y: float):
    """Return (edge_idx, foot_x, foot_y) for the polygon edge closest to source."""
    n = len(poly_x)
    best_dist = float("inf")
    best_idx = 0
    best_foot = (poly_x[0], poly_y[0])
    for i in range(n):
        j = (i + 1) % n
        dx, dy = poly_x[j] - poly_x[i], poly_y[j] - poly_y[i]
        # Ignore degenerate/duplicate zero-length edges (shorter than 0.5m)
        if dx * dx + dy * dy < 0.25:
            continue
        dist, fx, fy = _point_to_segment_dist(src_x, src_y, poly_x[i], poly_y[i], poly_x[j], poly_y[j])
        if dist < best_dist:
            best_dist = dist
            best_idx = i
            best_foot = (fx, fy)
    return best_idx, best_foot[0], best_foot[1]


def _edge_angle(poly_x, poly_y, edge_idx: int) -> float:
    j = (edge_idx + 1) % len(poly_x)
    return float(np.arctan2(poly_y[j] - poly_y[edge_idx], poly_x[j] - poly_x[edge_idx]))


def _rotate(x, y, angle: float):
    x = np.atleast_1d(np.asarray(x, dtype=float))
    y = np.atleast_1d(np.asarray(y, dtype=float))
    c, s = np.cos(angle), np.sin(angle)
    return x * c + y * s, -x * s + y * c


def _unrotate(xr, yr, angle: float):
    xr = np.atleast_1d(np.asarray(xr, dtype=float))
    yr = np.atleast_1d(np.asarray(yr, dtype=float))
    c, s = np.cos(angle), np.sin(angle)
    return xr * c - yr * s, xr * s + yr * c


def _unrotate1(xr: float, yr: float, angle: float) -> Tuple[float, float]:
    c, s = np.cos(angle), np.sin(angle)
    return float(xr * c - yr * s), float(xr * s + yr * c)


def _default_rectangle(field_area_ha: float):
    area_m2 = field_area_ha * 10_000
    w = float(np.sqrt(area_m2 * 1.5))
    h = area_m2 / w
    return (
        np.array([0.0, w, w, 0.0, 0.0]),
        np.array([0.0, 0.0, h, h, 0.0]),
    )


# ── Main geometry function ────────────────────────────────────────────────────

def compute_field_layout(
    polygon_coords: Optional[List[List[float]]],  # [[lat, lon], ...]
    lateral_spacing: float = 1.0,
    emitter_spacing: float = 0.3,
    field_area_ha: float = 0.5,
    water_source_coords: Optional[List[float]] = None,  # [lat, lon]
) -> Dict[str, Any]:
    """
    Compute the 2D field layout geometry.
    Returns a dict of trace data ready to be serialised to JSON and consumed
    by the frontend (Plotly) or the PDF exporter (server-side Plotly image).
    """

    # 1. Build polygon in local metres ----------------------------------------
    if polygon_coords and len(polygon_coords) >= 3:
        px, py, lon0, lat0, mpl, mpp = _latlon_to_metres(polygon_coords)
        if not (np.isclose(px[0], px[-1]) and np.isclose(py[0], py[-1])):
            px = np.append(px, px[0])
            py = np.append(py, py[0])
        use_polygon = True
    else:
        px, py = _default_rectangle(field_area_ha)
        lon0 = lat0 = mpl = mpp = 0.0
        use_polygon = False

    ox, oy = px[:-1].tolist(), py[:-1].tolist()   # open ring for pip + edge tests
    ox_np, oy_np = np.array(ox), np.array(oy)

    # 2. Water source in local metres -----------------------------------------
    if water_source_coords and use_polygon:
        w1, w2 = water_source_coords[0], water_source_coords[1]
        ws_lat, ws_lon = (w1, w2) if abs(w1) < 10.0 and abs(w2) > 15.0 else (w2, w1)
        src_x = (ws_lon - lon0) * mpl
        src_y = (ws_lat - lat0) * mpp
    else:
        src_x = float(ox_np.mean())
        src_y = float(oy_np.max())   # default: top edge (uphill)

    # 3. Nearest edge to water source -----------------------------------------
    edge_idx, foot_x, foot_y = _nearest_edge(ox, oy, src_x, src_y)
    angle = _edge_angle(ox, oy, edge_idx)

    # 4. Rotate into edge-aligned frame ----------------------------------------
    px_r, py_r = _rotate(px, py, angle)
    ox_r, oy_r = _rotate(ox_np, oy_np, angle)
    src_xr_arr, src_yr_arr = _rotate(np.array([src_x]), np.array([src_y]), angle)
    src_xr, src_yr = float(src_xr_arr[0]), float(src_yr_arr[0])

    xmin_r, xmax_r, ymin_r, ymax_r = _polygon_bbox(px_r, py_r)
    field_width_r  = xmax_r - xmin_r
    field_height_r = ymax_r - ymin_r

    ml_yr = float(oy_r[edge_idx])
    inward = +1.0 if abs(ml_yr - ymin_r) <= abs(ml_yr - ymax_r) else -1.0

    # 5. Mainline: EXACT start and end vertices of the snapped edge (full edge length)
    v1_x = float(ox[edge_idx])
    v1_y = float(oy[edge_idx])
    next_idx = (edge_idx + 1) % len(ox)
    v2_x = float(ox[next_idx])
    v2_y = float(oy[next_idx])
    ml_x_s, ml_y_s = v1_x, v1_y
    ml_x_e, ml_y_e = v2_x, v2_y
    ml_length = float(np.hypot(ml_x_e - ml_x_s, ml_y_e - ml_y_s))
    mainline = [ml_x_s, ml_y_s, ml_x_e, ml_y_e]

    # In rotated frame, find the exact X-span of the mainline edge
    v1_xr = float(ox_r[edge_idx])
    v2_xr = float(ox_r[next_idx])
    ml_xr_min = min(v1_xr, v2_xr)
    ml_xr_max = max(v1_xr, v2_xr)

    # 6. Lateral positions across the rotated field ----------------------------
    lateral_xr_positions = np.arange(
        xmin_r + lateral_spacing,
        xmax_r - lateral_spacing / 2,
        lateral_spacing,
    )

    # 7. Sweep laterals — scan inward from mainline, clip to polygon ----------
    lateral_segments: List[List[float]] = []   # [[x0,y0,x1,y1], ...]
    emitter_xs: List[float] = []
    emitter_ys: List[float] = []
    seen_emitters = set()
    lateral_roots: List[Tuple[float, float]] = []
    valid_lateral_xrs: List[float] = []
    total_emitters_count = 0

    n_scan = 2000
    for lx_r in lateral_xr_positions:
        # Scan along Y in rotated frame
        scan_yr = np.linspace(ymin_r - 0.5, ymax_r + 0.5, n_scan)
        scan_xr = np.full_like(scan_yr, lx_r)
        scan_xw, scan_yw = _unrotate(scan_xr, scan_yr, angle)

        inside_mask = np.array([
            _point_in_polygon(float(scan_xw[i]), float(scan_yw[i]), ox, oy)
            for i in range(n_scan)
        ])

        if not inside_mask.any():
            continue

        # Extract contiguous runs so laterals never cross outside regions (e.g. in L-shaped fields)
        padded = np.pad(inside_mask.astype(int), (1, 1), "constant")
        changes = np.diff(padded)
        starts = np.where(changes == 1)[0]
        ends = np.where(changes == -1)[0]

        for s_idx, e_idx in zip(starts, ends):
            lyr_start = float(scan_yr[s_idx])
            lyr_end = float(scan_yr[e_idx - 1])
            lat_span = lyr_end - lyr_start
            if lat_span < 0.25:
                continue

            # Segments always oriented monotonically along +Yr: guarantees identical angle for all laterals
            lxw_bot, lyw_bot = _unrotate1(lx_r, lyr_start, angle)
            lxw_top, lyw_top = _unrotate1(lx_r, lyr_end, angle)

            lateral_segments.append([lxw_bot, lyw_bot, lxw_top, lyw_top])
            # Lateral root attaches closest to mainline edge
            root = (lxw_bot, lyw_bot) if inward > 0 else (lxw_top, lyw_top)
            lateral_roots.append(root)
            valid_lateral_xrs.append(float(lx_r))

            # Mathematical true emitter count
            n_lat_emitters = max(1, int(round(lat_span / emitter_spacing)))
            total_emitters_count += n_lat_emitters

            # Emitter sampling for display: cap at ~3,000 dots total, no duplicates at lateral ends
            if len(emitter_xs) < 3000:
                # Emitters placed with half-step inset: prevents duplicate placement at lateral endpoints
                eyr = np.linspace(
                    lyr_start + (emitter_spacing * 0.5),
                    lyr_end - (emitter_spacing * 0.5),
                    n_lat_emitters,
                )
                if len(eyr) > 50:
                    eyr = eyr[::max(1, len(eyr) // 35)]
                exr = np.full_like(eyr, lx_r)
                exw, eyw = _unrotate(exr, eyr, angle)
                for x_val, y_val in zip(exw.tolist(), eyw.tolist()):
                    key = (round(x_val, 2), round(y_val, 2))
                    if key not in seen_emitters and len(emitter_xs) < 3000:
                        seen_emitters.add(key)
                        emitter_xs.append(float(x_val))
                        emitter_ys.append(float(y_val))

    total_emitters = total_emitters_count

    # 8. Sub-main stubs: mainline attachment point → lateral root
    # Ensures attachment point is clamped to the mainline edge extent,
    # and the connector line is clipped to stay strictly inside the field boundary.
    sub_segments: List[List[float]] = []
    n_ox = len(ox)
    for (lrx, lry), lxr in zip(lateral_roots, valid_lateral_xrs):
        # Clamped attachment point on mainline edge
        clamped_lxr = float(np.clip(lxr, ml_xr_min, ml_xr_max))
        mc_x, mc_y = _unrotate1(clamped_lxr, ml_yr, angle)

        # Distance from mainline attachment point to lateral root
        d = float(np.hypot(lrx - mc_x, lry - mc_y))
        if d < 0.25:
            # Lateral root already touches the mainline directly
            continue

        # Clip connector line to stay strictly inside the polygon boundary
        n_clip_pts = max(15, int(d * 4))
        pts_x = np.linspace(mc_x, lrx, n_clip_pts)
        pts_y = np.linspace(mc_y, lry, n_clip_pts)
        in_mask = []
        for x, y in zip(pts_x, pts_y):
            if _point_in_polygon(x, y, ox, oy):
                in_mask.append(True)
            else:
                # Tolerance of 0.35m for points right on the polygon boundary edge
                min_d = min(np.hypot(x - ox[k], y - oy[k]) for k in range(n_ox))
                in_mask.append(min_d <= 0.35)

        if any(in_mask):
            valid_indices = [idx for idx, val in enumerate(in_mask) if val]
            p_s = (pts_x[valid_indices[0]], pts_y[valid_indices[0]])
            p_e = (pts_x[valid_indices[-1]], pts_y[valid_indices[-1]])
            if np.hypot(p_e[0] - p_s[0], p_e[1] - p_s[1]) >= 0.25:
                sub_segments.append([float(p_s[0]), float(p_s[1]), float(p_e[0]), float(p_e[1])])

    # 9. Pump / water source position -----------------------------------------
    if water_source_coords and use_polygon:
        pump_x, pump_y = src_x, src_y
    elif lateral_xr_positions.size > 0:
        pump_x, pump_y = _unrotate1(
            (ml_xr_min + ml_xr_max) / 2.0,
            ml_yr - inward * field_height_r * 0.12,
            angle,
        )
    else:
        pump_x, pump_y = float(px.mean()), float(py.min())

    # Supply line: pump → nearest point on mainline
    _, supply_foot_x, supply_foot_y = _point_to_segment_dist(
        pump_x, pump_y, ml_x_s, ml_y_s, ml_x_e, ml_y_e
    )

    # 9. Derived metrics -------------------------------------------------------
    total_lateral_m = sum(
        float(np.hypot(s[2] - s[0], s[3] - s[1])) for s in lateral_segments
    )
    area_m2 = field_area_ha * 10_000
    orient_deg = float(np.degrees(angle) % 180)

    return {
        # Polygon boundary (closed, world metres)
        "boundary_x": px.tolist(),
        "boundary_y": py.tolist(),

        # Laterals as flat [x0,y0,x1,y1] segments
        "lateral_segments": lateral_segments,

        # Emitters
        "emitter_x": emitter_xs,
        "emitter_y": emitter_ys,
        "total_emitters": total_emitters,

        # Mainline
        "mainline": [ml_x_s, ml_y_s, ml_x_e, ml_y_e],
        "mainline_length_m": round(ml_length, 1),

        # Sub-main stubs
        "sub_segments": sub_segments,

        # Pump/source
        "pump_x": pump_x,
        "pump_y": pump_y,
        "supply_foot_x": supply_foot_x,
        "supply_foot_y": supply_foot_y,

        # Summary metrics
        "num_laterals": len(lateral_segments),
        "total_lateral_m": round(total_lateral_m, 1),
        "area_m2": round(area_m2),
        "area_ha": field_area_ha,
        "mainline_edge_angle_deg": round(orient_deg, 1),
        "lateral_spacing_m": lateral_spacing,
        "emitter_spacing_m": emitter_spacing,
        "field_width_m": round(field_width_r, 1),
        "field_height_m": round(field_height_r, 1),
        "is_real_polygon": use_polygon,
    }
