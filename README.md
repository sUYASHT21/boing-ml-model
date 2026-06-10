# Predictive Lead Time Engine (V2)

This repository contains the machine learning pipeline and Streamlit dashboard for predicting supply chain vendor lead times.

## ⚠️ What to Change Before Running
Before running the scripts on a new machine, open the code files and update the file paths to match your local system:
1. **`v2_database_pipeline.py`**: Update `INPUT_FILE` to point to the raw `.xlsx` data file, and `OUTPUT_FILE` to where you want the clean CSV saved.
2. **`v2_model_training.py`**: Update `INPUT_FILE` to point to the clean CSV, and `MODEL_OUTPUT` to where you want the `.pkl` file saved.
3. **`v2_app.py`**: Update `DATA_PATH` (clean CSV) and `MODEL_PATH` (`.pkl` file).

## 🛠️ Installation Requirements
Run this command in your terminal to install the required libraries:
```bash
pip install pandas scikit-learn streamlit sqlalchemy openpyxl psycopg2-binary