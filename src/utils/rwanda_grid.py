#!/usr/bin/env python
import math
# -*- coding: utf-8 -*-
"""
rwanda_grid.py — Rwanda National Grid Reference System

Implements parsing and coordinate conversion for Rwanda national grid cell references
(e.g., KG802ST, KG 802 ST) to WGS84 coordinates using UTM Zone 36S (EPSG:32736).

The Rwanda national grid uses the UTM coordinate system:
- Zone: 36S (covers all of Rwanda)
- 100km squares identified by letter pairs (e.g., KG)
- Sub-cell precision via additional letters

Reference: Rwanda's national grid is based on the UTM Military Grid Reference System (MGRS)
"""

import re
import math
from dataclasses import dataclass
from typing import Optional, Tuple, List

# Try to import pyproj for coordinate transformations
try:
    from pyproj import Transformer, CRS
    PYPROJ_AVAILABLE = True
except ImportError:
    PYPROJ_AVAILABLE = False
    print("⚠️ pyproj not available - coordinate transformations limited")


# Constants
UTM_ZONE = 36
UTM_HEMISPHERE = 'S'  # Southern hemisphere
UTM_EPSG = 32736      # EPSG code for UTM Zone 36S
WGS84_EPSG = 4326     # EPSG code for WGS84

# Rwanda lies approximately within:
# Latitude: -2.9° to -1.0° S (approximately)
# Longitude: 28.9° to 30.9° E (approximately)
RWANDA_BOUNDS = {
    'min_lat': -2.9,
    'max_lat': -1.0,
    'min_lng': 28.9,
    'max_lng': 30.9
}

# Known MGRS grid reference for Rwanda areas
# These are approximate center points of 100km squares
# Format: (zone_prefix, (approx_lat, approx_lng, approx_utm_easting, approx_utm_northing))
# These values are calibrated based on pyproj transformation:
# - Kigali (30.06°E, -1.95°S) -> UTM (172963, 9783781)
# - This rounds to ~170000, 9780000 for the 100km square (or 173000, 9784000)
MGR_REFERENCE_POINTS = {
    # Central Rwanda (Kigali area) - KG 100km square
    # Using 173000, 9784000 gives better accuracy
    'KG': (-1.95, 30.06, 173000, 9784000),  # Near Kigali
}

# UTM Zone 36S false easting and northing
FALSE_EASTING = 500000  # meters
FALSE_NORTHING = 10000000  # meters (for southern hemisphere)

# Grid cell size constants
# Each 100km square is divided into:
# - 10 subdivisions in easting (0-9) = 10km each
# - 10 subdivisions in northing (A-J, excluding I and O) = 10km each
# Each 10km sub-square can be further divided into 10x10 = 100 cells of 1km each
# And each 1km cell can be subdivided into 10x10 = 100 cells of 100m each

# Letter sequences for northing (row) within 100km square
# UTM uses A-V (excluding I and O) for 100km squares
# For sub-cells, we use a similar approach

# Northing letter sequence (going north)
NORTHING_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Excludes I and O

# Easting letter sequence (going east)
EASTING_LETTERS = 'ABCDEFGHJKLMNPQRSTUVWXYZ'  # Excludes I and O


@dataclass
class RwandaGridCell:
    """Represents a parsed Rwanda national grid cell reference."""
    # Original input
    raw_input: str
    
    # Parsed components
    zone_prefix: str          # e.g., "KG"
    easting_block: str        # e.g., "802"
    northing_block: str       # e.g., "ST"
    
    # Numeric values
    easting_100km: int       # 100km grid square easting (0-9)
    northing_100km: int      # 100km grid square northing (0-9)
    easting_km: int          # km offset within 100km square (0-99)
    northing_km: int         # km offset within 100km square (0-99)
    sub_easting: int         # 100m subdivision (0-9)
    sub_northing: int        # 100m subdivision (0-9)
    
    # Precision level
    precision: str           # '100km', '10km', '1km', '100m'
    
    # Calculated coordinates
    utm_easting: float      # UTM easting in meters
    utm_northing: float      # UTM northing in meters
    latitude: float         # WGS84 latitude
    longitude: float        # WGS84 longitude
    
    # Cell dimensions
    cell_size_m: float      # Cell size in meters
    area_ha: float          # Approximate area in hectares
    
    # Corner coordinates (for drawing boundary)
    corners_utm: List[Tuple[float, float]]  # List of (easting, northing) corners
    corners_wgs84: List[Tuple[float, float]]  # List of (lat, lng) corners


def _letter_to_number(letter: str) -> int:
    """Convert a letter to its numeric position (A=0, B=1, ..., Z=25, excluding I,O)."""
    letter = letter.upper()
    # Map letters to positions excluding I and O
    valid_letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    if letter not in valid_letters:
        raise ValueError(f"Invalid letter: {letter}")
    # Adjust for missing I and O
    if letter > 'I':
        offset = 1
    else:
        offset = 0
    if letter > 'O':
        offset += 1
    return valid_letters.index(letter) - offset


def _number_to_letter(number: int) -> str:
    """Convert a number (0-23) back to its letter representation."""
    valid_letters = 'ABCDEFGHJKLMNPQRSTUVWXYZ'
    if number < 0 or number >= len(valid_letters):
        raise ValueError(f"Invalid number: {number}")
    return valid_letters[number]


def _parse_grid_reference(grid_ref: str) -> Tuple[str, str, str]:
    """
    Parse a Rwanda grid reference into its components.
    
    Args:
        grid_ref: Grid reference like "KG802ST" or "KG 802 ST"
        
    Returns:
        Tuple of (zone_prefix, easting_block, northing_block)
    """
    # Normalize input: remove spaces and convert to uppercase
    normalized = re.sub(r'\s+', '', grid_ref).upper()
    
    # Pattern: 2 letters + 2-3 digits + 2 letters
    pattern = r'^([A-Z]{2})(\d{2,3})([A-Z]{2})$'
    match = re.match(pattern, normalized)
    
    if not match:
        raise ValueError(
            f"Invalid grid reference format: '{grid_ref}'. "
            f"Expected format: KG802ST or KG 802 ST (2 letters, 2-3 digits, 2 letters)"
        )
    
    zone_prefix = match.group(1)
    easting_block = match.group(2)
    northing_block = match.group(3)
    
    return zone_prefix, easting_block, northing_block


def _get_100km_square_offset(zone_prefix: str) -> Tuple[int, int]:
    """
    Get the 100km square offset for a given zone prefix using calibrated reference points.
    
    This function uses known reference points for Rwanda's MGRS grid system.
    
    Returns:
        Tuple of (easting_offset_100km, northing_offset_100km)
    """
    if len(zone_prefix) != 2:
        raise ValueError(f"Invalid zone prefix: {zone_prefix}")
    
    # If we have a reference point, use it as the base
    if zone_prefix in MGR_REFERENCE_POINTS:
        ref_lat, ref_lng, ref_easting, ref_northing = MGR_REFERENCE_POINTS[zone_prefix]
        return ref_easting, ref_northing
    
    # For other zone prefixes, use a more general calculation
    # Based on the MGRS system, the 100km square offsets can be calculated
    # using the standard UTM grid
    
    col_letter = zone_prefix[0]  # Easting letter
    row_letter = zone_prefix[1]  # Northing letter
    
    # Get letter indices (0-based)
    col_index = _letter_to_number(col_letter)
    row_index = _letter_to_number(row_letter)
    
    # For UTM zone 36:
    # - Easting letters (G through V) cover the zone
    # - For Rwanda, the main squares are around G-K (easting)
    # - Northing letters around K-M (around 1.5°S latitude)
    
    # Calculate offsets based on letter positions relative to reference
    # Each letter represents 100km
    
    # Use KG as reference point and adjust
    if 'KG' in MGR_REFERENCE_POINTS:
        ref_easting, ref_northing = MGR_REFERENCE_POINTS['KG']
        
        # Calculate the difference in letter positions
        col_diff = col_index - _letter_to_number('K')
        row_diff = row_index - _letter_to_number('G')
        
        easting_100km = ref_easting + (col_diff * 100000)
        northing_100km = ref_northing + (row_diff * 100000)
        
        return easting_100km, northing_100km
    
    # Fallback: use false easting/northing
    easting_100km = FALSE_EASTING + (col_index * 100000)
    northing_100km = FALSE_NORTHING + (row_index * 100000)
    
    return easting_100km, northing_100km


def parse_grid_reference(grid_ref: str) -> RwandaGridCell:
    """
    Parse a Rwanda grid reference and convert to coordinates.
    
    Args:
        grid_ref: Grid reference like "KG802ST" or "KG 802 ST"
        
    Returns:
        RwandaGridCell with all parsed and calculated data
        
    Example:
        >>> cell = parse_grid_reference("KG802ST")
        >>> print(cell.latitude, cell.longitude)
        -1.2345 29.5678
    """
    # Parse the grid reference
    zone_prefix, easting_block, northing_block = _parse_grid_reference(grid_ref)
    
    # Determine precision based on easting block length
    # For 2-digit (10km precision): e.g., "80" = 80 * 1km = 80km
    # For 3-digit (1km precision): e.g., "802" = 802 * 100m = 80.2km
    if len(easting_block) == 2:
        precision = '10km'
        easting_m = int(easting_block) * 1000  # e.g., "80" -> 80 * 1000 = 80000m = 80km
        easting_km = int(easting_block)  # For storage in dataclass
        sub_easting = 0
    elif len(easting_block) == 3:
        precision = '1km'
        # Each digit = 100m, so the whole number * 100 gives meters
        # e.g., "802" = 802 * 100 = 80200m = 80.2km
        easting_m = int(easting_block) * 100  # e.g., "802" -> 802 * 100 = 80200m
        easting_km = int(easting_block) // 10  # For storage, 802 // 10 = 80
        sub_easting = 0  # Already included in the 3-digit format
    else:
        raise ValueError(f"Invalid easting block length: {len(easting_block)}")
    
    # Parse northing block (2 letters)
    # First letter = 10km row within 100km square, Second letter = 1km within that row
    # MGRS within a 100km square: each letter represents 10km (first) and 1km (second)
    # The letter pair gives position within the 100km square
    # For 10km precision: only first letter matters (S = 10km row)
    # For 1km precision: both letters (ST = 10km row + 1km position)
    if len(northing_block) == 2:
        if precision == '10km':
            precision = '10km'
            # First letter = 10km row (0-9 within square)
            northing_km = _letter_to_number(northing_block[0]) * 10  # e.g., "S" -> 1 * 10 = 10km
            sub_northing = 0
        else:
            precision = '1km'
            # First letter = 10km row, second letter = 1km within that row
            # e.g., "ST": S=18 in full sequence but within 100km square means row 1 (10-19km)
            # So we need mod 10 to get position within square
            row_letter_val = _letter_to_number(northing_block[0]) % 10  # 0-9, row within 100km square
            col_letter_val = _letter_to_number(northing_block[1]) % 10  # 0-9, position within row
            northing_km = row_letter_val * 10 + col_letter_val  # e.g., row 1 (10km) + 8 = 18km
            sub_northing = 0
    else:
        raise ValueError(f"Invalid northing block: {northing_block}")
    
    # Get 100km square base coordinates
    base_easting, base_northing = _get_100km_square_offset(zone_prefix)
    
    # Calculate UTM coordinates
    # Add meter offsets
    utm_easting = base_easting + easting_m + (sub_easting * 100)
    utm_northing = base_northing + (northing_km * 1000) + (sub_northing * 100)
    
    # Determine cell size based on precision
    if precision == '10km':
        cell_size_m = 10000
    elif precision == '1km':
        cell_size_m = 1000
    else:
        cell_size_m = 100
    
    # Calculate area in hectares
    area_ha = (cell_size_m * cell_size_m) / 10000
    
    # Calculate corners (for boundary drawing)
    half_size = cell_size_m / 2
    corners_utm = [
        (utm_easting - half_size, utm_northing - half_size),  # SW
        (utm_easting + half_size, utm_northing - half_size),  # SE
        (utm_easting + half_size, utm_northing + half_size),  # NE
        (utm_easting - half_size, utm_northing + half_size),  # NW
    ]
    
    # Convert to WGS84
    latitude, longitude = utm_to_wgs84(utm_easting, utm_northing)
    
    # Convert corners to WGS84
    corners_wgs84 = [utm_to_wgs84(e, n) for e, n in corners_utm]
    
    # Calculate 100km grid square indices
    easting_100km_index = _letter_to_number(zone_prefix[0])
    northing_100km_index = _letter_to_number(zone_prefix[1])
    
    return RwandaGridCell(
        raw_input=grid_ref,
        zone_prefix=zone_prefix,
        easting_block=easting_block,
        northing_block=northing_block,
        easting_100km=easting_100km_index,
        northing_100km=northing_100km_index,
        easting_km=easting_km,
        northing_km=northing_km,
        sub_easting=sub_easting,
        sub_northing=sub_northing,
        precision=precision,
        utm_easting=utm_easting,
        utm_northing=utm_northing,
        latitude=latitude,
        longitude=longitude,
        cell_size_m=cell_size_m,
        area_ha=area_ha,
        corners_utm=corners_utm,
        corners_wgs84=corners_wgs84
    )


def utm_to_wgs84(easting: float, northing: float) -> Tuple[float, float]:
    """
    Convert UTM Zone 36S coordinates to WGS84 lat/lng.
    
    Args:
        easting: UTM easting in meters
        northing: UTM northing in meters
        
    Returns:
        Tuple of (latitude, longitude) in degrees
    """
    if not PYPROJ_AVAILABLE:
        # Fallback: approximate conversion
        # Rwanda is around 29.5°E, 1.5°S
        # UTM zone 36 has central meridian at 33°E
        # 1 degree easting ≈ 111320 * cos(lat) meters
        # 1 degree northing ≈ 111320 meters
        
        central_meridian = 33.0
        lat_ref = -1.5  # Reference latitude for Rwanda
        
        # Calculate longitude
        m_per_deg = 111320 * math.cos(math.radians(lat_ref))
        lng_offset = (easting - FALSE_EASTING) / m_per_deg
        longitude = central_meridian + lng_offset
        
        # Calculate latitude
        # This is a rough approximation
        lat_offset = (northing - FALSE_NORTHING) / 111320
        latitude = -lat_offset
        
        return latitude, longitude
    
    # Use pyproj for accurate conversion
    try:
        transformer = Transformer.from_crs(
            CRS.from_epsg(UTM_EPSG),
            CRS.from_epsg(WGS84_EPSG),
            always_xy=True
        )
        lng, lat = transformer.transform(easting, northing)
        return lat, lng
    except Exception as e:
        print(f"⚠️ pyproj transformation failed: {e}")
        # Fallback to approximate
        central_meridian = 33.0
        lat_ref = -1.5
        m_per_deg = 111320 * math.cos(math.radians(lat_ref))
        lng_offset = (easting - FALSE_EASTING) / m_per_deg
        longitude = central_meridian + lng_offset
        lat_offset = (northing - FALSE_NORTHING) / 111320
        latitude = -lat_offset
        return latitude, longitude


def wgs84_to_utm(lat: float, lng: float) -> Tuple[float, float]:
    """
    Convert WGS84 lat/lng to UTM Zone 36S coordinates.
    
    Args:
        lat: Latitude in degrees
        lng: Longitude in degrees
        
    Returns:
        Tuple of (easting, northing) in meters
    """
    if not PYPROJ_AVAILABLE:
        # Fallback approximation
        central_meridian = 33.0
        m_per_deg = 111320 * math.cos(math.radians(lat))
        
        easting = FALSE_EASTING + (lng - central_meridian) * m_per_deg
        northing = FALSE_NORTHING + lat * 111320
        
        return easting, northing
    
    try:
        transformer = Transformer.from_crs(
            CRS.from_epsg(WGS84_EPSG),
            CRS.from_epsg(UTM_EPSG),
            always_xy=True
        )
        x, y = transformer.transform(lng, lat)
        return x, y
    except Exception as e:
        print(f"⚠️ pyproj transformation failed: {e}")
        central_meridian = 33.0
        m_per_deg = 111320 * math.cos(math.radians(lat))
        easting = FALSE_EASTING + (lng - central_meridian) * m_per_deg
        northing = FALSE_NORTHING + lat * 111320
        return easting, northing


def is_valid_grid_reference(grid_ref: str) -> bool:
    """
    Check if a string is a valid Rwanda grid reference.
    
    Args:
        grid_ref: Grid reference to validate
        
    Returns:
        True if valid, False otherwise
    """
    try:
        _parse_grid_reference(grid_ref)
        return True
    except ValueError:
        return False


def is_within_rwanda(lat: float, lng: float) -> bool:
    """
    Check if coordinates are within Rwanda bounds.
    
    Args:
        lat: Latitude in degrees
        lng: Longitude in degrees
        
    Returns:
        True if within Rwanda, False otherwise
    """
    return (RWANDA_BOUNDS['min_lat'] <= lat <= RWANDA_BOUNDS['max_lat'] and
            RWANDA_BOUNDS['min_lng'] <= lng <= RWANDA_BOUNDS['max_lng'])


def format_grid_reference(lat: float, lng: float, precision: str = '1km') -> str:
    """
    Format WGS84 coordinates as a Rwanda grid reference.
    
    Args:
        lat: Latitude in degrees
        lng: Longitude in degrees
        precision: Desired precision ('10km', '1km', or '100m')
        
    Returns:
        Grid reference string (e.g., "KG802ST")
    """
    # Convert to UTM
    easting, northing = wgs84_to_utm(lat, lng)
    
    # Determine 100km square
    col_index = int((easting - FALSE_EASTING) // 100000)
    row_index = int((northing - FALSE_NORTHING) // 100000)
    
    # Clamp to valid range
    col_index = max(0, min(col_index, len(EASTING_LETTERS) - 1))
    row_index = max(0, min(row_index, len(NORTHING_LETTERS) - 1))
    
    zone_prefix = EASTING_LETTERS[col_index] + NORTHING_LETTERS[row_index]
    
    # Calculate offsets within 100km square
    easting_offset = int((easting - FALSE_EASTING) % 100000)
    northing_offset = int((northing - FALSE_NORTHING) % 100000)
    
    if precision == '10km':
        easting_10km = easting_offset // 10000
        northing_10km = northing_offset // 10000
        easting_str = f"{easting_10km}"
        northing_str = NORTHING_LETTERS[northing_10km]
    elif precision == '1km':
        easting_km = easting_offset // 1000
        northing_km = northing_offset // 1000
        easting_str = f"{easting_km:02d}"
        northing_str = NORTHING_LETTERS[northing_km // 10] + NORTHING_LETTERS[northing_km % 10]
    else:  # 100m
        easting_100m = easting_offset // 100
        northing_100m = northing_offset // 100
        easting_str = f"{easting_100m:03d}"
        northing_str = NORTHING_LETTERS[northing_100m // 10] + NORTHING_LETTERS[northing_100m % 10]
    
    return f"{zone_prefix}{easting_str}{northing_str}"


def get_bounding_box(grid_cell: RwandaGridCell, padding_m: float = 0) -> Tuple[float, float, float, float]:
    """
    Get bounding box for a grid cell with optional padding.
    
    Args:
        grid_cell: The RwandaGridCell to get bounding box for
        padding_m: Optional padding in meters
        
    Returns:
        Tuple of (min_lat, max_lat, min_lng, max_lng)
    """
    if padding_m > 0:
        # Convert padding from meters to degrees (approximate)
        lat_padding = padding_m / 111320
        lng_padding = padding_m / (111320 * math.cos(math.radians(grid_cell.latitude)))
    else:
        lat_padding = lng_padding = 0
    
    lats = [corner[0] for corner in grid_cell.corners_wgs84]
    lngs = [corner[1] for corner in grid_cell.corners_wgs84]
    
    return (
        min(lats) - lat_padding,
        max(lats) + lat_padding,
        min(lngs) - lng_padding,
        max(lngs) + lng_padding
    )


# ─────────────────────────────────────────────────────────────────────────────
# Main entry point for testing
# ─────────────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys
    
    # Test with example grid reference
    test_refs = [
        "KG802ST",
        "KG 802 ST",
        "KG90MS",  # 10km precision
        "KG9015",  # Another format variation
    ]
    
    print("=" * 70)
    print("RWANDA GRID REFERENCE CONVERTER")
    print("=" * 70)
    print()
    
    for ref in test_refs:
        print(f"Testing: {ref}")
        try:
            if is_valid_grid_reference(ref):
                cell = parse_grid_reference(ref)
                print(f"  ✓ Valid")
                print(f"    Zone: {cell.zone_prefix}")
                print(f"    Easting block: {cell.easting_block}")
                print(f"    Northing block: {cell.northing_block}")
                print(f"    Precision: {cell.precision}")
                print(f"    UTM: E={cell.utm_easting:.0f}m, N={cell.utm_northing:.0f}m")
                print(f"    WGS84: {cell.latitude:.6f}°, {cell.longitude:.6f}°")
                print(f"    Cell size: {cell.cell_size_m:.0f}m")
                print(f"    Area: {cell.area_ha:.2f} ha")
                print(f"    Corners (SW→SE→NE→NW):")
                for i, corner in enumerate(cell.corners_wgs84):
                    print(f"      {i+1}: {corner[0]:.6f}°, {corner[1]:.6f}°")
            else:
                print(f"  ✗ Invalid format")
        except Exception as e:
            print(f"  ✗ Error: {e}")
        print()
    
    # Test reverse conversion
    print("-" * 70)
    print("Testing reverse conversion (WGS84 → Grid):")
    test_coords = [
        (-1.9536, 30.1106),  # Kigali
        (-2.0686, 29.7472),  # Ruhengeri
        (-2.6092, 29.2958),  # Kibuye
    ]
    
    for lat, lng in test_coords:
        grid_ref = format_grid_reference(lat, lng, '1km')
        print(f"  {lat:.4f}°, {lng:.4f}° → {grid_ref}")
    
    print()
    print("=" * 70)
