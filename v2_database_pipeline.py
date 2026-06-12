import pandas as pd
import os
from sqlalchemy import create_engine
from sqlalchemy.engine import URL
from dotenv import load_dotenv

# Load the hidden environment variables
load_dotenv()

INPUT_FILE = os.getenv('RAW_DATA_PATH', 'raw_data.xlsx')
OUTPUT_FILE = os.getenv('CLEAN_DATA_PATH', 'v2_ml_ready_features.csv')

# Safely pull the password from .env
raw_password = os.getenv('SUPABASE_PASSWORD', '')

# Construct the Supabase URI using SQLAlchemy's secure URL builder
SUPABASE_URI = URL.create(
    drivername="postgresql",
    username="postgres.aapsfndsgoepmlsefosq",
    password=raw_password, 
    host="aws-1-ap-northeast-1.pooler.supabase.com",
    port=5432,
    database="postgres"
)

def main():
    print("\n" + "="*50)
    print("STARTING VERSION 2.0 DATA PIPELINE")
    print("="*50)

    print("Loading raw data...")
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

    print("Engineering new AI features...")
    
    df['SCHED_LINE_CRT_DATE'] = pd.to_datetime(df['SCHED_LINE_CRT_DATE'], errors='coerce')
    df['Order_Month'] = df['SCHED_LINE_CRT_DATE'].dt.month
    df['Order_Month'] = df['Order_Month'].fillna(1) 

    vendor_avg = df.groupby('Vendor Name - ID')['Delivered in Full Days'].transform('mean')
    df['Vendor_Historical_Avg_Days'] = vendor_avg.round(1)

    df = df.drop(columns=['SCHED_LINE_CRT_DATE'])

    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Cleaned V2 data saved locally: {df.shape[0]} rows ready for Machine Learning.")

    try:
        print("Pushing V2 data to Supabase (Creating new v2_ml_training_data table)...")
        engine = create_engine(SUPABASE_URI)
        
        df.to_sql('v2_ml_training_data', engine, if_exists='replace', index=False)
        
        print("SUCCESS! V2 Data is now live in the Cloud.")
    except Exception as e:
        print(f"Failed to write to Supabase: {e}")

if __name__ == "__main__":
    main()