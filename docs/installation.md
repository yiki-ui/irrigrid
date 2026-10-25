# Installation Guide

## AI-Based Drip Irrigation DSS for Rwanda

### System Requirements

- **Operating System**: Windows 10/11, Linux, or macOS
- **Python**: 3.10 or higher
- **RAM**: 8GB minimum (16GB recommended)
- **Disk Space**: ~3GB for dependencies
- **Internet**: Required for weather API and package installation

### Installation Steps

#### 1. Install Python

Download and install Python 3.10+ from [python.org](https://www.python.org/downloads/)

#### 2. Create Virtual Environment

```bash
python -m venv venv
```

#### 3. Activate Virtual Environment

**Windows:**
```bash
venv\Scripts\activate
```

**Linux/macOS:**
```bash
source venv/bin/activate
```

#### 4. Install Dependencies

```bash
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

#### 5. Initialize Database

```bash
python scripts/setup_database.py
```

### Troubleshooting

#### PyVista Installation Issues

If PyVista fails to install on Windows:
```bash
pip install --upgrade pip
pip install pyvista --no-cache-dir
```

#### Kivy Installation Issues

```bash
pip install kivy[base] kivy[media]
pip install kivymd
```

### Verification

Run the demo to verify installation:
```bash
python demo.py
```
