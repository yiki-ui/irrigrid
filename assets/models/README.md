# 3D Models Directory

Place your Blender-exported GLB files here.

## Folder Structure

```
models/
├── irrigation/          # Irrigation system components
│   ├── water_tank_500L.glb
│   ├── pump_centrifugal.glb
│   ├── filter_sand.glb
│   ├── emitter_inline.glb
│   └── ... (36 components total)
│
├── terrain/            # Ground and terrain elements
│   ├── soil_bed_flat.glb
│   ├── soil_bed_raised.glb
│   └── ground_stake.glb
│
└── crops/              # Crop/plant models
    ├── tomato_plant.glb
    ├── pepper_plant.glb
    └── lettuce_plant.glb
```

## Export Settings (Blender)

1. **File → Export → glTF 2.0 (.glb)**
2. **Format**: GLB (Binary)
3. **Include**: ✅ Normals, ✅ UVs
4. **Geometry**: ✅ Apply Modifiers
5. **Target**: 500-2000 triangles per asset

## Naming Convention

Use lowercase with underscores:
- `component_type_variant.glb`
- Examples:
  - `emitter_inline_2lph.glb`
  - `pipe_ldpe_16mm.glb`
  - `tank_vertical_1000L.glb`

## Loading in Code

```python
from rendering import ModelLoader

loader = ModelLoader(models_directory="assets/models")

# Load model
asset = loader.load_glb("assets/models/irrigation/emitter_inline.glb")

# Add to scene
scene.add_object(asset, position=(0, 0, 0))
```

## Asset Checklist

See **BLENDER_ASSET_CREATION_GUIDE.md** for detailed instructions on creating each component.

### Priority Assets (Start Here):
1. ✅ Inline Emitter (300-500 triangles)
2. ✅ Lateral Pipe 16mm (100-200 triangles)
3. ✅ Water Tank 500L (800-1200 triangles)
4. ✅ Tee Connector (300-500 triangles)

### Full List (36 Components):
See **3D_ENGINE_SUMMARY.md** for complete asset list.

---

**Note**: The engine works with primitive shapes (cube, sphere, cylinder, pipe) even without GLB files. Create assets gradually as needed.
