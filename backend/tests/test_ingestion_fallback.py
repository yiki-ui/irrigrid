#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test suite verifying graceful fallback of NASA POWER and NDVI ingestion
when network connection is deliberately broken.
"""

from unittest.mock import patch
import requests
from backend.ingestion.nasa_power import get_weather_data
from backend.ingestion.ndvi import get_ndvi_data


def test_nasa_power_graceful_fallback_on_network_error():
    """Verify get_weather_data returns valid cached data instead of raising when network fails."""
    # Deliberately raise ConnectionError on requests.get
    with patch("requests.get", side_effect=requests.exceptions.ConnectionError("Simulated network outage")):
        weather = get_weather_data(-1.50, 29.63, timeout_sec=1)
        assert weather is not None
        assert "t_min" in weather
        assert "t_max" in weather
        assert "humidity" in weather
        assert weather["source"] in ["nasa_power_cache", "pre_seeded_cache", "climatology_fallback"]


def test_ndvi_graceful_fallback_and_valid_values():
    """Verify get_ndvi_data returns cached or baseline NDVI without crashing."""
    ndvi_info = get_ndvi_data(-1.50, 29.63)
    assert ndvi_info is not None
    assert 0.0 <= ndvi_info["ndvi"] <= 1.0
    assert "status" in ndvi_info
    assert "kc_multiplier" in ndvi_info
