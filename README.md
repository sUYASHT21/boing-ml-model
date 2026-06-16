# 📊 Vendor Risk & Performance Dashboard (V4)

An enterprise-grade Business Intelligence and Machine Learning application designed to automate historical vendor performance analysis and predict future order delivery dates.

## 🚀 Overview
This application replaces manual spreadsheet tracking with a fully automated, cloud-hosted dashboard. It provides fleet-wide vendor risk assessment, isolates individual vendor improvement trends month-over-month, and uses a trained AI model to predict exact delivery dates for new purchase orders.

---

## ✨ Core Features

### 1. Fleet-Wide Analytics
* **Risk Categorization:** Automatically segments vendors into Reliable, Late, and Critical Risk categories based on their historical ability to meet contract deadlines.
* **Speed Tracking:** Tracks "Head Time" (expected delivery speed) to highlight the fastest overall suppliers for urgent orders.
* **Dynamic Time Filters:** Users can instantly slice the data by Last 30 Days, Last Quarter, Last Year, or any custom date range.

### 2. Vendor Deep Dive
* **Comparative Improvement Tracking:** Isolates a single supplier and graphs their average delay month-over-month to visualize operational improvement or degradation over time.

### 3. Live ML Predictions
* **AI Lead Time Predictor:** Uses a pre-trained Random Forest algorithm (`v2_rf_model.pkl`) to predict the exact delivery date of a new order. 
* **Smart Defaults:** The user simply selects the Vendor, the Contract Deadline, and the Order Date. The system automatically pulls the vendor's historical average and primary program from the cloud database to generate an accurate prediction without requiring manual data entry.

---

## 🔄 Data Maintenance & Updates (Delta Load)

The backend data pipeline (`v2_database_pipeline.py`) is engineered with **Smart Delta Load** architecture. This means it automatically protects the database from duplicate entries and prevents accidental data deletion.

### Step 1: Formatting the Excel File
When updating the dashboard with a new month of data, the file **must** meet these requirements:
* Named exactly: `raw_data.xlsx`
* Placed in the main project folder.
* Must contain the following column headers exactly as written:
  * `Vendor Name - ID`
  * `Program (MG4)`
  * `Requested Lead Time`
  * `SCHED_LINE_CRT_DATE`
  * `Delivered in Full Days`

### Step 2: Running the Pipeline
You do not need to manually separate old data from new data. 

When you receive new data, simply download the client's updated Master Excel Sheet (containing all old and new data), name it `raw_data.xlsx`, and run the following command in your terminal:
`python3 v2_database_pipeline.py`

**How the Delta Load Works:**
1. The script pings the cloud database and finds the absolute latest delivery date currently on record (e.g., April 30th).
2. It scans the new `raw_data.xlsx` file and throws away every row that happened on or before April 30th.
3. It takes only the net-new rows (May 1st onward) and safely appends them to the cloud database.
4. If you accidentally run the same file twice, the pipeline will recognize there is no new data and safely abort without creating duplicates.

---

## 🛠️ Technical Architecture
* **Frontend:** Streamlit (Python)
* **Backend Database:** Supabase (Cloud PostgreSQL)
* **Data Processing:** Pandas, SQLAlchemy
* **Machine Learning:** Scikit-Learn (Random Forest Regressor, ColumnTransformer, OneHotEncoder)
* **Deployment:** Streamlit Community Cloud