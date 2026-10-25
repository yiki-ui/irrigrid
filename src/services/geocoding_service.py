#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Nominatim Geocoding Service for Rwanda
Provides smart search with autocomplete for Rwanda administrative units
"""

import os
import json
import time
import urllib.request
import urllib.parse
import urllib.error
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class GeocodingResult:
    """Result from Nominatim geocoding"""
    display_name: str
    lat: float
    lon: float
    type: str  # city, town, village, administrative
    address: Dict  # Full address details from OSM
    
    @property
    def place_type(self) -> str:
        """Get human-readable place type"""
        addr = self.address
        if addr.get('city'):
            return "City"
        elif addr.get('town'):
            return "Town"
        elif addr.get('village'):
            return "Village"
        elif addr.get('municipality'):
            return "Municipality"
        elif addr.get('county'):
            return "County"
        elif addr.get('state'):
            return "State/Province"
        elif addr.get('country'):
            return "Country"
        return self.type.title()
    
    @property
    def hierarchy_string(self) -> str:
        """Get formatted hierarchy string"""
        addr = self.address
        parts = []
        
        # Add cell/village if present
        if addr.get('village'):
            parts.append(addr['village'])
        if addr.get('neighbourhood'):
            parts.append(addr['neighbourhood'])
        
        # Add administrative levels
        if addr.get('city'):
            parts.append(addr['city'])
        if addr.get('town'):
            parts.append(addr['town'])
        if addr.get('municipality'):
            parts.append(addr['municipality'])
        
        # Add district
        if addr.get('county'):
            parts.append(addr['county'])
        
        # Add province
        if addr.get('state'):
            parts.append(addr['state'])
        
        return " → ".join(parts) if parts else self.display_name


class NominatimGeocoder:
    """
    Nominatim geocoding service for Rwanda
    Free API, no key required but requires proper usage policy
    """
    
    BASE_URL = "https://nominatim.openstreetmap.org/search"
    
    @property
    def USER_AGENT(self) -> str:
        contact_email = os.getenv("CONTACT_EMAIL", "").strip()
        return f"IrriDSS/1.0 ({contact_email})" if contact_email else "IrriDSS/1.0 (irrigation-dss)"
    
    # Rate limiting
    _last_request_time = 0
    MIN_REQUEST_INTERVAL = 1.0  # 1 second between requests
    
    def __init__(self):
        self.last_results: List[GeocodingResult] = []
    
    def _rate_limit(self):
        """Enforce rate limiting"""
        current_time = time.time()
        elapsed = current_time - self._last_request_time
        if elapsed < self.MIN_REQUEST_INTERVAL:
            time.sleep(self.MIN_REQUEST_INTERVAL - elapsed)
        self._last_request_time = time.time()
    
    def _make_request(self, params: Dict) -> List[GeocodingResult]:
        """Make request to Nominatim API"""
        self._rate_limit()
        
        # Add default parameters
        params['format'] = 'json'
        params['addressdetails'] = '1'
        params['limit'] = '10'
        
        # Build URL
        query_string = urllib.parse.urlencode(params)
        url = f"{self.BASE_URL}?{query_string}"
        
        # Create request with proper headers
        request = urllib.request.Request(
            url,
            headers={
                'User-Agent': self.USER_AGENT,
                'Accept': 'application/json'
            }
        )
        
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            results = []
            for item in data:
                result = GeocodingResult(
                    display_name=item.get('display_name', ''),
                    lat=float(item.get('lat', 0)),
                    lon=float(item.get('lon', 0)),
                    type=item.get('type', 'unknown'),
                    address=item.get('address', {})
                )
                results.append(result)
            
            self.last_results = results
            return results
            
        except urllib.error.URLError as e:
            print(f"❌ Network error: {e}")
            return []
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {e}")
            return []
        except Exception as e:
            print(f"❌ Geocoding error: {e}")
            return []
    
    def search(self, query: str, focus_rwanda: bool = True) -> List[GeocodingResult]:
        """
        Search for a location
        
        Args:
            query: Search query (e.g., "Kimironko", "Gasabo district")
            focus_rwanda: If True, adds "Rwanda" to query automatically
            
        Returns:
            List of geocoding results
        """
        if not query or len(query.strip()) < 2:
            return []
        
        # Clean query
        query = query.strip()
        
        # Add Rwanda to focus search on Rwandan locations
        if focus_rwanda and 'rwanda' not in query.lower():
            query = f"{query}, Rwanda"
        
        return self._make_request({'q': query})
    
    def reverse(self, lat: float, lon: float) -> Optional[GeocodingResult]:
        """
        Reverse geocode coordinates to address
        
        Args:
            lat: Latitude
            lon: Longitude
            
        Returns:
            Geocoding result or None
        """
        self._rate_limit()
        
        params = {
            'lat': str(lat),
            'lon': str(lon),
            'format': 'json',
            'addressdetails': '1',
            'zoom': '18'  # Most detailed
        }
        
        query_string = urllib.parse.urlencode(params)
        url = f"https://nominatim.openstreetmap.org/reverse?{query_string}"
        
        request = urllib.request.Request(
            url,
            headers={'User-Agent': self.USER_AGENT}
        )
        
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                data = json.loads(response.read().decode('utf-8'))
                
            if data.get('lat') and data.get('lon'):
                return GeocodingResult(
                    display_name=data.get('display_name', ''),
                    lat=float(data.get('lat', 0)),
                    lon=float(data.get('lon', 0)),
                    type=data.get('type', 'unknown'),
                    address=data.get('address', {})
                )
        except Exception as e:
            print(f"❌ Reverse geocoding error: {e}")
        
        return None
    
    def search_rwanda_admin(self, admin_level: str, name: str) -> List[GeocodingResult]:
        """
        Search for Rwanda administrative units
        
        Args:
            admin_level: 'province', 'district', 'sector', 'cell', 'village'
            name: Name to search for
            
        Returns:
            List of results
        """
        # Build query based on admin level
        if admin_level == 'province':
            query = f"{name} province Rwanda"
        elif admin_level == 'district':
            query = f"{name} district Rwanda"
        elif admin_level == 'sector':
            query = f"{name} sector Rwanda"
        elif admin_level == 'cell':
            query = f"{name} cell Rwanda"
        elif admin_level == 'village':
            query = f"{name} village Rwanda"
        else:
            query = f"{name} Rwanda"
        
        return self.search(query)


# Singleton instance
_geocoder: Optional[NominatimGeocoder] = None


def get_geocoder() -> NominatimGeocoder:
    """Get singleton geocoder instance"""
    global _geocoder
    if _geocoder is None:
        _geocoder = NominatimGeocoder()
    return _geocoder


def search_location(query: str) -> List[GeocodingResult]:
    """Convenience function for searching locations"""
    return get_geocoder().search(query)


def reverse_geocode(lat: float, lon: float) -> Optional[GeocodingResult]:
    """Convenience function for reverse geocoding"""
    return get_geocoder().reverse(lat, lon)


if __name__ == "__main__":
    # Test the geocoder
    print("Testing Nominatim Geocoder...")
    print()
    
    # Test basic search
    results = search_location("Kimironko")
    print(f"Search 'Kimironko': {len(results)} results")
    for r in results[:3]:
        print(f"  - {r.display_name[:60]}...")
        print(f"    Type: {r.place_type}, Coords: {r.lat}, {r.lon}")
    print()
    
    # Test with district
    results = search_location("Gasabo")
    print(f"Search 'Gasabo': {len(results)} results")
    for r in results[:3]:
        print(f"  - {r.display_name[:60]}...")
    print()
    
    # Test full query
    results = search_location("Bibare Cell Gasabo Rwanda")
    print(f"Search 'Bibare Cell Gasabo Rwanda': {len(results)} results")
    for r in results[:3]:
        print(f"  - {r.display_name[:60]}...")
