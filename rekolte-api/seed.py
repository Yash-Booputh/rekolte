"""
Run once to seed MongoDB with harvest data and satellite features from CSV files.
Usage: python seed.py
"""
import sys
import os
import pandas as pd
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv()

MONGODB_URI = os.environ["MONGODB_URI"]
CSV_DIR = os.path.join(os.path.dirname(__file__), "..", "model")

client = MongoClient(MONGODB_URI)
db = client["rekolte"]

def seed_harvest():
    path = os.path.join(CSV_DIR, "season_end_data.csv")
    df = pd.read_csv(path)
    count = 0
    for _, row in df.iterrows():
        doc = {
            "season": int(row["season"]),
            "week": int(row["bulletin_number"]) if pd.notna(row.get("bulletin_number")) else None,
            "region": str(row["region"]).upper(),
            "surface_harvested": float(row["surface_harvested"]) if pd.notna(row.get("surface_harvested")) else None,
            "cane_production": float(row["cane_production"]) if pd.notna(row.get("cane_production")) else None,
            "sugar_production": float(row["sugar_production"]) if pd.notna(row.get("sugar_production")) else None,
            "extraction_rate": float(row["extraction_rate"]) if pd.notna(row.get("extraction_rate")) else None,
            "tch": float(row["tch"]) if pd.notna(row.get("tch")) else None,
            "tsh": float(row["tsh"]) if pd.notna(row.get("tsh")) else None,
            "source_bulletin": str(row.get("source_file", "")),
        }
        db.harvest_data.update_one(
            {"season": doc["season"], "region": doc["region"]},
            {"$set": doc},
            upsert=True,
        )
        count += 1
    print(f"Seeded {count} harvest records.")

NDVI_MONTHLY   = ["ndvi_june", "ndvi_july", "ndvi_aug", "ndvi_sep", "ndvi_oct", "ndvi_nov", "ndvi_dec"]
RAIN_MONTHLY   = ["rainfall_june", "rainfall_july", "rainfall_aug", "rainfall_sep", "rainfall_oct", "rainfall_nov", "rainfall_dec"]
TEMP_MONTHLY   = ["temp_june", "temp_july", "temp_aug", "temp_sep", "temp_oct", "temp_nov", "temp_dec"]

def seed_satellite():
    path = os.path.join(CSV_DIR, "satellite_features.csv")
    df = pd.read_csv(path)

    # Impute missing monthly NDVI with row ndvi_mean (matches training notebook)
    for col in NDVI_MONTHLY:
        if col in df.columns:
            df[col] = df[col].fillna(df["ndvi_mean"])

    count = 0
    for _, row in df.iterrows():
        ndvi_monthly = {col: float(row[col]) if col in df.columns and pd.notna(row.get(col)) else None
                        for col in NDVI_MONTHLY}
        rain_monthly = {col: float(row[col]) if col in df.columns and pd.notna(row.get(col)) else None
                        for col in RAIN_MONTHLY}
        temp_monthly = {col: float(row[col]) if col in df.columns and pd.notna(row.get(col)) else None
                        for col in TEMP_MONTHLY}

        doc = {
            "season":            int(row["season"]),
            "region":            str(row["region"]).upper(),
            "satellite":         str(row.get("satellite", "")),   # landsat7 / landsat8 / sentinel2
            "satellite_source":  str(row.get("satellite", "")),   # kept for backwards compat
            "observation_count": int(row["observation_count"]) if pd.notna(row.get("observation_count")) else 0,
            "ndvi_mean":         float(row["ndvi_mean"])         if pd.notna(row.get("ndvi_mean"))        else None,
            "ndvi_max":          float(row["ndvi_max"])          if pd.notna(row.get("ndvi_max"))         else None,
            "ndvi_cumulative":   float(row["ndvi_cumulative"])   if pd.notna(row.get("ndvi_cumulative"))  else None,
            **ndvi_monthly,
            **rain_monthly,
            **temp_monthly,
        }
        db.satellite_features.update_one(
            {"season": doc["season"], "region": doc["region"]},
            {"$set": doc},
            upsert=True,
        )
        count += 1
    print(f"Seeded {count} satellite feature records (NDVI + rainfall + temperature).")

if __name__ == "__main__":
    print("Seeding harvest data...")
    seed_harvest()
    print("Seeding satellite features...")
    seed_satellite()
    print("Done.")
