#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
dem_slope.py — Point slope extraction from Rwanda DEM (SRTM 30m)

Reads the local DEM file (TM_Rwanda projected CRS), transforms WGS84 lat/lon
to the DEM's native coordinate system, and computes slope percentage from an
11×11 pixel neighbourhood using numpy gradient.

Dependencies: rasterio, pyproj, numpy  (all in conda env 'dss')
"""

import numpy as np
from pathlib import Path
from typing import Optional

import rasterio
from pyproj import Transformer

# ── Default DEM path (relative to project root) ─────────────────────────────
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent   # src/terrain/ → src/ → project root
DEM_PATH = _PROJECT_ROOT / "data" / "SRTM" / "DEM30_ASHER.tif"

# ── Module-level lazy cache ──────────────────────────────────────────────────
_dem_dataset = None        # rasterio.DatasetReader (kept open for performance)
_transformer = None        # pyproj.Transformer  (WGS84 → DEM CRS)


def _ensure_dem_open():
    """Open the DEM raster once and cache the dataset + transformer."""
    global _dem_dataset, _transformer
    if _dem_dataset is not None:
        return

    if not DEM_PATH.exists():
        raise FileNotFoundError(f"DEM not found at {DEM_PATH}")

    _dem_dataset = rasterio.open(DEM_PATH)
    dem_crs = _dem_dataset.crs

    # Build a WGS84 → DEM CRS transformer
    _transformer = Transformer.from_crs("EPSG:4326", dem_crs, always_xy=True)


def get_slope_at_point(lat: float, lon: float,
                       window_size: int = 11,
                       cell_size: float = 30.0) -> Optional[float]:
    """
    Extract terrain slope (%) at a WGS84 point from the Rwanda DEM.

    Parameters
    ----------
    lat : float
        Latitude in decimal degrees (WGS84, EPSG:4326).
    lon : float
        Longitude in decimal degrees (WGS84, EPSG:4326).
    window_size : int
        Side length of the square pixel window (default 11 → 330m × 330m).
        Must be odd.
    cell_size : float
        DEM cell resolution in metres (default 30m for SRTM).

    Returns
    -------
    float or None
        Slope in percent at the point, or None if the point falls outside
        the DEM bounds.
    """
    _ensure_dem_open()

    # ── 1. Transform WGS84 → DEM CRS ────────────────────────────────────────
    # pyproj with always_xy=True expects (lon, lat) → (easting, northing)
    easting, northing = _transformer.transform(lon, lat)

    # ── 2. Convert projected coords to pixel row/col ─────────────────────────
    row, col = _dem_dataset.index(easting, northing)

    # ── 3. Bounds check ──────────────────────────────────────────────────────
    half = window_size // 2
    nrows, ncols = _dem_dataset.shape

    if (row - half < 0 or row + half >= nrows or
            col - half < 0 or col + half >= ncols):
        # Point too close to edge or entirely outside
        return None

    # ── 4. Read elevation window ─────────────────────────────────────────────
    window = rasterio.windows.Window(
        col_off=col - half,
        row_off=row - half,
        width=window_size,
        height=window_size,
    )
    elev = _dem_dataset.read(1, window=window).astype(np.float64)

    # Handle nodata
    nodata = _dem_dataset.nodata
    if nodata is not None:
        mask = elev == nodata
        if mask.all():
            return None
        if mask.any():
            elev[mask] = np.nanmean(elev[~mask])

    # ── 5. Compute slope via numpy gradient ──────────────────────────────────
    dy, dx = np.gradient(elev, cell_size)
    slope_rad = np.arctan(np.sqrt(dx ** 2 + dy ** 2))
    slope_pct = np.tan(slope_rad) * 100.0

    # Return the centre-pixel slope (most representative)
    centre = window_size // 2
    return float(slope_pct[centre, centre])


def close_dem():
    """Explicitly close the cached DEM dataset (optional cleanup)."""
    global _dem_dataset, _transformer
    if _dem_dataset is not None:
        _dem_dataset.close()
        _dem_dataset = None
        _transformer = None


# ── Quick self-test ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Kigali city centre
    kigali_lat = -1.9441
    kigali_lon = 30.0619

    print(f"Testing slope extraction at Kigali ({kigali_lat}, {kigali_lon})...")
    print(f"DEM: {DEM_PATH}")
    print(f"DEM exists: {DEM_PATH.exists()}")

    slope = get_slope_at_point(kigali_lat, kigali_lon)

    if slope is not None:
        print(f"✅ Slope at Kigali: {slope:.2f}%")
        if slope < 1:
            print("   → Very flat terrain")
        elif slope < 5:
            print("   → Gentle slope (typical Kigali plateau)")
        elif slope < 15:
            print("   → Moderate slope (hillside)")
        else:
            print("   → Steep terrain (ridge / valley wall)")
    else:
        print("❌ Point is outside DEM bounds or no valid data")

    close_dem()
