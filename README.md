# Vendor Risk & Performance Dashboard

An automated Business Intelligence (BI) dashboard that analyzes historical vendor delivery data to calculate actual "Head Times" (expected delivery delays) and categorize supply chain risks.

---

## System Architecture & File Structure

### 1. Data Engineering & Database Pipeline (`v2_database_pipeline.py`)
* **What it does:** Ingests raw historical Excel data, engineers predictive KPIs (like `Vendor_Historical_Avg_Days`), and syncs the clean data to a Supabase (PostgreSQL) cloud database.
* **Outputs:** * Saves a local file: `v2_ml_ready_features.csv`
  * Updates the cloud database table: `v2_ml_training_data`

### 2. Interactive BI Dashboard (`v2_app.py`)
* **What it does:** Launches a zero-input, reactive Streamlit web application. It consumes the cleaned `.csv` data to provide a dynamic 4-tab Vendor Leaderboard, sorting vendors by Reliability, Velocity, and Critical Risk, alongside side-by-side visual analytics.

### 3. AI Model Training (`v2_model_training.py` - Optional)
* **What it does:** An offline script that trains a Random Forest Regressor on the historical data. *(Note: This predictive model is preserved for architectural reference, but the primary dashboard has been pivoted to a pure BI logic model based on stakeholder requirements).*

## Data Paths
```bash
RAW_DATA_PATH=/path/to/your/raw_data.xlsx
CLEAN_DATA_PATH=/path/to/your/v2_ml_ready_features.csv
MODEL_PATH=/path/to/your/v2_rf_model.pkl
```

## Database Secrets
```bash
SUPABASE_PASSWORD=your_database_password_here
SUPABASE_URI=your_url
```
---
## Launch the Dashboard
```bash
python3 -m streamlit run v2_app.py
```

## 1. Installation Requirements
Run this command in your terminal to install the necessary Python libraries:
```bash
pip3 install pandas streamlit python-dotenv sqlalchemy openpyxl scikit-learn