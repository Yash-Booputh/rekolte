# Rékolte - Sugarcane Yield Prediction System

**Student:** Yashvin Booputh (M01006629)
**Module:** CST3990 Undergraduate Individual Projects - Middlesex University Mauritius (Spring 2025/2026)
**Supervisor:** Mr Reekesh Kumar Lall

Predicts sugarcane TCH (tonnes cane per hectare) across 5 regions of Mauritius by combining 18 years of harvest bulletin data (2008–2025) with MODIS/Landsat/Sentinel-2 satellite imagery via Google Earth Engine, served through a Flask REST API and an Ionic + Vue 3 dashboard.

---

## Quick Links

| Resource                                 | Link                                                                                    |
| ---------------------------------------- | --------------------------------------------------------------------------------------- |
| GitHub Repository                        | https://github.com/Yash-Booputh/rekolte                                                 |
| Live API (Render)                        | https://rekolte.onrender.com                                                            |
| Google Drive — all project files        | https://drive.google.com/drive/folders/19xcPdUTKmQ6SwwywC3ESEJSsSCLgvisH?usp=drive_link |
| Dataset —`season_end_data.csv`        | https://drive.google.com/file/d/1rf0nmIoWNOl-Rswx6n0FnQXDDUVqik3V/view?usp=drive_link   |
| Notebook 1 — Feature Extraction         | https://drive.google.com/file/d/1z9OR0ND42NLBqnyyrq2H4B6JTrD2KK46/view?usp=drive_link   |
| Notebook 2 — Model Training (v3)        | https://drive.google.com/file/d/11ZnWg68qbV5ZrSmZOZ400AbpfD9k32Ud/view?usp=drive_link   |
| Harvest Bulletins 2008–2025 (~500 PDFs) | https://drive.google.com/drive/folders/1kM8gtdRc3eIqdlBBooZDix-6-44VA1zD?usp=drive_link |
| Live Frontend (GitHub Pages)             | https://yash-booputh.github.io/rekolte/                                               |
| GEE Project ID                           | `rekolte-491422` (project number: 228444571212)                                       |

> **Note:** The API on Render is on a free tier and may take ~30 seconds to wake up on first request (UptimeRobot pings it every 5 minutes to keep it warm).

---

## Repository Structure

```
Rékolte/
├── model/                          # ML pipeline notebooks and data
│   ├── season_end_data.csv         # Master dataset: 90 rows (18 seasons × 5 regions)
│   ├── 01_pre_harvest_extraction.ipynb   # GEE feature extraction (run on Colab)
│   └── 02_pre_harvest_training_v3.ipynb  # Model training — v3 XGBoost (run on Colab)
├── rekolte-api/                    # Flask backend (deployed on Render)
│   ├── app.py                      # App factory, 7 blueprints
│   ├── routes/                     # auth, predict, harvest, bulletins, model_mgmt, reports, notifications
│   ├── models/                     # Trained model files
│   └── requirements.txt
└── sugarcane-yield-app/            # Ionic 8 + Vue 3 frontend
    ├── src/views/                  # 5 views: Login, Dashboard, RegionDetail, HistoricalData, ModelComparison
    └── src/services/api.ts         # All API calls
```

---

## ML Pipeline

The pipeline runs on Google Colab and requires access to the GEE project `rekolte-491422`. Both notebooks are already computed — outputs and model files are saved to the Google Drive folder linked above.

### Notebook 1 — Feature Extraction (`01_pre_harvest_extraction.ipynb`)

Extracts pre-harvest features for each region and season using Google Earth Engine:

- **MODIS MOD13Q1** — NDVI, 16-day composites, Oct(Y-1) to May(Y) window
- **CHIRPS** — Monthly rainfall, Oct to May
- **ERA5-Land** — Monthly mean temperature, Oct to May
- **IBTRACS** — Cyclone max wind speed within 200 km of Mauritius, Jan to May
- **NOAA CPC ONI** — ENSO anomaly for DJF of the prediction year

Output: `pre_harvest_features.csv` → saved to Drive `model_v3/`

To run:

1. Open in Google Colab
2. Authenticate with a Google account that has access to GEE project `rekolte-491422`
3. Run all cells — outputs are written directly to the linked Google Drive folder

### Notebook 2 — Model Training (`02_pre_harvest_training_v3.ipynb`)

Trains the v3 pre-harvest XGBoost model on 39 features using Leave-One-Season-Out cross-validation.

**Model performance:**

| Metric            | XGBoost (v3, active) | Random Forest (baseline) |
| ----------------- | -------------------- | ------------------------ |
| LOSO R²          | 0.5484               | 0.4174                   |
| LOSO RMSE         | 7.29 TCH             | 8.28 TCH                 |
| 2025 Holdout R²  | 0.7717               | 0.5393                   |
| 2025 Holdout RMSE | 4.14 TCH             | 5.88 TCH                 |

Top features: `ndvi_may` (1), `surface_prev` (2), `ndvi_growth` (3), `ndvi_jan_may_mean` (4)

Output files saved to Drive `model_v3/`:

- `xgb_model_v3.ubj` — trained XGBoost model
- `rf_model_v3.joblib` — trained Random Forest model
- `feature_cols_v3.json` — ordered feature list (39 features)
- `best_params_v3.json` — tuned hyperparameters

---

## Dataset

**`season_end_data.csv`** — 90 rows, one per region per season (2008–2025).

| Column                | Description                               |
| --------------------- | ----------------------------------------- |
| `season`            | Harvest year (2008–2025)                 |
| `region`            | NORD / SUD / EST / OUEST / CENTRE         |
| `surface_harvested` | Hectares harvested                        |
| `cane_production`   | Tonnes of cane                            |
| `sugar_production`  | Tonnes of sugar                           |
| `tch`               | Tonnes cane per hectare (target variable) |
| `tsh`               | Tonnes sugar per hectare                  |

Extracted from ~500 harvest bulletin PDFs using `model/extract_bulletins.py`. Bulletins sourced from:

- 2020–2025: https://mauritius-chamber-of-agriculture.org/statistics/sugar-sector-2/
- 2008–2019: https://www.msiri.mu/index.php?langue=eng&rub=188

---

## Backend API

The Flask API is live at **https://rekolte.onrender.com**.

All endpoints (except `/api/ping`) require a JWT bearer token obtained via Google OAuth (`POST /api/auth/google`).

| Method | Endpoint                        | Description                                           |
| ------ | ------------------------------- | ----------------------------------------------------- |
| GET    | `/api/ping`                   | Health check                                          |
| POST   | `/api/auth/google`            | Exchange Google ID token → JWT                       |
| GET    | `/api/harvest`                | Historical harvest data (filterable by region/season) |
| GET    | `/api/ndvi/latest`            | Latest pre-harvest NDVI features per region           |
| POST   | `/api/predict`                | Run prediction for a region (`{"region": "NORD"}`)  |
| GET    | `/api/predictions`            | Stored predictions (filterable by region/season)      |
| GET    | `/api/bulletins`              | List uploaded bulletins                               |
| POST   | `/api/bulletins/upload`       | Upload bulletin PDF to Google Drive                   |
| GET    | `/api/models`                 | List model configurations and metrics                 |
| POST   | `/api/models/upload`          | Upload a new model file                               |
| POST   | `/api/models/:id/activate`    | Set a model as active                                 |
| POST   | `/api/reports/generate`       | Generate PDF yield report (download)                  |
| GET    | `/api/notifications`          | Fetch notifications for logged-in user                |
| POST   | `/api/notifications/read-all` | Mark all notifications as read                        |

### Running the API locally

```bash
cd rekolte-api
pip install -r requirements.txt

# Set environment variables:
export MONGO_URI="<MongoDB Atlas connection string>"
export JWT_SECRET="<your secret>"
export GOOGLE_CLIENT_ID="<GCP OAuth client ID>"
export GOOGLE_SERVICE_ACCOUNT_JSON='<service account JSON as single-line string>'

python app.py
```

---

## Frontend

Ionic 8 + Vue 3 SPA with 5 views:

- **Login** — Google OAuth sign-in
- **Dashboard** — Interactive Leaflet choropleth map of Mauritius coloured by predicted TCH
- **Region Detail** — Per-region prediction trigger and feature breakdown
- **Historical Data** — 18-season harvest data with charts; bulletin viewer and upload
- **Model Comparison** — LOSO metrics, holdout performance, feature importance; model upload and activation

The frontend is deployed at **https://yash-booputh.github.io/rekolte/** and connects to the live Render API automatically — no setup needed.

### Running locally (optional)

```bash
cd sugarcane-yield-app
npm install

# Create .env file:
echo "VITE_API_URL=https://rekolte.onrender.com" > .env
echo "VITE_GOOGLE_CLIENT_ID=<GCP OAuth client ID>" >> .env

npm run dev
```

Open http://localhost:5173 and sign in with any Google account. Roles are assigned in MongoDB — new accounts default to `agronomist`.

---

## Using the Dashboard

The live dashboard is at **https://yash-booputh.github.io/rekolte/**

### 1. Sign in

- Click **Sign in with Google** and authenticate with any Google account.
- First-time accounts are assigned the `agronomist` role automatically. To access admin features (model upload, bulletin upload), the account role must be set to `admin` in MongoDB.

### 2. Dashboard

- An interactive choropleth map of Mauritius shows all 5 sugarcane regions coloured by predicted TCH for the current season.
- Hover over a region to see its predicted TCH value.
- Click a region to go directly to its detail page.

### 3. Region Detail

- Shows the latest pre-harvest satellite features for that region (NDVI May, NDVI growth, cyclone wind, ENSO index).
- Click **Run Prediction** to trigger the model and store a new prediction. The result appears immediately with predicted TCH and, if the season is complete, the actual TCH for comparison.

### 4. Historical Data

- Browse cumulative harvest data across all 18 seasons (2008–2025) with line and bar charts.
- Use the region/season filters to narrow down.
- **View Bulletins** — lists all uploaded PDFs; click to preview or download from Google Drive.
- **Upload Bulletin** (admin only) — upload a new harvest bulletin PDF; it is stored in Google Drive and indexed in the database.

### 5. Model Comparison

- Displays LOSO cross-validation metrics and 2025 holdout results for all uploaded models side by side.
- Shows feature importance chart and predicted vs actual scatter plot for the active model.
- **Upload Model** (admin only) — upload a `.ubj` (XGBoost) or `.joblib` (Random Forest) file.
- **Activate** — sets a model as active; all subsequent predictions use it.

### 6. Notifications

- The bell icon in the navbar shows unread notifications (new predictions, bulletin uploads).
- Click to mark as read.

---

## Tech Stack

| Layer          | Technology                                                     |
| -------------- | -------------------------------------------------------------- |
| Satellite data | Google Earth Engine (MODIS, Landsat, Sentinel-2, CHIRPS, ERA5) |
| ML             | scikit-learn (Random Forest), XGBoost                          |
| Backend        | Flask + gunicorn, Python 3.11                                  |
| Database       | MongoDB Atlas (free M0)                                        |
| File storage   | Google Drive (service account)                                 |
| Auth           | Google OAuth 2.0 + JWT                                         |
| Frontend       | Ionic 8, Vue 3, Vite, Tailwind CSS                             |
| Maps           | Leaflet.js                                                     |
| Charts         | Chart.js + vue-chartjs                                         |
| Hosting (API)  | Render.com (free tier)                                         |
| PDF reports    | ReportLab                                                      |
