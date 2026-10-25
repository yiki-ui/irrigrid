#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Offline Search Service for Rwanda Administrative Units
Uses local CSV data when network is unavailable
"""

import csv
import os
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


@dataclass
class OfflineLocation:
    """Offline location from CSV"""
    province: str
    district: str
    sector: str
    cell: str
    village: str
    latitude: float
    longitude: float
    altitude: float
    climate_zone: str
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'province': self.province,
            'district': self.district,
            'sector': self.sector,
            'cell': self.cell,
            'village': self.village,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'altitude': self.altitude,
            'climate_zone': self.climate_zone
        }


class OfflineSearchService:
    """
    Offline search service using local CSV data
    Provides basic administrative hierarchy search without network
    """
    
    def __init__(self):
        self.locations: List[OfflineLocation] = []
        self._load_data()
    
    def _load_data(self):
        """Load CSV data"""
        # Base directory for resolution
        base_dir = Path(__file__).parent.parent.parent.absolute()
        
        # Try multiple paths for the CSV file
        possible_paths = [
            base_dir / "assets" / "rwanda_admin.csv",
            base_dir / "data" / "rwanda_admin.csv",
            Path("assets/rwanda_admin.csv"),
            Path("data/rwanda_admin.csv"),
        ]
        
        csv_path = None
        for path in possible_paths:
            if path.exists():
                csv_path = path
                break
        
        if not csv_path:
            print("⚠️ Rwanda admin CSV not found, offline search unavailable")
            return
        
        try:
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    try:
                        location = OfflineLocation(
                            province=row.get('province', '').strip(),
                            district=row.get('district', '').strip(),
                            sector=row.get('sector', '').strip(),
                            cell=row.get('cell', '').strip(),
                            village=row.get('village', '').strip(),
                            latitude=float(row.get('latitude', 0)),
                            longitude=float(row.get('longitude', 0)),
                            altitude=float(row.get('altitude', 1500)),
                            climate_zone=row.get('climate_zone', 'midland').strip()
                        )
                        self.locations.append(location)
                    except (ValueError, KeyError) as e:
                        continue
            
            print(f"✅ Loaded {len(self.locations)} offline locations")
            
        except Exception as e:
            print(f"❌ Error loading offline data: {e}")
    
    def search(self, query: str, max_results: int = 10) -> List[OfflineLocation]:
        """
        Search for locations matching query
        
        Args:
            query: Search query
            max_results: Maximum results to return
            
        Returns:
            List of matching locations
        """
        if not query or len(query.strip()) < 1:
            return []
        
        query_lower = query.lower().strip()
        results = []
        
        for loc in self.locations:
            # Check all fields
            if (query_lower in loc.province.lower() or
                query_lower in loc.district.lower() or
                query_lower in loc.sector.lower() or
                query_lower in loc.cell.lower() or
                query_lower in loc.village.lower()):
                results.append(loc)
            
            if len(results) >= max_results:
                break
        
        return results
    
    def get_provinces(self) -> List[str]:
        """Get all provinces"""
        provinces = set(loc.province for loc in self.locations)
        return sorted(provinces)
    
    def get_districts(self, province: str) -> List[str]:
        """Get districts in province"""
        districts = set(
            loc.district for loc in self.locations 
            if loc.province == province
        )
        return sorted(districts)
    
    def get_sectors(self, province: str, district: str) -> List[str]:
        """Get sectors in district"""
        sectors = set(
            loc.sector for loc in self.locations 
            if loc.province == province and loc.district == district
        )
        return sorted(sectors)
    
    def get_cells(self, province: str, district: str, sector: str) -> List[str]:
        """Get cells in sector"""
        cells = set(
            loc.cell for loc in self.locations 
            if loc.province == province and loc.district == district 
            and loc.sector == sector and loc.cell
        )
        return sorted(cells)
    
    def get_location_by_coords(self, lat: float, lon: float, 
                               tolerance: float = 0.1) -> Optional[OfflineLocation]:
        """
        Find closest location to coordinates
        
        Args:
            lat: Latitude
            lon: Longitude
            tolerance: Search radius in degrees
            
        Returns:
            Closest location or None
        """
        closest = None
        min_dist = float('inf')
        
        for loc in self.locations:
            dist = ((loc.latitude - lat) ** 2 + (loc.longitude - lon) ** 2) ** 0.5
            if dist < min_dist and dist < tolerance:
                min_dist = dist
                closest = loc
        
        return closest


# Singleton instance
_offline_service: Optional[OfflineSearchService] = None


def get_offline_service() -> OfflineSearchService:
    """Get singleton offline service"""
    global _offline_service
    if _offline_service is None:
        _offline_service = OfflineSearchService()
    return _offline_service


def search_offline(query: str) -> List[OfflineLocation]:
    """Convenience function for offline search"""
    return get_offline_service().search(query)


if __name__ == "__main__":
    # Test offline search
    print("Testing Offline Search Service...")
    print()
    
    service = get_offline_service()
    
    # Test provinces
    print(f"Provinces: {service.get_provinces()}")
    print()
    
    # Test districts
    print(f"Kigali City districts: {service.get_districts('Kigali City')}")
    print()
    
    # Test sectors
    print(f"Gasabo sectors: {service.get_sectors('Kigali City', 'Gasabo')[:5]}...")
    print()
    
    # Test cells
    print(f"Kimironko cells: {service.get_cells('Kigali City', 'Gasabo', 'Kimironko')}")
    print()
    
    # Test search
    results = service.search("Kimironko")
    print(f"Search 'Kimironko': {len(results)} results")
    for r in results[:3]:
        print(f"  - {r.sector}, {r.cell}, {r.district}")
