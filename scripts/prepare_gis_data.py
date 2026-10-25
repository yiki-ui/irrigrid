#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GIS Data Preparation Script
Converts raw shapefiles and rasters to web-ready formats

Requirements: pip install -r requirements_gis_processing.txt
Run once to prepare data, then can uninstall heavy libraries
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

import json
from typing import Dict, List
import warnings
warnings.filterwarnings('ignore')

try:
    import geopandas as gpd
    import rasterio
    from rasterio.warp import calculate_default_transform, reproject, Resampling
    from shapely.geometry import mapping
    HAS_GIS_LIBS = True
except ImportError:
    HAS_GIS_LIBS = False
    print("❌ GIS libraries not installed!")
    print("Install with: pip install -r requirements_gis_processing.txt")
    sys.exit(1)


class GISDataPreparation:
    """Prepare GIS data for web/desktop use"""
    
    def __init__(self, data_dir: str = None):
        """Initialize with data directory"""
        if data_dir is None:
            self.data_dir = Path(__file__).parent.parent / "data" / "gis & hydraulic modeling"
        else:
            self.data_dir = Path(data_dir)
        
        self.output_dir = Path(__file__).parent.parent / "data" / "processed_gis"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"📁 Data directory: {self.data_dir}")
        print(f"📁 Output directory: {self.output_dir}")
    
    def convert_shapefile_to_geojson(self, 
                                     shapefile_path: Path, 
                                     output_name: str = None,
                                     simplify_tolerance: float = None) -> Path:
        """
        Convert shapefile to GeoJSON
        
        Args:
            shapefile_path: Path to .shp file
            output_name: Output filename (without extension)
            simplify_tolerance: Simplification tolerance in degrees (e.g., 0.001)
            
        Returns:
            Path to created GeoJSON file
        """
        print(f"\n🔄 Converting: {shapefile_path.name}")
        
        try:
            # Read shapefile
            gdf = gpd.read_file(shapefile_path)
            
            # Ensure WGS84 (EPSG:4326) for web compatibility
            if gdf.crs and gdf.crs.to_epsg() != 4326:
                print(f"   Reprojecting from {gdf.crs} to EPSG:4326")
                gdf = gdf.to_crs(epsg=4326)
            
            # Simplify geometry if requested (reduces file size)
            if simplify_tolerance:
                print(f"   Simplifying geometry (tolerance={simplify_tolerance})")
                gdf['geometry'] = gdf['geometry'].simplify(simplify_tolerance)
            
            # Create output filename
            if output_name is None:
                output_name = shapefile_path.stem
            output_path = self.output_dir / f"{output_name}.geojson"
            
            # Write GeoJSON
            gdf.to_file(output_path, driver='GeoJSON')
            
            file_size_mb = output_path.stat().st_size / (1024 * 1024)
            print(f"✅ Created: {output_path.name} ({file_size_mb:.2f} MB)")
            print(f"   Features: {len(gdf)}")
            print(f"   CRS: EPSG:4326 (WGS84)")
            
            return output_path
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def extract_dem_metadata(self, dem_path: Path) -> Dict:
        """
        Extract DEM metadata
        
        Args:
            dem_path: Path to DEM file
            
        Returns:
            Dictionary with DEM info
        """
        print(f"\n📊 Analyzing DEM: {dem_path.name}")
        
        try:
            with rasterio.open(dem_path) as src:
                metadata = {
                    'width': src.width,
                    'height': src.height,
                    'bands': src.count,
                    'crs': str(src.crs),
                    'bounds': src.bounds._asdict(),
                    'transform': list(src.transform),
                    'resolution': (src.res[0], src.res[1]),
                    'nodata': src.nodata,
                    'dtype': str(src.dtypes[0])
                }
                
                # Read elevation statistics
                data = src.read(1, masked=True)
                metadata['elevation'] = {
                    'min': float(data.min()),
                    'max': float(data.max()),
                    'mean': float(data.mean()),
                    'std': float(data.std())
                }
                
                print(f"✅ DEM Info:")
                print(f"   Size: {metadata['width']} x {metadata['height']} pixels")
                print(f"   Resolution: {metadata['resolution'][0]:.2f} meters")
                print(f"   CRS: {metadata['crs']}")
                print(f"   Elevation range: {metadata['elevation']['min']:.0f} - {metadata['elevation']['max']:.0f} m")
                
                # Save metadata
                meta_path = self.output_dir / f"{dem_path.stem}_metadata.json"
                with open(meta_path, 'w') as f:
                    json.dump(metadata, f, indent=2)
                print(f"   Saved metadata: {meta_path.name}")
                
                return metadata
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def create_dem_tiles(self, dem_path: Path, zoom_levels: List[int] = None):
        """
        Create DEM tiles for web visualization (placeholder)
        Note: Full implementation requires gdal2tiles
        
        Args:
            dem_path: Path to DEM
            zoom_levels: Zoom levels to generate
        """
        print(f"\n🗺️ DEM Tiling: {dem_path.name}")
        print("   For full tiling, use: gdal2tiles.py")
        print(f"   Command: gdal2tiles.py -z 8-14 {dem_path} output/tiles/")
        print("   (Requires GDAL command-line tools)")
    
    def inspect_shapefile(self, shapefile_path: Path) -> Dict:
        """
        Inspect shapefile and show attributes
        
        Args:
            shapefile_path: Path to shapefile
            
        Returns:
            Dictionary with shapefile info
        """
        print(f"\n🔍 Inspecting: {shapefile_path.name}")
        
        try:
            gdf = gpd.read_file(shapefile_path)
            
            info = {
                'feature_count': len(gdf),
                'crs': str(gdf.crs),
                'bounds': gdf.total_bounds.tolist(),
                'geometry_type': gdf.geom_type.unique().tolist(),
                'columns': gdf.columns.tolist(),
                'column_types': {col: str(dtype) for col, dtype in gdf.dtypes.items()}
            }
            
            print(f"✅ Shapefile Info:")
            print(f"   Features: {info['feature_count']}")
            print(f"   Geometry: {', '.join(info['geometry_type'])}")
            print(f"   CRS: {info['crs']}")
            print(f"   Columns: {len(info['columns'])}")
            
            # Show sample attributes
            if len(gdf.columns) > 1:
                print(f"\n   Attributes:")
                for col in gdf.columns[:10]:  # First 10 columns
                    if col != 'geometry':
                        print(f"      - {col}: {info['column_types'][col]}")
            
            # Show first feature
            if len(gdf) > 0:
                print(f"\n   Sample Feature:")
                for col in gdf.columns:
                    if col != 'geometry':
                        print(f"      {col}: {gdf.iloc[0][col]}")
            
            return info
            
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    def prepare_all_shapefiles(self):
        """Convert all key shapefiles to GeoJSON"""
        
        print("\n" + "="*60)
        print("🚀 STARTING GIS DATA PREPARATION")
        print("="*60)
        
        conversions = [
            # Rivers
            {
                'path': self.data_dir / "rivers" / "River.shp",
                'name': 'rwanda_rivers',
                'simplify': 0.001  # Simplify to reduce file size
            },
            # Catchments
            {
                'path': self.data_dir / "Shape files from RWAFA" / "Catchment_Level1" / "Catchment_Level1.shp",
                'name': 'catchments_level1',
                'simplify': 0.0005
            },
            {
                'path': self.data_dir / "Shape files from RWAFA" / "Catchment_Level2" / "Catchment_Level2.shp",
                'name': 'catchments_level2',
                'simplify': 0.0005
            },
            # Administrative boundaries
            {
                'path': self.data_dir / "Shape files from RWAFA" / "RWA_adm" / "RWA_adm0.shp",
                'name': 'rwanda_boundary',
                'simplify': None
            },
            {
                'path': self.data_dir / "Shape files from RWAFA" / "RWA_adm" / "RWA_adm1.shp",
                'name': 'rwanda_provinces',
                'simplify': 0.0001
            },
            {
                'path': self.data_dir / "Shape files from RWAFA" / "RWA_adm" / "RWA_adm2.shp",
                'name': 'rwanda_districts',
                'simplify': 0.0001
            },
            {
                'path': self.data_dir / "Shape files from RWAFA" / "RWA_adm" / "RWA_adm3.shp",
                'name': 'rwanda_sectors',
                'simplify': 0.0001
            },
            # Rainfall stations
            {
                'path': self.data_dir / "Rainfall data _Phocas" / "Rainfall data" / "climate.shp",
                'name': 'rainfall_stations',
                'simplify': None
            },
            # Erosion control
            {
                'path': self.data_dir / "erosion control" / "Erosion_control_data.shp",
                'name': 'erosion_control',
                'simplify': 0.001  # Large file, significant simplification
            }
        ]
        
        success_count = 0
        for conversion in conversions:
            if conversion['path'].exists():
                result = self.convert_shapefile_to_geojson(
                    conversion['path'],
                    conversion['name'],
                    conversion['simplify']
                )
                if result:
                    success_count += 1
            else:
                print(f"\n⚠️  Not found: {conversion['path']}")
        
        print("\n" + "="*60)
        print(f"✅ Conversion complete: {success_count}/{len(conversions)} files")
        print(f"📁 Output directory: {self.output_dir}")
        print("="*60)
    
    def analyze_dem(self):
        """Analyze DEM data"""
        dem_path = self.data_dir / "dems" / "DEM30_ASHER.tif"
        
        if dem_path.exists():
            self.extract_dem_metadata(dem_path)
            self.create_dem_tiles(dem_path)
        else:
            print(f"⚠️  DEM not found: {dem_path}")
    
    def create_data_catalog(self):
        """Create catalog of all converted data"""
        
        print("\n📋 Creating data catalog...")
        
        catalog = {
            'title': 'Rwanda GIS Data Catalog',
            'description': 'Processed GIS data for irrigation DSS',
            'crs': 'EPSG:4326 (WGS84)',
            'datasets': []
        }
        
        # List all GeoJSON files
        for geojson_file in self.output_dir.glob("*.geojson"):
            try:
                gdf = gpd.read_file(geojson_file)
                dataset = {
                    'name': geojson_file.stem,
                    'file': geojson_file.name,
                    'feature_count': len(gdf),
                    'geometry_type': gdf.geom_type.unique().tolist(),
                    'bounds': gdf.total_bounds.tolist(),
                    'size_mb': geojson_file.stat().st_size / (1024 * 1024)
                }
                catalog['datasets'].append(dataset)
            except Exception as e:
                print(f"   ⚠️  Error reading {geojson_file.name}: {e}")
        
        # Save catalog
        catalog_path = self.output_dir / "data_catalog.json"
        with open(catalog_path, 'w') as f:
            json.dump(catalog, f, indent=2)
        
        print(f"✅ Catalog created: {catalog_path.name}")
        print(f"   Total datasets: {len(catalog['datasets'])}")
        
        return catalog


def main():
    """Main execution"""
    
    print("""
╔══════════════════════════════════════════════════════════════╗
║           GIS DATA PREPARATION TOOLKIT                       ║
║     Convert Shapefiles & Rasters to Web-Ready Formats       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    if not HAS_GIS_LIBS:
        print("❌ Required libraries not installed!")
        print("\nInstall with:")
        print("   pip install -r requirements_gis_processing.txt")
        print("\nOr use conda:")
        print("   conda install -c conda-forge geopandas rasterio")
        return
    
    # Initialize preparation tool
    prep = GISDataPreparation()
    
    # Menu
    print("\nWhat would you like to do?")
    print("1. Convert all shapefiles to GeoJSON")
    print("2. Analyze DEM data")
    print("3. Inspect specific shapefile")
    print("4. Create data catalog")
    print("5. Do everything (full preparation)")
    print("0. Exit")
    
    choice = input("\nEnter choice (0-5): ").strip()
    
    if choice == "1":
        prep.prepare_all_shapefiles()
        prep.create_data_catalog()
    
    elif choice == "2":
        prep.analyze_dem()
    
    elif choice == "3":
        print("\nAvailable shapefiles:")
        print("1. Rivers")
        print("2. Catchments Level 1")
        print("3. Districts")
        print("4. Erosion Control")
        print("5. Rainfall Stations")
        
        sub_choice = input("Select shapefile (1-5): ").strip()
        
        shapefiles = {
            "1": prep.data_dir / "rivers" / "River.shp",
            "2": prep.data_dir / "Shape files from RWAFA" / "Catchment_Level1" / "Catchment_Level1.shp",
            "3": prep.data_dir / "Shape files from RWAFA" / "RWA_adm" / "RWA_adm2.shp",
            "4": prep.data_dir / "erosion control" / "Erosion_control_data.shp",
            "5": prep.data_dir / "Rainfall data _Phocas" / "Rainfall data" / "climate.shp"
        }
        
        if sub_choice in shapefiles:
            prep.inspect_shapefile(shapefiles[sub_choice])
    
    elif choice == "4":
        prep.create_data_catalog()
    
    elif choice == "5":
        print("\n🚀 Running full data preparation...")
        prep.prepare_all_shapefiles()
        prep.analyze_dem()
        prep.create_data_catalog()
        
        print("\n" + "="*60)
        print("✅ FULL PREPARATION COMPLETE!")
        print("="*60)
        print("\nNext steps:")
        print("1. Check output folder: data/processed_gis/")
        print("2. Review data_catalog.json")
        print("3. Use GeoJSON files in your web visualization")
        print("4. (Optional) Uninstall heavy libraries to save space:")
        print("   pip uninstall geopandas rasterio fiona -y")
    
    else:
        print("Exiting...")


if __name__ == "__main__":
    main()
