# ============= scripts/install_dependencies.py =============
"""
Install and verify dependencies
"""
import subprocess
import sys

def install_dependencies():
    """Install all required packages"""
    print("Installing dependencies...")
    
    try:
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", "-r", "requirements.txt"
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Error installing dependencies: {e}")
        return False

def verify_imports():
    """Verify critical imports"""
    critical_packages = [
        'numpy', 'pandas', 'sklearn', 'xgboost',
        'pyvista', 'matplotlib', 'kivy', 'sqlalchemy',
        'geopandas', 'folium', 'reportlab'
    ]
    
    print("\nVerifying critical packages...")
    failed = []
    
    for package in critical_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package}")
            failed.append(package)
    
    if failed:
        print(f"\n✗ Failed to import: {', '.join(failed)}")
        return False
    else:
        print("\n✓ All critical packages verified")
        return True

if __name__ == "__main__":
    if install_dependencies() and verify_imports():
        print("\n✓ Installation complete and verified!")
    else:
        print("\n✗ Installation encountered issues")
        sys.exit(1)