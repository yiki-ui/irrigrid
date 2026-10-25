# API Reference

## Core Modules

### ETOCalculator

```python
from src.core.eto_calculator import ETOCalculator

eto = ETOCalculator.calculate_eto(
    tmin=18.0,
    tmax=28.0,
    rhmin=50,
    rhmax=80,
    wind_speed=2.5,
    sunshine_hours=8,
    latitude=-1.9403,
    elevation=1500,
    day_of_year=150
)
```

### ETCCalculator

```python
from src.core.etc_calculator import ETCCalculator
from src.models.crop import CropDatabase

crop = CropDatabase.get_crop("Tomato")
kc = ETCCalculator.get_kc_value(crop, days_after_planting=30)
etc = ETCCalculator.calculate_etc(eto=5.0, kc=kc)
```

### IrrigationDesignService

```python
from src.core.irrigation_service import IrrigationDesignService
from datetime import datetime

service = IrrigationDesignService()

design = service.design_complete_system(
    crop_name="Tomato",
    soil_type="Clay Loam",
    area_ha=2.0,
    latitude=-1.9403,
    longitude=29.8739,
    elevation=1500,
    planting_date=datetime(2025, 1, 1)
)
```

## AI Modules

### SystemRecommender

```python
from src.ai.recommender import SystemRecommender

recommender = SystemRecommender()

# Get emitter recommendation
emitter = recommender.recommend_emitter("Clay Loam")

# Get complete system design
design = recommender.recommend_system_design(
    area_ha=2.0,
    crop="Tomato",
    soil="Clay Loam",
    budget=5000000
)
```

## Database Operations

### CRUD Operations

```python
from config.database import SessionLocal
from src.database.crud import UserCRUD, ProjectCRUD

db = SessionLocal()

# Create user
user = UserCRUD.create_user(
    db=db,
    username="farmer1",
    email="farmer@example.com",
    hashed_password="hashed_pwd",
    role="farmer"
)

# Create project
project = ProjectCRUD.create_project(
    db=db,
    user_id=user.id,
    name="My Farm",
    province="Kigali",
    district="Gasabo",
    area_hectares=2.0
)
```

## Visualization

### 2D Visualization

```python
from src.visualization.viz_2d import DripSystem2DVisualizer

viz = DripSystem2DVisualizer()
fig = viz.plot_irrigation_schedule(schedule)
fig.savefig("schedule.png")
```

### 3D Visualization

```python
from src.visualization.viz_3d import DripSystem3DVisualizer
import numpy as np

viz3d = DripSystem3DVisualizer()
dem = np.random.rand(100, 100) * 10
terrain = viz3d.create_terrain(dem, bounds=(0, 100, 0, 100))
viz3d.show()
```

## Reports

### PDF Generation

```python
from src.reports.pdf_generator import PDFReportGenerator

pdf = PDFReportGenerator("report.pdf")
pdf.add_title("Irrigation System Design Report")
pdf.add_section("Project Details", "Farm location: Gasabo...")
pdf.build()
```

### Excel Export

```python
from src.reports.export_utils import ExportUtils

ExportUtils.export_to_excel(design_data, "design.xlsx")
ExportUtils.export_to_json(design_data, "design.json")
```
