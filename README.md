## System Architecture & File Structure

The pipeline is split into three distinct stages. **They must be executed in order.**

### 1. Data Engineering & Database Pipeline (`v2_database_pipeline.py`)
* **What it does:** Ingests raw historical Excel data, removes data leakage columns, engineers predictive KPIs (like `Vendor_Historical_Avg_Days`), and syncs the clean data to a Supabase (PostgreSQL) cloud database.
* **Outputs:** * Saves a local file: `v2_ml_ready_features.csv`
  * Updates the cloud database table: `v2_ml_training_data`

### 2. AI Model Training (`v2_model_training.py`)
* **What it does:** Loads the cleaned CSV data and trains a highly accurate **Random Forest Regressor** (R² Score: 0.95). It learns vendor behaviors, seasonal trends, and requested deadline impacts.
* **Outputs:** * Saves the trained model weights as: `v2_rf_model.pkl`

### 3. Interactive UI / Dashboard (`v2_app.py`)
* **What it does:** Launches a reactive Streamlit web application. It consumes the trained `.pkl` model and the `.csv` data to provide real-time calendar date predictions and a smart-sorted Vendor Leaderboard.

---

## Configuration (Crucial First Step)
Before running the pipeline on your local machine, you must open the Python files and update the absolute file paths to match your system directory.

**In `v2_database_pipeline.py`:**
* Change `INPUT_FILE` to the path of your raw `.xlsx` data.
* Change `OUTPUT_FILE` to the path where you want the clean `.csv` saved.

**In `v2_model_training.py`:**
* Change `INPUT_FILE` to the exact path of the `.csv` created in step 1.
* Change `MODEL_OUTPUT` to the path where you want the `.pkl` saved.

**In `v2_app.py`:**
* Change `DATA_PATH` to the `.csv` path.
* Change `MODEL_PATH` to the `.pkl` path.

---

## Installation Requirements
Run this command in your terminal to install the necessary Python libraries:
```bash
pip install pandas scikit-learn streamlit sqlalchemy openpyxl psycopg2-binary