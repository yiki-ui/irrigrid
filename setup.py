# ============================================
# FILE: setup.py
# Setup script for package installation
# ============================================

from setuptools import setup, find_packages

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="irrigation-dss",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="AI-Based Decision Support System for Low-Cost Semi-Portable Drip Irrigation Design",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/irrigation-dss",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Agriculture",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    entry_points={
        "console_scripts": [
            "irrigation-dss=gui.main:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.kv", "*.json", "*.csv", "*.png", "*.jpg"],
    },
)
