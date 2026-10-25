#!/usr/bin/env python
import math
# -*- coding: utf-8 -*-
"""
NASA POWER API Client
Access to NASA's Prediction of Worldwide Energy Resources (POWER) database
for agricultural and climate data

API Documentation: https://power.larc.nasa.gov/docs/
No API key required for basic use

FIX LOG:
- [CRITICAL] Removed incorrect kWh -> MJ conversion (ALLSKY_SFC_SW_DWN in AG 
  community is already MJ/m2/day). This was causing ETo to be ~2x too high.
- [MINOR] elevation is now a parameter instead of hardcoded 1500m
"""

import os
import requests
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import time
import math


class NASAPowerAPI:
    """
    Client for NASA POWER API

    Provides access to:
    - Solar radiation data
    - Temperature (min, max, avg)
    - Humidity
    - Wind speed
    - Precipitation
    - Historical climate data (1981-present)
    """

    BASE_URL = "https://power.larc.nasa.gov/api/temporal"

    # NASA POWER parameter codes
    PARAMETERS = {
        'T2M': 'Temperature at 2 Meters (C)',
        'T2M_MIN': 'Minimum Temperature at 2 Meters (C)',
        'T2M_MAX': 'Maximum Temperature at 2 Meters (C)',
        'T2MDEW': 'Dew/Frost Point at 2 Meters (C)',
        'RH2M': 'Relative Humidity at 2 Meters (%)',
        'PRECTOTCORR': 'Precipitation Corrected (mm/day)',
        'WS2M': 'Wind Speed at 2 Meters (m/s)',
        'WS10M': 'Wind Speed at 10 Meters (m/s)',
        # NOTE: In AG community this is MJ/m2/day NOT kWh/m2/day
        'ALLSKY_SFC_SW_DWN': 'All Sky Surface Shortwave Downward Irradiance (MJ/m2/day)',
    }

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self.session = requests.Session()
        contact_email = os.getenv("CONTACT_EMAIL", "").strip()
        ua = f"IrrigationDSS/1.0 ({contact_email})" if contact_email else "IrrigationDSS/1.0 (Agricultural Research)"
        self.session.headers.update({
            'User-Agent': ua,
            'Accept': 'application/json'
        })

    def get_daily_data(
        self,
        latitude: float,
        longitude: float,
        start_date: str,
        end_date: str,
        parameters: Optional[List[str]] = None
    ) -> Dict:
        if parameters is None:
            parameters = [
                'T2M', 'T2M_MIN', 'T2M_MAX', 'T2MDEW',
                'RH2M', 'PRECTOTCORR', 'WS2M',
                'ALLSKY_SFC_SW_DWN'
            ]

        url = f"{self.BASE_URL}/daily/point"
        params = {
            'parameters': ','.join(parameters),
            'community': 'AG',
            'longitude': longitude,
            'latitude': latitude,
            'start': start_date,
            'end': end_date,
            'format': 'JSON'
        }

        try:
            print(f"[NASA] Fetching POWER data for ({latitude}, {longitude})...")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            print(f"[NASA] Received data for {len(parameters)} parameters")
            return data
        except requests.exceptions.Timeout:
            print(f"[NASA] API timeout - servers may be slow, try again")
            raise
        except requests.exceptions.RequestException as e:
            print(f"[NASA] API error: {e}")
            raise

    def get_climatology(
        self,
        latitude: float,
        longitude: float,
        parameters: Optional[List[str]] = None
    ) -> Dict:
        if parameters is None:
            parameters = [
                'T2M', 'T2M_MIN', 'T2M_MAX', 'T2MDEW',
                'RH2M', 'PRECTOTCORR', 'WS2M',
                'ALLSKY_SFC_SW_DWN'
            ]

        url = f"{self.BASE_URL}/climatology/point"
        params = {
            'parameters': ','.join(parameters),
            'community': 'AG',
            'longitude': longitude,
            'latitude': latitude,
            'format': 'JSON'
        }

        try:
            print(f"[NASA] Fetching climatology for ({latitude}, {longitude})...")
            response = self.session.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            data = response.json()
            print(f"[NASA] Received climatology data")
            return data
        except Exception as e:
            print(f"[NASA] Climatology error: {e}")
            raise

    def get_monthly_averages(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int] = None
    ) -> Dict[str, List[float]]:
        if year:
            start_date = f"{year}0101"
            end_date = f"{year}1231"
            data = self.get_daily_data(latitude, longitude, start_date, end_date)
            return self._calculate_monthly_averages(data)
        else:
            data = self.get_climatology(latitude, longitude)
            return self._extract_monthly_from_climatology(data)

    def _calculate_monthly_averages(self, daily_data: Dict) -> Dict[str, List[float]]:
        try:
            parameters = daily_data['properties']['parameter']
            monthly_avgs = {}

            for param_name, daily_values in parameters.items():
                months = [[] for _ in range(12)]
                for date_str, value in daily_values.items():
                    if value == -999:
                        continue
                    try:
                        date = datetime.strptime(date_str, '%Y%m%d')
                        months[date.month - 1].append(value)
                    except:
                        continue
                monthly_avgs[param_name] = [
                    sum(month_data) / len(month_data) if month_data else 0
                    for month_data in months
                ]
            return monthly_avgs
        except Exception as e:
            print(f"Error calculating monthly averages: {e}")
            return {}

    def _extract_monthly_from_climatology(self, climatology_data: Dict) -> Dict[str, List[float]]:
        try:
            parameters = climatology_data['properties']['parameter']
            monthly_data = {}
            month_keys = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN',
                          'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']

            for param_name, values in parameters.items():
                if isinstance(values, dict):
                    monthly_values = []
                    for month_key in month_keys:
                        val = values.get(month_key, 0)
                        if val == -999 or val is None:
                            val = 0
                        monthly_values.append(val)
                    monthly_data[param_name] = monthly_values
                elif isinstance(values, (int, float)):
                    monthly_data[param_name] = [values / 12] * 12
            return monthly_data
        except Exception as e:
            print(f"Error extracting climatology: {e}")
            import traceback
            traceback.print_exc()
            return {}

    def get_irrigation_parameters(
        self,
        latitude: float,
        longitude: float,
        year: Optional[int] = None,
        elevation: float = 1500.0
    ) -> Dict:
        """
        Get irrigation-specific climate parameters.

        Args:
            latitude:  Decimal degrees (negative = south)
            longitude: Decimal degrees
            year:      Specific year or None for 30-year climatology
            elevation: Site elevation in metres (default 1500 for Rwanda highlands)

        Returns:
            Dictionary with irrigation parameters formatted for DSS use
        """
        monthly_data = self.get_monthly_averages(latitude, longitude, year)

        if not monthly_data:
            return {}

        days_in_month = [31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
        rainfall_daily = monthly_data.get('PRECTOTCORR', [0] * 12)
        rainfall_monthly = [rainfall_daily[i] * days_in_month[i] for i in range(12)]

        # ----------------------------------------------------------------
        # CRITICAL FIX: ALLSKY_SFC_SW_DWN from NASA AG community is
        # already in MJ/m2/day.  The old code multiplied by 3.6
        # (kWh->MJ conversion) which is WRONG and caused ETo to be ~2x
        # too high.  We now use the values directly.
        # ----------------------------------------------------------------
        solar_radiation_mj = monthly_data.get('ALLSKY_SFC_SW_DWN', [0] * 12)

        irrigation_params = {
            'temperature':          monthly_data.get('T2M',          [0] * 12),
            'temp_min':             monthly_data.get('T2M_MIN',       [0] * 12),
            'temp_max':             monthly_data.get('T2M_MAX',       [0] * 12),
            'temp_dew':             monthly_data.get('T2MDEW',        [0] * 12),
            'rainfall_mm':          rainfall_monthly,
            'humidity':             monthly_data.get('RH2M',          [0] * 12),
            'wind_speed':           monthly_data.get('WS2M',          [0] * 12),
            # Keep raw field for transparency; label clarifies units
            'solar_radiation_mj':   solar_radiation_mj,
        }

        # Calculate ETo using the corrected solar radiation
        eto_daily = self._calculate_fao56_eto(
            temp_min=irrigation_params['temp_min'],
            temp_max=irrigation_params['temp_max'],
            temp_dew=irrigation_params['temp_dew'],
            humidity=irrigation_params['humidity'],
            wind_speed=irrigation_params['wind_speed'],
            solar_radiation=irrigation_params['solar_radiation_mj'],
            latitude=latitude,
            elevation=elevation          # <-- now passed in, not hardcoded
        )

        irrigation_params['eto_monthly_mm'] = [
            eto_daily[i] * days_in_month[i] for i in range(12)
        ]
        irrigation_params['eto_daily_mm'] = eto_daily

        irrigation_params['source']     = 'NASA POWER (FAO-56 PM)'
        irrigation_params['latitude']   = latitude
        irrigation_params['longitude']  = longitude
        irrigation_params['year']       = year or 'Climatology (30-year avg)'
        irrigation_params['eto_method'] = 'FAO-56 Penman-Monteith'

        return irrigation_params

    def _calculate_fao56_eto(
        self,
        temp_min: List[float],
        temp_max: List[float],
        temp_dew: List[float],
        humidity: List[float],
        wind_speed: List[float],
        solar_radiation: List[float],
        latitude: float,
        elevation: float = 1500.0      # <-- now a real parameter
    ) -> List[float]:
        """
        Calculate reference evapotranspiration using FAO-56 Penman-Monteith.

        FAO-56 Eq. 6:
        ETo = (0.408*Delta*(Rn-G) + gamma*(900/(T+273))*u2*(es-ea))
              / (Delta + gamma*(1+0.34*u2))

        Args:
            solar_radiation: Monthly Rs in MJ/m2/day (NOT kWh — already converted)
            elevation:       Site elevation in metres
        """
        eto_monthly = []

        for month in range(12):
            T_min  = temp_min[month]
            T_max  = temp_max[month]
            T_dew  = temp_dew[month] if temp_dew else T_min - 2
            u2     = wind_speed[month]
            Rs     = solar_radiation[month]   # MJ/m2/day — correct units

            if T_min == 0 and T_max == 0:
                eto_monthly.append(0.0)
                continue

            T_mean = (T_max + T_min) / 2

            # 1. Atmospheric pressure — FAO-56 Eq. 7
            P = 101.3 * ((293 - 0.0065 * elevation) / 293) ** 5.26

            # 2. Psychrometric constant — FAO-56 Eq. 8
            gamma = 0.000665 * P

            # 3. Slope of saturation vapour pressure curve — FAO-56 Eq. 13
            delta = (4098 * 0.6108 * math.exp((17.27 * T_mean) /
                     (T_mean + 237.3))) / (T_mean + 237.3) ** 2

            # 4. Saturation vapour pressure — FAO-56 Eq. 11
            es_tmax = 0.6108 * math.exp((17.27 * T_max) / (T_max + 237.3))
            es_tmin = 0.6108 * math.exp((17.27 * T_min) / (T_min + 237.3))
            es = (es_tmax + es_tmin) / 2

            # 5. Actual vapour pressure — FAO-56 Eq. 14 (dew point preferred)
            if T_dew is not None and T_dew > -50:
                ea = 0.6108 * math.exp((17.27 * T_dew) / (T_dew + 237.3))
            else:
                ea = es * (humidity[month] / 100) if humidity[month] > 0 else es * 0.5

            # 6. Radiation calculations
            Gsc         = 0.0820                          # solar constant MJ/m2/min
            day_of_year = 15 + month * 30                 # mid-month
            lat_rad     = math.radians(latitude)

            dr          = 1 + 0.033 * math.cos(2 * math.pi * day_of_year / 365)
            delta_solar = 0.409 * math.sin(2 * math.pi * day_of_year / 365 - 1.39)
            ws          = math.acos(-math.tan(lat_rad) * math.tan(delta_solar))

            # Extraterrestrial radiation — FAO-56 Eq. 21
            Ra = (24 * 60 / math.pi) * Gsc * dr * (
                ws * math.sin(lat_rad) * math.sin(delta_solar) +
                math.cos(lat_rad) * math.cos(delta_solar) * math.sin(ws)
            )

            # Clear-sky radiation — FAO-56 Eq. 37
            Rso = (0.75 + 2e-5 * elevation) * Ra

            # Use provided Rs; fall back to Angstrom estimate
            Rs_actual = Rs if Rs > 0 else (0.25 + 0.5 * 0.5) * Ra

            # Net shortwave — FAO-56 Eq. 38
            Rns = (1 - 0.23) * Rs_actual

            # Net longwave — FAO-56 Eq. 39
            sigma = 4.903e-9
            Rnl = sigma * (
                ((T_max + 273.16) ** 4 + (T_min + 273.16) ** 4) / 2
            ) * (0.34 - 0.14 * math.sqrt(max(ea, 0))) * (
                1.35 * Rs_actual / Rso - 0.35
            )

            Rn = Rns - Rnl   # Net radiation — FAO-56 Eq. 40
            G  = 0           # Soil heat flux = 0 for daily (FAO-56 assumption)

            # 7. FAO-56 Penman-Monteith — Eq. 6
            denominator = delta + gamma * (1 + 0.34 * u2)
            if denominator == 0:
                eto_monthly.append(0.0)
                continue

            numerator = (
                0.408 * delta * (Rn - G) +
                gamma * (900 / (T_mean + 273)) * u2 * (es - ea)
            )

            eto_monthly.append(max(0.0, round(numerator / denominator, 3)))

        return eto_monthly

    @staticmethod
    def validate_coordinates(latitude: float, longitude: float) -> bool:
        return -90 <= latitude <= 90 and -180 <= longitude <= 180

    @staticmethod
    def format_date(date: datetime) -> str:
        return date.strftime('%Y%m%d')


# ============= Helper Functions =============

def get_rwanda_climate_from_nasa(
    latitude: float,
    longitude: float,
    elevation: float = 1500.0
) -> Dict:
    api = NASAPowerAPI()
    return api.get_irrigation_parameters(latitude, longitude, elevation=elevation)


# ============= Test/Demo =============

if __name__ == "__main__":
    print("=" * 70)
    print("NASA POWER API - IRRIGATION DSS INTEGRATION TEST")
    print("=" * 70)
    print()

    kigali_lat  = -1.9536
    kigali_lon  = 30.0606
    kigali_elev = 1567.0   # metres

    print(f"Testing with Kigali, Rwanda:")
    print(f"  Latitude:  {kigali_lat}")
    print(f"  Longitude: {kigali_lon}")
    print(f"  Elevation: {kigali_elev} m")
    print()

    try:
        api = NASAPowerAPI()

        print("[1] Fetching irrigation parameters from NASA POWER...")
        irrigation_data = api.get_irrigation_parameters(
            kigali_lat, kigali_lon, elevation=kigali_elev
        )

        if irrigation_data:
            print("\n[OK] Successfully retrieved NASA climate data!")
            print(f"\nSource: {irrigation_data['source']}")
            print(f"Period: {irrigation_data['year']}")
            print()

            months = ['Jan','Feb','Mar','Apr','May','Jun',
                      'Jul','Aug','Sep','Oct','Nov','Dec']

            print(f"{'Month':<8} {'Temp(C)':>10} {'Rain(mm)':>10} "
                  f"{'RH(%)':>8} {'Wind(m/s)':>10} "
                  f"{'ETo(mm/day)':>12} {'ETo(mm/mo)':>12}")
            print("-" * 75)

            for i in range(12):
                print(f"{months[i]:<8} "
                      f"{irrigation_data['temperature'][i]:>10.1f} "
                      f"{irrigation_data['rainfall_mm'][i]:>10.0f} "
                      f"{irrigation_data['humidity'][i]:>8.1f} "
                      f"{irrigation_data['wind_speed'][i]:>10.2f} "
                      f"{irrigation_data['eto_daily_mm'][i]:>12.3f} "
                      f"{irrigation_data['eto_monthly_mm'][i]:>12.1f}")

            print()
            avg_eto = sum(irrigation_data['eto_daily_mm']) / 12
            print(f"Annual Summary:")
            print(f"  Avg Temperature : {sum(irrigation_data['temperature'])/12:.1f} C")
            print(f"  Total Rainfall  : {sum(irrigation_data['rainfall_mm']):.0f} mm/year")
            print(f"  Avg Humidity    : {sum(irrigation_data['humidity'])/12:.1f}%")
            print(f"  Avg ETo         : {avg_eto:.3f} mm/day  "
                  f"(expected 3.5-5.0 for Kigali)")
            print(f"  Total ETo       : {sum(irrigation_data['eto_monthly_mm']):.0f} mm/year")

        print()
        print("=" * 70)
        print("[OK] NASA POWER API TEST COMPLETE!")
        print("=" * 70)

    except Exception as e:
        print(f"[FAILED] Test failed: {e}")
        import traceback
        traceback.print_exc()