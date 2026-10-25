#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick GIS Data Inspector
Inspect raw GIS files without full conversion

This script works WITHOUT geopandas if not installed
Shows basic file information and structure
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import struct
from typing import Dict, List

# Try to import GIS libraries (optional)
try:
    import geopandas as gpd
    HAS_GEOPANDAS = True
except ImportError:
    HAS_GEOPANDAS = False


class GISInspector:
    """Inspect GIS files with or without geopandas"""
    
    def __init__(self, data_dir: str = None):
        """Initialize inspector"""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "data" / "gis & hydraulic modeling"
        else:
            self.data_dir = Path(data_dir)
    
    def read_shp_header(self, shp_path: Path) -> Dict:
        """
        Read shapefile header (works without geopandas)
        
        Args:
            shp_path: Path to .shp file
            
        Returns:
            Dict with basic info
        """
        try:
            with open(shp_path, 'rb') as f:
                # Read header (100 bytes)
                header = f.read(100)
                
                # File code (should be 9994)
                file_code = struct.unpack('>i', header[0:4])[0]
                
                # File length (in 16-bit words)
                file_length_words = struct.unpack('>i', header[24:28])[0]
                file_length_bytes = file_length_words * 2
                
                # Version
                version = struct.unpack('<i', header[28:32])[0]
                
                # Shape type
                shape_type_code = struct.unpack('<i', header[32:36])[0]
                shape_types = {
                    0: "Null",
                    1: "Point",
                    3: "Polyline",
                    5: "Polygon",
                    8: "MultiPoint",
                    11: "PointZ",
                    13: "PolylineZ",
                    15: "PolygonZ",
                    18: "MultiPointZ",
                    21: "PointM",
                    23: "PolylineM",
                    25: "PolygonM",
                    28: "MultiPointM",
                    31: "MultiPatch"
                }
                shape_type = shape_types.get(shape_type_code, f"Unknown ({shape_type_code})")
                
                # Bounding box
                xmin = struct.unpack('<d', header[36:44])[0]
                ymin = struct.unpack('<d', header[44:52])[0]
                xmax = struct.unpack('<d', header[52:60])[0]
                ymax = struct.unpack('<d', header[60:68])[0]
                
                return {
                    'file_code': file_code,
                    'file_size_mb': file_length_bytes / (1024 * 1024),
                    'version': version,
                    'shape_type': shape_type,
                    'bounds': {
                        'xmin': xmin,
                        'ymin': ymin,
                        'xmax': xmax,
                        'ymax': ymax
                    }
                }
        except Exception as e:
            return {'error': str(e)}
    
    def read_dbf_header(self, dbf_path: Path) -> Dict:
        """
        Read DBF (attribute table) header
        
        Args:
            dbf_path: Path to .dbf file
            
        Returns:
            Dict with field info
        """
        try:
            with open(dbf_path, 'rb') as f:
                # Read header
                header = f.read(32)
                
                # Number of records
                num_records = struct.unpack('<I', header[4:8])[0]
                
                # Header size
                header_size = struct.unpack('<H', header[8:10])[0]
                
                # Record size
                record_size = struct.unpack('<H', header[10:12])[0]
                
                # Read field descriptors
                fields = []
                f.seek(32)  # Skip to field descriptors
                
                while True:
                    field_desc = f.read(32)
                    if field_desc[0] == 0x0D:  # End of field descriptors
                        break
                    
                    # Field name (null-terminated)
                    field_name = field_desc[0:11].decode('ascii', errors='ignore').strip('\x00')
                    
                    # Field type
                    field_type_code = chr(field_desc[11])
                    field_types = {
                        'C': 'Character',
                        'N': 'Numeric',
                        'F': 'Float',
                        'D': 'Date',
                        'L': 'Logical',
                        'M': 'Memo'
                    }
                    field_type = field_types.get(field_type_code, field_type_code)
                    
                    # Field length
                    field_length = field_desc[16]
                    
                    fields.append({
                        'name': field_name,
                        'type': field_type,
                        'length': field_length
                    })
                
                return {
                    'num_records': num_records,
                    'num_fields': len(fields),
                    'fields': fields
                }
        except Exception as e:
            return {'error': str(e)}
    
    def read_prj_file(self, prj_path: Path) -> str:
        """
        Read projection file
        
        Args:
            prj_path: Path to .prj file
            
        Returns:
            WKT string
        """
        try:
            with open(prj_path, 'r') as f:
                return f.read().strip()
        except Exception as e:
            return f"Error: {e}"
    
    def inspect_shapefile_basic(self, shp_path: Path):
        """
        Basic inspection without geopandas
        
        Args:
            shp_path: Path to .shp file
        """
        print(f"\n{'='*60}")
        print(f"📄 SHAPEFILE: {shp_path.name}")
        print(f"{'='*60}")
        
        # Check if files exist
        base_path = shp_path.with_suffix('')
        shp_file = base_path.with_suffix('.shp')
        dbf_file = base_path.with_suffix('.dbf')
        prj_file = base_path.with_suffix('.prj')
        
        print(f"\n📁 Files:")
        for ext in ['.shp', '.shx', '.dbf', '.prj', '.cpg']:
            file = base_path.with_suffix(ext)
            if file.exists():
                size_mb = file.stat().st_size / (1024 * 1024)
                print(f"   ✅ {file.name} ({size_mb:.2f} MB)")
            else:
                print(f"   ❌ {file.name} (missing)")
        
        # Read .shp header
        if shp_file.exists():
            print(f"\n🗺️  Geometry Info:")
            shp_info = self.read_shp_header(shp_file)
            if 'error' not in shp_info:
                print(f"   Shape Type: {shp_info['shape_type']}")
                print(f"   File Size: {shp_info['file_size_mb']:.2f} MB")
                print(f"   Bounds:")
                print(f"      X: {shp_info['bounds']['xmin']:.4f} to {shp_info['bounds']['xmax']:.4f}")
                print(f"      Y: {shp_info['bounds']['ymin']:.4f} to {shp_info['bounds']['ymax']:.4f}")
            else:
                print(f"   Error: {shp_info['error']}")
        
        # Read .dbf header
        if dbf_file.exists():
            print(f"\n📊 Attribute Info:")
            dbf_info = self.read_dbf_header(dbf_file)
            if 'error' not in dbf_info:
                print(f"   Records: {dbf_info['num_records']:,}")
                print(f"   Fields: {dbf_info['num_fields']}")
                print(f"\n   Field List:")
                for field in dbf_info['fields'][:15]:  # Show first 15 fields
                    print(f"      - {field['name']}: {field['type']} ({field['length']})")
                if len(dbf_info['fields']) > 15:
                    print(f"      ... and {len(dbf_info['fields']) - 15} more fields")
            else:
                print(f"   Error: {dbf_info['error']}")
        
        # Read .prj file
        if prj_file.exists():
            print(f"\n🌐 Projection:")
            prj_text = self.read_prj_file(prj_file)
            # Show first 100 chars
            print(f"   {prj_text[:100]}...")
    
    def inspect_shapefile_full(self, shp_path: Path):
        """
        Full inspection with geopandas
        
        Args:
            shp_path: Path to .shp file
        """
        if not HAS_GEOPANDAS:
            print("\n⚠️  Geopandas not installed. Using basic inspection...")
            self.inspect_shapefile_basic(shp_path)
            return
        
        print(f"\n{'='*60}")
        print(f"📄 SHAPEFILE (Full): {shp_path.name}")
        print(f"{'='*60}")
        
        try:
            gdf = gpd.read_file(shp_path)
            
            print(f"\n📊 Summary:")
            print(f"   Features: {len(gdf):,}")
            print(f"   Geometry Type: {', '.join(gdf.geom_type.unique())}")
            print(f"   CRS: {gdf.crs}")
            print(f"   Bounds: {gdf.total_bounds}")
            
            print(f"\n📋 Attributes ({len(gdf.columns)} columns):")
            for col in gdf.columns:
                if col != 'geometry':
                    dtype = gdf[col].dtype
                    non_null = gdf[col].notna().sum()
                    print(f"   - {col}: {dtype} ({non_null:,} non-null)")
            
            print(f"\n🔍 Sample Data (first feature):")
            if len(gdf) > 0:
                for col in gdf.columns:
                    if col != 'geometry':
                        value = gdf.iloc[0][col]
                        print(f"   {col}: {value}")
            
            # Geometry stats
            print(f"\n📐 Geometry Statistics:")
            areas = gdf.geometry.area
            print(f"   Area (degrees²):")
            print(f"      Min: {areas.min():.6f}")
            print(f"      Max: {areas.max():.6f}")
            print(f"      Mean: {areas.mean():.6f}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
    
    def list_all_shapefiles(self):
        """List all shapefiles in data directory"""
        print(f"\n{'='*60}")
        print(f"📁 AVAILABLE SHAPEFILES")
        print(f"{'='*60}")
        print(f"Location: {self.data_dir}\n")
        
        shapefiles = list(self.data_dir.rglob("*.shp"))
        
        if not shapefiles:
            print("No shapefiles found!")
            return []
        
        for i, shp in enumerate(shapefiles, 1):
            rel_path = shp.relative_to(self.data_dir)
            size_mb = shp.stat().st_size / (1024 * 1024)
            print(f"{i:2d}. {rel_path}")
            print(f"    Size: {size_mb:.2f} MB")
        
        return shapefiles
    
    def inspect_dem(self, dem_path: Path):
        """
        Inspect DEM/raster file
        
        Args:
            dem_path: Path to DEM file
        """
        print(f"\n{'='*60}")
        print(f"🏔️  DEM/RASTER: {dem_path.name}")
        print(f"{'='*60}")
        
        if not dem_path.exists():
            print("❌ File not found!")
            return
        
        size_mb = dem_path.stat().st_size / (1024 * 1024)
        print(f"\n📁 File Size: {size_mb:.2f} MB")
        
        # Check for metadata files
        metadata_files = ['.tfw', '.aux.xml', '.ovr']
        print(f"\n📄 Associated Files:")
        for ext in metadata_files:
            meta_file = Path(str(dem_path) + ext)
            if meta_file.exists():
                meta_size = meta_file.stat().st_size / 1024
                print(f"   ✅ {meta_file.name} ({meta_size:.1f} KB)")
        
        # Try to read with rasterio if available
        try:
            import rasterio
            with rasterio.open(dem_path) as src:
                print(f"\n🗺️  Raster Info:")
                print(f"   Dimensions: {src.width} x {src.height} pixels")
                print(f"   Bands: {src.count}")
                print(f"   CRS: {src.crs}")
                print(f"   Resolution: {src.res[0]:.2f} x {src.res[1]:.2f} meters")
                print(f"   Bounds: {src.bounds}")
                
                # Read elevation stats
                data = src.read(1, masked=True)
                print(f"\n📊 Elevation Statistics:")
                print(f"   Min: {data.min():.1f} m")
                print(f"   Max: {data.max():.1f} m")
                print(f"   Mean: {data.mean():.1f} m")
                print(f"   Std Dev: {data.std():.1f} m")
        except ImportError:
            print(f"\n⚠️  rasterio not installed - install for detailed info")
            print(f"   pip install rasterio")
        except Exception as e:
            print(f"\n❌ Error reading raster: {e}")


def auto_inspect_all():
    """Automatically inspect all key GIS datasets"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║              GIS DATA INSPECTOR - AUTO MODE                  ║
║    Automatic inspection of all GIS files                    ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if HAS_GEOPANDAS:
        print("✅ Geopandas available - Full inspection enabled\n")
    else:
        print("⚠️  Geopandas not installed - Basic inspection only\n")
    
    inspector = GISInspector()
    
    # Key datasets to inspect
    key_datasets = [
        ("Rivers", "rivers/River.shp"),
        ("Catchment Level 1", "Shape files from RWAFA/Catchment_Level1/Catchment_Level1.shp"),
        ("Catchment Level 2", "Shape files from RWAFA/Catchment_Level2/Catchment_Level2.shp"),
        ("Districts (Admin Level 2)", "Shape files from RWAFA/RWA_adm/RWA_adm2.shp"),
        ("Rainfall Stations", "Rainfall data _Phocas/Rainfall data/climate.shp"),
        ("Erosion Control", "erosion control/Erosion_control_data.shp"),
    ]
    
    print("="*60)
    print("INSPECTING ALL KEY DATASETS")
    print("="*60)
    
    # Inspect shapefiles
    for name, rel_path in key_datasets:
        shp_path = inspector.data_dir / rel_path
        if shp_path.exists():
            if HAS_GEOPANDAS:
                inspector.inspect_shapefile_full(shp_path)
            else:
                inspector.inspect_shapefile_basic(shp_path)
        else:
            print(f"\n{'='*60}")
            print(f"❌ {name}: NOT FOUND")
            print(f"{'='*60}")
            print(f"   Expected: {rel_path}\n")
    
    # Inspect DEM
    dem_path = inspector.data_dir / "dems" / "DEM30_ASHER.tif"
    if dem_path.exists():
        inspector.inspect_dem(dem_path)
    else:
        print(f"\n{'='*60}")
        print(f"❌ DEM: NOT FOUND")
        print(f"{'='*60}")
        print(f"   Expected: dems/DEM30_ASHER.tif\n")
    
    print("\n" + "="*60)
    print("✅ INSPECTION COMPLETE")
    print("="*60)


def main():
    """Main menu"""
    
    import sys
    
    # Check for --auto flag
    if len(sys.argv) > 1 and sys.argv[1] == '--auto':
        auto_inspect_all()
        return
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║              GIS DATA INSPECTOR                              ║
║    Quick inspection of shapefiles and raster data           ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if HAS_GEOPANDAS:
        print("✅ Geopandas available - Full inspection enabled")
    else:
        print("⚠️  Geopandas not installed - Basic inspection only")
        print("   Install with: pip install geopandas")
    
    inspector = GISInspector()
    
    while True:
        print("\n" + "="*60)
        print("MAIN MENU")
        print("="*60)
        print("1. List all shapefiles")
        print("2. Inspect specific shapefile")
        print("3. Inspect DEM")
        print("4. Quick overview of key datasets")
        print("5. AUTO-INSPECT ALL (no prompts)")
        print("0. Exit")
        
        choice = input("\nEnter choice (0-5): ").strip()
        
        if choice == "0":
            print("\nExiting...")
            break
        
        elif choice == "1":
            shapefiles = inspector.list_all_shapefiles()
            
            if shapefiles:
                try:
                    num = int(input("\nEnter number to inspect (0 to skip): "))
                    if 0 < num <= len(shapefiles):
                        if HAS_GEOPANDAS:
                            inspector.inspect_shapefile_full(shapefiles[num-1])
                        else:
                            inspector.inspect_shapefile_basic(shapefiles[num-1])
                except ValueError:
                    pass
        
        elif choice == "2":
            print("\nKey datasets:")
            datasets = {
                "1": "rivers/River.shp",
                "2": "Shape files from RWAFA/Catchment_Level1/Catchment_Level1.shp",
                "3": "Shape files from RWAFA/Catchment_Level2/Catchment_Level2.shp",
                "4": "Shape files from RWAFA/RWA_adm/RWA_adm2.shp",
                "5": "Rainfall data _Phocas/Rainfall data/climate.shp",
                "6": "erosion control/Erosion_control_data.shp"
            }
            
            for key, path in datasets.items():
                print(f"   {key}. {path}")
            
            sub = input("\nSelect dataset (1-6): ").strip()
            if sub in datasets:
                shp_path = inspector.data_dir / datasets[sub]
                if shp_path.exists():
                    if HAS_GEOPANDAS:
                        inspector.inspect_shapefile_full(shp_path)
                    else:
                        inspector.inspect_shapefile_basic(shp_path)
                else:
                    print(f"❌ Not found: {shp_path}")
        
        elif choice == "3":
            dem_path = inspector.data_dir / "dems" / "DEM30_ASHER.tif"
            inspector.inspect_dem(dem_path)
        
        elif choice == "4":
            print("\n🚀 Quick Overview of Key Datasets\n")
            
            key_files = [
                ("Rivers", "rivers/River.shp"),
                ("Catchments L1", "Shape files from RWAFA/Catchment_Level1/Catchment_Level1.shp"),
                ("Districts", "Shape files from RWAFA/RWA_adm/RWA_adm2.shp"),
                ("Rainfall", "Rainfall data _Phocas/Rainfall data/climate.shp"),
                ("DEM", "dems/DEM30_ASHER.tif")
            ]
            
            for name, rel_path in key_files:
                file_path = inspector.data_dir / rel_path
                if file_path.exists():
                    size_mb = file_path.stat().st_size / (1024 * 1024)
                    print(f"✅ {name:15s}: {size_mb:7.2f} MB - {rel_path}")
                else:
                    print(f"❌ {name:15s}: Missing - {rel_path}")
        
        elif choice == "5":
            auto_inspect_all()
            break


if __name__ == "__main__":
    main()
