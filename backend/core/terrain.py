#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Core Terrain — SRTM 30m DEM Elevation & Slope Extraction
Reused from desktop dem_slope.py with graceful fallbacks.
Zero FastAPI/HTTP imports.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import numpy as np

# Path to Rwanda SRTM DEM
_BASE_DIR = Path(__file__).resolve().parent.parent.parent
DEM_PATH = _BASE_DIR / "data" / "SRTM" / "DEM30_ASHER.tif"

_dem_dataset = None
_transformer = None
_geo_available = False

try:
    import rasterio
    from pyproj import Transformer
    _geo_available = True
except ImportError:
    _geo_available = False


def _ensure_dem_open() -> bool:
    """Lazily open DEM and create coordinate transformer once."""
    global _dem_dataset, _transformer
    if not _geo_available or not DEM_PATH.exists():
        return False
    if _dem_dataset is not None:
        return True
    try:
        _dem_dataset = rasterio.open(DEM_PATH)
        _transformer = Transformer.from_crs("EPSG:4326", _dem_dataset.crs, always_xy=True)
        return True
    except Exception:
        return False


def get_elevation_and_slope(lat: float, lon: float, window_size: int = 11, cell_size: float = 30.0) -> Dict[str, float]:
    """
    Extract elevation (m ASL) and slope (%) at a WGS84 coordinate.
    Falls back to representative Rwanda average values if outside bounds or raster unavailable.
    """
    if _ensure_dem_open():
        try:
            easting, northing = _transformer.transform(lon, lat)
            row, col = _dem_dataset.index(easting, northing)
            half = window_size // 2
            nrows, ncols = _dem_dataset.shape

            if 0 <= row - half and row + half < nrows and 0 <= col - half and col + half < ncols:
                window = rasterio.windows.Window(col_off=col - half, row_off=row - half, width=window_size, height=window_size)
                elev_window = _dem_dataset.read(1, window=window).astype(np.float64)

                nodata = _dem_dataset.nodata
                if nodata is not None and nodata in elev_window:
                    elev_window[elev_window == nodata] = np.nan

                center_val = elev_window[half, half]
                if not np.isnan(center_val):
                    dy, dx = np.gradient(elev_window, cell_size)
                    slope_rad = np.arctan(np.sqrt(dx ** 2 + dy ** 2))
                    slope_pct = float(np.tan(slope_rad)[half, half] * 100.0)
                    return {
                        "elevation_m": round(float(center_val), 1),
                        "slope_percent": round(max(0.1, slope_pct), 2),
                        "source": "SRTM_30m"
                    }
        except Exception:
            pass

    # Standard fallback for Rwanda highlands/plateaus (e.g. Musanze / Kigali)
    return {
        "elevation_m": 1650.0,
        "slope_percent": 2.5,
        "source": "rwanda_default_baseline"
    }


def analyze_polygon_terrain(coordinates: List[List[float]]) -> Dict[str, float]:
    """
    Given a list of [lon, lat] or [lat, lon] polygon boundary coordinates,
    computes average elevation and representative slope across the polygon vertices.
    """
    if not coordinates:
        return {"elevation_m": 1600.0, "slope_percent": 2.0, "source": "default"}

    elevations = []
    slopes = []
    for pt in coordinates:
        # Handle [lon, lat] or [lat, lon]
        p1, p2 = pt[0], pt[1]
        lat, lon = (p1, p2) if abs(p1) < 5.0 and abs(p2) > 25.0 else (p2, p1)
        res = get_elevation_and_slope(lat, lon)
        elevations.append(res["elevation_m"])
        slopes.append(res["slope_percent"])

    return {
        "elevation_m": round(float(np.mean(elevations)), 1),
        "min_elevation_m": round(float(np.min(elevations)), 1),
        "max_elevation_m": round(float(np.max(elevations)), 1),
        "slope_percent": round(float(np.mean(slopes)), 2),
        "source": "polygon_srtm_sampled"
    }


if __name__ == "__main__":
    # Self-test at Kigali (-1.9441, 30.0619) and Musanze (-1.4998, 29.6349)
    print("Testing terrain elevation & slope extraction:")
    for name, (lat, lon) in [("Kigali", (-1.9441, 30.0619)), ("Musanze", (-1.4998, 29.6349))]:
        data = get_elevation_and_slope(lat, lon)
        print(f" - {name} ({lat}, {lon}): {data['elevation_m']}m elev, {data['slope_percent']}% slope ({data['source']})")
