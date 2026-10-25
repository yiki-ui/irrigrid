# Irrigation Components - 3D Assets

Place your Blender-exported GLB files here.

## 📋 Asset Checklist (36 Components)

### ✅ Water System
- [ ] `water_tank_500L.glb` - 500 liter water tank
- [ ] `water_tank_1000L.glb` - 1000 liter water tank
- [ ] `pump_centrifugal.glb` - Centrifugal pump
- [ ] `filter_sand.glb` - Sand/media filter
- [ ] `filter_disc.glb` - Disc filter
- [ ] `filter_screen.glb` - Screen filter

### ✅ Control Components
- [ ] `pressure_regulator.glb` - Pressure regulator
- [ ] `control_valve.glb` - Manual control valve
- [ ] `venturi_injector.glb` - Venturi fertilizer injector
- [ ] `pressure_gauge.glb` - Pressure gauge

### ✅ Pipes
- [ ] `mainline_hdpe_32mm.glb` - HDPE main pipe 32mm
- [ ] `mainline_hdpe_40mm.glb` - HDPE main pipe 40mm
- [ ] `submain_ldpe_25mm.glb` - LDPE submain 25mm
- [ ] `lateral_ldpe_16mm.glb` - LDPE lateral 16mm

### ✅ Fittings
- [ ] `elbow_90deg.glb` - 90° elbow connector
- [ ] `tee_connector.glb` - T-junction connector
- [ ] `reducer.glb` - Pipe reducer
- [ ] `end_cap.glb` - Pipe end cap
- [ ] `air_release_valve.glb` - Air release valve

### ✅ Emitters
- [ ] `emitter_inline.glb` - Inline drip emitter
- [ ] `emitter_online.glb` - Online drip emitter
- [ ] `takeoff_connector.glb` - Take-off connector
- [ ] `grommet.glb` - Rubber grommet
- [ ] `end_plug.glb` - Lateral end plug
- [ ] `drip_stake.glb` - Drip stake support
- [ ] `flow_control_valve.glb` - Flow control valve
- [ ] `pc_dripper.glb` - Pressure compensating dripper
- [ ] `coupler.glb` - Pipe coupler/joiner

### ✅ Sensors & Automation
- [ ] `moisture_sensor.glb` - Soil moisture sensor
- [ ] `pressure_sensor.glb` - Pressure sensor
- [ ] `flow_meter.glb` - Water flow meter
- [ ] `solenoid_valve.glb` - Electric solenoid valve
- [ ] `controller_box.glb` - Irrigation controller

### ✅ Power System
- [ ] `solar_panel.glb` - Solar panel
- [ ] `battery.glb` - Battery unit

---

## 🎨 Creating Assets in Blender

### Quick Steps:
1. **Model** the component (keep it simple!)
2. **Optimize** geometry (500-2000 triangles)
3. **Apply** modifiers
4. **Add** material/color
5. **Export** as GLB:
   - File → Export → glTF 2.0 (.glb)
   - Format: **GLB (Binary)**
   - Include: ✅ Normals, ✅ UVs
   - Geometry: ✅ Apply Modifiers

### Triangle Budget:
| Component Type | Target Triangles |
|----------------|------------------|
| Small (emitter, connector) | 200-500 |
| Medium (valve, gauge) | 500-1000 |
| Large (filter, pump) | 1000-2000 |
| Very Large (tank) | 1500-3000 |

---

## 💻 Loading in Code

### Automatic Discovery:
```python
from rendering import ModelLoader

loader = ModelLoader()
library = loader.get_asset_library()

# Shows all available assets
print(library)
# {'emitter_inline': 'assets/models/irrigation/emitter_inline.glb', ...}
```

### Load Specific Asset:
```python
# By name
emitter = loader.load_glb("assets/models/irrigation/emitter_inline.glb")

# From library
if 'emitter_inline' in library:
    emitter = loader.load_glb(library['emitter_inline'])

# Add to scene
scene.add_object(emitter, position=(10, 0.1, 5))
```

### Check What's Available:
```bash
python list_available_assets.py
```

---

## 📏 Recommended Dimensions (Real-World Scale)

Use **meters** as units in Blender:

| Component | Typical Size |
|-----------|-------------|
| Inline Emitter | 0.03m × 0.02m |
| Lateral Pipe (16mm) | 0.016m diameter |
| Mainline Pipe (40mm) | 0.04m diameter |
| Water Tank (500L) | 0.8m diameter × 1.5m height |
| Pump | 0.4m × 0.3m × 0.3m |
| Filter | 0.5m diameter × 1.2m height |
| Pressure Gauge | 0.06m diameter |

---

## 🎨 Recommended Colors

```python
# Use these colors for consistency
PIPE_BLACK = (0.1, 0.1, 0.1)
PIPE_GRAY = (0.3, 0.3, 0.3)
EMITTER_GREEN = (0.1, 0.3, 0.1)
TANK_BLUE = (0.2, 0.5, 0.9)
FILTER_YELLOW = (0.9, 0.7, 0.2)
PUMP_RED = (0.8, 0.2, 0.2)
VALVE_BRASS = (0.7, 0.6, 0.3)
SENSOR_WHITE = (0.9, 0.9, 0.9)
```

---

## ✅ Validation Checklist

Before exporting, verify:
- [ ] Triangle count < 2000
- [ ] Scale applied (Ctrl+A → Scale)
- [ ] Rotation applied (Ctrl+A → Rotation)
- [ ] Location at origin (Alt+G)
- [ ] Normals facing outward
- [ ] No overlapping faces
- [ ] Material assigned
- [ ] Proper naming (lowercase, underscores)

---

## 🚀 Priority Order

Start with these essential components:

1. **Inline Emitter** (most common, used hundreds of times)
2. **Lateral Pipe 16mm** (connects emitters)
3. **Tee Connector** (connects laterals to submain)
4. **Water Tank** (water source)
5. **Mainline Pipe** (main distribution)

Then expand to filters, valves, sensors, etc.

---

## 💡 Tips

- **Start simple**: Basic shapes work great!
- **Test early**: Export and test in engine frequently
- **Reuse models**: Copy and modify existing assets
- **Use primitives**: Engine has built-in cube/sphere/cylinder if needed
- **Optimize later**: Get it working first, optimize second

---

**Need help? See:**
- `BLENDER_ASSET_CREATION_GUIDE.md` - Detailed creation guide
- `3D_RENDERING_ENGINE_GUIDE.md` - Engine documentation
- `rendering/example_usage.py` - Code examples
