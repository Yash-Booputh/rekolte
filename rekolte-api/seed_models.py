"""
Registers RF and XGBoost models in MongoDB.
Run once: python seed_models.py
"""
import datetime
from dotenv import load_dotenv
from pymongo import MongoClient
import os

load_dotenv()

client = MongoClient(os.environ["MONGODB_URI"])
db = client["rekolte"]

db.model_config.delete_many({})

models = [
    {
        "type": "RandomForest",
        "filepath": "rf_model.joblib",
        "r_squared": 0.43,
        "rmse": 6.8,
        "mae": 5.2,
        "is_active": False,
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
    {
        "type": "XGBoost",
        "filepath": "xgb_model.joblib",
        "r_squared": 0.51,
        "rmse": 6.2,
        "mae": 4.9,
        "is_active": True,  # XGBoost is active by default (better R²)
        "uploaded_at": datetime.datetime.utcnow(),
        "uploaded_by": "seed",
    },
]

result = db.model_config.insert_many(models)
print(f"Inserted {len(result.inserted_ids)} model configs.")
print("XGBoost set as active model.")
