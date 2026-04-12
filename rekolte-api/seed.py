"""
Run once to seed MongoDB with harvest data and pre-harvest satellite features.
Usage: python seed.py
"""
import sys
import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
MODEL_DIR   = os.path.join(os.path.dirname(__file__), "..", "model")
CSV_DIR     = MODEL_DIR
FINAL_DIR   = os.path.join(MODEL_DIR, "final_notebook_output")

client = MongoClient(MONGODB_URI)
db = client["rekolte"]

# ── Hardcoded external climate indicators (computed in 02_pre_harvest_training_v3.ipynb) ──
# Cyclone: max sustained wind (km/h) within 200 km of Mauritius, Jan-May (IBTRACS v04r00)
CYCLONE_LOOKUP = {
    2009:   0.0, 2010:   0.0, 2011:   0.0, 2012:   0.0,
    2013:  55.6, 2014: 101.9, 2015:   0.0, 2016:   0.0,
    2017:  70.4, 2018: 120.4, 2019:   0.0,
    2020:  70.4, 2021:  40.7, 2022:   0.0, 2023:   0.0,
    2024:   0.0, 2025:   0.0,
}

# ENSO: ONI anomaly for DJF of prediction year (Dec Y-1 + Jan Y + Feb Y), NOAA CPC
ENSO_LOOKUP = {
    2009: -0.85, 2010:  1.50, 2011: -1.31, 2012: -0.72,
    2013: -0.29, 2014: -0.28, 2015:  0.69, 2016:  2.63,
    2017: -0.19, 2018: -0.77, 2019:  0.89, 2020:  0.64,
    2021: -0.91, 2022: -0.82, 2023: -0.54, 2024:  1.92,
    2025: -0.45,
}


def seed_harvest():
    path = os.path.join(CSV_DIR, "season_end_data.csv")
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        doc = {
            "season":            int(row["season"]),
            "week":              int(row["bulletin_number"]) if pd.notna(row.get("bulletin_number")) else None,
            "region":            str(row["region"]).upper(),
            "surface_harvested": float(row["surface_harvested"]) if pd.notna(row.get("surface_harvested")) else None,
            "cane_production":   float(row["cane_production"])   if pd.notna(row.get("cane_production"))   else None,
            "sugar_production":  float(row["sugar_production"])  if pd.notna(row.get("sugar_production"))  else None,
            "extraction_rate":   float(row["extraction_rate"])   if pd.notna(row.get("extraction_rate"))   else None,
            "tch":               float(row["tch"])               if pd.notna(row.get("tch"))               else None,
            "tsh":               float(row["tsh"])               if pd.notna(row.get("tsh"))               else None,
            "source_bulletin":   str(row.get("source_file", "")),
        }
        db.harvest_data.update_one(
            {"season": doc["season"], "region": doc["region"]},
            {"$set": doc},
            upsert=True,
        )
        count += 1
    print(f"Seeded {count} harvest records.")


def seed_pre_harvest():
    feat_path    = os.path.join(FINAL_DIR, "pre_harvest_features.csv")
    harvest_path = os.path.join(CSV_DIR,   "season_end_data.csv")

    df      = pd.read_csv(feat_path)
    df_harv = pd.read_csv(harvest_path)
    df["region"] = df["region"].str.upper()

    # ── Build surface_prev lookup: surface_harvested in season Y-1 ────────────
    surf = (
        df_harv[["season", "region", "surface_harvested"]]
        .copy()
        .assign(region=lambda x: x["region"].str.upper())
    )
    surf_lookup = surf.set_index(["region", "season"])["surface_harvested"].to_dict()

    # ── Derived NDVI features (match training notebook exactly) ───────────────
    df["ndvi_growth"]       = df["ndvi_may"] - df["ndvi_oct"]
    df["ndvi_jan_may_mean"] = df[["ndvi_jan","ndvi_feb","ndvi_mar","ndvi_apr","ndvi_may"]].mean(axis=1)

    # ── External climate indicators ───────────────────────────────────────────
    df["cyclone_max_wind"] = df["season"].map(CYCLONE_LOOKUP).fillna(0.0)
    df["enso_oni_djf"]     = df["season"].map(ENSO_LOOKUP).fillna(0.0)

    count = 0
    for _, row in df.iterrows():
        region = str(row["region"]).upper()
        season = int(row["season"])

        # surface_prev: harvested area of previous season
        surface_prev = surf_lookup.get((region, season - 1))
        if surface_prev is None or pd.isna(surface_prev):
            surface_prev = surf_lookup.get((region, season))  # fallback: own season
        if surface_prev is None or pd.isna(surface_prev):
            surface_prev = 5000.0  # global fallback

        doc = {
            "season":  season,
            "region":  region,
            # Lagged NDVI (previous season Jun-Dec)
            "ndvi_lag_mean":        float(row["ndvi_lag_mean"]),
            "ndvi_lag_max":         float(row["ndvi_lag_max"]),
            "ndvi_lag_std":         float(row["ndvi_lag_std"]),
            "ndvi_lag_cumulative":  float(row["ndvi_lag_cumulative"]),
            # Lagged climate
            "rainfall_lag_total":   float(row["rainfall_lag_total"]),
            "temp_lag_mean":        float(row["temp_lag_mean"]),
            # MODIS NDVI Oct-May
            "ndvi_oct":   float(row["ndvi_oct"]),
            "ndvi_nov":   float(row["ndvi_nov"]),
            "ndvi_dec":   float(row["ndvi_dec"]),
            "ndvi_jan":   float(row["ndvi_jan"]),
            "ndvi_feb":   float(row["ndvi_feb"]),
            "ndvi_mar":   float(row["ndvi_mar"]),
            "ndvi_apr":   float(row["ndvi_apr"]),
            "ndvi_may":   float(row["ndvi_may"]),
            # CHIRPS monthly rainfall Oct-May
            "rainfall_oct": float(row["rainfall_oct"]),
            "rainfall_nov": float(row["rainfall_nov"]),
            "rainfall_dec": float(row["rainfall_dec"]),
            "rainfall_jan": float(row["rainfall_jan"]),
            "rainfall_feb": float(row["rainfall_feb"]),
            "rainfall_mar": float(row["rainfall_mar"]),
            "rainfall_apr": float(row["rainfall_apr"]),
            "rainfall_may": float(row["rainfall_may"]),
            # ERA5 monthly temperature Oct-May
            "temp_oct": float(row["temp_oct"]),
            "temp_nov": float(row["temp_nov"]),
            "temp_dec": float(row["temp_dec"]),
            "temp_jan": float(row["temp_jan"]),
            "temp_feb": float(row["temp_feb"]),
            "temp_mar": float(row["temp_mar"]),
            "temp_apr": float(row["temp_apr"]),
            "temp_may": float(row["temp_may"]),
            # Derived features
            "ndvi_growth":       float(row["ndvi_growth"]),
            "ndvi_jan_may_mean": float(row["ndvi_jan_may_mean"]),
            # External climate indicators
            "cyclone_max_wind": float(row["cyclone_max_wind"]),
            "enso_oni_djf":     float(row["enso_oni_djf"]),
            # Harvested area from previous season
            "surface_prev": float(surface_prev),
        }
        db.pre_harvest_features.update_one(
            {"season": season, "region": region},
            {"$set": doc},
            upsert=True,
        )
        count += 1
    print(f"Seeded {count} pre-harvest feature records (39-feature v3 schema).")


if __name__ == "__main__":
    print("Seeding harvest data...")
    seed_harvest()
    print("Seeding pre-harvest features...")
    seed_pre_harvest()
    print("Done.")
