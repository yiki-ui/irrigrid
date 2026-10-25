# User Manual

## AI-Based Drip Irrigation Design System

### Getting Started

#### Running the Application

1. **GUI Mode** (Full Application):
   ```bash
   python main.py
   ```

2. **Demo Mode** (Command Line):
   ```bash
   python demo.py
   ```

### Using the GUI

#### 1. Login Screen
- Default credentials: `demo` / `demo123`
- Or register a new account

#### 2. Dashboard
- View active projects
- Access system tools
- Monitor water savings

#### 3. Creating a New Project

**Step 1: Project Information**
- Enter project name
- Select province and district
- Enter sector name

**Step 2: Farm Details**
- Select crop type from database
- Enter farm area (hectares)
- Select soil type

**Step 3: System Design**
- System automatically generates optimal design
- View emitter specifications
- Review cost estimates

**Step 4: Results**
- Irrigation schedule
- Water requirements
- Economic analysis
- 2D/3D visualizations

### Features

#### Water Requirements Calculation
- Automatic ETo calculation using FAO Penman-Monteith
- Crop-specific ETc based on growth stage
- Daily soil water balance

#### System Design
- AI-powered component selection
- Optimal emitter spacing
- Lateral and mainline sizing
- Pump requirements

#### Economic Analysis
- Complete cost breakdown
- ROI calculation
- Payback period
- Water savings estimation

#### Reports
- PDF reports
- Excel exports
- Bill of Materials
- Irrigation schedules

### Tips for Best Results

1. **Accurate Location**: Provide precise GPS coordinates for better weather data
2. **Soil Testing**: Use actual soil test results when available
3. **Regular Updates**: Update irrigation schedules based on actual rainfall
4. **System Maintenance**: Follow maintenance recommendations

### Supported Crops

- Tomato
- Bell Pepper
- Cabbage
- Onion
- Carrot
- Avocado
- Mango
- Banana

### Supported Soil Types

- Sandy Loam
- Loam
- Clay Loam
- Silty Loam
- Sandy Clay Loam
- Clay
