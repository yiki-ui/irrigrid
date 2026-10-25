#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IrriGrid Ingestion: NISR Baseline Survey
Loads bundled NISR agriculture CSV into SQLite cache at startup and serves district data.
"""

import csv
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional

_BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = _BASE_DIR / "cache" / "data.db"
CSV_PATH = _BASE_DIR / "data" / "nisr_ag_survey.csv"


def init_nisr_table(db_path: Path = DB_PATH) -> None:
    """Create nisr_baseline table and populate it from bundled CSV."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nisr_baseline (
                district TEXT PRIMARY KEY,
                province TEXT,
                avg_farm_size_ha REAL,
                main_crops TEXT,
                irrigation_adoption_pct REAL,
                typical_soil TEXT,
                baseline_yield_kg_ha REAL,
                irrigated_yield_kg_ha REAL,
                annual_rainfall_mm REAL
            )
        """)

        if CSV_PATH.exists():
            with open(CSV_PATH, mode="r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = [
                    (
                        r["district"], r["province"], float(r["avg_farm_size_ha"]),
                        r["main_crops"], float(r["irrigation_adoption_pct"]),
                        r["typical_soil"], float(r["baseline_yield_kg_ha"]),
                        float(r["irrigated_yield_kg_ha"]), float(r["annual_rainfall_mm"])
                    )
                    for r in reader
                ]
                cur.executemany("""
                    INSERT OR REPLACE INTO nisr_baseline VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, rows)
        conn.commit()


def get_district_baseline(district: str, db_path: Path = DB_PATH) -> Optional[Dict]:
    """Fetch baseline stats for a specific district (case-insensitive)."""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT * FROM nisr_baseline WHERE LOWER(district) = LOWER(?)", (district.strip(),))
            row = cur.fetchone()
        return dict(row) if row else None
    except Exception:
        return None


def list_all_districts(db_path: Path = DB_PATH) -> List[Dict]:
    """List all districts with provinces and baseline summaries."""
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT district, province, typical_soil, avg_farm_size_ha, main_crops FROM nisr_baseline ORDER BY district")
            rows = [dict(r) for r in cur.fetchall()]
        return rows
    except Exception:
        return []


if __name__ == "__main__":
    init_nisr_table()
    d = get_district_baseline("Musanze")
    print(f"Loaded NISR baseline. Musanze: {d}")
