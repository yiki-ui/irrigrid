#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Backend Entrypoint (FastAPI)
Stateless decision support API for smallholder drip irrigation design in Rwanda.
"""

from contextlib import asynccontextmanager
from pathlib import Path
import sys

# Ensure repository root is in Python path for access to src/ if needed
_BASE_DIR = Path(__file__).resolve().parent.parent
if str(_BASE_DIR) not in sys.path:
    sys.path.insert(0, str(_BASE_DIR))

from dotenv import load_dotenv
load_dotenv(_BASE_DIR / ".env")
load_dotenv()

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.routes import districts, climate, vegetation, optimize, ai_agronomist, layout, agronomy
from backend.ingestion.nisr_baseline import init_nisr_table
from backend.ingestion.nasa_power import init_nasa_cache
from backend.ingestion.ndvi import init_ndvi_cache


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup initialization: verify SQLite cache tables."""
    init_nisr_table()
    init_nasa_cache()
    init_ndvi_cache()
    yield


app = FastAPI(
    title="IrriGrid API",
    description="Stateless single-purpose drip irrigation design engine for Rwanda smallholders",
    version="1.0.0",
    lifespan=lifespan
)

cors_origins_env = os.getenv("CORS_ORIGINS", "").strip()
if cors_origins_env:
    cors_origins = [orig.strip() for orig in cors_origins_env.split(",") if orig.strip()]
else:
    cors_origins = ["https://irrigrid.pages.dev", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API v1 Router Registration
app.include_router(districts.router, prefix="/api/v1")
app.include_router(climate.router, prefix="/api/v1")
app.include_router(vegetation.router, prefix="/api/v1")
app.include_router(optimize.router, prefix="/api/v1")
app.include_router(ai_agronomist.router, prefix="/api/v1")
app.include_router(layout.router, prefix="/api/v1")
app.include_router(agronomy.router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "app": "IrriGrid API",
        "description": "Stateless smallholder drip irrigation design tool",
        "version": "1.0.0",
        "status": "operational",
        "docs": "/docs"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
