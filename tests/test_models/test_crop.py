# ============= tests/test_models/test_crop.py =============
import pytest
from src.models.crop import CropDatabase, CropModel

def test_crop_database():
    """Test crop database"""
    tomato = CropDatabase.get_crop("Tomato")
    
    assert tomato is not None
    assert tomato.name == "Tomato"
    assert tomato.kc_initial > 0
    assert tomato.kc_mid > tomato.kc_initial
    assert tomato.root_depth > 0

def test_all_crops_loadable():
    """Test all crops can be loaded"""
    for crop_name in CropDatabase.CROPS.keys():
        crop = CropDatabase.get_crop(crop_name)
        assert crop is not None
        assert isinstance(crop, CropModel)

def test_invalid_crop():
    """Test invalid crop name"""
    crop = CropDatabase.get_crop("InvalidCrop")
    assert crop is None
