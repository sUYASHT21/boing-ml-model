import streamlit as st
import pandas as pd
import os
import urllib.parse
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(page_title="Vendor Risk & Performance Dashboard", layout="wide")

raw_password = os.getenv('SUPABASE_PASSWORD', '')
SUPABASE_PASSWORD = urllib.parse.quote_plus(raw_password)

SUPABASE_URI = f"postgresql://postgres.aapsfndsgoepmlsefosq:{SUPABASE_PASSWORD}@aws-1-ap-northeast-1.pooler.supabase.com:5432/postgres"

@st.cache_data(ttl=3600)
def load_data():
    engine = create_engine(SUPABASE_URI)
    query = "SELECT * FROM v2_ml_training_data"
    df = pd.read_sql(query, engine)
    

    df['Delay_Days'] = df['Delivered in Full Days'] - df['Requested Lead Time']
    return df

def main():
    st.title("Vendor Risk & Performance Dashboard")
    st.markdown("Automated historical analysis of vendor delivery reliability and expected head times.")
    
    try:
        df = load_data()
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return

    vendor_stats = df.groupby('Vendor Name - ID').agg(
        Total_Orders=('Vendor Name - ID', 'count'),
        Avg_Requested_Days=('Requested Lead Time', 'mean'),
        Avg_Actual_Days=('Delivered in Full Days', 'mean'),
        Avg_Delay=('Delay_Days', 'mean')
    ).reset_index()
    
    vendor_stats['Avg_Requested_Days'] = vendor_stats['Avg_Requested_Days'].round(0).astype(int)
    vendor_stats['Avg_Actual_Days'] = vendor_stats['Avg_Actual_Days'].round(0).astype(int)
    vendor_stats['Avg_Delay'] = vendor_stats['Avg_Delay'].round(0).astype(int)
    
    def categorize_vendor(delay):
        if delay <= 0:
            return "🟢 Reliable (On Time / Early)"
        elif 1 <= delay <= 10:
            return "🟡 Late (1-10 Days)"
        else:
            return "🔴 Critically Late (11+ Days)"
            
    def categorize_speed(days):
        if days <= 30:
            return "⚡ Fast (≤ 30 Days)"
        elif days <= 90:
            return "⏱️ Standard (31-90 Days)"
        else:
            return "🐢 Slow (91+ Days)"
            
    vendor_stats['Risk Category'] = vendor_stats['Avg_Delay'].apply(categorize_vendor)
    vendor_stats['Speed Category'] = vendor_stats['Avg_Actual_Days'].apply(categorize_speed)
    
    col1, col2, col3 = st.columns(3)
    col1.metric("🟢 Reliable Vendors", len(vendor_stats[vendor_stats['Avg_Delay'] <= 0]))
    col2.metric("🟡 Late Vendors", len(vendor_stats[(vendor_stats['Avg_Delay'] > 0) & (vendor_stats['Avg_Delay'] <= 10)]))
    col3.metric("🔴 Critical Vendors", len(vendor_stats[vendor_stats['Avg_Delay'] > 10]))
    
    st.markdown("---")
    
    st.subheader("📊 Fleet-Wide Vendor Analytics")
    chart_col1, chart_col2 = st.columns(2)
    
    with chart_col1:
        st.markdown("**Risk Distribution (Delay)**")
        risk_counts = vendor_stats['Risk Category'].value_counts()
        st.bar_chart(risk_counts)
        
    with chart_col2:
        st.markdown("**Delivery Speed Distribution (Head Time)**")
        speed_counts = vendor_stats['Speed Category'].value_counts()
        st.bar_chart(speed_counts)
    
    st.markdown("---")
    
    display_df = vendor_stats[['Risk Category', 'Vendor Name - ID', 'Total_Orders', 'Avg_Requested_Days', 'Avg_Actual_Days', 'Avg_Delay']]
    display_df.columns = [
        'Risk Category', 
        'Vendor Name', 
        'Total Historical Orders', 
        'Average Contract Deadline', 
        'Expected Delivery (Head Time)', 
        'Average Delay (Days)'
    ]
    
    tab1, tab2, tab3, tab4 = st.tabs([
        "🟢 Ranked by Reliability", 
        "⚡ Fastest Overall", 
        "🔴 Critical (Late)", 
        "🐢 Slowest (Head Time Warning)"
    ])
    
    with tab1:
        st.subheader("Most Reliable Vendors")
        st.write("Sorted by lowest average delay. They consistently hit their contract deadlines.")
        rel_df = display_df.sort_values(by='Average Delay (Days)').reset_index(drop=True)
        rel_df.index = rel_df.index + 1
        st.dataframe(rel_df, use_container_width=True, height=400)

    with tab2:
        st.subheader("Fastest Overall Vendors")
        st.write("Sorted by lowest Expected Delivery (Head Time). Best for urgent orders.")
        fast_df = display_df.sort_values(by='Expected Delivery (Head Time)').reset_index(drop=True)
        fast_df.index = fast_df.index + 1
        st.dataframe(fast_df, use_container_width=True, height=400)

    with tab3:
        st.subheader("Critical Risk: Consistently Late")
        st.write("Vendors averaging 11+ days late. Highest risk of missing deadlines.")
        crit_df = display_df[display_df['Risk Category'].str.contains("🔴")]
        
        if not crit_df.empty:
            crit_df = crit_df.sort_values(by='Average Delay (Days)', ascending=False).reset_index(drop=True)
            crit_df.index = crit_df.index + 1
            st.dataframe(crit_df, use_container_width=True, height=400)
        else:
            st.success("No vendors are currently in the critical delay category.")
            
    with tab4:
        st.subheader("Critical Risk: Slowest Head Times")
        st.write("Vendors with the longest overall delivery times, regardless of whether they hit their contract deadlines.")
        slow_df = display_df.sort_values(by='Expected Delivery (Head Time)', ascending=False).reset_index(drop=True)
        slow_df.index = slow_df.index + 1
        st.dataframe(slow_df, use_container_width=True, height=400)

if __name__ == "__main__":
    main()