# ============= src/models/crop.py =============
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class CropModel(BaseModel):
    name: str
    scientific_name: str
    kc_initial: float = Field(ge=0, le=2)
    kc_mid: float = Field(ge=0, le=2)
    kc_end: float = Field(ge=0, le=2)
    root_depth: float = Field(gt=0, description="in meters")
    growth_stages_days: List[int] = Field(default=[30, 40, 50, 30])
    ky: float = Field(default=1.0, description="Yield response factor")
    varieties: List[str] = Field(default=[], description="Common varieties in Rwanda")
    planting_density: int = Field(default=25000, description="plants per hectare")
    water_productivity: float = Field(default=15.0, description="kg/m3")
    expected_yield: float = Field(default=30.0, description="tons per hectare")
    market_price: float = Field(default=500.0, description="RWF per kg")

class CropCreate(BaseModel):
    """Schema for creating a new crop"""
    name: str = Field(..., min_length=2, max_length=100)
    scientific_name: str
    kc_initial: float = Field(ge=0, le=2)
    kc_mid: float = Field(ge=0, le=2)
    kc_end: float = Field(ge=0, le=2)
    root_depth: float = Field(gt=0, description="in meters")
    growth_stages_days: List[int] = Field(default=[30, 40, 50, 30])
    ky: float = Field(default=1.0, description="Yield response factor")

class CropResponse(BaseModel):
    """Schema for crop response"""
    id: int
    name: str
    scientific_name: str
    kc_initial: float
    kc_mid: float
    kc_end: float
    root_depth: float
    ky: float
    
    class Config:
        from_attributes = True

class CropDetail(CropResponse):
    """Detailed crop information"""
    growth_stages_days: List[int]
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
class CropDatabase:
    """Comprehensive Rwanda Crop Database with 25+ crops"""
    CROPS = {
        # VEGETABLES
        "Tomato": {
            "scientific_name": "Solanum lycopersicum",
            "kc_initial": 0.6, "kc_mid": 1.15, "kc_end": 0.8,
            "root_depth": 0.7, "growth_stages_days": [25, 40, 45, 25],
            "ky": 1.05, "varieties": ["Tycoon", "Onyx", "Anna F1", "Saim", "Komeza"],
            "planting_density": 25000, "water_productivity": 15.0,
            "expected_yield": 35.0, "market_price": 600.0
        },
        "Bell Pepper": {
            "scientific_name": "Capsicum annuum",
            "kc_initial": 0.6, "kc_mid": 1.05, "kc_end": 0.9,
            "root_depth": 0.5, "growth_stages_days": [25, 35, 40, 20],
            "ky": 1.1, "varieties": ["California Wonder", "Yolo Wonder"],
            "planting_density": 30000, "water_productivity": 12.0,
            "expected_yield": 25.0, "market_price": 800.0
        },
        "Chili Pepper": {
            "scientific_name": "Capsicum annuum",
            "kc_initial": 0.6, "kc_mid": 1.05, "kc_end": 0.9,
            "root_depth": 0.5, "growth_stages_days": [25, 35, 40, 25],
            "ky": 1.1, "varieties": ["Cayenne", "Habanero", "Local varieties"],
            "planting_density": 35000, "water_productivity": 10.0,
            "expected_yield": 15.0, "market_price": 1200.0
        },
        "Cabbage": {
            "scientific_name": "Brassica oleracea var. capitata",
            "kc_initial": 0.7, "kc_mid": 1.05, "kc_end": 0.95,
            "root_depth": 0.5, "growth_stages_days": [20, 30, 50, 15],
            "ky": 0.95, "varieties": ["Copenhagen Market", "Gloria F1"],
            "planting_density": 40000, "water_productivity": 18.0,
            "expected_yield": 40.0, "market_price": 300.0
        },
        "Broccoli": {
            "scientific_name": "Brassica oleracea var. italica",
            "kc_initial": 0.7, "kc_mid": 1.05, "kc_end": 0.95,
            "root_depth": 0.5, "growth_stages_days": [20, 25, 35, 15],
            "ky": 0.95, "varieties": ["Marathon F1", "Calabrese"],
            "planting_density": 35000, "water_productivity": 16.0,
            "expected_yield": 12.0, "market_price": 1500.0
        },
        "Onion": {
            "scientific_name": "Allium cepa",
            "kc_initial": 0.7, "kc_mid": 1.05, "kc_end": 0.75,
            "root_depth": 0.4, "growth_stages_days": [15, 25, 70, 40],
            "ky": 1.1, "varieties": ["Red Creole", "Bombay Red"],
            "planting_density": 500000, "water_productivity": 14.0,
            "expected_yield": 30.0, "market_price": 400.0
        },
        "Carrot": {
            "scientific_name": "Daucus carota subsp. sativus",
            "kc_initial": 0.7, "kc_mid": 1.05, "kc_end": 0.95,
            "root_depth": 0.5, "growth_stages_days": [20, 30, 60, 20],
            "ky": 1.0, "varieties": ["Nantes", "Kuroda", "Chantenay"],
            "planting_density": 800000, "water_productivity": 16.0,
            "expected_yield": 35.0, "market_price": 350.0
        },
        "Spinach": {
            "scientific_name": "Spinacia oleracea",
            "kc_initial": 0.7, "kc_mid": 1.0, "kc_end": 0.95,
            "root_depth": 0.3, "growth_stages_days": [20, 20, 25, 10],
            "ky": 1.0, "varieties": ["Bloomsdale", "Savoy"],
            "planting_density": 600000, "water_productivity": 12.0,
            "expected_yield": 20.0, "market_price": 500.0
        },
        "Lettuce": {
            "scientific_name": "Lactuca sativa",
            "kc_initial": 0.7, "kc_mid": 1.0, "kc_end": 0.95,
            "root_depth": 0.3, "growth_stages_days": [20, 30, 15, 10],
            "ky": 1.0, "varieties": ["Grand Rapids", "Great Lakes"],
            "planting_density": 80000, "water_productivity": 10.0,
            "expected_yield": 25.0, "market_price": 600.0
        },
        "Cucumber": {
            "scientific_name": "Cucumis sativus",
            "kc_initial": 0.6, "kc_mid": 1.0, "kc_end": 0.75,
            "root_depth": 0.7, "growth_stages_days": [20, 30, 40, 15],
            "ky": 1.1, "varieties": ["Poinsett", "Marketmore"],
            "planting_density": 40000, "water_productivity": 13.0,
            "expected_yield": 40.0, "market_price": 400.0
        },
        
        # FRUITS
        "Avocado": {
            "scientific_name": "Persea americana",
            "kc_initial": 0.6, "kc_mid": 0.85, "kc_end": 0.75,
            "root_depth": 1.0, "growth_stages_days": [60, 120, 120, 60],
            "ky": 0.85, "varieties": ["Hass", "Fuerte", "Pinkerton"],
            "planting_density": 400, "water_productivity": 8.0,
            "expected_yield": 15.0, "market_price": 1500.0
        },
        "Mango": {
            "scientific_name": "Mangifera indica",
            "kc_initial": 0.6, "kc_mid": 0.85, "kc_end": 0.7,
            "root_depth": 1.5, "growth_stages_days": [60, 90, 120, 90],
            "ky": 0.8, "varieties": ["Kent", "Tommy Atkins", "Apple Mango"],
            "planting_density": 200, "water_productivity": 7.0,
            "expected_yield": 20.0, "market_price": 800.0
        },
        "Orange": {
            "scientific_name": "Citrus sinensis",
            "kc_initial": 0.7, "kc_mid": 0.65, "kc_end": 0.7,
            "root_depth": 1.2, "growth_stages_days": [60, 90, 120, 95],
            "ky": 0.8, "varieties": ["Valencia", "Navel"],
            "planting_density": 400, "water_productivity": 9.0,
            "expected_yield": 25.0, "market_price": 500.0
        },
        "Lemon": {
            "scientific_name": "Citrus limon",
            "kc_initial": 0.7, "kc_mid": 0.65, "kc_end": 0.7,
            "root_depth": 1.2, "growth_stages_days": [60, 90, 120, 95],
            "ky": 0.8, "varieties": ["Eureka", "Lisbon"],
            "planting_density": 400, "water_productivity": 8.5,
            "expected_yield": 20.0, "market_price": 600.0
        },
        "Papaya": {
            "scientific_name": "Carica papaya",
            "kc_initial": 0.6, "kc_mid": 0.8, "kc_end": 0.75,
            "root_depth": 0.8, "growth_stages_days": [60, 120, 150, 60],
            "ky": 0.85, "varieties": ["Solo", "Red Lady", "Sunrise"],
            "planting_density": 1600, "water_productivity": 12.0,
            "expected_yield": 50.0, "market_price": 400.0
        },
        "Banana": {
            "scientific_name": "Musa acuminata × balbisiana",
            "kc_initial": 0.5, "kc_mid": 1.1, "kc_end": 1.0,
            "root_depth": 0.6, "growth_stages_days": [120, 90, 120, 60],
            "ky": 1.35, "varieties": ["Cavendish", "Gros Michel", "Local cooking"],
            "planting_density": 2000, "water_productivity": 20.0,
            "expected_yield": 40.0, "market_price": 300.0
        },
        "Pineapple": {
            "scientific_name": "Ananas comosus",
            "kc_initial": 0.5, "kc_mid": 0.3, "kc_end": 0.3,
            "root_depth": 0.3, "growth_stages_days": [60, 120, 600, 10],
            "ky": 0.8, "varieties": ["Smooth Cayenne", "MD2"],
            "planting_density": 50000, "water_productivity": 15.0,
            "expected_yield": 60.0, "market_price": 350.0
        },
        
        # CASH CROPS
        "Coffee Arabica": {
            "scientific_name": "Coffea arabica",
            "kc_initial": 0.9, "kc_mid": 0.95, "kc_end": 0.95,
            "root_depth": 1.5, "growth_stages_days": [90, 90, 120, 60],
            "ky": 0.8, "varieties": ["Bourbon", "Mayaguez 139"],
            "planting_density": 2000, "water_productivity": 0.5,
            "expected_yield": 2.0, "market_price": 3000.0
        },
        "Coffee Robusta": {
            "scientific_name": "Coffea canephora",
            "kc_initial": 0.9, "kc_mid": 0.95, "kc_end": 0.95,
            "root_depth": 1.5, "growth_stages_days": [90, 90, 120, 60],
            "ky": 0.8, "varieties": ["Local clones"],
            "planting_density": 2500, "water_productivity": 0.6,
            "expected_yield": 2.5, "market_price": 2500.0
        },
        "Tea": {
            "scientific_name": "Camellia sinensis",
            "kc_initial": 0.95, "kc_mid": 1.0, "kc_end": 1.0,
            "root_depth": 1.0, "growth_stages_days": [150, 365, 365, 365],
            "ky": 0.9, "varieties": ["Local clones", "Assam"],
            "planting_density": 13000, "water_productivity": 0.8,
            "expected_yield": 3.0, "market_price": 1500.0
        },
        "Cassava": {
            "scientific_name": "Manihot esculenta",
            "kc_initial": 0.3, "kc_mid": 0.8, "kc_end": 0.3,
            "root_depth": 1.0, "growth_stages_days": [20, 40, 90, 60],
            "ky": 0.8, "varieties": ["Local disease-resistant"],
            "planting_density": 10000, "water_productivity": 25.0,
            "expected_yield": 25.0, "market_price": 150.0
        },
        "Maize": {
            "scientific_name": "Zea mays",
            "kc_initial": 0.3, "kc_mid": 1.2, "kc_end": 0.6,
            "root_depth": 1.0, "growth_stages_days": [20, 35, 40, 30],
            "ky": 1.25, "varieties": ["MH14", "WH505", "Hybrid"],
            "planting_density": 53000, "water_productivity": 18.0,
            "expected_yield": 6.0, "market_price": 400.0
        },
        "Beans": {
            "scientific_name": "Phaseolus vulgaris",
            "kc_initial": 0.4, "kc_mid": 1.15, "kc_end": 0.35,
            "root_depth": 0.5, "growth_stages_days": [20, 30, 40, 20],
            "ky": 1.15, "varieties": ["Climbing beans", "Bush beans"],
            "planting_density": 200000, "water_productivity": 12.0,
            "expected_yield": 2.5, "market_price": 800.0
        },
        "Irish Potato": {
            "scientific_name": "Solanum tuberosum",
            "kc_initial": 0.5, "kc_mid": 1.15, "kc_end": 0.75,
            "root_depth": 0.4, "growth_stages_days": [25, 30, 45, 30],
            "ky": 1.1, "varieties": ["Victoria", "Kinigi", "Cruza"],
            "planting_density": 40000, "water_productivity": 20.0,
            "expected_yield": 30.0, "market_price": 250.0
        },
        "Sweet Potato": {
            "scientific_name": "Ipomoea batatas",
            "kc_initial": 0.5, "kc_mid": 1.15, "kc_end": 0.65,
            "root_depth": 1.0, "growth_stages_days": [20, 30, 50, 30],
            "ky": 1.1, "varieties": ["Orange-fleshed", "White-fleshed"],
            "planting_density": 40000, "water_productivity": 22.0,
            "expected_yield": 25.0, "market_price": 200.0
        }
    }
    
    @classmethod
    def get_crop(cls, name: str) -> Optional[CropModel]:
        if name in cls.CROPS:
            data = cls.CROPS[name]
            return CropModel(name=name, **data)
        return None