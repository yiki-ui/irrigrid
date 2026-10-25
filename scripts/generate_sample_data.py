# ============= scripts/generate_sample_data.py =============
"""
Generate sample data for testing
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

def generate_weather_data(days: int = 365):
    """Generate sample weather data"""
    print(f"Generating {days} days of weather data...")
    
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    
    data = {
        'date': dates,
        'tmin': np.random.uniform(15, 20, days),
        'tmax': np.random.uniform(23, 30, days),
        'rainfall': np.random.exponential(5, days),
        'humidity': np.random.uniform(60, 90, days),
        'wind_speed': np.random.uniform(1, 4, days),
        'sunshine_hours': np.random.uniform(5, 10, days)
    }
    
    df = pd.DataFrame(data)
    
    # Create data directory
    data_dir = Path("data/climate")
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    output_file = data_dir / "sample_weather.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✓ Weather data saved to {output_file}")
    return df

def generate_soil_moisture_data(days: int = 30):
    """Generate sample soil moisture tracking data"""
    print(f"Generating {days} days of soil moisture data...")
    
    dates = [datetime.now() - timedelta(days=i) for i in range(days, 0, -1)]
    
    # Simulate soil moisture depletion and refill
    moisture = []
    current = 0
    for _ in range(days):
        # Depletion
        current += np.random.uniform(3, 7)
        # Occasional irrigation
        if current > 30 or np.random.random() < 0.3:
            current = 0
        moisture.append(current)
    
    data = {
        'date': dates,
        'soil_moisture_depletion_mm': moisture,
        'irrigation_applied_mm': [30 if m == 0 else 0 for m in moisture[1:]] + [0]
    }
    
    df = pd.DataFrame(data)
    
    data_dir = Path("data/climate")
    output_file = data_dir / "sample_soil_moisture.csv"
    df.to_csv(output_file, index=False)
    
    print(f"✓ Soil moisture data saved to {output_file}")
    return df

def main():
    print("=" * 60)
    print("Sample Data Generation")
    print("=" * 60)
    
    generate_weather_data(365)
    generate_soil_moisture_data(30)
    
    print("\n✓ Sample data generation complete!")

if __name__ == "__main__":
    main()
