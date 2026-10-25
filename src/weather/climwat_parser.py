#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FAO CLIMWAT 2.0 Parser
======================
Read standard FAO CLIMWAT 2.0 exported files:
- .pen : Penman-Monteith reference evapotranspiration (ETo)
- .cli : Climate summary (Tmin, Tmax, RHmin, RHmax, wind, sunshine, rainfall)

Provides a unified interface that allows downstream services
to fall back to CLIMWAT data when NASA POWER is unavailable.

Usage
-----
    from src.weather.climwat_parser import parse_climwat
    climwat = parse_climwat(station="KIGALI", data_dir="data/climate")
    eto_monthly = climwat["eto_mm"]
"""

import os
from pathlib import Path
from typing import Dict, List, Optional


class CLIMWATParsingError(Exception):
    """Raised when a CLIMWAT file cannot be parsed."""
    pass


def _read_lines(path: Path) -> List[str]:
    if not path.exists():
        raise CLIMWATParsingError(f"CLIMWAT file not found: {path}")
    with open(path, "r", encoding="utf-8", errors="ignore") as fh:
        return [line.rstrip("\n") for line in fh]


def parse_pen_file(path: Path) -> Dict[str, object]:
    """
    Parse a CLIMWAT .pen file.

    Expected format (whitespace or tab separated):
        Station : KIGALI
        Country : Rwanda
        Lat     : -1.9403
        Long    : 29.8739
        Elev    : 1567
        ETo (mm/month) row with 12 values: J F M A M J J A S O N D

    Returns
    -------
    {
        "station": str,
        "country": str,
        "latitude": Optional[float],
        "longitude": Optional[float],
        "elevation_m": Optional[float],
        "eto_mm": [float x 12],
    }
    """
    lines = _read_lines(path)
    meta: Dict[str, Optional[float]] = {
        "latitude": None,
        "longitude": None,
        "elevation_m": None,
    }
    station = None
    country = None
    monthly_values: List[Optional[float]] = [None] * 12

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith("station"):
            station = stripped.split(":", 1)[-1].strip()
        elif lower.startswith("country"):
            country = stripped.split(":", 1)[-1].strip()
        elif lower.startswith("lat"):
            try:
                meta["latitude"] = float(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        elif lower.startswith("long"):
            try:
                meta["longitude"] = float(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        elif lower.startswith("elev"):
            try:
                meta["elevation_m"] = float(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        else:
            parts = stripped.replace("\t", " ").split()
            try:
                nums = [float(p) for p in parts[:12]]
                if len(nums) == 12 and all(v is not None for v in nums):
                    monthly_values = nums
            except ValueError:
                pass

    if any(v is None for v in monthly_values):
        raise CLIMWATParsingError(
            f"Could not parse 12 monthly ETo values from {path}"
        )

    return {
        "station": station,
        "country": country,
        "latitude": meta["latitude"],
        "longitude": meta["longitude"],
        "elevation_m": meta["elevation_m"],
        "eto_mm": monthly_values,  # type: ignore[return-value]
    }


def parse_cli_file(path: Path) -> Dict[str, object]:
    """
    Parse a CLIMWAT .cli file.

    Expected format:
        Header: Station / Country / Lat / Long / Elev
        Monthly rows with 12 values for:
        Tmin(C), Tmax(C), RHmin(%), RHmax(%), Wind(m/s), Sunshine(h), Rain(mm)

    Returns
    -------
    {
        "station": str,
        "country": str,
        "latitude": Optional[float],
        "longitude": Optional[float],
        "elevation_m": Optional[float],
        "tmin_c": List[Optional[float]],
        "tmax_c": List[Optional[float]],
        "rhmin_pct": List[Optional[float]],
        "rhmax_pct": List[Optional[float]],
        "wind_speed_ms": List[Optional[float]],
        "sunshine_h": List[Optional[float]],
        "rain_mm": List[Optional[float]],
    }
    """
    lines = _read_lines(path)
    meta: Dict[str, Optional[float]] = {
        "latitude": None,
        "longitude": None,
        "elevation_m": None,
    }
    station = None
    country = None

    monthly_values: Dict[str, List[Optional[float]]] = {
        "tmin_c": [None] * 12,
        "tmax_c": [None] * 12,
        "rhmin_pct": [None] * 12,
        "rhmax_pct": [None] * 12,
        "wind_speed_ms": [None] * 12,
        "sunshine_h": [None] * 12,
        "rain_mm": [None] * 12,
    }

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        lower = stripped.lower()
        if lower.startswith("station"):
            station = stripped.split(":", 1)[-1].strip()
        elif lower.startswith("country"):
            country = stripped.split(":", 1)[-1].strip()
        elif lower.startswith("lat"):
            try:
                meta["latitude"] = float(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        elif lower.startswith("long"):
            try:
                meta["longitude"] = float(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        elif lower.startswith("elev"):
            try:
                meta["elevation_m"] = float(stripped.split(":")[-1].strip())
            except ValueError:
                pass
        else:
            parts = stripped.replace("\t", " ").split()
            try:
                nums = [float(p) for p in parts[:12]]
                if len(nums) == 12:
                    keys = [
                        "tmin_c", "tmax_c", "rhmin_pct", "rhmax_pct",
                        "wind_speed_ms", "sunshine_h", "rain_mm"
                    ]
                    for key, value in zip(keys, nums):
                        monthly_values[key] = [value] * 12
            except ValueError:
                pass

    return {
        "station": station,
        "country": country,
        "latitude": meta["latitude"],
        "longitude": meta["longitude"],
        "elevation_m": meta["elevation_m"],
        **monthly_values,  # type: ignore[arg-type]
    }


def try_parse_climwat(
    station: str,
    data_dir: str = "data/climate",
) -> Optional[Dict[str, object]]:
    """
    Try to parse both CLIMWAT files for a station.

    Parameters
    ----------
    station : str
        Station name/identifier used in the filename, e.g. "KIGALI".
    data_dir : str
        Directory where .pen and .cli files are stored.

    Returns
    -------
    dict with unified monthly arrays if both files are found and valid,
    or None if files are missing.
    """
    base = Path(data_dir)
    pen_path = base / f"{station}.pen"
    cli_path = base / f"{station}.cli"

    pen = None
    cli = None

    if pen_path.exists():
        pen = parse_pen_file(pen_path)
    if cli_path.exists():
        cli = parse_cli_file(cli_path)

    if pen is None and cli is None:
        return None

    merged: Dict[str, object] = {
        "station": (pen or {}).get("station") or (cli or {}).get("station"),
        "country": (pen or {}).get("country") or (cli or {}).get("country"),
        "latitude": (pen or {}).get("latitude") or (cli or {}).get("latitude"),
        "longitude": (pen or {}).get("longitude") or (cli or {}).get("longitude"),
        "elevation_m": (pen or {}).get("elevation_m") or (cli or {}).get("elevation_m"),
        "source": "CLIMWAT 2.0",
    }

    if pen:
        merged["eto_mm"] = pen["eto_mm"]  # type: ignore[assignment]
    else:
        merged["eto_mm"] = [None] * 12  # type: ignore[assignment]

    if cli:
        for key in (
            "tmin_c",
            "tmax_c",
            "rhmin_pct",
            "rhmax_pct",
            "wind_speed_ms",
            "sunshine_h",
            "rain_mm",
        ):
            merged[key] = cli[key]  # type: ignore[index]
    else:
        for key in (
            "tmin_c",
            "tmax_c",
            "rhmin_pct",
            "rhmax_pct",
            "wind_speed_ms",
            "sunshine_h",
            "rain_mm",
        ):
            merged[key] = [None] * 12

    return merged


def get_climwat_fallback(latitude: float, longitude: float,
                         data_dir: str = "data/climate") -> Optional[Dict[str, object]]:
    """
    Convenience helper: if a station-level CLIMWAT dataset exists in *data_dir*
    that is usable for the requested coordinates, return the parsed dict.

    This does NOT perform spatial nearest-station matching; that should be
    implemented by `GeographicService` or higher layers. Here we simply
    expose the parsed surface as an integration seam.
    """
    candidates = list(Path(data_dir).glob("*.pen"))
    if not candidates:
        return None
    for pen_path in candidates:
        station = pen_path.stem
        result = try_parse_climwat(station=station, data_dir=data_dir)
        if result:
            return result
    return None
