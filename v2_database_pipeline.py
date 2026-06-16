import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

load_dotenv()

INPUT_FILE = os.getenv('RAW_DATA_PATH', 'raw_data.xlsx')
OUTPUT_FILE = os.getenv('CLEAN_DATA_PATH', 'v4_ml_ready_features.csv')

raw_password = os.getenv('SUPABASE_PASSWORD', '')

SUPABASE_URI = URL.create(
    drivername="postgresql",
    username="postgres.aapsfndsgoepmlsefosq",
    password=raw_password, 
    host="aws-1-ap-northeast-1.pooler.supabase.com",
    port=5432,
    database="postgres"
)

def get_max_date(engine):
    try:
        query = 'SELECT MAX("Delivery_Date") as max_date FROM v2_ml_training_data'
        result = pd.read_sql(query, engine)
        max_date = result['max_date'].iloc[0]
        return pd.to_datetime(max_date) if pd.notnull(max_date) else None
    except Exception:
        return None

def main():
    print("\n" + "="*50)
    print("STARTING V4.0 DELTA-LOAD DATA PIPELINE")
    print("="*50)

    engine = create_engine(SUPABASE_URI)
    max_db_date = get_max_date(engine)
    
    if max_db_date:
        print(f"Cloud Database found. Latest delivery date on record: {max_db_date.date()}")
    else:
        print("No existing data found in Cloud. Proceeding with full initial load.")

    print("Loading raw Master Sheet...")
    try:
        df = pd.read_excel(INPUT_FILE, engine='openpyxl')
    except FileNotFoundError:
        print(f"Error: Could not find the file at {INPUT_FILE}")
        return

    cols_to_keep = [
        'Vendor Name - ID', 
        'Program (MG4)', 
        'Requested Lead Time',
        'SCHED_LINE_CRT_DATE',
        'Delivered in Full Days'
    ]
    
    missing_cols = [col for col in cols_to_keep if col not in df.columns]
    if missing_cols:
        print(f"Error: Missing columns in raw data: {missing_cols}")
        return
        
    df = df[cols_to_keep].copy()
    
    print("Cleaning Data...")
    df = df.dropna(subset=['Delivered in Full Days', 'Requested Lead Time'])
    df = df[df['Delivered in Full Days'] >= 0]
    df = df[df['Requested Lead Time'] >= 0]

    df['Vendor Name - ID'] = df['Vendor Name - ID'].fillna('Unknown')
    df['Program (MG4)'] = df['Program (MG4)'].fillna('Unknown')

    print("Engineering time-series features...")
    df['SCHED_LINE_CRT_DATE'] = pd.to_datetime(df['SCHED_LINE_CRT_DATE'], errors='coerce')
    df['Delivery_Date'] = df['SCHED_LINE_CRT_DATE'] + pd.to_timedelta(df['Delivered in Full Days'], unit='D')

    vendor_avg = df.groupby('Vendor Name - ID')['Delivered in Full Days'].transform('mean')
    df['Vendor_Historical_Avg_Days'] = vendor_avg.round(1)

    if max_db_date:
        original_count = len(df)
        df = df[df['Delivery_Date'] > max_db_date].copy()
        new_count = len(df)
        print(f"Delta Filter: Ignored {original_count - new_count} historical rows. Found {new_count} net-new rows.")
        
        if new_count == 0:
            print("SUCCESS: Database is already up to date. No new data to push.")
            return
        sql_behavior = 'append'
    else:
        sql_behavior = 'replace'

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Cleaned delta data saved locally: {df.shape[0]} rows ready.")

    try:
        print(f"Pushing delta data to Supabase (Mode: {sql_behavior.upper()})...")
        df.to_sql('v2_ml_training_data', engine, if_exists=sql_behavior, index=False)
        print("SUCCESS! Delta Data is now live in the Cloud.")
    except Exception as e:
        print(f"Failed to write to Supabase: {e}")

if __name__ == "__main__":
    main()