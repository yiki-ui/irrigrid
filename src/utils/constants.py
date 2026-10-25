# ============= src/utils/constants.py =============
"""Application constants"""

# Physical constants
LATENT_HEAT_VAPORIZATION = 2.45  # MJ/kg
SPECIFIC_HEAT_AIR = 1.013e-3  # MJ/kg/°C
STEFAN_BOLTZMANN = 4.903e-9  # MJ/K⁴/m²/day
SOLAR_CONSTANT = 0.0820  # MJ/m²/min

# Drip irrigation parameters
DEFAULT_EMITTER_FLOW_RATE = 2.0  # L/h
DEFAULT_EMITTER_SPACING = 0.3  # m
DEFAULT_LATERAL_SPACING = 0.75  # m
DEFAULT_SYSTEM_EFFICIENCY = 0.90  # 90%

# Soil moisture thresholds
CRITICAL_DEPLETION = 0.5  # 50% of RAW
REFILL_POINT = 0.35  # 35% of RAW

# Economic parameters
DEFAULT_WATER_COST = 0.5  # $/m³
DEFAULT_LABOR_COST = 5.0  # $/hour
DEFAULT_POWER_COST = 0.15  # $/kWh